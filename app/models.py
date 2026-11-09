from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Регулярка на имя и фамилию
_NAME_RE = re.compile(r"^[А-ЯЁ][а-яё]*$")

# Регулярка на email
_EMAIL_RE = re.compile(
    r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+"
    r"(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
    r"@(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+"
    r"[A-Za-z]{2,63}$"
)

# Регулярка на номер телефона
_PHONE_ALLOWED_RE = re.compile(r"^\+?[0-9\s\-()]+$")

# Максимальный возраст
_MAX_AGE_YEARS = 120

_FUTURE_TOLERANCE = timedelta(minutes=5)


class AppealReason(str, Enum):
    NO_NETWORK = "нет доступа к сети"
    PHONE_NOT_WORKING = "не работает телефон"
    NO_LETTERS = "не приходят письма"


class Appeal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    last_name: str = Field(
        min_length=1,
        max_length=50,
        description="Фамилия: только кириллица, с заглавной буквы",
        examples=["Фонов"],
    )
    first_name: str = Field(
        min_length=1,
        max_length=50,
        description="Имя: только кириллица, с заглавной буквы",
        examples=["Александр"],
    )
    birth_date: date = Field(
        description="Дата рождения в формате YYYY-MM-DD",
        examples=["2004-04-27"],
    )
    phone: str = Field(
        description="Номер телефона; хранится в нормализованном виде +7XXXXXXXXXX",
        examples=["+7 999 123-45-67"],
    )
    email: str = Field(
        max_length=254,
        description="Адрес электронной почты",
        examples=["fonovad@edu.hse.ru"],
    )
    reasons: List[AppealReason] = Field(
        min_length=1,
        description="Причины обращения: от одной до трёх, без повторов",
        examples=[["нет доступа к сети", "не работает телефон"]],
    )
    detected_at: datetime = Field(
        description="Дата и время обнаружения проблемы",
        examples=["2026-11-09T10:15:00"],
    )

    @field_validator("last_name", "first_name", mode="before")
    @classmethod
    def _strip_name(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("last_name", "first_name")
    @classmethod
    def _validate_name(cls, value: str, info) -> str:
        if not _NAME_RE.fullmatch(value):
            raise ValueError(
                f"поле {info.field_name!r} должно содержать только кириллицу "
                "и начинаться с заглавной буквы"
            )
        return value

    @field_validator("birth_date")
    @classmethod
    def _validate_birth_date(cls, value: date) -> date:
        today = date.today()
        if value > today:
            raise ValueError("дата рождения не может быть в будущем")
        oldest_allowed = today - timedelta(days=_MAX_AGE_YEARS * 365 + _MAX_AGE_YEARS // 4)
        if value < oldest_allowed:
            raise ValueError(
                f"дата рождения не может быть раньше {oldest_allowed.isoformat()}"
            )
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def _strip_phone(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: str) -> str:
        if not _PHONE_ALLOWED_RE.fullmatch(value):
            raise ValueError(
                "номер телефона может содержать только цифры, пробелы, "
                "'+', '-', '(', ')'"
            )
        digits = re.sub(r"\D", "", value)
        # 8XXXXXXXXXX и 7XXXXXXXXXX приводим к десятизначному номеру.
        if len(digits) == 11 and digits[0] in "78":
            digits = digits[1:]
        if len(digits) != 10 or digits[0] in "01":
            raise ValueError(
                "номер телефона должен содержать 10 цифр после кода страны "
                "(например, +79991234567)"
            )
        return "+7" + digits

    @field_validator("email", mode="before")
    @classmethod
    def _strip_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        if not _EMAIL_RE.fullmatch(value):
            raise ValueError("некорректный адрес электронной почты")
        local_part, domain = value.rsplit("@", 1)
        if len(local_part) > 64:
            raise ValueError("локальная часть адреса не может быть длиннее 64 символов")
        return f"{local_part}@{domain.lower()}"

    @field_validator("reasons", mode="before")
    @classmethod
    def _normalize_reasons(cls, value: object) -> object:
        if isinstance(value, (list, tuple)):
            return [item.strip() if isinstance(item, str) else item for item in value]
        return value

    @field_validator("reasons")
    @classmethod
    def _validate_reasons(cls, value: List[AppealReason]) -> List[AppealReason]:
        if not value:
            raise ValueError("нужно указать хотя бы одну причину обращения")
        if len(set(value)) != len(value):
            raise ValueError("причины обращения не должны повторяться")
        return value

    @field_validator("detected_at")
    @classmethod
    def _validate_detected_at(cls, value: datetime) -> datetime:
        now = datetime.now(tz=value.tzinfo) if value.tzinfo else datetime.now()
        if value > now + _FUTURE_TOLERANCE:
            raise ValueError(
                "дата и время обнаружения проблемы не могут быть в будущем"
            )
        return value


class AppealResponse(Appeal):
    id: str = Field(
        description="Идентификатор обращения (имя json-файла без расширения)",
        examples=["20261109T101500123456-1a2b3c4d5e6f"],
    )
