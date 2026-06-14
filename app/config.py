from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class Settings:
    db_path: Path
    station_count: int
    business_tz: str


def get_settings() -> Settings:
    db_path = Path(os.getenv("QUEUE_DB_PATH", "data/queue.sqlite3"))
    station_count = int(os.getenv("CALL_STATION_COUNT", "2"))
    business_tz = os.getenv("BUSINESS_TZ", "Asia/Shanghai")
    return Settings(db_path=db_path, station_count=station_count, business_tz=business_tz)
