import shutil
import tempfile
from datetime import date, datetime

import openpyxl

_SHEET = "FIT TRACK CHART"
_HEADER_ROW = 8
_DATA_START_ROW = 9

_COL_STYLE = 3
_COL_TD = 11
_COL_QA = 13
_COL_FIT_DUE = 18
_COL_PP_DUE = 20
_COL_TOP_DUE = 22
_COL_FIT_DONE = 101
_COL_PP_DONE = 102
_COL_TOP_DONE = 103

STAGE_COLS = {"FIT": _COL_FIT_DONE, "PP": _COL_PP_DONE, "TOP": _COL_TOP_DONE}
DUE_COLS = {"FIT": _COL_FIT_DUE, "PP": _COL_PP_DUE, "TOP": _COL_TOP_DUE}


def _as_date(value):
    return value.date() if isinstance(value, datetime) else None


def read_fit_track_rows(path: str) -> list[dict]:
    # 사용자가 엑셀을 열어둔 채로 스케줄이 돌 수 있어 파일 잠금을 피하려고 임시 복사본을 읽는다.
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        shutil.copy2(path, tmp.name)
        wb = openpyxl.load_workbook(tmp.name, data_only=True)
    ws = wb[_SHEET]
    rows = []
    for r in ws.iter_rows(min_row=_DATA_START_ROW, values_only=True):
        style_code = r[_COL_STYLE]
        if not style_code or not isinstance(style_code, str):
            continue
        rows.append({
            "style_code": style_code,
            "td": r[_COL_TD],
            "qa": r[_COL_QA],
            "fit_due": _as_date(r[_COL_FIT_DUE]),
            "pp_due": _as_date(r[_COL_PP_DUE]),
            "top_due": _as_date(r[_COL_TOP_DUE]),
            "fit_done": r[_COL_FIT_DONE] == 1,
            "pp_done": r[_COL_PP_DONE] == 1,
            "top_done": r[_COL_TOP_DONE] == 1,
        })
    return rows


OWNER_BY_STAGE = {"FIT": "TD", "PP": "QA", "TOP": "QA"}


def compute_progress_from_xlsx(rows: list[dict], as_of_date: date) -> dict:
    result = {"TD": {}, "QA": {}}
    done_fields = {"FIT": "fit_done", "PP": "pp_done", "TOP": "top_done"}
    due_fields = {"FIT": "fit_due", "PP": "pp_due", "TOP": "top_due"}

    for row in rows:
        for stage in ("FIT", "PP", "TOP"):
            is_done = row[done_fields[stage]]
            due = row[due_fields[stage]]
            is_due = bool(due and due <= as_of_date)

            owner_type = OWNER_BY_STAGE[stage]
            bucket = result[owner_type].setdefault(
                stage, {"total_done": 0, "total_all": 0, "baseline_done": 0, "baseline_all": 0}
            )
            bucket["total_all"] += 1
            if is_done:
                bucket["total_done"] += 1
            if is_due:
                bucket["baseline_all"] += 1
                if is_done:
                    bucket["baseline_done"] += 1

    return result
