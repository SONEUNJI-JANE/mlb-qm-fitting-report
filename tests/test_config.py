import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.config import resolve_as_of_date, week_id_for


def test_resolve_as_of_date_default_friday_from_monday():
    # 2026-08-03은 월요일. 직전 금요일은 2026-07-31.
    settings = {"as_of_weekday": "FRI", "as_of_date_override": None}
    result = resolve_as_of_date(settings, run_date=date(2026, 8, 3))
    assert result == date(2026, 7, 31), result


def test_resolve_as_of_date_from_friday_itself():
    # 실행일 자체가 금요일이면 그 날짜가 직전 금요일(당일 포함 X, 반드시 이전 주)
    settings = {"as_of_weekday": "FRI", "as_of_date_override": None}
    result = resolve_as_of_date(settings, run_date=date(2026, 7, 31))
    assert result == date(2026, 7, 24), result


def test_resolve_as_of_date_override_wins():
    settings = {"as_of_weekday": "FRI", "as_of_date_override": "2026-07-30"}
    result = resolve_as_of_date(settings, run_date=date(2026, 8, 3))
    assert result == date(2026, 7, 30), result


def test_week_id_for():
    assert week_id_for(date(2026, 7, 31)) == "2026-W31", week_id_for(date(2026, 7, 31))


if __name__ == "__main__":
    test_resolve_as_of_date_default_friday_from_monday()
    test_resolve_as_of_date_from_friday_itself()
    test_resolve_as_of_date_override_wins()
    test_week_id_for()
    print("OK: test_config")
