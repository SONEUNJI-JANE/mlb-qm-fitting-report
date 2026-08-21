import os
import re
from datetime import date

DELIVERY_DATE_SETTING_KEY = "mlb_qm_delivery_date_overrides"
_PRODUCT_CODE_PREFIX = re.compile(r"^[A-Z]\d{2}[A-Z](.+)$")

_KG_PROXY_URL = "https://dcsai.fnf.co.kr/server/proxy/kg"
_DAISY_ENDPOINT = "/metrics/kr/scm/sourcing/order-recaps"
_BRAND_CODE = "M"  # MLB
_SEASONS = ["26F", "27S"]
_PAGE_SIZE = 5000


def strip_product_code_prefix(product_code: str) -> str:
    """DCS AI 소싱 API의 product_code(예: "M26F3ABN01666")에서 브랜드+시즌 접두어(4글자)를
    떼고 우리 style_code(예: "3ABN01666")와 맞춘다."""
    m = _PRODUCT_CODE_PREFIX.match(product_code or "")
    return m.group(1) if m else product_code


def aggregate_delivery_overrides(rows: list[dict]) -> dict:
    """get_kr_scm_sourcing_order_recaps 응답 rows -> {style_code: 가장 빠른 expected_arrival_date}.
    한 style에 색상/PO가 여러 개면 각기 다른 입고예정일이 있는데, 가장 빠른 날짜를 보수적으로
    (=일찍부터 챙겨야 할 기준으로) 대표값으로 쓴다."""
    overrides: dict = {}
    for row in rows:
        style_code = strip_product_code_prefix(row.get("product_code"))
        arrival = row.get("expected_arrival_date")
        if not arrival:
            continue
        current = overrides.get(style_code)
        if current is None or arrival < current:
            overrides[style_code] = arrival
    return overrides


def top_submit_to_shipment_gap_days(rows: list[dict]) -> list[int]:
    """top_submit_date -> expected_shipment_date 실측 갭(영업일 아님, 달력일). "선적 며칠 전에
    TOP이 끝나야 하는지"를 감이 아니라 과거 실적으로 답하기 위한 통계용. 음수/이상치(200일 초과)는 skip."""
    gaps = []
    for row in rows:
        top_submit = row.get("top_submit_date")
        shipment = row.get("expected_shipment_date")
        if not (top_submit and shipment):
            continue
        gap = (date.fromisoformat(shipment[:10]) - date.fromisoformat(top_submit[:10])).days
        if 0 <= gap <= 200:
            gaps.append(gap)
    return gaps


def _fetch_daisy_page(api_key: str, endpoint: str, params: dict) -> dict:
    """dcs-ai-cli/MCP 없이 KG 프록시를 직접 호출한다. dcs-ai-cli fetch는 daisy 태그 라우팅을
    지원 안 해서(2026-08-20 확인, 404) 쓸 수 없었는데, 프록시 자체를 직접 쳐보니
    "api-tags" 헤더(소문자 하이픈)로 daisy 업스트림까지 정상 라우팅됨을 확인했다
    (2026-08-21). query string은 url에 직접 붙여야 한다 — body의 별도 params 필드는 안 먹힘."""
    import requests
    from urllib.parse import urlencode

    query = urlencode(params, doseq=True)
    resp = requests.post(
        _KG_PROXY_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "api-tags": "fnf-daisy-api",
        },
        json={"url": f"{endpoint}?{query}", "method": "GET"},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_sourcing_order_recaps(api_key: str, season: str) -> list[dict]:
    """브랜드 M, 시즌 하나의 한국 소싱 오더요약 전량을 페이징해서 가져온다."""
    rows = []
    page = 1
    while True:
        params = {"brand_code": _BRAND_CODE, "season": season, "page_size": _PAGE_SIZE, "page": page}
        result = _fetch_daisy_page(api_key, _DAISY_ENDPOINT, params)
        page_rows = result["data"]
        rows.extend(page_rows)
        if not result["pagination"]["has_next"]:
            break
        page += 1
    return rows


def sync_delivery_dates(settings: dict) -> dict:
    from src.service.mlb_qm_fitting_report.supabase_client import upsert_setting
    import json

    api_key = os.environ["DCSAI_API_KEY"]
    all_rows = []
    for season in _SEASONS:
        all_rows.extend(fetch_sourcing_order_recaps(api_key, season))

    overrides = aggregate_delivery_overrides(all_rows)
    upsert_setting(settings, DELIVERY_DATE_SETTING_KEY, json.dumps(overrides))

    gaps = top_submit_to_shipment_gap_days(all_rows)
    return {"rows": len(all_rows), "styles": len(overrides), "top_ship_gap_n": len(gaps)}


if __name__ == "__main__":
    from src.service.mlb_qm_fitting_report.config import load_settings

    settings = load_settings()
    result = sync_delivery_dates(settings)
    print(f"synced: {result}")
