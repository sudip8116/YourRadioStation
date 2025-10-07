class MusicPlayer {
  constructor() {
    this.audioPlayer = document.getElementById("audio-player");
    this.playPauseBtn = document.getElementById("play-pause");
    this.albumArt = document.querySelector("#bar-anim");
    this.album = document.querySelector(".album-art");
    this.progress = document.getElementById("progress");
    this.totalTimeLabel = document.getElementById("total-time");
    this.barAnim = new BarAnimation();
    this.isPlaying = false;
    this.current_song_index = 0;
    this.song_loaded = false;
    this.init();
  }

  formatTime(seconds) {
    const min = Math.floor(seconds / 60);
    const sec = Math.floor(seconds % 60);
    return `${min.toString().padStart(2, "0")}:${sec
      .toString()
      .padStart(2, "0")}`;
  }

  getCurrentSong() {
    this.song_loaded = false;
    fetch("/get-song")
      .then((res) => res.json())
      .then((data) => {
        if ("error" in data) {
          console.log("Error in song loading")
          return;
        }
        console.log("loading song...");
        document.getElementById("song-title").textContent = data.title;
        this.audioPlayer.src = "data:audio/mp3;base64," + data.audio;
        this.albumArt.style.backgroundImage = `url("data:image/png;base64,${data.image}")`;
        this.audioPlayer.volume = 1;
        this.audioPlayer.onloadedmetadata = () => {
          this.totalTimeLabel.textContent = `00:00/${this.formatTime(
            this.audioPlayer.duration
          )}`;
          this.song_loaded = true;
          console.log("song loaded");
          if (this.isPlaying) {
            this.isPlaying = false;
            this.togglePlayPause();
          }
        };
      });
  }

  togglePlayPause() {
    if (!this.song_loaded) return;
    if (!this.isPlaying) {
      this.syncAudio();
      this.audioPlayer.play().catch(console.log);
      this.playPauseBtn.textContent = "❚❚";
      this.album.classList.add("rotate");
      this.barAnim.start();
    } else {
      this.audioPlayer.pause();
      this.playPauseBtn.textContent = "▶";
      this.album.classList.remove("rotate");
      this.barAnim.stop();
    }
    this.isPlaying = !this.isPlaying;
  }

  syncAudio() {
    fetch("/get-position")
      .then((res) => res.json())
      .then((data) => {
        console.log(data);
        console.log((Date.now() / 1000) % data.mod);
        const currTime = ((Date.now() / 1000) % data.mod) - data.t;
        this.audioPlayer.currentTime = currTime;
      });
  }

  update_song_index(song_index) {
    if (this.current_song_index !== song_index) {
      this.current_song_index = song_index;
      console.log("song index not matched");
      this.getCurrentSong();
    } else console.log("Song index  matched");
  }

  handleTimeUpdate() {
    this.progress.value =
      (this.audioPlayer.currentTime / this.audioPlayer.duration) * 100;
    this.totalTimeLabel.textContent = `${this.formatTime(
      this.audioPlayer.currentTime
    )}/${this.formatTime(this.audioPlayer.duration)}`;
  }

  init() {
    this.getCurrentSong();
    this.playPauseBtn.addEventListener("click", () => this.togglePlayPause());
    this.audioPlayer.addEventListener("timeupdate", () =>
      this.handleTimeUpdate()
    );
    this.barAnim.stop();
  }
}

class BackgroundChanger {
  constructor() {
    this.cover = document.querySelector(".cover");
    this.prev_background_index = 1;
  }

  changeBackground(background_index) {
    if (background_index === this.prev_background_index) return;
    this.prev_background_index = background_index;
    const url = `url("/static/images/background/image-${background_index}.jpg")`;
    this.cover.style.backgroundImage = url;
  }
}

class BarAnimation {
  constructor() {
    this.animate = false;
    this.bars = Array.from(document.querySelectorAll(".bar"));
    this.update();
  }

  start() {
    this.animate = true;
    this.updateBar();
  }
  stop() {
    this.animate = false;
    this.updateBar();
  }
  updateBar() {
    const color = this.getRandomColor();
    this.bars.forEach((bar) => {
      if (!this.animate) {
        bar.style.height = "0";
        bar.style.backgroundColor = "rgba(0, 0, 0, 0)";
      } else {
        bar.style.height = `${20 + Math.random() * 80}%`;
        bar.style.backgroundColor = color;
      }
      setTimeout(() => {}, 50);
    });
  }

  update() {
    setInterval(() => {
      if (!this.animate) return;
      const color = this.getRandomColor();
      this.bars.forEach((bar) => {
        bar.style.height = `${20 + Math.random() * 80}%`;
        bar.style.backgroundColor = color;
      });
    }, 200);
  }

  getRandomColor() {
    const letters = "0123456789ABCDEF";
    let color = "#";
    for (let i = 0; i < 6; i++)
      color += letters[Math.floor(Math.random() * 16)];
    return color;
  }
}

function fetch_server_data() {
  fetch("/get-additional-data")
    .then((res) => res.json())
    .then((data) => {
      backgroundChanger.changeBackground(data.bi);
      player.update_song_index(data.si);
    });
}

const player = new MusicPlayer();
const backgroundChanger = new BackgroundChanger();
fetch_server_data();
setInterval(fetch_server_data, 5000);
