from datetime import date

from src.service.mlb_qm_fitting_report.xlsx_source import compute_label

STAGES = ["FIT", "PP", "TOP"]
DUE_FIELD_BY_STAGE = {"FIT": "qc_due", "PP": "pp_due", "TOP": "top_due"}
# 담당은 역할 기준(FIT=TD, PP/TOP=QA) — 개별 스타일에 담당자 이름이 채워져 있는지와 무관하게 항상 집계한다.
# styles.qa 컬럼이 시즌 전체에서 비어있어도(예: 27SS) PP/TOP 집계 자체는 빠지면 안 된다.
OWNER_BY_STAGE = {"FIT": "TD", "PP": "QA", "TOP": "QA"}


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


_ROUND_LABELS = ["1ST", "2ND", "3RD", "4TH", "5TH"]


def _round_label(round_num) -> str | None:
    if round_num is None:
        return None
    if 1 <= round_num <= len(_ROUND_LABELS):
        return _ROUND_LABELS[round_num - 1]
    return f"{round_num}TH"


def _all_records_by_style_and_stage(records: list[dict]) -> dict:
    """(style_code, stage) -> 그 스타일·단계의 모든 record, round 오름차순 정렬."""
    grouped: dict = {}
    for r in records:
        grouped.setdefault((r["style_code"], r["stage"]), []).append(r)
    for recs in grouped.values():
        recs.sort(key=lambda r: (r["round"], r["updated_at"]))
    return grouped


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
            if stage == "FIT" and not is_done:
                # 보정 승인 = FIT 승인(보정 통과하면 FIT 생략하고 PP로 직행하는 경우가 많음).
                prep_record = latest.get((style["style_code"], "보정"))
                is_done = bool(prep_record and prep_record["status"] == "Approved")
            is_due = bool(due and due <= as_of_date)

            owner_type = OWNER_BY_STAGE[stage]
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


def build_raw_rows(styles: list[dict], records: list[dict]) -> dict:
    """season -> [{"style_code", "fit_due"/"pp_due"/"top_due" (iso|None), "fit_done"/"pp_done"/"top_done" (bool)}]
    대시보드가 브라우저에서 직접 기준대비를 재계산할 수 있게 스타일 단위 원본을 그대로 실어보낸다.
    styles.qc_due/pp_due/top_due(고정, 업스트림에서 이미 ETD+수량+구분 기준으로 계산되어 들어온 값)를
    우선 쓰고, 없을 때만 label(구분+워시+수량)+etd로 대시보드 DUE DATE 설정 기준표를 적용해 계산한다
    (26FW의 DUE_DATA(2) 우선 + ETD/오프셋 폴백 구조와 동일)."""
    latest = _latest_status_by_style_and_stage(records)
    all_records = _all_records_by_style_and_stage(records)
    result: dict = {}

    def _rounds_list(style_code: str, stage: str) -> list[dict]:
        # updated_at만 있고 별도 접수일(received) 컬럼은 없어서, received도 confirm_date와
        # 같은 값을 쓴다(회차→회차 리드타임 계산이 그나마 뭔가 값을 갖도록 하기 위한 근사치).
        return [
            {
                "round": _round_label(r["round"]),
                "received": r["updated_at"][:10],
                "status": r["status"],
                "confirm_date": r["updated_at"][:10],
                "reason": None,
            }
            for r in all_records.get((style_code, stage), [])
        ]

    for style in styles:
        if style.get("co") == "DROP":
            continue
        season = style["season"]
        qty_total = (style.get("qty_kr") or 0) + (style.get("qty_cn") or 0)
        row = {
            "style_code": style["style_code"],
            "vendor": style.get("vendor"),
            "item": style.get("item"),
            "quarter": style.get("quarter"),
            "td": style.get("td"),
            "qa": style.get("qa"),
            "label": compute_label(style.get("item"), style.get("washed"), qty_total),
            "etd": style.get("earliest_etd"),
            "detail": {},
        }
        prep_record = latest.get((style["style_code"], "보정"))
        prep_rounds = _rounds_list(style["style_code"], "보정")
        prep_approved = bool(prep_record and prep_record["status"] == "Approved")

        for stage in STAGES:
            due = _parse_date(style.get(DUE_FIELD_BY_STAGE[stage]))
            record = latest.get((style["style_code"], stage))
            rounds = _rounds_list(style["style_code"], stage)
            row[f"{stage.lower()}_due"] = due.isoformat() if due else None
            is_done = bool(record and record["status"] == "Approved")
            if stage == "FIT" and not is_done:
                is_done = prep_approved  # 보정 승인 = FIT 승인(FIT 생략하고 PP로 직행)
            row[f"{stage.lower()}_done"] = is_done
            row["detail"][stage] = {
                "round": _round_label(record["round"]) if record else None,
                "status": record["status"] if record else None,
                "confirm_date": record["updated_at"][:10] if record else None,
                "reason": None,
                "first_received": rounds[0]["received"] if rounds else None,
                "rounds": rounds,
            }
        # 보정은 집계 대상 stage는 아니지만, FIT이 아직 시작 전일 때 "이전 단계" 상세로 보여준다.
        row["detail"]["보정"] = {
            "round": _round_label(prep_record["round"]) if prep_record else None,
            "status": prep_record["status"] if prep_record else None,
            "confirm_date": prep_record["updated_at"][:10] if prep_record else None,
            "reason": None,
            "first_received": prep_rounds[0]["received"] if prep_rounds else None,
            "rounds": prep_rounds,
        }
        if row["detail"]["FIT"]["round"] is None and prep_approved:
            row["detail"]["FIT"]["status"] = "생략(보정→PP 직행)"
        result.setdefault(season, []).append(row)

    return result
