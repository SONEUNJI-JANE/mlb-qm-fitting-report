import json

import requests

_STYLES_FIELDS = "style_code,item,quarter,season,td,qa,co,qc_due,pp_due,top_due,vendor,washed,qty_kr,qty_cn,earliest_etd"
_FITTING_FIELDS = "style_code,stage,round,status,updated_at,comment"
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


def upsert_styles(settings: dict, rows: list[dict]) -> None:
    """style_code 유니크 제약으로 merge-duplicates upsert (있으면 갱신, 없으면 추가)."""
    if not rows:
        return
    headers = _headers(settings)
    headers["Content-Type"] = "application/json"
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
    url = f"{settings['supabase_url']}/rest/v1/styles"
    resp = requests.post(url, headers=headers, params={"on_conflict": "style_code"}, json=rows, timeout=60)
    resp.raise_for_status()


def upsert_fitting_records(settings: dict, rows: list[dict]) -> None:
    """fitting_records엔 (style_code, stage, round) 유니크 제약이 없어서, 있으면 PATCH·없으면
    POST로 직접 upsert한다(느리지만 매주 한 번 도는 로컬 스크립트라 문제없음)."""
    headers = _headers(settings)
    headers["Content-Type"] = "application/json"
    url = f"{settings['supabase_url']}/rest/v1/fitting_records"
    for row in rows:
        match = {
            "style_code": f"eq.{row['style_code']}",
            "stage": f"eq.{row['stage']}",
            "round": f"eq.{row['round']}",
        }
        existing = requests.get(url, headers=_headers(settings), params={**match, "select": "id"}, timeout=30)
        existing.raise_for_status()
        if existing.json():
            resp = requests.patch(url, headers={**headers, "Prefer": "return=minimal"}, params=match, json=row, timeout=30)
        else:
            resp = requests.post(url, headers={**headers, "Prefer": "return=minimal"}, json=[row], timeout=30)
        resp.raise_for_status()


def fetch_setting(settings: dict, key: str) -> str | None:
    """settings 테이블의 key -> value(문자열). 없으면 None."""
    url = f"{settings['supabase_url']}/rest/v1/settings"
    resp = requests.get(url, headers=_headers(settings), params={"select": "value", "key": f"eq.{key}"}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or not rows[0]["value"]:
        return None
    return rows[0]["value"]


def upsert_setting(settings: dict, key: str, value: str) -> None:
    """settings 테이블에 key/value upsert(key 유니크, merge-duplicates)."""
    headers = _headers(settings)
    headers["Content-Type"] = "application/json"
    headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
    url = f"{settings['supabase_url']}/rest/v1/settings"
    resp = requests.post(url, headers=headers, json={"key": key, "value": value}, timeout=30)
    resp.raise_for_status()


def fetch_overrides(settings: dict, week_id: str) -> list[dict]:
    """대시보드 셀 수정 [적용] 버튼이 settings 테이블에 써놓은 해당 주차 오버라이드 목록. 없으면 빈 리스트."""
    url = f"{settings['supabase_url']}/rest/v1/settings"
    resp = requests.get(url, headers=_headers(settings), params={"select": "value", "key": f"eq.mlb_qm_fitting_overrides_{week_id}"}, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    if not rows or not rows[0]["value"]:
        return []
    return json.loads(rows[0]["value"])
