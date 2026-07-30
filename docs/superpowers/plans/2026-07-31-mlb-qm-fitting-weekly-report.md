# MLB QM Fitting 주간 미팅노트 자동 생성 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Supabase(styles/fitting_records)에서 MLB QM Fitting 시즌별 FIT/PP/TOP 진척률(총량대비/기준대비)을 매주 자동 집계해, 과거 주차를 누적 보존하는 단일 HTML 대시보드로 생성·배포한다.

**Architecture:** Python 배치 스크립트(fetch → aggregate → override 병합 → chase 경고 계산 → snapshot append → HTML 빌드)가 매주 cron으로 실행되고, 결과물을 `dcs-ai-cli app update`로 DCS AI Quick Dashboard에 재배포한다. Supabase는 읽기 전용, 오버라이드/스냅샷은 로컬 JSON 파일로 관리한다.

**Tech Stack:** Python 3.13 (uv 가상환경), `requests`(Supabase REST 호출), 표준 라이브러리(json/datetime)만으로 집계, `dcs-ai-cli`(Quick Dashboard 배포).

## Global Constraints

- 원본 Supabase DB는 절대 쓰기 금지 (읽기 전용 REST 호출만)
- 이번 스코프는 FIT/PP/TOP 3단계만. CAD 지표(요척협의/PP GRADING CFM)는 제외
- `python` 실행은 항상 프로젝트 `.venv` 사용, `src/` import하는 스크립트는 `PYTHONPATH=.` 필수 (프로젝트 루트 CLAUDE.md 규칙)
- 폴더 구조는 `src/{util,service,core,output,download}` 유지
- 테스트는 프레임워크 없이 `assert` 기반 self-check 스크립트로 작성 (pytest 등 미도입)
- 코드 내 주석 최소화, 의미 자명한 이름 사용

---

## File Structure

```
config/
  report_settings.json          # as_of_weekday, as_of_date_override, supabase url/anon key
src/service/mlb_qm_fitting_report/
  __init__.py
  config.py                     # 설정 로드 + as_of_date 계산
  supabase_client.py            # styles/fitting_records REST fetch (얇은 I/O 레이어)
  aggregate.py                  # 총량대비/기준대비 % 계산 (순수 함수)
  chase.py                      # 체이스 경고 기준 초과 스타일 계산 (순수 함수)
  overrides.py                  # overrides/{week}.json 로드 + 병합
  snapshots.py                  # weekly_snapshots.json append/조회
  report_builder.py             # snapshots.json → index.html 렌더링
  run_weekly.py                 # 위 전부를 순서대로 실행하는 오케스트레이터
overrides/
  .gitkeep
src/output/
  weekly_snapshots.json         # 누적 주차 데이터 (git 커밋 대상)
  dashboard/
    index.html                  # 배포 산출물 (build_report.py가 생성)
tests/
  test_config.py
  test_aggregate.py
  test_chase.py
  test_overrides.py
  test_snapshots.py
```

각 파일 책임은 하나씩: `config.py`는 설정/날짜만, `supabase_client.py`는 네트워크 I/O만(테스트 대상 아님, 얇게 유지), `aggregate.py`/`chase.py`/`overrides.py`/`snapshots.py`는 전부 순수 함수라 네트워크 없이 단위테스트 가능. `run_weekly.py`가 이들을 조립.

---

## Task 1: 프로젝트 초기 설정

**Files:**
- Create: `config/report_settings.json`
- Create: `src/service/mlb_qm_fitting_report/__init__.py`
- Create: `overrides/.gitkeep`
- Create: `.gitignore`
- Create: `pyproject.toml` (uv 프로젝트 메타)

**Interfaces:**
- Produces: `config/report_settings.json`의 스키마 — 이후 Task 2의 `config.py`가 그대로 파싱

- [ ] **Step 1: uv로 Python 3.13 가상환경 생성**

```bash
uv python install 3.13
uv venv --python 3.13
```

- [ ] **Step 2: pyproject.toml 작성**

```toml
[project]
name = "mlb-qm-fitting-report"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "requests>=2.32",
]
```

- [ ] **Step 3: 의존성 설치**

```bash
uv sync
```

- [ ] **Step 4: 폴더/파일 생성**

```bash
mkdir -p src/service/mlb_qm_fitting_report src/output/dashboard overrides tests
touch src/service/mlb_qm_fitting_report/__init__.py overrides/.gitkeep
```

- [ ] **Step 5: config/report_settings.json 작성**

```json
{
  "supabase_url": "https://ppeedhejhbgshdjnlrha.supabase.co",
  "supabase_anon_key": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBwZWVkaGVqaGJnc2hkam5scmhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI3NTI3NjEsImV4cCI6MjA5ODMyODc2MX0.URjHO5l8QKkiyMSADdxsjuouOlwJPwrhMSlBBDq7sPA",
  "as_of_weekday": "FRI",
  "as_of_date_override": null
}
```

- [ ] **Step 6: .gitignore 작성**

```
.venv/
__pycache__/
*.pyc
```

