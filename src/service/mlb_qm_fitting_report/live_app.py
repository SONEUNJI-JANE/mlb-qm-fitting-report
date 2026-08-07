import json
import time
from datetime import date
from typing import Callable

from fastapi import FastAPI, Response

from src.service.mlb_qm_fitting_report.config import load_settings, resolve_as_of_date, week_id_for
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records, fetch_setting
from src.service.mlb_qm_fitting_report.aggregate import compute_progress, build_raw_rows
from src.service.mlb_qm_fitting_report.report_builder import build_report_html
from src.service.mlb_qm_fitting_report.sync_26fw import STYLE_CODES_SETTING_KEY

SEASONS = ["27SS", "26FW"]

app = FastAPI()


class SnapshotCache:
    """fetch_fn 결과를 ttl_seconds 동안 캐싱한다. fetch_fn이 실패하면 마지막
    성공값을 stale=True로 반환하고, 성공한 적이 없으면 예외를 그대로 던진다."""

    def __init__(self, ttl_seconds: int):
        self._ttl = ttl_seconds
        self._data = None
        self._fetched_at = 0.0

    def get(self, fetch_fn: Callable[[], dict]) -> tuple[dict, bool]:
        now = time.monotonic()
        if self._data is not None and (now - self._fetched_at) < self._ttl:
            return self._data, False
        try:
            fresh = fetch_fn()
        except Exception:
            if self._data is not None:
                return self._data, True
            raise
        self._data = fresh
        self._fetched_at = now
        return self._data, False


def build_snapshot_payload(settings: dict) -> dict:
    """Supabase 시즌(27SS/26FW)만 걸러서 report_builder.build_report_html이 기대하는
    snapshots shape으로 만든다. compute_progress/build_raw_rows가 이미 season별로
    그룹핑해서 반환하므로, 여기선 SEASONS에 속하는 스타일만 넘기면 나머지는 그대로 재사용된다.

    styles 테이블은 26FW 쪽을 다른 시스템(PLM)도 같이 쓰고 있어서 엑셀에 없는 스타일이
    섞여 들어올 수 있다 — sync_26fw.py가 저장해둔 "실제 엑셀에 있던 정확한 목록"으로
    26FW만 한 번 더 걸러서 항상 엑셀 기준 숫자와 일치하게 한다."""
    as_of_date = resolve_as_of_date(settings, run_date=date.today())
    week_id = week_id_for(as_of_date)

    styles = [s for s in fetch_styles(settings) if s.get("season") in SEASONS]

    valid_26fw = fetch_setting(settings, STYLE_CODES_SETTING_KEY)
    if valid_26fw:
        valid_26fw_codes = set(json.loads(valid_26fw))
        styles = [s for s in styles if s.get("season") != "26FW" or s["style_code"] in valid_26fw_codes]

    records = fetch_fitting_records(settings)
    style_codes = {s["style_code"] for s in styles}
    records = [r for r in records if r["style_code"] in style_codes]

    progress = compute_progress(styles, records, as_of_date)
    raw = build_raw_rows(styles, records)

    return {
        "weeks": {
            week_id: {
                "as_of_date": as_of_date.isoformat(),
                "progress": progress,
                "warnings": [],
                "raw": raw,
            }
        }
    }


_cache = SnapshotCache(ttl_seconds=300)  # 5분


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/")
def root():
    settings = load_settings()
    payload, is_stale = _cache.get(lambda: build_snapshot_payload(settings))
    html = build_report_html(payload, settings)
    headers = {"X-Data-Stale": "true"} if is_stale else {}
    return Response(content=html, media_type="text/html", headers=headers)
