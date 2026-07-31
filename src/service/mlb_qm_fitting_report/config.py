import json
import os
from datetime import date, timedelta

_WEEKDAY_MAP = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def _load_dotenv(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def load_settings(path: str = "config/report_settings.json") -> dict:
    _load_dotenv()
    with open(path, "r", encoding="utf-8") as f:
        settings = json.load(f)
    settings["supabase_url"] = os.environ["SUPABASE_URL"]
    settings["supabase_anon_key"] = os.environ["SUPABASE_ANON_KEY"]
    return settings


def resolve_as_of_date(settings: dict, run_date: date) -> date:
    override = settings.get("as_of_date_override")
    if override:
        return date.fromisoformat(override)

    target_weekday = _WEEKDAY_MAP[settings.get("as_of_weekday", "FRI")]
    days_back = (run_date.weekday() - target_weekday) % 7
    if days_back == 0:
        days_back = 7
    return run_date - timedelta(days=days_back)


def week_id_for(as_of_date: date) -> str:
    iso_year, iso_week, _ = as_of_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"