`config/report_settings.json`은 anon key(공개용 클라이언트 키)만 담으므로 커밋 대상에서 제외하지 않는다. `weekly_snapshots.json`도 히스토리 보존을 위해 커밋 대상이다(gitignore 미포함).

- [ ] **Step 7: Commit**

```bash
git add config pyproject.toml .gitignore overrides/.gitkeep src/service/mlb_qm_fitting_report/__init__.py
git commit -m "chore: scaffold mlb-qm-fitting-report project structure"
```

---

## Task 2: 설정 로드 + as_of_date 계산

**Files:**
- Create: `src/service/mlb_qm_fitting_report/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: `config/report_settings.json` (Task 1에서 생성)
- Produces:
  - `load_settings(path: str = "config/report_settings.json") -> dict`
  - `resolve_as_of_date(settings: dict, run_date: date) -> date`
  - `week_id_for(as_of_date: date) -> str` — 예: `2026-W31` (ISO week, `date.isocalendar()` 기반)

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_config.py
import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.config import resolve_as_of_date, week_id_for


def test_resolve_as_of_date_default_friday_from_monday():
    # 2026-08-03은 월요일. 직전 금요일은 2026-07-31.
    settings = {"as_of_weekday": "FRI", "as_of_date_override": None}
    result = resolve_as_of_date(settings, run_date=date(2026, 8, 3))
    assert result == date(2026, 7, 31), result


def test_resolve_as_of_date_from_friday_itself():
    # 실행일 자체가 금요일이면 그 날짜가 직전 금요일(당일 포함 X, 반드시 이전 주)
    settings = {"as_of_weekday": "FRI", "as_of_date_override": None}
    result = resolve_as_of_date(settings, run_date=date(2026, 7, 31))
    assert result == date(2026, 7, 24), result


def test_resolve_as_of_date_override_wins():
    settings = {"as_of_weekday": "FRI", "as_of_date_override": "2026-07-30"}
    result = resolve_as_of_date(settings, run_date=date(2026, 8, 3))
    assert result == date(2026, 7, 30), result


def test_week_id_for():
    assert week_id_for(date(2026, 7, 31)) == "2026-W31", week_id_for(date(2026, 7, 31))


if __name__ == "__main__":
    test_resolve_as_of_date_default_friday_from_monday()
    test_resolve_as_of_date_from_friday_itself()
    test_resolve_as_of_date_override_wins()
    test_week_id_for()
    print("OK: test_config")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_config.py`
Expected: `ModuleNotFoundError: No module named 'src.service.mlb_qm_fitting_report.config'`

- [ ] **Step 3: 최소 구현 작성**

