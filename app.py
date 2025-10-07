import json
import os
from flask import Flask, Response, send_from_directory
from flask import render_template, request, jsonify
from scripts.audio_manager import AudioManager, AudioPlayer
from scripts.background_mnager import BackgroundManager
from pathlib import Path

BASE_DIR = Path(__name__).resolve().parent
AUTH_KEY = "3f9a7b2c1d8e4f6a0b9c2d7e8f1a3b"

blank_data = {"t": 0, "mod": 1}
with open("save-data.json", "w") as file:
    file.write(json.dumps(blank_data))

app = Flask(__name__, static_url_path="/static")
audioManager = AudioManager(BASE_DIR)
backgroundManager = BackgroundManager(BASE_DIR, 100)
print(backgroundManager.background_path)

audioPlayer = AudioPlayer(audioManager)
audioPlayer.start()
backgroundManager.start()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/upload-song", methods=["POST"])
def upload_song():
    if request.headers.get("auth", "null") != AUTH_KEY:
        return "Authorizaion Failed"
    json_data = request.get_json()
    save_name = request.headers.get("file-name", None)
    audioManager.save_song_data(json_data, save_name)
    return "Success"


@app.route("/update-songs-list")
def update_songs_list():
    if request.headers.get("auth", "null") != AUTH_KEY:
        return "Authorizaion Failed"
    audioManager.update_songs_list()
    return "Success"


@app.route("/get-songs-list")
def get_song_list():
    if request.headers.get("auth", "null") != AUTH_KEY:
        return jsonify([])
    return jsonify(audioManager.song_list)


@app.route("/delete-all-songs")
def delete_all_songs():
    if request.headers.get("auth", "null") != AUTH_KEY:
        return "Shit!"
    suc = audioManager.delete_all_songs()
    return f"Shit!! {suc}"


@app.route("/delete-song")
def delete_songs():
    if request.headers.get("auth", "null") != AUTH_KEY:
        return "Shit!"
    suc = audioManager.delete_song(request.headers.get("song-path", "null"))
    return f"Shit!! {suc}"


@app.route("/restart-player")
def restart_player():
    if request.headers.get("auth", "null") != AUTH_KEY:
        return "failed to restart"
    audioPlayer.restart_player()
    return f"player restarted"


# public urls
@app.route("/get-song")
def get_song():
    if audioPlayer.current_song:
        print("current song request success")
        return Response(audioPlayer.current_song.song_json, mimetype="application/json")
    else:
        print("current song request failed")
        return jsonify({"error": True})


@app.route("/get-position")
def get_position():
    try:
        with open("save-data.json", "r") as fi:
            return Response(fi.read(), mimetype="application/json")
    except:
        return jsonify(blank_data)

@app.route("/get-additional-data")
def get_additional_data():
    return jsonify(
        {
            "bi": backgroundManager.current_background_index,
            "si": audioPlayer.current_song_index,
        }
    )


# if __name__ == "__main__":
#    app.run("0.0.0.0", debug=True)
