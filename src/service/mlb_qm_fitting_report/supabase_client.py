import requests

_STYLES_FIELDS = "style_code,item,quarter,season,td,qa,qc_due,pp_due,top_due"
_FITTING_FIELDS = "style_code,stage,round,status,updated_at"


def _headers(settings: dict) -> dict:
    key = settings["supabase_anon_key"]
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _get_all(settings: dict, table: str, fields: str) -> list[dict]:
    url = f"{settings['supabase_url']}/rest/v1/{table}"
    params = {"select": fields, "limit": "10000"}
    resp = requests.get(url, headers=_headers(settings), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_styles(settings: dict) -> list[dict]:
    return _get_all(settings, "styles", _STYLES_FIELDS)


def fetch_fitting_records(settings: dict) -> list[dict]:
    return _get_all(settings, "fitting_records", _FITTING_FIELDS)
