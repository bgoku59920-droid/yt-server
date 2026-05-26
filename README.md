# YT Stream Server

Free YouTube audio stream server using yt-dlp + Flask.
Deploy on Render.com free tier.

## Endpoints
GET /stream?id=VIDEO_ID   → { url, title, artist, thumbnail, duration }
GET /search?q=QUERY       → { results: [...] }
GET /ping                 → { pong: true }

## Deploy on Render.com
1. Push this folder to a GitHub repo
2. Go to render.com → New → Web Service
3. Connect your GitHub repo
4. Build command: pip install -r requirements.txt
5. Start command: gunicorn main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 60
6. Click Deploy
