import json
import sys
from datetime import date
from unittest.mock import patch

sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from src.service.mlb_qm_fitting_report.live_app import app, SnapshotCache


def test_healthcheck():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_cache_returns_fresh_value_within_ttl():
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        return {"n": calls["n"]}

    cache = SnapshotCache(ttl_seconds=60)
    data1, stale1 = cache.get(fetch)
    data2, stale2 = cache.get(fetch)

    assert data1 == {"n": 1}
    assert data2 == {"n": 1}  # 두 번째 호출은 캐시에서 옴, fetch 다시 안 부름
    assert stale1 is False
    assert stale2 is False
    assert calls["n"] == 1


def test_cache_falls_back_to_stale_on_fetch_error():
    calls = {"n": 0}

    def fetch():
        calls["n"] += 1
        if calls["n"] == 1:
            return {"n": 1}
        raise RuntimeError("supabase down")

    cache = SnapshotCache(ttl_seconds=0)  # 매번 새로 fetch 시도하게
    data1, stale1 = cache.get(fetch)
    data2, stale2 = cache.get(fetch)  # ttl=0이라 다시 fetch 시도 -> 실패 -> stale 캐시 반환

    assert data1 == {"n": 1}
    assert stale1 is False
    assert data2 == {"n": 1}
    assert stale2 is True


def test_cache_raises_when_no_prior_success():
    def fetch():
        raise RuntimeError("supabase down")

    cache = SnapshotCache(ttl_seconds=60)
    try:
        cache.get(fetch)
        assert False, "expected RuntimeError"
    except RuntimeError:
        pass


STYLES_FIXTURE = [
    {
        "style_code": "S1", "item": "DK", "quarter": "Main TS", "season": "27SS",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    },
    {
        # 26FW도 SEASONS에 들어있으니 같이 나와야 함
        "style_code": "S2", "item": "DK", "quarter": "Main TS", "season": "26FW",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    },
    {
        # SEASONS에 없는 시즌은 섞이면 안 됨
        "style_code": "S3", "item": "DK", "quarter": "Main TS", "season": "25FW",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    },
    {
        # 26FW인데 sync_26fw가 저장한 "실제 엑셀 목록"엔 없는 스타일(다른 시스템이 얹어놓은 것) -> 빠져야 함
        "style_code": "S4", "item": "DK", "quarter": "Main TS", "season": "26FW",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    },
]
RECORDS_FIXTURE = [
    {"style_code": "S1", "stage": "FIT", "round": 1, "status": "Approved", "updated_at": "2026-01-01T00:00:00"},
]


_FROZEN_KST_TODAY = date(2026, 8, 7)


def _fake_settings_store(initial: dict = None):
    """fetch_setting/upsert_setting을 실제 상태처럼 흉내내는 인메모리 store."""
    store = dict(initial or {})

    def fake_fetch(settings, key):
        return store.get(key)

    def fake_upsert(settings, key, value):
        store[key] = value

    return store, fake_fetch, fake_upsert


def test_current_live_as_of_on_friday_uses_today():
    from src.service.mlb_qm_fitting_report.live_app import current_live_as_of
    friday = date(2026, 8, 7)  # 실제로 금요일
    assert current_live_as_of(friday) == friday


def test_current_live_as_of_on_weekday_uses_last_friday():
    from src.service.mlb_qm_fitting_report.live_app import current_live_as_of
    monday = date(2026, 8, 10)
    assert current_live_as_of(monday) == date(2026, 8, 7)  # 지난주 금요일


def test_friday_of_week_id():
    from src.service.mlb_qm_fitting_report.live_app import friday_of_week_id
    assert friday_of_week_id("2026-W32") == date(2026, 8, 7)


def test_compute_week_data_excludes_records_after_as_of_date():
    """과거 주차를 얼릴 때, 그 날짜 이후에 확정된 상태는 반영되면 안 된다(그래야 지난주/이번주가
    실제로 다르게 나옴 — 안 그러면 항상 '지금 상태'로만 계산돼서 둘이 똑같아 보이는 버그가 남)."""
    from src.service.mlb_qm_fitting_report.live_app import _compute_week_data

    styles = [{
        "style_code": "S1", "item": "DK", "quarter": "Main TS", "season": "27SS",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    }]
    records = [
        {"style_code": "S1", "stage": "FIT", "round": 1, "status": "Rejected", "updated_at": "2026-07-25T00:00:00"},
        {"style_code": "S1", "stage": "FIT", "round": 2, "status": "Approved", "updated_at": "2026-08-05T00:00:00"},
    ]
    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=styles), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=records), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", return_value=None):
        past_week = _compute_week_data(settings, date(2026, 7, 31))  # 2ND(8/5)는 아직 안 일어남
        current_week = _compute_week_data(settings, date(2026, 8, 7))  # 2ND(8/5)까지 반영됨

    assert past_week["progress"]["27SS"]["TD"]["FIT"]["total_done"] == 0  # 아직 Rejected 상태였음
    assert current_week["progress"]["27SS"]["TD"]["FIT"]["total_done"] == 1  # 지금은 Approved


