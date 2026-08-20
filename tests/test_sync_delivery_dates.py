import sys
sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.sync_delivery_dates import (
    strip_product_code_prefix, aggregate_delivery_overrides, top_submit_to_shipment_gap_days,
)


def test_strip_product_code_prefix():
    assert strip_product_code_prefix("M26F3ABN01666") == "3ABN01666"
    assert strip_product_code_prefix("X27S3ADKS3171") == "3ADKS3171"
    assert strip_product_code_prefix("") == ""
    assert strip_product_code_prefix(None) is None


def test_aggregate_delivery_overrides_picks_earliest_across_pos_and_colors():
    rows = [
        {"product_code": "M26F3ABN01666", "expected_arrival_date": "2026-08-09"},
        {"product_code": "M26F3ABN01666", "expected_arrival_date": "2026-07-26"},  # 더 이름 -> 대표값
        {"product_code": "M26F3ABNB0166", "expected_arrival_date": "2026-08-01"},
        {"product_code": "M26F3ABN01666", "expected_arrival_date": None},  # 날짜 없는 행은 skip
    ]
    result = aggregate_delivery_overrides(rows)
    assert result == {"3ABN01666": "2026-07-26", "3ABNB0166": "2026-08-01"}


def test_top_submit_to_shipment_gap_days_skips_missing_and_outliers():
    rows = [
        {"top_submit_date": "2026-06-13", "expected_shipment_date": "2026-07-10"},  # 27일
        {"top_submit_date": None, "expected_shipment_date": "2026-07-10"},
        {"top_submit_date": "2026-06-13", "expected_shipment_date": None},
        {"top_submit_date": "2026-06-13", "expected_shipment_date": "2027-06-13"},  # 365일, outlier skip
    ]
    gaps = top_submit_to_shipment_gap_days(rows)
    assert gaps == [27]


if __name__ == "__main__":
    test_strip_product_code_prefix()
    test_aggregate_delivery_overrides_picks_earliest_across_pos_and_colors()
    test_top_submit_to_shipment_gap_days_skips_missing_and_outliers()
    print("OK: test_sync_delivery_dates")
