import copy
import json
import os
from datetime import date


def load_snapshots(path: str = "src/output/weekly_snapshots.json") -> dict:
    if not os.path.exists(path):
        return {"weeks": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_snapshot(snapshots: dict, week_id: str, as_of_date: date, progress: dict, warnings: list[dict], raw: dict = None) -> dict:
    result = copy.deepcopy(snapshots)
    result["weeks"][week_id] = {
        "as_of_date": as_of_date.isoformat(),
        "progress": progress,
        "warnings": warnings,
        "raw": raw or {},
    }
    return result


def save_snapshots(snapshots: dict, path: str = "src/output/weekly_snapshots.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2, sort_keys=True)
