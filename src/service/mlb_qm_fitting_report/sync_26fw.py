from src.service.mlb_qm_fitting_report.xlsx_source import _ROUND_LABELS

SEASON = "26FW"
_ROUND_NUMBER = {label: i + 1 for i, label in enumerate(_ROUND_LABELS)}


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
    확정일(confirm_date)도 접수일(received)도 없는 회차는 언제 그 상태가 됐는지 알 수 없어 skip."""
    records = []
    style_code = raw_row["style_code"]
    for stage, detail in raw_row["detail"].items():
        for r in detail["rounds"]:
            round_num = _ROUND_NUMBER.get(r["round"])
            date = r["confirm_date"] or r["received"]
            if round_num is None or not date:
                continue
            records.append({
                "style_code": style_code,
                "stage": stage,
                "round": round_num,
                "status": r["status"],
                "updated_at": f"{date}T00:00:00+00:00",
            })
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
