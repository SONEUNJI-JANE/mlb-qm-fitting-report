import re
from datetime import date

DELIVERY_DATE_SETTING_KEY = "mlb_qm_delivery_date_overrides"
_PRODUCT_CODE_PREFIX = re.compile(r"^[A-Z]\d{2}[A-Z](.+)$")


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


# 이 스크립트는 dcs-ai-cli로 자동 실행할 수 없다 — get_kr_scm_sourcing_order_recaps가
# "fnf-daisy-api" 태그로 라우팅되는데 dcs-ai-cli fetch가 이 라우팅을 아직 지원하지 않아
# 404가 난다(2026-08-20 확인). 그래서 지금은 Claude Code 세션 안에서 dcsai MCP
# (execute_kg_api_to_context)로 직접 페이징 조회 -> aggregate_delivery_overrides() ->
# upsert_setting(DELIVERY_DATE_SETTING_KEY)으로 수동 반영해야 한다. CLI가 daisy 라우팅을
# 지원하게 되면 sync_27ss_due.py처럼 Task Scheduler로 자동화할 수 있다.
if __name__ == "__main__":
    print(
        "이 스크립트는 자동 실행용이 아님 — Claude Code 세션에서 dcsai MCP로 데이터를 받아 "
        "aggregate_delivery_overrides()에 넣고 Supabase에 upsert하는 식으로 수동 실행할 것. "
        "자세한 내용은 파일 상단 주석 참고."
    )
