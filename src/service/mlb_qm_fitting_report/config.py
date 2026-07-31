import json
from datetime import date, timedelta

_WEEKDAY_MAP = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def load_settings(path: str = "config/report_settings.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
