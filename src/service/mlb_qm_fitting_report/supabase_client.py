import requests

_STYLES_FIELDS = "style_code,item,quarter,season,td,qa,co,qc_due,pp_due,top_due"
_FITTING_FIELDS = "style_code,stage,round,status,updated_at"


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