def test_build_snapshot_payload_first_visit_only_creates_current_week():
    from src.service.mlb_qm_fitting_report.live_app import build_snapshot_payload

    store, fake_fetch, fake_upsert = _fake_settings_store()
    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", side_effect=fake_fetch), \
         patch("src.service.mlb_qm_fitting_report.live_app.upsert_setting", side_effect=fake_upsert), \
         patch("src.service.mlb_qm_fitting_report.live_app.current_live_as_of", return_value=date(2026, 8, 7)), \
         patch("src.service.mlb_qm_fitting_report.live_app.kst_today", return_value=_FROZEN_KST_TODAY):
        payload = build_snapshot_payload(settings)

    assert list(payload["weeks"].keys()) == ["2026-W32"]
    week = payload["weeks"]["2026-W32"]
    assert week["as_of_date"] == "2026-08-07"
    assert set(week["raw"].keys()) == {"27SS", "26FW"}
    assert len(week["raw"]["26FW"]) == 2  # valid 목록 없어서 필터 없이 다 나옴(fail open): S2, S4


def test_build_snapshot_payload_freezes_previous_week_on_rollover():
    from src.service.mlb_qm_fitting_report.live_app import build_snapshot_payload

    # 지난주(2026-W31)까지 이미 라이브였던 상태로 시작.
    store, fake_fetch, fake_upsert = _fake_settings_store({"mlb_qm_live_week_id": "2026-W31"})
    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", side_effect=fake_fetch), \
         patch("src.service.mlb_qm_fitting_report.live_app.upsert_setting", side_effect=fake_upsert), \
         patch("src.service.mlb_qm_fitting_report.live_app.current_live_as_of", return_value=date(2026, 8, 7)), \
         patch("src.service.mlb_qm_fitting_report.live_app.kst_today", return_value=_FROZEN_KST_TODAY):
        payload = build_snapshot_payload(settings)

    weeks = payload["weeks"]
    assert set(weeks.keys()) == {"2026-W31", "2026-W32"}
    assert weeks["2026-W31"]["as_of_date"] == "2026-07-31"  # 얼려진 지난주
    assert weeks["2026-W32"]["as_of_date"] == "2026-08-07"  # 이번주(라이브)
    assert store["mlb_qm_live_week_id"] == "2026-W32"
    assert "mlb_qm_snapshot_2026-W31" in store  # 얼린 스냅샷이 저장됨


def test_build_snapshot_payload_does_not_recompute_already_frozen_week():
    from src.service.mlb_qm_fitting_report.live_app import build_snapshot_payload

    frozen_payload = json.dumps({"as_of_date": "2026-07-31", "progress": {}, "warnings": [], "raw": {"FROZEN": True}})
    store, fake_fetch, fake_upsert = _fake_settings_store({
        "mlb_qm_live_week_id": "2026-W31",
        "mlb_qm_snapshot_2026-W31": frozen_payload,
        "mlb_qm_known_week_ids": '["2026-W31"]',
    })
    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", side_effect=fake_fetch), \
         patch("src.service.mlb_qm_fitting_report.live_app.upsert_setting", side_effect=fake_upsert), \
         patch("src.service.mlb_qm_fitting_report.live_app.current_live_as_of", return_value=date(2026, 8, 7)), \
         patch("src.service.mlb_qm_fitting_report.live_app.kst_today", return_value=_FROZEN_KST_TODAY):
        payload = build_snapshot_payload(settings)

    # 이미 얼려진 주는 그 값(FROZEN 마커) 그대로 재사용, 새로 계산 안 함
    assert payload["weeks"]["2026-W31"]["raw"] == {"FROZEN": True}


def test_root_endpoint_returns_html():
    from src.service.mlb_qm_fitting_report.live_app import app as live_app

    store, fake_fetch, fake_upsert = _fake_settings_store()
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", side_effect=fake_fetch), \
         patch("src.service.mlb_qm_fitting_report.live_app.upsert_setting", side_effect=fake_upsert):
        client = TestClient(live_app)
        resp = client.get("/")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "MLB QM Weekly Analysis" in resp.text


if __name__ == "__main__":
    test_healthcheck()
    test_cache_returns_fresh_value_within_ttl()
    test_cache_falls_back_to_stale_on_fetch_error()
    test_cache_raises_when_no_prior_success()
    test_current_live_as_of_on_friday_uses_today()
    test_current_live_as_of_on_weekday_uses_last_friday()
    test_friday_of_week_id()
    test_compute_week_data_excludes_records_after_as_of_date()
    test_build_snapshot_payload_first_visit_only_creates_current_week()
    test_build_snapshot_payload_freezes_previous_week_on_rollover()
    test_build_snapshot_payload_does_not_recompute_already_frozen_week()
    test_root_endpoint_returns_html()
    print("OK: test_live_app")