```python
# src/service/mlb_qm_fitting_report/config.py
import json
from datetime import date, timedelta

_WEEKDAY_MAP = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}


def load_settings(path: str = "config/report_settings.json") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_as_of_date(settings: dict, run_date: date) -> date:
    override = settings.get("as_of_date_override")
    if override:
        return date.fromisoformat(override)

    target_weekday = _WEEKDAY_MAP[settings.get("as_of_weekday", "FRI")]
    days_back = (run_date.weekday() - target_weekday) % 7
    if days_back == 0:
        days_back = 7
    return run_date - timedelta(days=days_back)


def week_id_for(as_of_date: date) -> str:
    iso_year, iso_week, _ = as_of_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"
```

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_config.py`
Expected: `OK: test_config`

- [ ] **Step 5: Commit**

```bash
git add src/service/mlb_qm_fitting_report/config.py tests/test_config.py
git commit -m "feat: resolve as-of-date and week id from report settings"
```

---

## Task 3: Supabase REST 조회

**Files:**
- Create: `src/service/mlb_qm_fitting_report/supabase_client.py`

**Interfaces:**
- Consumes: `load_settings()` (Task 2) 결과의 `supabase_url`/`supabase_anon_key`
- Produces:
  - `fetch_styles(settings: dict) -> list[dict]` — 각 dict는 `style_code, item, quarter, season, td, qa, qc_due, pp_due, top_due` 키 포함
  - `fetch_fitting_records(settings: dict) -> list[dict]` — 각 dict는 `style_code, stage, round, status, updated_at` 키 포함

네트워크 I/O라 단위테스트 대상에서 제외(수동 smoke test로 검증). Task 4~7은 이 함수들이 반환하는 것과 동일한 shape의 dict 리스트를 인자로 받는 순수 함수라 네트워크 없이 테스트한다.

- [ ] **Step 1: 구현 작성**

```python
# src/service/mlb_qm_fitting_report/supabase_client.py
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
```

- [ ] **Step 2: 수동 smoke test로 실제 조회 확인**

Run:
```bash
PYTHONPATH=. .venv/Scripts/python -c "
from src.service.mlb_qm_fitting_report.config import load_settings
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records
s = load_settings()
styles = fetch_styles(s)
records = fetch_fitting_records(s)
print(len(styles), 'styles,', len(records), 'fitting_records')
print(styles[0])
print(records[0])
"
```
Expected: 두 리스트 모두 0보다 큰 길이, dict 키가 위 필드와 일치

- [ ] **Step 3: Commit**

```bash
git add src/service/mlb_qm_fitting_report/supabase_client.py
git commit -m "feat: fetch styles and fitting_records from supabase"
```

---

## Task 4: 진척률 집계 (총량대비 / 기준대비)

**Files:**
- Create: `src/service/mlb_qm_fitting_report/aggregate.py`
- Test: `tests/test_aggregate.py`

**Interfaces:**
- Consumes: `fetch_styles()` / `fetch_fitting_records()` (Task 3)와 동일 shape의 `list[dict]`, `as_of_date: date` (Task 2 `resolve_as_of_date` 결과)
- Produces: `compute_progress(styles: list[dict], records: list[dict], as_of_date: date) -> dict`

  반환 shape:
  ```python
  {
    "27SS": {                      # season
      "TD": {                      # owner_type: "TD" | "QA"
        "FIT": {"total_done": 30, "total_all": 100, "baseline_done": 30, "baseline_all": 40},
        "PP": {...}, "TOP": {...}
      },
      "QA": {...}
    },
    "26FW": {...}
  }
  ```
  퍼센트는 리포트 빌더(Task 8)에서 `done/all*100`으로 계산 (분모 0이면 0% 표시).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_aggregate.py
import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.aggregate import compute_progress

STYLES = [
    {"style_code": "A1", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-07-20", "pp_due": "2026-08-10", "top_due": "2026-09-01"},
    {"style_code": "A2", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-08-05", "pp_due": "2026-08-25", "top_due": "2026-09-15"},
]

RECORDS = [
    {"style_code": "A1", "stage": "FIT", "round": 1, "status": "Approved", "updated_at": "2026-07-15T00:00:00Z"},
    {"style_code": "A2", "stage": "FIT", "round": 1, "status": "Rejected", "updated_at": "2026-07-28T00:00:00Z"},
]


def test_total_vs_baseline_fit():
    as_of = date(2026, 7, 31)
    result = compute_progress(STYLES, RECORDS, as_of)

    fit_td = result["27SS"]["TD"]["FIT"]
    # 총량 대비: 2개 대상 중 1개(A1) Approved
    assert fit_td["total_done"] == 1, fit_td
    assert fit_td["total_all"] == 2, fit_td

    # 기준대비: qc_due <= 2026-07-31인 스타일은 A1(07-20)만. A2(08-05)는 아직 안 옴.
    assert fit_td["baseline_done"] == 1, fit_td
    assert fit_td["baseline_all"] == 1, fit_td


def test_qa_owner_mirrors_td_when_qa_field_set():
    as_of = date(2026, 7, 31)
    result = compute_progress(STYLES, RECORDS, as_of)
    fit_qa = result["27SS"]["QA"]["FIT"]
    assert fit_qa["total_all"] == 2, fit_qa


if __name__ == "__main__":
    test_total_vs_baseline_fit()
    test_qa_owner_mirrors_td_when_qa_field_set()
    print("OK: test_aggregate")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_aggregate.py`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 구현 작성**

