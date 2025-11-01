from threading import Thread
from time import sleep
import requests
import os

BOT_TOKEN = "7526670917:AAHKYMGAX9DbClRbRHodaCLRJlcCXz1z0yc"


def get_file(file_id: str):
    # Step 1: Get file path
    info_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
    file_info = requests.get(info_url).json()
    print(file_info)
    file_path = file_info["result"]["file_path"]

    # Step 2: Download file
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    local_name = os.path.basename(file_path)

    with requests.get(file_url, stream=True) as r:
        with open(f"{file_id}.bin", "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)


class LiveRadio:
    def __init__(self, count):
        self.target = count

    def start(self):
        Thread(target=self.count_thread).start()

    def count_thread(self):
        while True:
            self.target[0] += 1
            sleep(1)
