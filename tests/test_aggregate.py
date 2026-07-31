import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.aggregate import compute_progress

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


def test_qa_owner_mirrors_td_when_qa_field_set():
    as_of = date(2026, 7, 31)
    result = compute_progress(STYLES, RECORDS, as_of)
    fit_qa = result["27SS"]["QA"]["FIT"]
    assert fit_qa["total_all"] == 2, fit_qa


if __name__ == "__main__":
    test_total_vs_baseline_fit()
    test_qa_owner_mirrors_td_when_qa_field_set()
    print("OK: test_aggregate")
