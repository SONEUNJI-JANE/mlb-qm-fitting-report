import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.xlsx_source import compute_progress_from_xlsx

ROWS = [
    {"style_code": "A1", "td": "김철수", "qa": "이영희", "fit_due": date(2026, 7, 1), "pp_due": date(2026, 8, 1), "top_due": date(2026, 9, 1), "fit_done": True, "pp_done": True, "top_done": False},
    {"style_code": "A2", "td": "김철수", "qa": "이영희", "fit_due": date(2026, 7, 1), "pp_due": date(2026, 8, 1), "top_due": date(2026, 9, 1), "fit_done": True, "pp_done": False, "top_done": False},
]


def test_totals_from_done_flags():
    as_of = date(2026, 7, 31)
    result = compute_progress_from_xlsx(ROWS, as_of)
    assert result["TD"]["FIT"]["total_done"] == 2, result
    assert result["TD"]["FIT"]["total_all"] == 2, result
    assert result["QA"]["PP"]["total_done"] == 1, result
    assert result["QA"]["TOP"]["total_done"] == 0, result


def test_baseline_uses_due_dates():
    as_of = date(2026, 7, 31)
    result = compute_progress_from_xlsx(ROWS, as_of)
    # fit_due(7/1) and pp_due(8/1 not yet due) -> baseline only counts FIT as due
    assert result["TD"]["FIT"]["baseline_all"] == 2, result
    assert result["QA"]["PP"]["baseline_all"] == 0, result


if __name__ == "__main__":
    test_totals_from_done_flags()
    test_baseline_uses_due_dates()
    print("OK: test_xlsx_source")
