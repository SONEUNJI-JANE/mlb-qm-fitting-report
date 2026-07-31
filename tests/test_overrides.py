import sys

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.overrides import load_overrides, apply_overrides

PROGRESS = {
    "27SS": {
        "TD": {"FIT": {"total_done": 1, "total_all": 2, "baseline_done": 1, "baseline_all": 1}},
        "QA": {},
    }
}


def test_load_overrides_missing_file_returns_empty():
    assert load_overrides("2099-W01", overrides_dir="overrides") == []


def test_apply_overrides_replaces_total_only():
    overrides = [{"season": "27SS", "stage": "FIT", "owner_type": "TD", "override_numerator": 30, "override_denominator": 32}]
    result = apply_overrides(PROGRESS, overrides)

    fit_td = result["27SS"]["TD"]["FIT"]
    assert fit_td["total_done"] == 30, fit_td
    assert fit_td["total_all"] == 32, fit_td
    assert fit_td["baseline_done"] == 1, fit_td  # baseline은 그대로

    # 원본은 불변
    assert PROGRESS["27SS"]["TD"]["FIT"]["total_done"] == 1


if __name__ == "__main__":
    test_load_overrides_missing_file_returns_empty()
    test_apply_overrides_replaces_total_only()
    print("OK: test_overrides")
