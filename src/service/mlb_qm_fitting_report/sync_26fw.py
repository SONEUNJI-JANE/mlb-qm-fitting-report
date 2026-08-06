from src.service.mlb_qm_fitting_report.xlsx_source import _ROUND_LABELS

SEASON = "26FW"
_ROUND_NUMBER = {label: i + 1 for i, label in enumerate(_ROUND_LABELS)}
_DONE_FIELD_FOR_STAGE = {"FIT": "fit_done", "PP": "pp_done", "TOP": "top_done"}
_DUE_FIELD_FOR_STAGE = {"FIT": "fit_due", "PP": "pp_due", "TOP": "top_due"}


def map_style_row(raw_row: dict) -> dict:
    """read_fit_track_raw()의 한 행 -> Supabase styles upsert용 행."""
    return {
        "style_code": raw_row["style_code"],
        "item": raw_row["item"],
        "quarter": raw_row["quarter"],
        "season": SEASON,
        "td": raw_row["td"],
        "qa": raw_row["qa"],
        "vendor": raw_row["vendor"],
        "qc_due": raw_row["fit_due"],
        "pp_due": raw_row["pp_due"],
        "top_due": raw_row["top_due"],
        "earliest_etd": raw_row["etd"],
    }


def map_fitting_records(raw_row: dict) -> list[dict]:
    """raw_row["detail"][stage]["rounds"]에서 회차별로 fitting_records 행을 뽑는다.
    round 라벨("1ST" 등)은 fitting_records.round(정수) 컬럼에 맞게 숫자로 바꾼다.
    확정일(confirm_date)도 접수일(received)도 없는 회차는 언제 그 상태가 됐는지 알 수 없어 skip.

    엑셀엔 사람이 직접 체크하는 fit_done/pp_done/top_done 컬럼이 따로 있고, 이게 그 단계의
    진짜 완료 기준이다(정적 대시보드도 이 값을 그대로 씀). 회차 로그의 마지막 status가 그거랑
    다르면(기록이 늦게 올라오는 경우 등) 체크 컬럼을 우선해서 마지막 회차 status를 Approved로
    맞춰준다 — 안 그러면 live_app이 회차 로그만 보고 완료율을 실제보다 낮게 계산하게 된다.
    회차 로그가 아예 없는데(접수/확정일 기록 자체가 없음) 완료 체크만 돼있는 케이스도 있어서,
    그런 스타일은 due date를 confirm_date 대용으로 써서 최소한 완료 건수 카운트는 맞춘다
    (on-time 여부 같은 날짜 기반 지표는 이 대용값 때문에 부정확할 수 있음 — 알려진 한계)."""
    records = []
    style_code = raw_row["style_code"]
    for stage, detail in raw_row["detail"].items():
        stage_records = []
        for r in detail["rounds"]:
            round_num = _ROUND_NUMBER.get(r["round"])
            date = r["confirm_date"] or r["received"]
            if round_num is None or not date:
                continue
            stage_records.append({
                "style_code": style_code,
                "stage": stage,
                "round": round_num,
                "status": r["status"],
                "updated_at": f"{date}T00:00:00+00:00",
            })
        done_field = _DONE_FIELD_FOR_STAGE.get(stage)
        is_done = done_field and raw_row.get(done_field)
        if is_done and stage_records:
            stage_records[-1]["status"] = "Approved"
        elif is_done and not stage_records:
            due_field = _DUE_FIELD_FOR_STAGE.get(stage)
            fallback_date = raw_row.get(due_field) or raw_row.get("etd")
            if fallback_date:
                stage_records.append({
                    "style_code": style_code,
                    "stage": stage,
                    "round": 1,
                    "status": "Approved",
                    "updated_at": f"{fallback_date}T00:00:00+00:00",
                })
        records.extend(stage_records)
    return records


def sync_26fw(settings: dict) -> dict:
    """26FW 엑셀을 읽어 Supabase styles/fitting_records에 upsert. 반환: {"styles": N, "records": N}."""
    from src.service.mlb_qm_fitting_report.xlsx_source import read_fit_track_raw
    from src.service.mlb_qm_fitting_report.supabase_client import upsert_styles, upsert_fitting_records

    xlsx_path = settings["legacy_xlsx_sources"][SEASON]
    raw_apparel_path = settings.get("raw_apparel_sources", {}).get(SEASON)
    raw_rows = read_fit_track_raw(xlsx_path, raw_apparel_path)

    style_rows = [map_style_row(r) for r in raw_rows]
    record_rows = [rec for r in raw_rows for rec in map_fitting_records(r)]

    upsert_styles(settings, style_rows)
    upsert_fitting_records(settings, record_rows)
    return {"styles": len(style_rows), "records": len(record_rows)}


if __name__ == "__main__":
    from src.service.mlb_qm_fitting_report.config import load_settings

    settings = load_settings()
    result = sync_26fw(settings)
    print(f"synced: {result}")
