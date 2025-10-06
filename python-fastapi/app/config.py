from os import PathLike
from pathlib import Path
from pydantic import BaseModel
from secrets import token_urlsafe


class Config(BaseModel):
    session_secret_key: str = token_urlsafe(36)
    session_days: int = 14
    csrf_secret_key: str = token_urlsafe(36)
    magic_link_minutes: int = 15


def load(path: PathLike) -> Config:
    try:
        return Config.model_validate_json(Path(path).read_text())
    except FileNotFoundError:
        return Config()


def load_generate(path: PathLike) -> Config:
    loaded = load(path)
    if loaded.model_fields_set != Config.model_fields:
        # Some fields have default values. Persist them back to the file
        Path(path).write_text(loaded.model_dump_json(indent=4))
    return loaded
