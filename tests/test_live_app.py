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


def test_build_snapshot_payload_includes_27ss_and_26fw_only():
    from src.service.mlb_qm_fitting_report.live_app import build_snapshot_payload

    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", return_value='["S2"]'), \
         patch("src.service.mlb_qm_fitting_report.live_app.resolve_as_of_date", return_value=date(2026, 8, 6)):
        payload = build_snapshot_payload(settings)

    weeks = payload["weeks"]
    assert len(weeks) == 1
    week = next(iter(weeks.values()))
    assert week["as_of_date"] == "2026-08-06"
    assert set(week["progress"].keys()) == {"27SS", "26FW"}
    assert set(week["raw"].keys()) == {"27SS", "26FW"}
    assert week["raw"]["27SS"][0]["style_code"] == "S1"
    assert len(week["raw"]["26FW"]) == 1
    assert week["raw"]["26FW"][0]["style_code"] == "S2"  # S4는 valid 목록에 없어서 빠짐


def test_build_snapshot_payload_no_valid_list_keeps_all_26fw():
    """settings에 아직 목록이 없으면(첫 배포 등) 필터 없이 다 보여준다(fail open)."""
    from src.service.mlb_qm_fitting_report.live_app import build_snapshot_payload

    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", return_value=None), \
         patch("src.service.mlb_qm_fitting_report.live_app.resolve_as_of_date", return_value=date(2026, 8, 6)):
        payload = build_snapshot_payload(settings)

    week = next(iter(payload["weeks"].values()))
    assert len(week["raw"]["26FW"]) == 2  # S2, S4 둘 다


def test_root_endpoint_returns_html():
    from src.service.mlb_qm_fitting_report.live_app import app as live_app

    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_setting", return_value=None):
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
    test_build_snapshot_payload_includes_27ss_and_26fw_only()
    test_build_snapshot_payload_no_valid_list_keeps_all_26fw()
    test_root_endpoint_returns_html()
    print("OK: test_live_app")
