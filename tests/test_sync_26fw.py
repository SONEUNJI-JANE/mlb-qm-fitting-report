import sys
sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.sync_26fw import map_style_row, map_fitting_records

RAW_ROW = {
    "style_code": "3ADJB0001",
    "vendor": "V1",
    "item": "DJ",
    "quarter": "Main TS",
    "td": "김철수",
    "qa": "박영희",
    "label": "DENIM워싱일반",
    "etd": "2026-08-01",
    "fit_due": "2026-05-01",
    "pp_due": "2026-06-01",
    "top_due": "2026-07-01",
    "fit_done": True,
    "pp_done": False,
    "top_done": False,
    "detail": {
        "보정": {"round": None, "status": None, "confirm_date": None, "reason": None, "first_received": None, "rounds": []},
        "FIT": {
            "round": "2ND", "status": "Approved", "confirm_date": "2026-04-20", "reason": None,
            "first_received": "2026-04-01",
            "rounds": [
                {"round": "1ST", "received": "2026-04-01", "status": "Rejected", "confirm_date": "2026-04-10", "reason": "핏변경"},
                {"round": "2ND", "received": "2026-04-15", "status": "Approved", "confirm_date": "2026-04-20", "reason": None},
            ],
        },
        "PP": {"round": None, "status": None, "confirm_date": None, "reason": None, "first_received": None, "rounds": []},
        "TOP": {"round": None, "status": None, "confirm_date": None, "reason": None, "first_received": None, "rounds": []},
    },
}


def test_map_style_row():
    row = map_style_row(RAW_ROW)
    assert row["style_code"] == "3ADJB0001"
    assert row["season"] == "26FW"
    assert row["qc_due"] == "2026-05-01"
    assert row["pp_due"] == "2026-06-01"
    assert row["top_due"] == "2026-07-01"
    assert row["earliest_etd"] == "2026-08-01"
    assert row["vendor"] == "V1"


def test_map_fitting_records_converts_round_label_to_number():
    records = map_fitting_records(RAW_ROW)
    fit_records = [r for r in records if r["stage"] == "FIT"]
    assert len(fit_records) == 2

    r1 = next(r for r in fit_records if r["round"] == 1)
    assert r1["status"] == "Rejected"
    assert r1["updated_at"] == "2026-04-10T00:00:00+00:00"

    r2 = next(r for r in fit_records if r["round"] == 2)
    assert r2["status"] == "Approved"
    assert r2["updated_at"] == "2026-04-20T00:00:00+00:00"


def test_map_fitting_records_skips_empty_stages():
    records = map_fitting_records(RAW_ROW)
    stages = {r["stage"] for r in records}
    assert stages == {"FIT"}  # 보정/PP/TOP는 rounds가 비어있어서 안 나옴


def test_map_fitting_records_falls_back_to_received_date():
    raw_row = {
        "style_code": "S2",
        "detail": {
            "FIT": {"rounds": [{"round": "1ST", "received": "2026-01-01", "status": "Rejected", "confirm_date": None, "reason": None}]},
        },
    }
    records = map_fitting_records(raw_row)
    assert len(records) == 1
    assert records[0]["updated_at"] == "2026-01-01T00:00:00+00:00"


def test_map_fitting_records_skips_rounds_without_any_date():
    raw_row = {
        "style_code": "S3",
        "detail": {
            "FIT": {"rounds": [{"round": "1ST", "received": None, "status": "Rejected", "confirm_date": None, "reason": None}]},
        },
    }
    records = map_fitting_records(raw_row)
    assert records == []


if __name__ == "__main__":
    test_map_style_row()
    test_map_fitting_records_converts_round_label_to_number()
    test_map_fitting_records_skips_empty_stages()
    test_map_fitting_records_falls_back_to_received_date()
    test_map_fitting_records_skips_rounds_without_any_date()
    print("OK: test_sync_26fw")
