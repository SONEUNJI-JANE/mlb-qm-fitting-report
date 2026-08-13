import json
import time
from datetime import date, timedelta
from typing import Callable

from fastapi import FastAPI, Response

from src.service.mlb_qm_fitting_report.config import week_id_for, load_settings
from src.service.mlb_qm_fitting_report.supabase_client import (
    fetch_styles, fetch_fitting_records, fetch_setting, upsert_setting,
)
from src.service.mlb_qm_fitting_report.aggregate import compute_progress, build_raw_rows
from src.service.mlb_qm_fitting_report.report_builder import build_report_html
from src.service.mlb_qm_fitting_report.sync_26fw import STYLE_CODES_SETTING_KEY

SEASONS = ["27SS", "26FW"]
LIVE_WEEK_SETTING_KEY = "mlb_qm_live_week_id"
KNOWN_WEEKS_SETTING_KEY = "mlb_qm_known_week_ids"

app = FastAPI()


def current_live_as_of(today: date = None) -> date:
    """이번 주의 기준일(금요일). 오늘이 금요일이면 오늘, 아니면 가장 최근 지난 금요일
    (주말이면 이번 주 금요일, 월~목이면 지난주 금요일) — "이번 주는 계속 실시간"의 기준."""
    today = today or date.today()
    days_since_friday = (today.isoweekday() - 5) % 7  # ISO: Mon=1..Sun=7, Fri=5
    return today - timedelta(days=days_since_friday)


def friday_of_week_id(week_id: str) -> date:
    """'2026-W31' 같은 week_id -> 그 ISO 주의 금요일 날짜."""
    year, week = week_id.split("-W")
    return date.fromisocalendar(int(year), int(week), 5)


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


def _compute_week_data(settings: dict, as_of_date: date) -> dict:
    """Supabase 시즌(27SS/26FW)만 걸러서 그 as_of_date 기준 진행률/raw를 계산한다.

    styles 테이블은 26FW 쪽을 다른 시스템(PLM)도 같이 쓰고 있어서 엑셀에 없는 스타일이
    섞여 들어올 수 있다 — sync_26fw.py가 저장해둔 "실제 엑셀에 있던 정확한 목록"으로
    26FW만 한 번 더 걸러서 항상 엑셀 기준 숫자와 일치하게 한다.

    fitting_records는 updated_at(그 상태가 확정된 시점)이 as_of_date보다 나중인 건
    "그 시점엔 아직 일어나지 않은 일"이라 제외한다 — 안 그러면 과거 주차를 얼려도
    "그 날짜 기준 실제 상태"가 아니라 항상 "지금 상태"가 저장돼서 지난 주/이번 주가
    똑같이 보이는 문제가 생긴다."""
    styles = [s for s in fetch_styles(settings) if s.get("season") in SEASONS]

    valid_26fw = fetch_setting(settings, STYLE_CODES_SETTING_KEY)
    if valid_26fw:
        valid_26fw_codes = set(json.loads(valid_26fw))
        styles = [s for s in styles if s.get("season") != "26FW" or s["style_code"] in valid_26fw_codes]

    records = fetch_fitting_records(settings)
    style_codes = {s["style_code"] for s in styles}
    as_of_iso = as_of_date.isoformat()
    records = [r for r in records if r["style_code"] in style_codes and r["updated_at"][:10] <= as_of_iso]

    return {
        "as_of_date": as_of_date.isoformat(),
        "progress": compute_progress(styles, records, as_of_date),
        "warnings": [],
        "raw": build_raw_rows(styles, records),
    }


def _snapshot_setting_key(week_id: str) -> str:
    return f"mlb_qm_snapshot_{week_id}"


def _remark_setting_key(week_id: str) -> str:
    return f"mlb_qm_remark_{week_id}"


def build_snapshot_payload(settings: dict) -> dict:
    """매주 금요일 기준으로 주차를 나눈다. 이번 주(금요일 지나기 전)는 요청마다 실시간
    재계산하고, 지난 주는 한 번 계산한 값을 Supabase settings 테이블에 얼려서 저장해두고
    그대로 재사용한다(주가 넘어간 뒤 처음 들어온 요청이 그 얼리기를 트리거한다 — 서버가
    상시 대기하는 스케줄러가 없어서, 정확히 금요일 자정이 아니라 그 이후 첫 방문 시점
    값으로 얼려진다. 값 자체는 날짜 단위 계산이라 지연 며칠 안엔 결과가 같다)."""
    current_as_of = current_live_as_of()
    current_week_id = week_id_for(current_as_of)

    known_weeks_raw = fetch_setting(settings, KNOWN_WEEKS_SETTING_KEY)
    known_weeks = json.loads(known_weeks_raw) if known_weeks_raw else []

    last_live_week = fetch_setting(settings, LIVE_WEEK_SETTING_KEY)
    if last_live_week and last_live_week != current_week_id:
        if not fetch_setting(settings, _snapshot_setting_key(last_live_week)):
            frozen_as_of = friday_of_week_id(last_live_week)
            frozen_data = _compute_week_data(settings, frozen_as_of)
            upsert_setting(settings, _snapshot_setting_key(last_live_week), json.dumps(frozen_data))
        if last_live_week not in known_weeks:
            known_weeks.append(last_live_week)
    if last_live_week != current_week_id:
        upsert_setting(settings, LIVE_WEEK_SETTING_KEY, current_week_id)

    if current_week_id not in known_weeks:
        known_weeks.append(current_week_id)
    upsert_setting(settings, KNOWN_WEEKS_SETTING_KEY, json.dumps(known_weeks))

    weeks = {}
    for week_id in known_weeks:
        if week_id == current_week_id:
            continue
        frozen_json = fetch_setting(settings, _snapshot_setting_key(week_id))
        if frozen_json:
            weeks[week_id] = json.loads(frozen_json)

    # current_as_of(지난 금요일 또는 오늘)는 week_id 계산(=주 구간 판별)용일 뿐,
    # 아직 얼리지 않은 이번 주 데이터는 실제 오늘 날짜까지 실시간으로 다 보여줘야 한다.
    # current_as_of를 그대로 쓰면 월~목 사이엔 지난 금요일 이후 데이터가 필터링돼 누락된다.
    weeks[current_week_id] = _compute_week_data(settings, date.today())

    # 비고는 얼린 스냅샷 안에 같이 저장하지 않는다 — 얼린 뒤에도 계속 수정할 수 있어야 하므로
    # (브라우저가 직접 저장하는 값이라) 매번 최신값을 따로 붙여준다.
    for week_id, week_data in weeks.items():
        remarks_raw = fetch_setting(settings, _remark_setting_key(week_id))
        week_data["remarks"] = json.loads(remarks_raw) if remarks_raw else {}

    return {"weeks": weeks}


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
