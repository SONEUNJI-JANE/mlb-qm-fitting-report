import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.snapshots import append_snapshot

PROGRESS = {"27SS": {"TD": {}, "QA": {}}}
WARNINGS = [{"style_code": "A2", "season": "27SS", "owner": "김철수", "rule": "x", "due_date": None, "days_to_due": None}]


def test_append_new_week_preserves_existing():
    existing = {"weeks": {"2026-W30": {"as_of_date": "2026-07-24", "progress": {}, "warnings": []}}}
    result = append_snapshot(existing, "2026-W31", date(2026, 7, 31), PROGRESS, WARNINGS)

    assert "2026-W30" in result["weeks"], result["weeks"].keys()
    assert result["weeks"]["2026-W31"]["as_of_date"] == "2026-07-31"
    assert result["weeks"]["2026-W31"]["progress"] == PROGRESS
    assert result["weeks"]["2026-W31"]["warnings"] == WARNINGS


def test_append_same_week_overwrites_not_duplicates():
    existing = {"weeks": {"2026-W31": {"as_of_date": "2026-07-31", "progress": {}, "warnings": []}}}
    result = append_snapshot(existing, "2026-W31", date(2026, 7, 31), PROGRESS, WARNINGS)

    assert len(result["weeks"]) == 1
    assert result["weeks"]["2026-W31"]["progress"] == PROGRESS


if __name__ == "__main__":
    test_append_new_week_preserves_existing()
    test_append_same_week_overwrites_not_duplicates()
    print("OK: test_snapshots")