```python
# src/service/mlb_qm_fitting_report/aggregate.py
from datetime import date

STAGES = ["FIT", "PP", "TOP"]
DUE_FIELD_BY_STAGE = {"FIT": "qc_due", "PP": "pp_due", "TOP": "top_due"}
OWNER_FIELDS = {"TD": "td", "QA": "qa"}


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value[:10])


def _latest_status_by_style_and_stage(records: list[dict]) -> dict:
    """(style_code, stage) -> 가장 최신 record(round 최댓값, updated_at 최댓값)"""
    latest = {}
    for r in records:
        key = (r["style_code"], r["stage"])
        current = latest.get(key)
        if current is None or (r["round"], r["updated_at"]) > (current["round"], current["updated_at"]):
            latest[key] = r
    return latest


def compute_progress(styles: list[dict], records: list[dict], as_of_date: date) -> dict:
    latest = _latest_status_by_style_and_stage(records)
    result: dict = {}

    for style in styles:
        season = style["season"]
        result.setdefault(season, {"TD": {}, "QA": {}})

        for stage in STAGES:
            due_field = DUE_FIELD_BY_STAGE[stage]
            due = _parse_date(style.get(due_field))
            record = latest.get((style["style_code"], stage))
            is_done = bool(record and record["status"] == "Approved")
            is_due = bool(due and due <= as_of_date)

            for owner_type, style_field in OWNER_FIELDS.items():
                owner_name = style.get(style_field)
                if not owner_name:
                    continue
                bucket = result[season][owner_type].setdefault(
                    stage, {"total_done": 0, "total_all": 0, "baseline_done": 0, "baseline_all": 0}
                )
                bucket["total_all"] += 1
                if is_done:
                    bucket["total_done"] += 1
                if is_due:
                    bucket["baseline_all"] += 1
                    if is_done:
                        bucket["baseline_done"] += 1

    return result
```

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_aggregate.py`
Expected: `OK: test_aggregate`

- [ ] **Step 5: Commit**

```bash
git add src/service/mlb_qm_fitting_report/aggregate.py tests/test_aggregate.py
git commit -m "feat: compute total-vs-all and baseline-vs-due progress rates"
```

---

## Task 5: 체이스 경고 계산

**Files:**
- Create: `src/service/mlb_qm_fitting_report/chase.py`
- Test: `tests/test_chase.py`

**Interfaces:**
- Consumes: 동일한 `styles`/`records`/`as_of_date` (Task 4와 동일 shape)
- Produces: `compute_chase_warnings(styles: list[dict], records: list[dict], as_of_date: date) -> list[dict]`

  반환 원소 shape: `{"style_code": "A2", "season": "27SS", "owner": "김철수", "rule": "FIT Rej/IntRej 1차 → 다음 FIT 샘플 접수", "due_date": "2026-08-05", "days_to_due": 3}`

  규칙 상수는 image3 스크린샷("체이스 경고 기준 설정") 값을 그대로 코드에 반영한다. `ref`가 due-date 필드면 "due - as_of <= threshold_days"일 때 경고, `ref`가 `"elapsed"`면 "as_of - 최신기록일 >= threshold_days"일 때 경고.

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_chase.py
import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.chase import compute_chase_warnings

STYLES = [
    {"style_code": "A2", "season": "27SS", "td": "김철수", "qa": "이영희", "qc_due": "2026-08-05", "pp_due": "2026-08-25", "top_due": "2026-09-15"},
]

RECORDS = [
    {"style_code": "A2", "stage": "FIT", "round": 1, "status": "Rejected", "updated_at": "2026-07-28T00:00:00Z"},
]


def test_fit_rejected_round1_warns_within_30_days_of_qc_due():
    # as_of=2026-07-31, qc_due=2026-08-05 → 5일 남음 <= 30일 임계값 → 경고
    as_of = date(2026, 7, 31)
    warnings = compute_chase_warnings(STYLES, RECORDS, as_of)
    assert len(warnings) == 1, warnings
    assert warnings[0]["style_code"] == "A2"
    assert warnings[0]["rule"].startswith("FIT Rej"), warnings[0]


def test_no_warning_when_far_from_due():
    as_of = date(2026, 6, 1)  # qc_due까지 65일 남음, 임계값 30일 초과 → 경고 없음
    warnings = compute_chase_warnings(STYLES, RECORDS, as_of)
    assert warnings == [], warnings


if __name__ == "__main__":
    test_fit_rejected_round1_warns_within_30_days_of_qc_due()
    test_no_warning_when_far_from_due()
    print("OK: test_chase")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_chase.py`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 구현 작성**

