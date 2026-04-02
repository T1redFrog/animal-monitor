import json
import os

HISTORY_FILE = 'history.json'

class HistoryManager:
    def __init__(self):
        if not os.path.exists(HISTORY_FILE):
            self._save([])

    def _load(self):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _save(self, data):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add(self, record):
        data = self._load()
        data.append(record)
        self._save(data)

    def get_all(self):
        return self._load()

    def clear(self):
        self._save([])
