from pathlib import Path
import os


class PathManager:
    base_dir: Path = None
    audio_path = "audios"
    save_data = "save-data"

    @staticmethod
    def init(file_path: str):
        PathManager.base_dir = Path(file_path).resolve().parent
        print(f"Path initialized as {PathManager.base_dir}")

    @staticmethod
    def get_path(path: str):
        return PathManager.base_dir / path.lstrip("/\\")

    @staticmethod
    def create_path(path: str):
        os.makedirs(PathManager.get_path(path), exist_ok=True)

    @staticmethod
    def exists_path(path):
        return os.path.exists(path)
