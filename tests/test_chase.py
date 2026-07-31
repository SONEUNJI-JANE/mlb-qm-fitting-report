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


def test_no_warning_when_already_past_due():
    # qc_due=2026-08-05, as_of=2026-09-01 → days_to_due=-27 (지남) → 경고 목록에서 제외
    as_of = date(2026, 9, 1)
    warnings = compute_chase_warnings(STYLES, RECORDS, as_of)
    assert warnings == [], warnings


def test_later_stage_wins_over_higher_round_earlier_stage():
    # FIT round3 Approved 보다 PP round2 Approved 가 진행상 더 뒤 단계 → PP 기록으로 resolve 되어야 함
    styles = [
        {"style_code": "B1", "season": "27SS", "td": "김철수", "qa": "이영희",
         "qc_due": "2026-08-05", "pp_due": "2026-08-25", "top_due": "2026-09-15"},
    ]
    records = [
        {"style_code": "B1", "stage": "FIT", "round": 3, "status": "Approved", "updated_at": "2026-07-20T00:00:00Z"},
        {"style_code": "B1", "stage": "PP", "round": 2, "status": "Approved", "updated_at": "2026-07-25T00:00:00Z"},
    ]
    # as_of=2026-08-10: pp_due까지 15일(<=20) → 잘못 FIT을 고르면 "FIT Approved→PP" 경고가 뜬다.
    # top_due까지는 36일(>28) → 올바르게 PP를 고르면 "PP Approved→TOP" 경고는 뜨지 않는다.
    as_of = date(2026, 8, 10)
    warnings = compute_chase_warnings(styles, records, as_of)
    assert warnings == [], warnings  # 경고가 뜨면 FIT 기록이 잘못 선택된 것


def test_thresholds_override_widens_window():
    # 기본 30일 임계값이면 qc_due까지 65일 남은 건 경고 안 뜸(test_no_warning_when_far_from_due).
    # config에서 이 규칙 임계값을 90일로 넓히면 같은 상황에서 경고가 떠야 함.
    as_of = date(2026, 6, 1)
    thresholds = {"FIT Rej/IntRej 1차 → 다음 FIT 샘플 접수": 90}
    warnings = compute_chase_warnings(STYLES, RECORDS, as_of, thresholds=thresholds)
    assert len(warnings) == 1, warnings


if __name__ == "__main__":
    test_fit_rejected_round1_warns_within_30_days_of_qc_due()
    test_no_warning_when_far_from_due()
    test_no_warning_when_already_past_due()
    test_later_stage_wins_over_higher_round_earlier_stage()
    test_thresholds_override_widens_window()
    print("OK: test_chase")
