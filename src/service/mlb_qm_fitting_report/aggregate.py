from datetime import date

STAGES = ["FIT", "PP", "TOP"]
DUE_FIELD_BY_STAGE = {"FIT": "qc_due", "PP": "pp_due", "TOP": "top_due"}
OWNER_FIELDS = {"TD": "td", "QA": "qa"}


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value[:10])


def _latest_status_by_style_and_stage(records: list[dict]) -> dict:
    """(style_code, stage) -> 가장 최신 record(round 최댓값, updated_at 최댓값)"""
    latest = {}
    for r in records:
        key = (r["style_code"], r["stage"])
        current = latest.get(key)
        if current is None or (r["round"], r["updated_at"]) > (current["round"], current["updated_at"]):
            latest[key] = r
    return latest


def compute_progress(styles: list[dict], records: list[dict], as_of_date: date) -> dict:
    latest = _latest_status_by_style_and_stage(records)
    result: dict = {}

    for style in styles:
        if style.get("co") == "DROP":
            continue

        season = style["season"]
        result.setdefault(season, {"TD": {}, "QA": {}})

        for stage in STAGES:
            due_field = DUE_FIELD_BY_STAGE[stage]
            due = _parse_date(style.get(due_field))
            record = latest.get((style["style_code"], stage))
            is_done = bool(record and record["status"] == "Approved")
            is_due = bool(due and due <= as_of_date)

            for owner_type, style_field in OWNER_FIELDS.items():
                owner_name = style.get(style_field)
                if not owner_name:
                    continue
                bucket = result[season][owner_type].setdefault(
                    stage, {"total_done": 0, "total_all": 0, "baseline_done": 0, "baseline_all": 0}
                )
                bucket["total_all"] += 1
                if is_done:
                    bucket["total_done"] += 1
                if is_due:
                    bucket["baseline_all"] += 1
                    if is_done:
                        bucket["baseline_done"] += 1

    return result
