import json

import requests

_STYLES_FIELDS = "style_code,item,quarter,season,td,qa,co,qc_due,pp_due,top_due,vendor,washed,qty_kr,qty_cn,earliest_etd"
_FITTING_FIELDS = "style_code,stage,round,status,updated_at"
_REPORT_CONFIG_KEY = "mlb_qm_fitting_report_config"


def _headers(settings: dict) -> dict:
    key = settings["supabase_anon_key"]
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _get_all(settings: dict, table: str, fields: str, order: str) -> list[dict]:
    url = f"{settings['supabase_url']}/rest/v1/{table}"
    headers = _headers(settings)
    headers["Range-Unit"] = "items"
    all_rows = []
    start = 0
    page_size = 1000
    while True:
        headers["Range"] = f"{start}-{start + page_size - 1}"
        resp = requests.get(url, headers=headers, params={"select": fields, "order": order}, timeout=30)
        resp.raise_for_status()
        page = resp.json()
        all_rows.extend(page)
        if len(page) < page_size:
            break
        start += page_size
    return all_rows


def fetch_styles(settings: dict) -> list[dict]:
    return _get_all(settings, "styles", _STYLES_FIELDS, "style_code")


def fetch_fitting_records(settings: dict) -> list[dict]:
    return _get_all(settings, "fitting_records", _FITTING_FIELDS, "style_code,round")


def fetch_report_config(settings: dict) -> dict | None:
    """대시보드의 [적용] 버튼이 settings 테이블에 써놓은 as_of 기준값. 없으면 None(로컬 기본값 사용)."""
    url = f"{settings['supabase_url']}/rest/v1/settings"
    resp = requests.get(url, headers=_headers(settings), params={"select": "value", "key": f"eq.{_REPORT_CONFIG_KEY}"}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or not rows[0]["value"]:
        return None
    return json.loads(rows[0]["value"])


def fetch_due_offsets(settings: dict, season: str) -> dict | None:
    """대시보드 '{시즌} DUE DATE 설정 기준' 표 [적용] 버튼이 저장한 라벨별 QC/PP/TOP 오프셋.
    없으면 None(코드 기본값 사용)."""
    url = f"{settings['supabase_url']}/rest/v1/settings"
    resp = requests.get(url, headers=_headers(settings), params={"select": "value", "key": f"eq.mlb_qm_fitting_due_offsets_{season}"}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or not rows[0]["value"]:
        return None
    return json.loads(rows[0]["value"])


def fetch_overrides(settings: dict, week_id: str) -> list[dict]:
    """대시보드 셀 수정 [적용] 버튼이 settings 테이블에 써놓은 해당 주차 오버라이드 목록. 없으면 빈 리스트."""
    url = f"{settings['supabase_url']}/rest/v1/settings"
    resp = requests.get(url, headers=_headers(settings), params={"select": "value", "key": f"eq.mlb_qm_fitting_overrides_{week_id}"}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or not rows[0]["value"]:
        return []
    return json.loads(rows[0]["value"])
