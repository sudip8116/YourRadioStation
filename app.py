from flask import Flask, request, jsonify
import yt_dlp

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "status": "ok",
        "routes": ["/search?q=", "/get-url?url="]
    })


@app.route("/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify({"error": "q parameter missing"}), 400

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(f"ytsearch10:{query}", download=False)

    videos = []
    for v in result.get("entries", []):
        videos.append({
            "title": v.get("title"),
            "url": f"https://www.youtube.com/watch?v={v.get('id')}",
            "duration": v.get("duration"),
            "channel": v.get("uploader")
        })

    return jsonify(videos)


@app.route("/get-url", methods=["POST"])
def get_audio_url():
    data = request.get_json(silent=True) or {}
    video_url = data.get("url")

    if not video_url:
        return jsonify({"error": "url parameter missing"}), 400

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "format": "bestaudio/best"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

    return jsonify({
        "title": info.get("title"),
        "audio_url": info["url"],
        "ext": info.get("ext"),
        "filesize": info.get("filesize")
    })