```python
# src/service/mlb_qm_fitting_report/chase.py
from datetime import date

# 스크린샷 "체이스 경고 기준 설정" 값 그대로 반영.
# ref: 스타일 due-date 필드명, 또는 "elapsed"(최신 기록일로부터 경과일수 기준)
CHASE_RULES = [
    {"stage": "보정", "status": "Approved", "ref": "pp_due", "days": 20, "desc": "보정 Approved → PP 샘플 접수"},
    {"stage": "보정", "status": "Go to FIT", "ref": "elapsed", "days": 30, "desc": "보정 Go to FIT → 1ST FIT 샘플 접수"},
    {"stage": "보정", "status": "Rejected", "ref": "qc_due", "days": 45, "desc": "보정 Rejected → 다음 차수 보정 샘플 접수"},
    {"stage": "FIT", "status": "Approved", "ref": "pp_due", "days": 20, "desc": "FIT Approved → PP 샘플 접수"},
    {"stage": "FIT", "status": "Rejected", "round_max": 1, "ref": "qc_due", "days": 30, "desc": "FIT Rej/IntRej 1차 → 다음 FIT 샘플 접수"},
    {"stage": "FIT", "status": "Int Rej", "round_max": 1, "ref": "qc_due", "days": 30, "desc": "FIT Rej/IntRej 1차 → 다음 FIT 샘플 접수"},
    {"stage": "FIT", "status": "Rejected", "round_min": 2, "ref": "qc_due", "days": 15, "desc": "FIT Rej/IntRej 2차+ → 다음 FIT 샘플 접수"},
    {"stage": "FIT", "status": "Int Rej", "round_min": 2, "ref": "qc_due", "days": 15, "desc": "FIT Rej/IntRej 2차+ → 다음 FIT 샘플 접수"},
    {"stage": "PP", "status": "Approved", "ref": "top_due", "days": 28, "desc": "PP Approved → TOP 샘플 접수"},
    {"stage": "PP", "status": "Rejected", "ref": "pp_due", "days": 10, "desc": "PP Rej/IntRej → 다음 차수 PP 샘플 접수"},
    {"stage": "PP", "status": "Int Rej", "ref": "pp_due", "days": 10, "desc": "PP Rej/IntRej → 다음 차수 PP 샘플 접수"},
    {"stage": "TOP", "status": "Rejected", "ref": "top_due", "days": 14, "desc": "TOP Rej/IntRej → 다음 차수 TOP 샘플 접수"},
    {"stage": "TOP", "status": "Int Rej", "ref": "top_due", "days": 14, "desc": "TOP Rej/IntRej → 다음 차수 TOP 샘플 접수"},
]


def _parse_date(value):
    if not value:
        return None
    return date.fromisoformat(value[:10])


def _matches(rule: dict, record: dict) -> bool:
    if rule["stage"] != record["stage"] or rule["status"] != record["status"]:
        return False
    if "round_max" in rule and record["round"] > rule["round_max"]:
        return False
    if "round_min" in rule and record["round"] < rule["round_min"]:
        return False
    return True


def _latest_records_by_style(records: list[dict]) -> dict:
    latest = {}
    for r in records:
        key = r["style_code"]
        current = latest.get(key)
        if current is None or (r["round"], r["updated_at"]) > (current["round"], current["updated_at"]):
            latest[key] = r
    return latest


def compute_chase_warnings(styles: list[dict], records: list[dict], as_of_date: date) -> list[dict]:
    styles_by_code = {s["style_code"]: s for s in styles}
    latest = _latest_records_by_style(records)
    warnings = []

    for style_code, record in latest.items():
        style = styles_by_code.get(style_code)
        if not style:
            continue

        for rule in CHASE_RULES:
            if not _matches(rule, record):
                continue

            owner = style.get("td") or style.get("qa") or ""

            if rule["ref"] == "elapsed":
                last_change = date.fromisoformat(record["updated_at"][:10])
                days_elapsed = (as_of_date - last_change).days
                if days_elapsed >= rule["days"]:
                    warnings.append({
                        "style_code": style_code, "season": style.get("season"), "owner": owner,
                        "rule": rule["desc"], "due_date": None, "days_to_due": None,
                    })
            else:
                due = _parse_date(style.get(rule["ref"]))
                if due is None:
                    continue
                days_to_due = (due - as_of_date).days
                if days_to_due <= rule["days"]:
                    warnings.append({
                        "style_code": style_code, "season": style.get("season"), "owner": owner,
                        "rule": rule["desc"], "due_date": due.isoformat(), "days_to_due": days_to_due,
                    })
            break  # 스타일당 최신 기록은 하나의 규칙에만 매칭됨

    return warnings
```

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_chase.py`
Expected: `OK: test_chase`

- [ ] **Step 5: Commit**

```bash
git add src/service/mlb_qm_fitting_report/chase.py tests/test_chase.py
git commit -m "feat: compute chase warnings from due-date and elapsed-time thresholds"
```

---

## Task 6: 오버라이드 로드/병합

**Files:**
- Create: `src/service/mlb_qm_fitting_report/overrides.py`
- Test: `tests/test_overrides.py`

**Interfaces:**
- Consumes: `compute_progress()` (Task 4)의 반환 dict, `week_id_for()`(Task 2)로 만든 week_id
- Produces:
  - `load_overrides(week_id: str, overrides_dir: str = "overrides") -> list[dict]` — 파일 없으면 `[]`
  - `apply_overrides(progress: dict, overrides: list[dict]) -> dict` — 새 dict 반환(원본 비변경)

  override 파일(`overrides/{week_id}.json`) 원소 shape: `{"season": "27SS", "stage": "FIT", "owner_type": "TD", "override_numerator": 30, "override_denominator": 32}`. `total_done`/`total_all`을 이 값으로 교체하고, `baseline_done`/`baseline_all`은 그대로 둔다(총량 지표만 오버라이드 대상 — 기준대비는 due date 기반이라 별도 override 불필요, 필요해지면 후속 확장).

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_overrides.py
import sys

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.overrides import load_overrides, apply_overrides

PROGRESS = {
    "27SS": {
        "TD": {"FIT": {"total_done": 1, "total_all": 2, "baseline_done": 1, "baseline_all": 1}},
        "QA": {},
    }
}


def test_load_overrides_missing_file_returns_empty():
    assert load_overrides("2099-W01", overrides_dir="overrides") == []


def test_apply_overrides_replaces_total_only():
    overrides = [{"season": "27SS", "stage": "FIT", "owner_type": "TD", "override_numerator": 30, "override_denominator": 32}]
    result = apply_overrides(PROGRESS, overrides)

    fit_td = result["27SS"]["TD"]["FIT"]
    assert fit_td["total_done"] == 30, fit_td
    assert fit_td["total_all"] == 32, fit_td
    assert fit_td["baseline_done"] == 1, fit_td  # baseline은 그대로

    # 원본은 불변
    assert PROGRESS["27SS"]["TD"]["FIT"]["total_done"] == 1


if __name__ == "__main__":
    test_load_overrides_missing_file_returns_empty()
    test_apply_overrides_replaces_total_only()
    print("OK: test_overrides")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_overrides.py`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 구현 작성**

