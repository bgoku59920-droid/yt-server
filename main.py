from flask import Flask, request, jsonify
import yt_dlp
import threading

app = Flask(__name__)

# ── Keep-alive ping ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return jsonify({"status": "ok", "service": "YT Stream Server"})

@app.route("/ping")
def ping():
    return jsonify({"pong": True})

# ── Stream fetch ──────────────────────────────────────────────────────────────
@app.route("/stream")
def stream():
    video_id = request.args.get("id", "")
    if not video_id:
        return jsonify({"error": "Missing id param"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "format": "bestaudio[ext=webm]/bestaudio[ext=m4a]/bestaudio",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        # Use Android client — most reliable for plain URLs
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "skip": ["hls", "dash"],
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Get best audio URL
        stream_url = None
        best_abr   = 0

        formats = info.get("formats", [])
        for f in formats:
            # Audio only
            if f.get("vcodec", "none") != "none":
                continue
            if not f.get("url"):
                continue
            abr = f.get("abr") or f.get("tbr") or 0
            if abr > best_abr:
                best_abr   = abr
                stream_url = f["url"]

        # Fallback: just use the url directly
        if not stream_url:
            stream_url = info.get("url", "")

        if not stream_url:
            return jsonify({"error": "No stream URL found"}), 404

        # Thumbnail
        thumb = ""
        thumbnails = info.get("thumbnails", [])
        if thumbnails:
            thumb = thumbnails[-1].get("url", "")
        if not thumb:
            thumb = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

        return jsonify({
            "url":       stream_url,
            "title":     info.get("title",    "Unknown"),
            "artist":    info.get("uploader", "Unknown"),
            "thumbnail": thumb,
            "duration":  info.get("duration", 0),
        })

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── Search ────────────────────────────────────────────────────────────────────
@app.route("/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"error": "Missing q param"}), 400

    ydl_opts = {
        "quiet":        True,
        "no_warnings":  True,
        "extract_flat": True,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ytsearch20: = top 20 results
            info = ydl.extract_info(f"ytsearch20:{query}", download=False)

        results = []
        entries = info.get("entries", [])
        for e in entries:
            if not e:
                continue
            vid_id = e.get("id", "")
            if not vid_id:
                continue

            # Duration formatting
            dur_secs = e.get("duration") or 0
            dur_str  = ""
            if dur_secs:
                m = int(dur_secs) // 60
                s = int(dur_secs) % 60
                dur_str = f"{m}:{s:02d}"

            thumb = f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"

            results.append({
                "videoId":   vid_id,
                "title":     e.get("title",    "Unknown"),
                "artist":    e.get("uploader", e.get("channel", "Unknown")),
                "duration":  dur_str,
                "thumbnail": thumb,
            })

        return jsonify({"results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
