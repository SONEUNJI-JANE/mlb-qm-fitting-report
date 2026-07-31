# tests/test_chase.py
import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.chase import compute_chase_warnings

STYLES = [
    {"style_code": "A2", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-08-05", "pp_due": "2026-08-25", "top_due": "2026-09-15"},
]

RECORDS = [
    {"style_code": "A2", "stage": "FIT", "round": 1, "status": "Rejected", "updated_at": "2026-07-28T00:00:00Z"},
]


def test_fit_rejected_round1_warns_within_30_days_of_qc_due():
    # as_of=2026-07-31, qc_due=2026-08-05 → 5일 남음 <= 30일 임계값 → 경고
    as_of = date(2026, 7, 31)
    warnings = compute_chase_warnings(STYLES, RECORDS, as_of)
    assert len(warnings) == 1, warnings
    assert warnings[0]["style_code"] == "A2"
    assert warnings[0]["rule"].startswith("FIT Rej"), warnings[0]


def test_no_warning_when_far_from_due():
    as_of = date(2026, 6, 1)  # qc_due까지 65일 남음, 임계값 30일 초과 → 경고 없음
    warnings = compute_chase_warnings(STYLES, RECORDS, as_of)
    assert warnings == [], warnings


if __name__ == "__main__":
    test_fit_rejected_round1_warns_within_30_days_of_qc_due()
    test_no_warning_when_far_from_due()
    print("OK: test_chase")