```python
# src/service/mlb_qm_fitting_report/overrides.py
import copy
import json
import os


def load_overrides(week_id: str, overrides_dir: str = "overrides") -> list[dict]:
    path = os.path.join(overrides_dir, f"{week_id}.json")
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_overrides(progress: dict, overrides: list[dict]) -> dict:
    result = copy.deepcopy(progress)
    for entry in overrides:
        bucket = result.get(entry["season"], {}).get(entry["owner_type"], {}).get(entry["stage"])
        if bucket is None:
            continue
        bucket["total_done"] = entry["override_numerator"]
        bucket["total_all"] = entry["override_denominator"]
    return result
```

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_overrides.py`
Expected: `OK: test_overrides`

- [ ] **Step 5: Commit**

```bash
git add src/service/mlb_qm_fitting_report/overrides.py tests/test_overrides.py
git commit -m "feat: load and apply per-week numerator/denominator overrides"
```

---

## Task 7: 주차 스냅샷 append

**Files:**
- Create: `src/service/mlb_qm_fitting_report/snapshots.py`
- Test: `tests/test_snapshots.py`

**Interfaces:**
- Consumes: `week_id_for()`(Task 2), `apply_overrides()` 결과(Task 6), `compute_chase_warnings()` 결과(Task 5)
- Produces:
  - `load_snapshots(path: str = "src/output/weekly_snapshots.json") -> dict` — 파일 없으면 `{"weeks": {}}`
  - `append_snapshot(snapshots: dict, week_id: str, as_of_date: date, progress: dict, warnings: list[dict]) -> dict` — 새 dict 반환, 같은 week_id 재실행 시 해당 주만 덮어씀
  - `save_snapshots(snapshots: dict, path: str = "src/output/weekly_snapshots.json") -> None`

- [ ] **Step 1: 실패하는 테스트 작성**

```python
# tests/test_snapshots.py
import sys
from datetime import date

sys.path.insert(0, ".")
from src.service.mlb_qm_fitting_report.snapshots import append_snapshot

PROGRESS = {"27SS": {"TD": {}, "QA": {}}}
WARNINGS = [{"style_code": "A2", "season": "27SS", "owner": "김철수", "rule": "x", "due_date": None, "days_to_due": None}]


def test_append_new_week_preserves_existing():
    existing = {"weeks": {"2026-W30": {"as_of_date": "2026-07-24", "progress": {}, "warnings": []}}}
    result = append_snapshot(existing, "2026-W31", date(2026, 7, 31), PROGRESS, WARNINGS)

    assert "2026-W30" in result["weeks"], result["weeks"].keys()
    assert result["weeks"]["2026-W31"]["as_of_date"] == "2026-07-31"
    assert result["weeks"]["2026-W31"]["progress"] == PROGRESS
    assert result["weeks"]["2026-W31"]["warnings"] == WARNINGS


def test_append_same_week_overwrites_not_duplicates():
    existing = {"weeks": {"2026-W31": {"as_of_date": "2026-07-31", "progress": {}, "warnings": []}}}
    result = append_snapshot(existing, "2026-W31", date(2026, 7, 31), PROGRESS, WARNINGS)

    assert len(result["weeks"]) == 1
    assert result["weeks"]["2026-W31"]["progress"] == PROGRESS


if __name__ == "__main__":
    test_append_new_week_preserves_existing()
    test_append_same_week_overwrites_not_duplicates()
    print("OK: test_snapshots")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_snapshots.py`
Expected: `ModuleNotFoundError`

- [ ] **Step 3: 구현 작성**

```python
# src/service/mlb_qm_fitting_report/snapshots.py
import copy
import json
import os
from datetime import date


