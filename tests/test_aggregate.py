import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.aggregate import compute_progress, build_raw_rows

STYLES = [
    {"style_code": "A1", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-07-20", "pp_due": "2026-08-10", "top_due": "2026-09-01"},
    {"style_code": "A2", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-08-05", "pp_due": "2026-08-25", "top_due": "2026-09-15"},
]

RECORDS = [
    {"style_code": "A1", "stage": "FIT", "round": 1, "status": "Approved", "updated_at": "2026-07-15T00:00:00Z"},
    {"style_code": "A2", "stage": "FIT", "round": 1, "status": "Rejected", "updated_at": "2026-07-28T00:00:00Z"},
]


def test_total_vs_baseline_fit():
    as_of = date(2026, 7, 31)
    result = compute_progress(STYLES, RECORDS, as_of)

    fit_td = result["27SS"]["TD"]["FIT"]
    # 총량 대비: 2개 대상 중 1개(A1) Approved
    assert fit_td["total_done"] == 1, fit_td
    assert fit_td["total_all"] == 2, fit_td

    # 기준대비: qc_due <= 2026-07-31인 스타일은 A1(07-20)만. A2(08-05)는 아직 안 옴.
    assert fit_td["baseline_done"] == 1, fit_td
    assert fit_td["baseline_all"] == 1, fit_td


def test_fit_is_td_pp_top_are_qa_regardless_of_owner_fields():
    # 담당은 역할 기준: FIT=TD, PP/TOP=QA. styles.qa 값이 비어있어도(27SS 실제 상황) PP/TOP은 QA로 집계돼야 함.
    as_of = date(2026, 7, 31)
    styles = [
        {"style_code": "B1", "season": "27SS", "td": "김철수", "qa": "", "qc_due": "2026-07-20", "pp_due": "2026-08-10", "top_due": "2026-09-01"},
    ]
    records = [
        {"style_code": "B1", "stage": "PP", "round": 1, "status": "Approved", "updated_at": "2026-07-20T00:00:00Z"},
    ]
    result = compute_progress(styles, records, as_of)
    assert "PP" not in result["27SS"]["TD"], result["27SS"]["TD"]
    assert result["27SS"]["QA"]["PP"]["total_all"] == 1, result["27SS"]["QA"]
    assert result["27SS"]["QA"]["PP"]["total_done"] == 1, result["27SS"]["QA"]


def test_drop_styles_excluded():
    as_of = date(2026, 7, 31)
    styles = STYLES + [
        {"style_code": "A3", "season": "27SS", "td": "김철수", "qa": "이영희", "co": "DROP", "qc_due": "2026-07-20", "pp_due": "2026-08-10", "top_due": "2026-09-01"},
    ]
    records = RECORDS + [
        {"style_code": "A3", "stage": "FIT", "round": 1, "status": "Approved", "updated_at": "2026-07-15T00:00:00Z"},
    ]
    result = compute_progress(styles, records, as_of)
    fit_td = result["27SS"]["TD"]["FIT"]
    assert fit_td["total_all"] == 2, fit_td  # A3(DROP) excluded, still just A1/A2


def test_build_raw_rows_includes_full_round_history():
    styles = [
        {"style_code": "C1", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-07-20", "pp_due": "2026-08-10", "top_due": "2026-09-01"},
    ]
    records = [
        {"style_code": "C1", "stage": "FIT", "round": 1, "status": "Rejected",
         "received_date": "2026-07-10", "delivered_date": "2026-07-13", "updated_at": "2026-07-13T00:00:00Z"},
        {"style_code": "C1", "stage": "FIT", "round": 2, "status": "Approved",
         "received_date": "2026-07-28", "delivered_date": "2026-07-30", "updated_at": "2026-07-30T00:00:00Z"},
    ]
    result = build_raw_rows(styles, records)
    fit_detail = result["27SS"][0]["detail"]["FIT"]

    # 최신 회차 기준 요약 필드는 그대로 유지
    assert fit_detail["round"] == "2ND"
    assert fit_detail["status"] == "Approved"

    # 새로 추가된 전체 회차 이력
    rounds = fit_detail["rounds"]
    assert len(rounds) == 2
    assert rounds[0]["round"] == "1ST"
    assert rounds[0]["status"] == "Rejected"
    assert rounds[1]["round"] == "2ND"
    assert rounds[1]["status"] == "Approved"
    assert fit_detail["first_received"] == "2026-07-10"

    # 접수일(샘플 들어온 날)과 전달일(결과 내보낸 날)은 서로 다른 값이어야 한다 —
    # "내보낸 뒤 며칠 만에 다음 샘플이 들어왔나"를 재려면 둘이 구분돼야 한다.
    assert rounds[0]["received"] == "2026-07-10" and rounds[0]["confirm_date"] == "2026-07-13"
    assert rounds[1]["received"] == "2026-07-28" and rounds[1]["confirm_date"] == "2026-07-30"


def test_build_raw_rows_falls_back_when_dates_missing():
    """전달일이 비면 피팅일 -> updated_at 순으로 떨어지고, 접수일은 없으면 None으로 둔다
    (updated_at으로 때우면 리드타임이 0일로 잡혀 평균이 망가진다)."""
    styles = [{"style_code": "C2", "season": "27SS", "qc_due": "2026-07-20"}]
    records = [
        {"style_code": "C2", "stage": "FIT", "round": 1, "status": "Rejected",
         "received_date": None, "delivered_date": None, "fitting_date": "2026-07-12",
         "updated_at": "2026-07-19T00:00:00Z"},
    ]
    detail = build_raw_rows(styles, records)["27SS"][0]["detail"]["FIT"]
    assert detail["rounds"][0]["received"] is None
    assert detail["rounds"][0]["confirm_date"] == "2026-07-12"  # 피팅일로 폴백
    assert detail["first_received"] is None


if __name__ == "__main__":
    test_total_vs_baseline_fit()
    test_fit_is_td_pp_top_are_qa_regardless_of_owner_fields()
    test_drop_styles_excluded()
    test_build_raw_rows_includes_full_round_history()
    test_build_raw_rows_falls_back_when_dates_missing()
    print("OK: test_aggregate")
