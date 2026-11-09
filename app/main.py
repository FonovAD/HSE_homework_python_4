"""FastAPI-сервис сбора обращений абонентов."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, status

from app.models import Appeal, AppealResponse
from app.storage import JsonFileStorage

#: Каталог хранения по умолчанию; переопределяется переменной окружения.
DEFAULT_STORAGE_DIR = "data/appeals"
STORAGE_DIR_ENV = "APPEALS_STORAGE_DIR"


def create_app(storage_dir: Optional[os.PathLike] = None) -> FastAPI:
    """Создаёт приложение, привязанное к конкретному каталогу хранения."""
    directory = Path(
        storage_dir
        if storage_dir is not None
        else os.getenv(STORAGE_DIR_ENV, DEFAULT_STORAGE_DIR)
    )
    storage = JsonFileStorage(directory)

    application = FastAPI(
        title="Appeals Service",
        version="1.0.0",
        description=(
            "Сервис сбора обращений абонентов. Принимает обращение, "
            "валидирует все атрибуты моделью Pydantic и сохраняет его "
            "в отдельный json-файл на диске."
        ),
    )
    application.state.storage = storage

    @application.get("/health", tags=["service"], summary="Проверка доступности")
    def health() -> dict:
        return {"status": "ok"}

    @application.post(
        "/appeals",
        response_model=AppealResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["appeals"],
        summary="Принять обращение абонента",
        description=(
            "Принимает обращение (задачи 1, 2* и 3**), валидирует его "
            "и сохраняет в json-файл. В одном обращении может быть "
            "несколько причин."
        ),
    )
    def create_appeal(appeal: Appeal) -> AppealResponse:
        record = appeal.model_dump(mode="json")
        saved_path = storage.save(record)
        return AppealResponse(id=saved_path.stem, **record)

    return application


app = create_app()