def load_snapshots(path: str = "src/output/weekly_snapshots.json") -> dict:
    if not os.path.exists(path):
        return {"weeks": {}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def append_snapshot(snapshots: dict, week_id: str, as_of_date: date, progress: dict, warnings: list[dict]) -> dict:
    result = copy.deepcopy(snapshots)
    result["weeks"][week_id] = {
        "as_of_date": as_of_date.isoformat(),
        "progress": progress,
        "warnings": warnings,
    }
    return result


def save_snapshots(snapshots: dict, path: str = "src/output/weekly_snapshots.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(snapshots, f, ensure_ascii=False, indent=2, sort_keys=True)
```

- [ ] **Step 4: 테스트 실행해서 통과 확인**

Run: `PYTHONPATH=. .venv/Scripts/python tests/test_snapshots.py`
Expected: `OK: test_snapshots`

- [ ] **Step 5: Commit**

```bash
git add src/service/mlb_qm_fitting_report/snapshots.py tests/test_snapshots.py
git commit -m "feat: append weekly snapshot without losing prior weeks"
```

---

## Task 8: HTML 리포트 빌드

**Files:**
- Create: `src/service/mlb_qm_fitting_report/report_builder.py`
- Create: `src/output/weekly_snapshots.json` (빈 초기 상태로 커밋)

**Interfaces:**
- Consumes: `load_snapshots()`(Task 7) 결과 dict (`{"weeks": {week_id: {as_of_date, progress, warnings}}}`)
- Produces: `build_report_html(snapshots: dict) -> str` — 완성된 HTML 문자열. `run_weekly.py`(Task 9)가 이걸 `src/output/dashboard/index.html`에 씀

- [ ] **Step 1: 빈 초기 스냅샷 파일 생성**

```bash
mkdir -p src/output/dashboard
echo '{"weeks": {}}' > src/output/weekly_snapshots.json
```

- [ ] **Step 2: 구현 작성**

데이터는 `<script id="snapshot-data" type="application/json">`에 그대로 embed하고, 나머지는 클라이언트 JS로 렌더링한다(외부 fetch 없음 — 단일 파일로 배포 가능).

```python
# src/service/mlb_qm_fitting_report/report_builder.py
import json

_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MLB QM Fitting 주간 보고</title>
<style>
body{font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif;font-size:13px;background:#f0f1f4;color:#1a1a2e;margin:0}
.hdr{background:#1a1a2e;color:#fff;padding:14px 24px;display:flex;align-items:center;gap:12px}
.hdr h1{font-size:17px;margin:0}
select{padding:6px 10px;border-radius:6px;border:1px solid #ccc;font-size:12px}
.content{padding:20px;max-width:1100px;margin:0 auto}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:8px;overflow:hidden;margin-bottom:16px}
th,td{padding:8px 10px;border-bottom:1px solid #eee;text-align:left;font-size:12px}
th{background:#f8f9fa;color:#555}
.warn{color:#b3261e;font-weight:700}
.section-title{font-weight:700;margin:16px 0 8px}
</style>
</head>
<body>
<div class="hdr">
  <h1>MLB QM Fitting 주간 보고</h1>
  <select id="week-select" onchange="render()"></select>
</div>
<div class="content">
  <div class="section-title">진척률 (총량대비 % / 기준대비 %)</div>
  <table id="progress-table"><thead><tr><th>시즌</th><th>담당</th><th>단계</th><th>총량대비</th><th>기준대비</th></tr></thead><tbody></tbody></table>
  <div class="section-title">체이스 경고</div>
  <table id="warning-table"><thead><tr><th>스타일</th><th>시즌</th><th>담당</th><th>기준</th><th>Due</th><th>D-day</th></tr></thead><tbody></tbody></table>
</div>
<script id="snapshot-data" type="application/json">__SNAPSHOT_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('snapshot-data').textContent);
const weekIds = Object.keys(DATA.weeks).sort().reverse();
const sel = document.getElementById('week-select');
weekIds.forEach(w => { const o = document.createElement('option'); o.value = w; o.textContent = w + ' (기준일 ' + DATA.weeks[w].as_of_date + ')'; sel.appendChild(o); });

function pct(done, all) { return all > 0 ? Math.round(done / all * 1000) / 10 : 0; }

function render() {
  const week = DATA.weeks[sel.value];
  if (!week) return;
  const pBody = document.querySelector('#progress-table tbody');
  pBody.innerHTML = '';
  for (const season of Object.keys(week.progress).sort()) {
    for (const owner of ['TD', 'QA']) {
      for (const stage of Object.keys(week.progress[season][owner] || {})) {
        const m = week.progress[season][owner][stage];
        const row = document.createElement('tr');
        row.innerHTML = `<td>${season}</td><td>${owner}</td><td>${stage}</td>` +
          `<td>${pct(m.total_done, m.total_all)}% (${m.total_done}/${m.total_all})</td>` +
          `<td>${pct(m.baseline_done, m.baseline_all)}% (${m.baseline_done}/${m.baseline_all})</td>`;
        pBody.appendChild(row);
      }
    }
  }
  const wBody = document.querySelector('#warning-table tbody');
  wBody.innerHTML = '';
  for (const w of week.warnings) {
    const row = document.createElement('tr');
    row.className = 'warn';
    row.innerHTML = `<td>${w.style_code}</td><td>${w.season}</td><td>${w.owner}</td><td>${w.rule}</td><td>${w.due_date || '-'}</td><td>${w.days_to_due ?? '-'}</td>`;
    wBody.appendChild(row);
  }
}

if (weekIds.length) { sel.value = weekIds[0]; render(); }
</script>
</body>
</html>
"""


def build_report_html(snapshots: dict) -> str:
    return _TEMPLATE.replace("__SNAPSHOT_JSON__", json.dumps(snapshots, ensure_ascii=False))
```

- [ ] **Step 3: 수동 확인 — 빈 스냅샷으로 빌드해서 파일 열어보기**

```bash
PYTHONPATH=. .venv/Scripts/python -c "
from src.service.mlb_qm_fitting_report.snapshots import load_snapshots
from src.service.mlb_qm_fitting_report.report_builder import build_report_html
html = build_report_html(load_snapshots())
open('src/output/dashboard/index.html', 'w', encoding='utf-8').write(html)
print('written')
"
start src/output/dashboard/index.html
```
Expected: 브라우저에 헤더/빈 표 뜨고 콘솔 에러 없음 (주차 없어서 표는 비어있는 게 정상)

- [ ] **Step 4: Commit**

```bash
git add src/service/mlb_qm_fitting_report/report_builder.py src/output/weekly_snapshots.json src/output/dashboard/index.html
git commit -m "feat: build single-file dashboard html from weekly snapshots"
```

---

## Task 9: 오케스트레이터 (run_weekly.py) + 최초 수동 배포

**Files:**
- Create: `src/service/mlb_qm_fitting_report/run_weekly.py`

**Interfaces:**
- Consumes: Task 2~8의 모든 public 함수
- Produces: `main() -> None` — CLI 진입점. `src/output/weekly_snapshots.json`과 `src/output/dashboard/index.html`을 최신화

- [ ] **Step 1: 구현 작성**

```python
# src/service/mlb_qm_fitting_report/run_weekly.py
from datetime import date

from src.service.mlb_qm_fitting_report.config import load_settings, resolve_as_of_date, week_id_for
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records
from src.service.mlb_qm_fitting_report.aggregate import compute_progress
from src.service.mlb_qm_fitting_report.chase import compute_chase_warnings
from src.service.mlb_qm_fitting_report.overrides import load_overrides, apply_overrides
from src.service.mlb_qm_fitting_report.snapshots import load_snapshots, append_snapshot, save_snapshots
from src.service.mlb_qm_fitting_report.report_builder import build_report_html


def main() -> None:
    settings = load_settings()
    as_of_date = resolve_as_of_date(settings, run_date=date.today())
    week_id = week_id_for(as_of_date)

    styles = fetch_styles(settings)
    records = fetch_fitting_records(settings)

    progress = compute_progress(styles, records, as_of_date)
    overrides = load_overrides(week_id)
    progress = apply_overrides(progress, overrides)
    warnings = compute_chase_warnings(styles, records, as_of_date)

    snapshots = load_snapshots()
    snapshots = append_snapshot(snapshots, week_id, as_of_date, progress, warnings)
    save_snapshots(snapshots)

    html = build_report_html(snapshots)
    with open("src/output/dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"done: week={week_id} as_of={as_of_date.isoformat()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실행해서 실제 데이터로 스냅샷/리포트 생성 확인**

Run: `PYTHONPATH=. .venv/Scripts/python src/service/mlb_qm_fitting_report/run_weekly.py`
Expected: `done: week=2026-W... as_of=...` 출력, `src/output/weekly_snapshots.json`에 해당 주 데이터 채워짐, `src/output/dashboard/index.html` 열면 실제 시즌/진척률 표시

- [ ] **Step 3: Commit**

```bash
git add src/service/mlb_qm_fitting_report/run_weekly.py src/output/weekly_snapshots.json src/output/dashboard/index.html
git commit -m "feat: add weekly orchestrator script"
```

- [ ] **Step 4: Quick Dashboard 최초 배포**

```bash
dcs-ai-cli app deploy --type dashboard \
  --name mlb-qm-fitting-weekly \
  --display-name "MLB QM Fitting 주간 보고" \
  --path src/output/dashboard \
  --description "시즌별 FIT/PP/TOP 진척률 및 체이스 경고 주간 리포트"
```
Expected: 성공 응답과 함께 공유 URL(`https://dcsai.fnf.co.kr/server/quick-dashboard/mlb-qm-fitting-weekly`) 출력. 사용자에게 URL 공유.

---

## Task 10: 주간 자동 실행 등록

**Files:**
- 코드 변경 없음. `schedule` 스킬로 클라우드 cron 에이전트 등록

**Interfaces:**
- Consumes: Task 9의 `run_weekly.py` + 배포된 슬러그 `mlb-qm-fitting-weekly`

- [ ] **Step 1: 배포 명령을 재배포용으로 별도 기록**

최초 배포(Task 9)는 `app deploy`, 이후 매주는 `app update`(슬러그·URL 유지)를 써야 하므로 오케스트레이터 실행 뒤 아래 명령이 매주 함께 돌아야 함:

```bash
dcs-ai-cli app update mlb-qm-fitting-weekly --path src/output/dashboard
```

- [ ] **Step 2: `schedule` 스킬로 주간 cron 등록**

`/schedule` 호출해 아래 내용으로 매주 월요일 09:00(Asia/Seoul) 실행되는 routine 생성:

```bash
cd <repo-root> && \
PYTHONPATH=. .venv/Scripts/python src/service/mlb_qm_fitting_report/run_weekly.py && \
dcs-ai-cli app update mlb-qm-fitting-weekly --path src/output/dashboard
```

- [ ] **Step 3: 등록 확인**

`schedule` 스킬의 목록 조회로 등록된 routine이 다음 실행 시각(다음 월요일 09:00 KST)을 갖고 있는지 확인.

---

## Self-Review 결과

- **스펙 커버리지**: 총량대비/기준대비 진척률(Task 4), as_of_date 설정 분리(Task 2), 오버라이드(Task 6), 주차 누적(Task 7), chase 경고(Task 5), 단일 HTML 대시보드(Task 8), 배포 자동화(Task 9~10) — 스펙 전 섹션 매핑됨. CAD 지표는 스펙대로 제외.
- **타입 일관성**: `progress` dict shape(`{season: {owner_type: {stage: {total_done,total_all,baseline_done,baseline_all}}}}`)이 Task 4~9 전체에서 동일하게 사용됨. `week_id`(`YYYY-Www` 문자열)도 Task 2/6/7/9에서 일관.
- **플레이스홀더 없음**: 모든 스텝에 실행 가능한 실제 코드/명령 포함.
