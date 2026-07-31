import copy
import json
import os


def load_overrides(week_id: str, overrides_dir: str = "overrides") -> list[dict]:
    path = os.path.join(overrides_dir, f"{week_id}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_overrides(progress: dict, overrides: list[dict]) -> dict:
    result = copy.deepcopy(progress)
    for entry in overrides:
        bucket = result.get(entry["season"], {}).get(entry["owner_type"], {}).get(entry["stage"])
        if bucket is None:
            continue
        bucket["total_done"] = entry["override_numerator"]
        bucket["total_all"] = entry["override_denominator"]
    return result
