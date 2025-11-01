class GlowAnimation {
  constructor() {
    this.element = document.querySelector("#album-background");
  }
  start() {
    setInterval(() => {
      this.element.style.boxShadow = `0 0 10px ${this.getRadomColor()}, 0 0 20px ${this.getRadomColor()},
    0 0 40px ${this.getRadomColor()}, 0 0 60px ${this.getRadomColor()},
    0 0 80px ${this.getRadomColor()}`;
    }, 500);
  }

  stop() {
    this.element.style.boxShadow = `box-shadow: 0 0 10px rgba(0, 0, 0, 0), 0 0 20px rgba(0, 0, 0, 0),
    0 0 40px rgba(0, 0, 0, 0), 0 0 60px rgba(0, 0, 0, 0),
    0 0 80px rgba(0, 0, 0, 0);`;
  }

  getRadomColor() {
    const r = Math.floor(Math.random() * 255);
    const g = Math.floor(Math.random() * 255);
    const b = Math.floor(Math.random() * 255);
    const a = 0.3 + Math.random() * 0.7;
    return `rgba(${r}, ${g}, ${b}, ${a})`;
  }
}

class BackgroundChanger {
  constructor() {
    this.cover = document.querySelector("body");
  }

  changeBackground(background_index) {
    this.cover.style.transition = "background-image 1.5s ease-in-out";
    this.cover.style.backgroundImage = `url("/static/images/background/image-${background_index}.jpg")`;
  }
}

class LiveRadio {
  constructor() {
    this.audioPlayer = document.querySelector("audio");
    this.songTitle = document.querySelector("#song-title");
    this.playBtn = document.querySelector("#play-btn");
    this.albumArt = document.querySelector("#player-album");
    this.albumBackground = document.querySelector("#album-background");
    this.timeSlider = document.querySelector("#time-slider");
    this.playing = false;
    this.songLoaded = false;
    this.songPath = "";
    this.songId = 0;
    this.backgroundChanger = new BackgroundChanger();
    this.backGlow = new GlowAnimation();
    this.init();
  }

  init() {
    this.audioPlayer.volume = 1;
    this.playBtn.addEventListener("click", () => this.togglePlayPause());
    this.audioPlayer.addEventListener("timeupdate", () =>
      this.updateTimeSlider()
    );
    this.backGlow.stop();
    this.fetchSong();
  }

  togglePlayPause() {
    if (!this.songLoaded) return;
    if (!this.playing) {
      this.syncPosition();
      this.audioPlayer.play().catch(console.error);
      this.playBtn.textContent = "❚❚";
      this.albumArt.classList.add("rot");
      this.backGlow.start();
    } else {
      this.audioPlayer.pause();
      this.playBtn.textContent = "▶";
      this.albumArt.classList.remove("rot");
      this.backGlow.stop();
    }
    this.playing = !this.playing;
  }

  fetchSong() {
    fetch("/get-song")
      .then((res) => res.json())
      .then((data) => {
        if (data.error) return console.warn("❌ Song load failed");
        this.audioPlayer.src = "data:audio/mp3;base64," + data.audio;
        this.songTitle.textContent = data.title || "Unknown Song";
        this.albumBackground.style.backgroundImage = `url(data:image/png;base64,${data.image})`;
        this.audioPlayer.onloadedmetadata = () => {
          this.songLoaded = true;
          if (this.playing) {
            this.playing = false;
            this.togglePlayPause(); // sync state
          }
        };
      })
      .catch((err) => console.error("Fetch song error:", err));
  }

  syncPosition() {
    fetch("/get-song-position")
      .then((res) => res.json())
      .then((data) => {
        if (!data || !("t" in data)) return;
        this.audioPlayer.currentTime =
          ((Date.now() / 1000) % data.mod) - data.t;
      })
      .catch((err) => console.error(err));
  }

  update() {
    fetch("/get-bisi")
      .then((res) => res.json())
      .then((data) => {
        if (!data || "error" in data) return;
        this.backgroundChanger.changeBackground(data.bi);
        if (this.songId !== data.si) {
          this.songId = data.si;
          this.songLoaded = false;
          this.fetchSong(); // load new song
        }
      })
      .catch((err) => console.error(err));
  }

  updateTimeSlider() {
    if (!this.audioPlayer.duration) return;
    this.timeSlider.value =
      (this.audioPlayer.currentTime / this.audioPlayer.duration) * 100;
  }
}

const liveRadio = new LiveRadio();

liveRadio.update();
setInterval(() => liveRadio.update(), 2000);

console.log("🎵 Live Radio Debug: Ready!");
