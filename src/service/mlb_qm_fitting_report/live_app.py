import time
from datetime import date
from typing import Callable

from fastapi import FastAPI, Response

from src.service.mlb_qm_fitting_report.config import load_settings, resolve_as_of_date, week_id_for
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records
from src.service.mlb_qm_fitting_report.aggregate import compute_progress, build_raw_rows
from src.service.mlb_qm_fitting_report.report_builder import build_report_html

SEASON = "27SS"

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
    """27SS만 걸러서 report_builder.build_report_html이 기대하는 snapshots shape으로 만든다."""
    as_of_date = resolve_as_of_date(settings, run_date=date.today())
    week_id = week_id_for(as_of_date)

    styles = [s for s in fetch_styles(settings) if s.get("season") == SEASON]
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
