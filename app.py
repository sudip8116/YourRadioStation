import pickle
from flask import Flask
from flask import request, render_template, jsonify

from scripts.live_radio import LiveRadio


app = Flask(__name__, static_url_path="/static")
count = [0]


class AudioData:
    def __init__(self):
        self.title = ""
        self.duration = 0
        self.audio = None
        self.thumbnail = None


live_radio = LiveRadio(count)
live_radio.start()

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/get-song")
def get_song():
    return jsonify({"count": count[0]})


# if __name__ == "__main__":
#     app.run(debug=True)
