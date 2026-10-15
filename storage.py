import json
import os
from typing import Dict, Any

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "db"))
OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "out"))

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)


class FileStorage:
    @staticmethod
    def _get_path(collection: str) -> str:
        return os.path.join(DB_DIR, f"{collection}.json")

    @classmethod
    def load(cls, collection: str) -> Dict[str, Any]:
        filepath = cls._get_path(collection)
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    @classmethod
    def save(cls, collection: str, data: Dict[str, Any]) -> None:
        filepath = cls._get_path(collection)
        temp_path = f"{filepath}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_path, filepath)

    @classmethod
    def next_id(cls, collection: str) -> str:
        data = cls.load(collection)
        if not data:
            return "1"
        existing_ids = [int(k) for k in data.keys() if str(k).isdigit()]
        return str(max(existing_ids, default=0) + 1)