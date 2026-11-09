"""Сохранение обращений на диск в виде json-файлов."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# В требованиях не уточнено, на каждый запрос создавать новый json или добавлять в один файл все запросы.
# Решил записывать каждый запрос в отдельный файл
class JsonFileStorage:
    def __init__(self, directory: os.PathLike) -> None:
        self._directory = Path(directory)

    @property
    def directory(self) -> Path:
        return self._directory

    def save(self, payload: Dict[str, Any]) -> Path:
        self._directory.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        file_id = f"{timestamp}-{uuid.uuid4().hex[:12]}"
        final_path = self._directory / f"{file_id}.json"
        temp_path = self._directory / f".{file_id}.json.tmp"

        serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        with open(temp_path, "w", encoding="utf-8") as file:
            file.write(serialized)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, final_path)
        return final_path
