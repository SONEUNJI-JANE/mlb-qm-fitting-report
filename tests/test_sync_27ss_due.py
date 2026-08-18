import sys
sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.sync_27ss_due import read_due_overrides


def test_read_due_overrides_maps_o_p_r_s_columns(tmp_path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "▶27SS DATA "
    # 헤더는 3행, 데이터는 4행부터. O/P/R/S는 0-based 14/15/17/18 -> 1-based 15/16/18/19.
    header = [None] * 25
    ws.append([None] * 25)
    ws.append([None] * 25)
    ws.append(header)
    row = [None] * 25
    row[4] = "3ADKS3171"
    row[14] = "2026-09-30 00:00:00"
    row[15] = "2026-10-24 00:00:00"
    row[16] = "2026-11-13 00:00:00"  # PP 2차, 안 씀
    row[17] = "2026-11-18 00:00:00"
    row[18] = "2026-11-28 00:00:00"
    ws.append(row)

    path = tmp_path / "due.xlsx"
    wb.save(path)

    overrides = read_due_overrides(str(path))
    assert overrides == {
        "3ADKS3171": {
            "qc_due": "2026-09-30",
            "pp_due": "2026-10-24",
            "top_due": "2026-11-18",
            "top_due_2": "2026-11-28",
        }
    }


def test_read_due_overrides_skips_rows_without_style(tmp_path):
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "▶27SS DATA "
    ws.append([None] * 25)
    ws.append([None] * 25)
    ws.append([None] * 25)
    ws.append([None] * 25)  # style_code 없음

    path = tmp_path / "due.xlsx"
    wb.save(path)

    assert read_due_overrides(str(path)) == {}


if __name__ == "__main__":
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as d:
        test_read_due_overrides_maps_o_p_r_s_columns(Path(d))
    with tempfile.TemporaryDirectory() as d:
        test_read_due_overrides_skips_rows_without_style(Path(d))
    print("OK: test_sync_27ss_due")
