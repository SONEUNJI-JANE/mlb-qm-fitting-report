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


def test_map_fitting_records_done_flag_overrides_last_round_status():
    # 엑셀 완료 체크는 True인데 회차 로그의 마지막 status가 Rejected로 남아있는(기록 지연) 케이스.
    raw_row = {
        "style_code": "S4",
        "fit_done": True,
        "detail": {
            "FIT": {"rounds": [
                {"round": "1ST", "received": "2026-01-01", "status": "Rejected", "confirm_date": "2026-01-05", "reason": "핏변경"},
                {"round": "2ND", "received": "2026-01-10", "status": "Rejected", "confirm_date": "2026-01-15", "reason": "봉제"},
            ]},
        },
    }
    records = map_fitting_records(raw_row)
    assert len(records) == 2
    last = next(r for r in records if r["round"] == 2)
    assert last["status"] == "Approved"
    first = next(r for r in records if r["round"] == 1)
    assert first["status"] == "Rejected"  # 마지막 회차만 덮어씀


def test_map_fitting_records_done_flag_with_zero_rounds_falls_back_to_due_date():
    # 완료 체크는 돼있는데 회차 로그 자체가 아예 없는 케이스(실제 데이터에서 52건 발견됨).
    raw_row = {
        "style_code": "S5",
        "fit_done": True,
        "fit_due": "2026-05-01",
        "etd": "2026-08-01",
        "detail": {"FIT": {"rounds": []}},
    }
    records = map_fitting_records(raw_row)
    assert len(records) == 1
    assert records[0]["status"] == "Approved"
    assert records[0]["round"] == 1
    assert records[0]["updated_at"] == "2026-05-01T00:00:00+00:00"


def test_map_fitting_records_done_flag_no_dates_at_all_falls_back_to_today():
    # due도 etd도 없는 극단 케이스(실제 데이터에서 4건 발견됨) - 그래도 완료로는 잡혀야 함.
    raw_row = {
        "style_code": "S7",
        "fit_done": True,
        "fit_due": None,
        "etd": None,
        "detail": {"FIT": {"rounds": []}},
    }
    records = map_fitting_records(raw_row)
    assert len(records) == 1
    assert records[0]["status"] == "Approved"
    assert records[0]["updated_at"].endswith("T00:00:00+00:00")


def test_map_fitting_records_fit_skip_uses_prep_confirm_date_not_future_due():
    # 보정 승인 후 FIT 생략(보정->PP 직행)된 케이스. FIT 회차 로그는 없지만 fit_done=True.
    # 진짜 날짜는 보정 승인일이어야 한다 - due/etd(미래일 수 있음)를 쓰면 안 됨.
    raw_row = {
        "style_code": "S8",
        "fit_done": True,
        "fit_due": None,
        "etd": "2026-09-16",  # 미래 shipping 날짜 - 이게 confirm_date로 쓰이면 안 됨
        "detail": {
            "보정": {"confirm_date": "2026-05-07", "rounds": []},
            "FIT": {"rounds": []},
        },
    }
    records = map_fitting_records(raw_row)
    assert len(records) == 1
    assert records[0]["status"] == "Approved"
    assert records[0]["updated_at"] == "2026-05-07T00:00:00+00:00"


def test_map_fitting_records_future_fallback_date_capped_at_today():
    from datetime import date
    raw_row = {
        "style_code": "S9",
        "fit_done": True,
        "fit_due": "2099-01-01",  # 미래
        "etd": None,
        "detail": {"FIT": {"rounds": []}},
    }
    records = map_fitting_records(raw_row)
    assert len(records) == 1
    assert records[0]["updated_at"] == f"{date.today().isoformat()}T00:00:00+00:00"


def test_map_fitting_records_not_done_and_zero_rounds_produces_nothing():
    raw_row = {
        "style_code": "S6",
        "fit_done": False,
        "detail": {"FIT": {"rounds": []}},
    }
    assert map_fitting_records(raw_row) == []


if __name__ == "__main__":
    test_map_style_row()
    test_map_fitting_records_converts_round_label_to_number()
    test_map_fitting_records_skips_empty_stages()
    test_map_fitting_records_falls_back_to_received_date()
    test_map_fitting_records_skips_rounds_without_any_date()
    test_map_fitting_records_done_flag_overrides_last_round_status()
    test_map_fitting_records_done_flag_with_zero_rounds_falls_back_to_due_date()
    test_map_fitting_records_done_flag_no_dates_at_all_falls_back_to_today()
    test_map_fitting_records_fit_skip_uses_prep_confirm_date_not_future_due()
    test_map_fitting_records_future_fallback_date_capped_at_today()
    test_map_fitting_records_not_done_and_zero_rounds_produces_nothing()
    print("OK: test_sync_26fw")
