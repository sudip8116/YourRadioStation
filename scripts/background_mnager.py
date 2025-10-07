import json
import os
from random import randint
from threading import Thread
from time import sleep


class BackgroundManager:
    def __init__(self, data, base_dir, update_delay=60):
        self.data = data
        self.background_path = base_dir / "static/images/background/"
        self.max_back_count = 0
        self.current_background_index = 0
        self.update_delay = update_delay
        self.rename_backgrounds()
        self.get_random_background()

    def rename_backgrounds(self):
        backgrounds = os.listdir(self.background_path)

        # avoid overwriting by renaming in two steps
        for i, file in enumerate(backgrounds):
            os.rename(
                os.path.join(self.background_path, file),
                os.path.join(self.background_path, f"temp-{i+1}.jpg"),
            )

        temp_files = os.listdir(self.background_path)
        for i, file in enumerate(temp_files):
            os.rename(
                os.path.join(self.background_path, file),
                os.path.join(self.background_path, f"image-{i+1}.jpg"),
            )

        self.max_back_count = len(temp_files)

    def get_random_background(self):
        self.current_background_index = randint(1, self.max_back_count)
        self.data.write(json.dumps({"bi": self.current_background_index}))

    def start(self):
        Thread(target=self.update, daemon=True).start()

    def update(self):
        while True:
            self.get_random_background()
            sleep(self.update_delay)
