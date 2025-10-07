import os
import json
from random import randint
from threading import Thread, Lock
from time import sleep, time
import uuid


class Song:
    def __init__(self, song_json: str):
        self.song_json = song_json
        try:
            self.song: dict = json.loads(song_json)
            self.duration = self.format_duration(self.song.get("duration", "0"))
            self.title = self.song.get("title", "Unknown Title")
            self.artist = self.song.get("artist", "Unknown Artist")
        except json.JSONDecodeError:
            raise ValueError("Invalid song JSON format")

        self.start_time = {"t": 0, "mod": 1}

    def format_duration(self, duration: str):
        try:
            parts = list(map(int, duration.strip().split(":")))
            sec = 0
            for p in parts:
                sec = sec * 60 + p
            return sec
        except (ValueError, AttributeError):
            return 0

    def set_start_time(self, mod: int):
        self.start_time["t"] = time() % mod
        self.start_time["mod"] = mod


class AudioPlayer:
    def __init__(
        self, pos_data, song_index_data, audioManager: "AudioManager", mod=100000
    ):
        self.pos_data = pos_data
        self.song_index_data = song_index_data
        self.audioManager = audioManager
        self.mod = mod
        self.playing_index = 0
        self.current_song_index = 0
        self.running = False
        self.time_thread = None
        self.current_song: Song = None
        self.current_time = 0
        self.lock = Lock()
        self.playback_callbacks = []

    def start(self):
        if self.time_thread and self.time_thread.is_alive():
            return

        self.running = True
        self.time_thread = Thread(target=self.__start_thread, daemon=True)
        self.time_thread.start()
        self.load_song()

    def stop(self):
        self.running = False
        if self.time_thread and self.time_thread.is_alive():
            self.time_thread.join(timeout=5)

    def add_playback_callback(self, callback):
        self.playback_callbacks.append(callback)

    def _notify_callbacks(self, event_type, data=None):
        for callback in self.playback_callbacks:
            try:
                callback(event_type, data)
            except Exception:
                pass

    def restart_player(self):
        self.playing_index = 0
        self.stop()
        self.start()

    def load_song(self):
        suc, song = self.audioManager.get_song_data(self.playing_index)
        if suc:
            try:
                self.current_song = Song(song)
                self.current_song.set_start_time(self.mod)
                self.pos_data.write(json.dumps(self.current_song.start_time))
                self.current_song_index = randint(1111, 9999)
                self.song_index_data.write(json.dumps({"si": self.current_song_index}))
                self.current_time = 0
                self._notify_callbacks(
                    "song_changed",
                    {"song": self.current_song, "index": self.playing_index},
                )
            except ValueError:
                self._load_next_song()
        else:
            self._load_next_song()

    def _load_next_song(self):
        if self.audioManager.song_list:
            self.playing_index = randint(0, len(self.audioManager.song_list) - 1)
            self.load_song()

    def skip_song(self):
        self._load_next_song()

    def __start_thread(self):
        self.current_time = 0
        while self.running:
            if not self.current_song:
                self.load_song()
                continue

            self.current_time += 1
            self._notify_callbacks(
                "time_update",
                {
                    "current_time": self.current_time,
                    "total_duration": self.current_song.duration,
                },
            )

            if self.current_time >= self.current_song.duration:
                self._load_next_song()
                self.current_time = 0

            sleep(1)

    def get_current_time(self):
        return self.current_song.start_time

    def get_playback_progress(self):
        if self.current_song and self.current_song.duration > 0:
            return (self.current_time / self.current_song.duration) * 100
        return 0


class AudioManager:
    def __init__(self, base_dir: str):
        self.audio_path = base_dir / "audios/"
        self.song_list = []
        self.ensure_audio_directory()
        self.update_songs_list()

    def ensure_audio_directory(self):
        os.makedirs(self.audio_path, exist_ok=True)

    def update_songs_list(self):
        try:
            self.song_list = [
                os.path.join(self.audio_path, f)
                for f in os.listdir(self.audio_path)
                if f.endswith(".json")
            ]
        except OSError:
            self.song_list = []

    def save_song_data(self, song_data, save_name=None):
        if not save_name:
            save_name = f"{self.generate_hash()}.json"

        file_path = os.path.join(self.audio_path, save_name)
        try:
            json.loads(song_data)
            with open(file_path, "w") as file:
                file.write(song_data)
            self.update_songs_list()
            return True
        except (json.JSONDecodeError, IOError):
            return False

    def delete_all_songs(self):
        try:
            for file in os.listdir(self.audio_path):
                if file.endswith(".json"):
                    os.remove(os.path.join(self.audio_path, file))
            self.update_songs_list()
            return True
        except OSError:
            return False

    def delete_song(self, song_path):
        try:
            if os.path.exists(song_path) and song_path in self.song_list:
                os.remove(song_path)
                self.update_songs_list()
                return True
            return False
        except OSError:
            return False

    def generate_hash(self):
        return uuid.uuid4().hex

    def get_song_data(self, index):
        if not self.song_list:
            return False, "null"

        if index < 0 or index >= len(self.song_list):
            return False, "null"

        song_path = self.song_list[index]
        try:
            with open(song_path, "r") as file:
                song_data = file.read()
            return True, song_data
        except IOError:
            return False, "null"

    def get_song_count(self):
        return len(self.song_list)

    def validate_song_json(self, song_json):
        try:
            song_data = json.loads(song_json)
            required_fields = ["duration", "title"]
            for field in required_fields:
                if field not in song_data:
                    return False, f"Missing required field: {field}"
            return True, "Valid"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
