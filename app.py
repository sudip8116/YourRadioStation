import json
import os
from flask import Flask, Response, send_from_directory
from flask import render_template, request, jsonify
from scripts.audio_manager import AudioManager, AudioPlayer
from scripts.background_mnager import BackgroundManager
from pathlib import Path

BASE_DIR = Path(__name__).resolve().parent
AUTH_KEY = "3f9a7b2c1d8e4f6a0b9c2d7e8f1a3b"


class Data:
    def __init__(self, file: str, default: dict):

        self.default = json.dumps(default)
        self.file = file
        with open(file, "w") as f:
            f.write(self.default)

    def write(self, value):
        with open(self.file, "w") as f:
            f.write(value)

    def read(self):
        try:
            with open(self.file, "r") as f:
                return f.read()
        except:
            return self.default


app = Flask(__name__, static_url_path="/static")
pos_data = Data("pos-data.json", {"t": 0, "mod": 1})
back_index_data = Data("back-index.josn", {"bi": 1})
song_index_data = Data("song-index.json", {"si": 0})


audioManager = AudioManager(BASE_DIR)
backgroundManager = BackgroundManager(back_index_data, BASE_DIR, 100)
audioPlayer = AudioPlayer(pos_data, song_index_data, audioManager)
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
    return Response(pos_data.read(), mimetype="application/json")


@app.route("/get-song-index")
def get_song_index():
    return Response(song_index_data.read(), mimetype="application/json")


@app.route("/get-background-index")
def get_background_index():
    return Response(back_index_data.read(), mimetype="application/json")


# if __name__ == "__main__":
#    app.run("0.0.0.0", debug=True)
