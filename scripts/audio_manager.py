import os
import json
from random import choice, randint
from threading import Thread, Lock
from time import sleep, time
from datetime import datetime
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Song:
    def __init__(self, song_json: str):
        self.song_json = song_json
        try:
            self.song: dict = json.loads(song_json)
            self.duration = self.format_duration(self.song.get("duration", "0"))
            self.title = self.song.get("title", "Unknown Title")
            self.artist = self.song.get("artist", "Unknown Artist")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse song JSON: {e}")
            raise ValueError("Invalid song JSON format")

        self.start_time = {"t": 0, "mod": 1}

    def format_duration(self, duration: str):
        """Convert duration string (MM:SS or HH:MM:SS) to seconds"""
        try:
            parts = list(map(int, duration.strip().split(":")))
            sec = 0
            for p in parts:
                sec = sec * 60 + p
            return sec
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid duration format '{duration}', using 0: {e}")
            return 0

    def set_start_time(self, mod: int):
        self.start_time["t"] = time() % mod
        self.start_time["mod"] = mod

    def get_formatted_duration(self):
        """Return duration in MM:SS format"""
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"


class AudioPlayer:
    def __init__(self, audioManager: "AudioManager", mod=100000):
        self.audioManager = audioManager
        self.mod = mod
        self.playing_index = 0
        self.current_song_index = 0
        self.running = False
        self.time_thread = None
        self.current_song: Song = None
        self.current_time = 0
        self.lock = Lock()  # Thread safety for shared variables
        self.playback_callbacks = []

    def start(self):
        """Start the audio player thread"""
        if self.time_thread and self.time_thread.is_alive():
            logger.info("Audio player already running")
            return

        self.running = True
        self.time_thread = Thread(
            target=self.__start_thread, daemon=True, name="AudioPlayerThread"
        )
        self.time_thread.start()
        self.load_song()
        logger.info("Audio player started")

    def stop(self):
        """Stop the audio player thread"""
        self.running = False
        if self.time_thread and self.time_thread.is_alive():
            self.time_thread.join(timeout=5)  # Add timeout to prevent hanging
        logger.info("Audio player stopped")

    def add_playback_callback(self, callback):
        """Add callback for playback events (song change, time update)"""
        self.playback_callbacks.append(callback)

    def _notify_callbacks(self, event_type, data=None):
        """Notify all registered callbacks of playback events"""
        for callback in self.playback_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def restart_player(self):
        """Restart the player from the beginning"""
        self.playing_index = 0
        self.stop()
        self.start()

    def load_song(self):
        """Load a song at the current playing index"""
        logger.info("Loading song...")
        suc, song = self.audioManager.get_song_data(self.playing_index)
        if suc:
            try:
                self.current_song = Song(song)
                self.current_song.set_start_time(self.mod)
                self.current_song_index = randint(1111, 9999)
                self.current_time = 0
                logger.info(f"Song started at {self.current_song.start_time}")
                self._notify_callbacks(
                    "song_changed",
                    {"song": self.current_song, "index": self.playing_index},
                )
            except ValueError as e:
                logger.error(f"Failed to load song: {e}")
                self._load_next_song()
        else:
            logger.warning("Failed to get song data, loading next song")
            self._load_next_song()

    def _load_next_song(self):
        """Load a random next song"""
        if self.audioManager.song_list:
            self.playing_index = randint(0, len(self.audioManager.song_list) - 1)
            self.load_song()
        else:
            logger.warning("No songs available in playlist")

    def skip_song(self):
        """Skip to the next song"""
        self._load_next_song()

    def __start_thread(self):
        """Main playback thread"""
        self.current_time = 0
        while self.running:
            if not self.current_song:
                logger.info("No current song, loading...")
                self.load_song()
                continue

            # Update current time
            self.current_time += 1

            # Notify time update
            self._notify_callbacks(
                "time_update",
                {
                    "current_time": self.current_time,
                    "total_duration": self.current_song.duration,
                },
            )

            # Check if song ended
            if self.current_time >= self.current_song.duration:
                logger.info("Song ended, loading next...")
                self._load_next_song()
                self.current_time = 0
            else:
                logger.debug(
                    f"Playing index: {self.playing_index} | "
                    f"Time: {self.current_time}/{self.current_song.duration} | "
                    f"Song index: {self.current_song_index}"
                )

            sleep(1)

    def get_current_time(self):
        """Get current playback information"""
        return self.current_song.start_time

    def get_playback_progress(self):
        """Get playback progress as percentage"""
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
        """Ensure the audio directory exists"""
        os.makedirs(self.audio_path, exist_ok=True)

    def update_songs_list(self):
        """Update the list of available songs"""
        try:
            self.song_list = [
                os.path.join(self.audio_path, f)
                for f in os.listdir(self.audio_path)
                if f.endswith(".json")
            ]
            logger.info(f"Updated songs list: {len(self.song_list)} songs found")
        except OSError as e:
            logger.error(f"Failed to update songs list: {e}")
            self.song_list = []

    def save_song_data(self, song_data, save_name=None):
        """Save song data to a JSON file"""
        if not save_name:
            save_name = f"{self.generate_hash()}.json"

        file_path = os.path.join(self.audio_path, save_name)
        try:
            # Validate JSON before saving
            json.loads(song_data)
            with open(file_path, "w") as file:
                file.write(song_data)
            self.update_songs_list()
            logger.info(f"Song saved: {file_path}")
            return True
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to save song: {e}")
            return False

    def delete_all_songs(self):
        """Delete all song files"""
        try:
            for file in os.listdir(self.audio_path):
                if file.endswith(".json"):
                    os.remove(os.path.join(self.audio_path, file))
            self.update_songs_list()
            logger.info("All songs deleted")
            return True
        except OSError as e:
            logger.error(f"Failed to delete all songs: {e}")
            return False

    def delete_song(self, song_path):
        """Delete a specific song file"""
        try:
            if os.path.exists(song_path) and song_path in self.song_list:
                os.remove(song_path)
                self.update_songs_list()
                logger.info(f"Song deleted: {song_path}")
                return True
            return False
        except OSError as e:
            logger.error(f"Failed to delete song {song_path}: {e}")
            return False

    def generate_hash(self):
        """Generate a unique hash for song files"""
        return uuid.uuid4().hex

    def get_song_data(self, index):
        """Get song data by index"""
        if not self.song_list:
            logger.warning("No songs available")
            return False, "null"

        if index < 0 or index >= len(self.song_list):
            logger.warning(f"Invalid song index: {index}")
            return False, "null"

        song_path = self.song_list[index]
        try:
            with open(song_path, "r") as file:
                song_data = file.read()
            return True, song_data
        except IOError as e:
            logger.error(f"Failed to read song file {song_path}: {e}")
            return False, "null"

    def get_song_count(self):
        """Get total number of songs"""
        return len(self.song_list)

    def validate_song_json(self, song_json):
        """Validate song JSON structure"""
        try:
            song_data = json.loads(song_json)
            required_fields = ["duration", "title"]
            for field in required_fields:
                if field not in song_data:
                    return False, f"Missing required field: {field}"
            return True, "Valid"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"
