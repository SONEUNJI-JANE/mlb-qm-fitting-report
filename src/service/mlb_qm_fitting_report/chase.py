# src/service/mlb_qm_fitting_report/chase.py
from datetime import date

# 스크린샷 "체이스 경고 기준 설정" 값 그대로 반영.
# ref: 스타일 due-date 필드명, 또는 "elapsed"(최신 기록일로부터 경과일수 기준)
CHASE_RULES = [
    {"stage": "보정", "status": "Approved", "ref": "pp_due", "days": 20, "desc": "보정 Approved → PP 샘플 접수"},
    {"stage": "보정", "status": "Go to FIT", "ref": "elapsed", "days": 30, "desc": "보정 Go to FIT → 1ST FIT 샘플 접수"},
    {"stage": "보정", "status": "Rejected", "ref": "qc_due", "days": 45, "desc": "보정 Rejected → 다음 차수 보정 샘플 접수"},
    {"stage": "FIT", "status": "Approved", "ref": "pp_due", "days": 20, "desc": "FIT Approved → PP 샘플 접수"},
    {"stage": "FIT", "status": "Rejected", "round_max": 1, "ref": "qc_due", "days": 30, "desc": "FIT Rej/IntRej 1차 → 다음 FIT 샘플 접수"},
    {"stage": "FIT", "status": "Int Rej", "round_max": 1, "ref": "qc_due", "days": 30, "desc": "FIT Rej/IntRej 1차 → 다음 FIT 샘플 접수"},
    {"stage": "FIT", "status": "Rejected", "round_min": 2, "ref": "qc_due", "days": 15, "desc": "FIT Rej/IntRej 2차+ → 다음 FIT 샘플 접수"},
    {"stage": "FIT", "status": "Int Rej", "round_min": 2, "ref": "qc_due", "days": 15, "desc": "FIT Rej/IntRej 2차+ → 다음 FIT 샘플 접수"},
    {"stage": "PP", "status": "Approved", "ref": "top_due", "days": 28, "desc": "PP Approved → TOP 샘플 접수"},
    {"stage": "PP", "status": "Rejected", "ref": "pp_due", "days": 10, "desc": "PP Rej/IntRej → 다음 차수 PP 샘플 접수"},
    {"stage": "PP", "status": "Int Rej", "ref": "pp_due", "days": 10, "desc": "PP Rej/IntRej → 다음 차수 PP 샘플 접수"},
    {"stage": "TOP", "status": "Rejected", "ref": "top_due", "days": 14, "desc": "TOP Rej/IntRej → 다음 차수 TOP 샘플 접수"},
    {"stage": "TOP", "status": "Int Rej", "ref": "top_due", "days": 14, "desc": "TOP Rej/IntRej → 다음 차수 TOP 샘플 접수"},
]

STAGE_ORDER = {"보정": 0, "FIT": 1, "PP": 2, "TOP": 3}


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value[:10])


def _matches(rule: dict, record: dict) -> bool:
    if rule["stage"] != record["stage"] or rule["status"] != record["status"]:
        return False
    if "round_max" in rule and record["round"] > rule["round_max"]:
        return False
    if "round_min" in rule and record["round"] < rule["round_min"]:
        return False
    return True


def _latest_records_by_style(records: list[dict]) -> dict:
    latest = {}
    for r in records:
        key = r["style_code"]
        current = latest.get(key)
        key_r = (STAGE_ORDER[r["stage"]], r["round"], r["updated_at"])
        key_c = (STAGE_ORDER[current["stage"]], current["round"], current["updated_at"]) if current else None
        if current is None or key_r > key_c:
            latest[key] = r
    return latest


def compute_chase_warnings(styles: list[dict], records: list[dict], as_of_date: date) -> list[dict]:
    styles_by_code = {s["style_code"]: s for s in styles}
    latest = _latest_records_by_style(records)
    warnings = []

    for style_code, record in latest.items():
        style = styles_by_code.get(style_code)
        if not style:
            continue

        for rule in CHASE_RULES:
            if not _matches(rule, record):
                continue

            owner = style.get("td") or style.get("qa") or ""

            if rule["ref"] == "elapsed":
                last_change = date.fromisoformat(record["updated_at"][:10])
                days_elapsed = (as_of_date - last_change).days
                if days_elapsed >= rule["days"]:
                    warnings.append({
                        "style_code": style_code, "season": style.get("season"), "owner": owner,
                        "rule": rule["desc"], "due_date": None, "days_to_due": None,
                    })
            else:
                due = _parse_date(style.get(rule["ref"]))
                if due is None:
                    continue
                days_to_due = (due - as_of_date).days
                if 0 <= days_to_due <= rule["days"]:
                    warnings.append({
                        "style_code": style_code, "season": style.get("season"), "owner": owner,
                        "rule": rule["desc"], "due_date": due.isoformat(), "days_to_due": days_to_due,
                    })
            break  # 스타일당 최신 기록은 하나의 규칙에만 매칭됨

    return warnings
