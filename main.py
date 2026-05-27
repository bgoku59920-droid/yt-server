from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "YT Stream Server"})

@app.route("/ping")
def ping():
    return jsonify({"pong": True})

@app.route("/stream")
def stream():
    video_id = request.args.get("id", "")
    if not video_id:
        return jsonify({"error": "Missing id param"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "cookiefile": "cookies.txt",
        "extractor_args": {
            "youtube": {
                "player_client": ["default", "android"],
                "formats": "missing_pot",
            }
        },
        "socket_timeout": 30,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        stream_url = None
        best_abr = 0
        for f in info.get("formats", []):
            if f.get("vcodec", "none") != "none":
                continue
            if not f.get("url"):
                continue
            abr = f.get("abr") or f.get("tbr") or 0
            if abr > best_abr:
                best_abr = abr
                stream_url = f["url"]

        if not stream_url:
            stream_url = info.get("url", "")
        if not stream_url:
            return jsonify({"error": "No stream URL found"}), 404

        thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        thumbnails = info.get("thumbnails", [])
        if thumbnails:
            thumb = thumbnails[-1].get("url", thumb)

        return jsonify({
            "url":       stream_url,
            "title":     info.get("title",    "Unknown"),
            "artist":    info.get("uploader", "Unknown"),
            "thumbnail": thumb,
            "duration":  info.get("duration", 0),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing q param"}), 400

    ydl_opts = {
        "quiet":         True,
        "no_warnings":   True,
        "extract_flat":  True,
        "skip_download": True,
        "cookiefile":    "cookies.txt",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch20:{query}", download=False)

        results = []
        for e in info.get("entries", []):
            if not e:
                continue
            vid_id = e.get("id", "")
            if not vid_id:
                continue
            dur_secs = e.get("duration") or 0
            dur_str = ""
            if dur_secs:
                m = int(dur_secs) // 60
                s = int(dur_secs) % 60
                dur_str = f"{m}:{s:02d}"
            results.append({
                "videoId":   vid_id,
                "title":     e.get("title",    "Unknown"),
                "artist":    e.get("uploader", e.get("channel", "Unknown")),
                "duration":  dur_str,
                "thumbnail": f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg",
            })

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
