# 27SS Live Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 27SS 대시보드를 "매주 사람이 스냅샷 만들고 정적 파일 재배포" 구조에서, 요청마다 Supabase에서 실시간 계산해서 보여주는 작은 FastAPI 백엔드로 바꾼다. 26FW/정적 대시보드는 전혀 건드리지 않는다.

**Architecture:** 새 파일 하나(`live_app.py`)에 FastAPI 앱을 만들고, 기존 `supabase_client.py`/`aggregate.py`/`config.py`/`report_builder.py`를 그대로 import해서 재사용한다. `GET /` 요청이 오면: (1) 캐시가 신선하면 캐시된 HTML 반환, (2) 아니면 Supabase에서 27SS 데이터를 새로 가져와 기존 `build_report_html()`에 넣어 HTML을 새로 만들고 캐시에 저장, (3) Supabase 호출이 실패하면 마지막 성공 캐시를 `stale=true` 헤더와 함께 반환(캐시도 없으면 502).

**Tech Stack:** Python 3.13, FastAPI, uvicorn. 기존 `requests`/`openpyxl` 의존성은 그대로 둔다(openpyxl은 이 백엔드가 안 쓰지만 같은 패키지를 26FW 정적 빌드가 계속 쓰므로 제거하지 않는다).

## Global Constraints

- 기존 로직(`aggregate.py`, `report_builder.py`, `config.py`, `supabase_client.py`)은 **수정하지 않는다** — import해서 그대로 쓴다. 이번 작업으로 26FW 정적 빌드 경로(`run_weekly.py`)가 조금이라도 달라지면 안 된다.
- 새 코드는 `src/service/mlb_qm_fitting_report/live_app.py` 한 파일 + 테스트 파일 하나로 최대한 작게 유지한다.
- 에러 시 빈 화면 대신 항상 사람이 이해할 수 있는 응답(직전 캐시 또는 명확한 에러 메시지)을 준다.
- `python -m pytest` 대신 이 프로젝트 관례대로 각 테스트 파일을 `PYTHONPATH=. .venv/Scripts/python tests/test_X.py`로 직접 실행해서 확인한다(기존 테스트들과 동일한 방식, `if __name__ == "__main__":` 블록 사용).

---

### Task 1: FastAPI 의존성 추가 + 헬스체크 엔드포인트

**Files:**
- Modify: `pyproject.toml`
- Create: `src/service/mlb_qm_fitting_report/live_app.py`
- Test: `tests/test_live_app.py`

**Interfaces:**
- Produces: `app` (FastAPI 인스턴스, `live_app.py`에 정의) — 이후 태스크들이 이 파일에 라우트를 추가한다.

- [ ] **Step 1: 의존성 추가**

`pyproject.toml`의 `dependencies` 배열에 추가:

```toml
dependencies = [
    "requests>=2.32",
    "openpyxl>=3.1",
    "fastapi>=0.115",
    "uvicorn>=0.32",
]
```

- [ ] **Step 2: 설치**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && uv sync`
Expected: `fastapi`, `uvicorn`, `starlette` 등이 설치 로그에 나타남, 에러 없음.

- [ ] **Step 3: 실패하는 테스트 작성**

`tests/test_live_app.py`:

```python
import sys
sys.path.insert(0, ".")
from fastapi.testclient import TestClient
from src.service.mlb_qm_fitting_report.live_app import app


def test_healthcheck():
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


if __name__ == "__main__":
    test_healthcheck()
    print("OK: test_live_app")
```

- [ ] **Step 4: 테스트 실행해서 실패 확인**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python tests/test_live_app.py`
Expected: `ModuleNotFoundError: No module named 'src.service.mlb_qm_fitting_report.live_app'`

- [ ] **Step 5: 최소 구현**

`src/service/mlb_qm_fitting_report/live_app.py`:

```python
from fastapi import FastAPI

app = FastAPI()


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
```

- [ ] **Step 6: 테스트 통과 확인**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python tests/test_live_app.py`
Expected: `OK: test_live_app`

- [ ] **Step 7: 커밋**

```bash
git add pyproject.toml uv.lock src/service/mlb_qm_fitting_report/live_app.py tests/test_live_app.py
git commit -m "feat: add FastAPI skeleton for 27SS live backend"
```

---

### Task 2: 캐시-with-fallback 함수

**Files:**
- Modify: `src/service/mlb_qm_fitting_report/live_app.py`
- Modify: `tests/test_live_app.py`

**Interfaces:**
- Consumes: 없음(순수 함수, Supabase 호출은 인자로 주입받은 함수를 통해서만 함 — 테스트에서 가짜 함수로 교체 가능하게).
- Produces:
  - `class SnapshotCache` — `__init__(self, ttl_seconds: int)`, `get(self, fetch_fn: Callable[[], dict]) -> tuple[dict, bool]` (반환값: `(data, is_stale)`). `fetch_fn`이 예외를 던지면 마지막 성공 데이터를 `is_stale=True`로 반환하고, 캐시가 아예 없으면 그 예외를 그대로 다시 던진다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_live_app.py`에 추가:

```python
import time
from src.service.mlb_qm_fitting_report.live_app import SnapshotCache


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


if __name__ == "__main__":
    test_healthcheck()
    test_cache_returns_fresh_value_within_ttl()
    test_cache_falls_back_to_stale_on_fetch_error()
    test_cache_raises_when_no_prior_success()
    print("OK: test_live_app")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python tests/test_live_app.py`
Expected: `ImportError: cannot import name 'SnapshotCache'`

- [ ] **Step 3: 구현**

`live_app.py`에 추가 (import 추가: `import time`, `from typing import Callable`):

```python
import time
from typing import Callable

from fastapi import FastAPI

app = FastAPI()


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


@app.get("/healthz")
def healthz():
    return {"status": "ok"}
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python tests/test_live_app.py`
Expected: `OK: test_live_app`

- [ ] **Step 5: 커밋**

```bash
git add src/service/mlb_qm_fitting_report/live_app.py tests/test_live_app.py
git commit -m "feat: add TTL cache with stale-fallback for live backend"
```

---

### Task 3: `GET /` — 실제 27SS 데이터로 대시보드 렌더링

**Files:**
- Modify: `src/service/mlb_qm_fitting_report/live_app.py`
- Modify: `tests/test_live_app.py`

**Interfaces:**
- Consumes:
  - `load_settings() -> dict` (`config.py`)
  - `resolve_as_of_date(settings: dict, run_date: date) -> date` (`config.py`)
  - `week_id_for(as_of_date: date) -> str` (`config.py`)
  - `fetch_styles(settings: dict) -> list[dict]`, `fetch_fitting_records(settings: dict) -> list[dict]` (`supabase_client.py`)
  - `compute_progress(styles, records, as_of_date) -> dict` — `{season: {"TD": {...}, "QA": {...}}}` (`aggregate.py`)
  - `build_raw_rows(styles, records) -> dict` — `{season: [row, ...]}` (`aggregate.py`)
  - `build_report_html(snapshots: dict, settings: dict) -> str` (`report_builder.py`)
- Produces: `build_snapshot_payload(settings: dict) -> dict` — 27SS만 필터링해서
  `{"weeks": {week_id: {"as_of_date": iso, "progress": {...}, "warnings": [], "raw": {...}}}}` shape으로 반환.
  `GET /` 라우트가 이 함수 결과를 `SnapshotCache`에 넣고 `build_report_html`에 넘긴다.

- [ ] **Step 1: 실패하는 테스트 작성**

`tests/test_live_app.py`에 추가 (import 추가: `from datetime import date`, `from unittest.mock import patch`):

```python
from datetime import date
from unittest.mock import patch

STYLES_FIXTURE = [
    {
        "style_code": "S1", "item": "DK", "quarter": "Main TS", "season": "27SS",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    },
    {
        # 다른 시즌은 27SS 응답에 섞이면 안 됨
        "style_code": "S2", "item": "DK", "quarter": "Main TS", "season": "26FW",
        "td": "김철수", "qa": "박영희", "co": None, "qc_due": "2026-01-01",
        "pp_due": "2026-02-01", "top_due": "2026-03-01", "vendor": "V1",
        "washed": None, "qty_kr": 100, "qty_cn": 0, "earliest_etd": "2026-04-01",
    },
]
RECORDS_FIXTURE = [
    {"style_code": "S1", "stage": "FIT", "round": 1, "status": "Approved", "updated_at": "2026-01-01T00:00:00"},
]


def test_build_snapshot_payload_filters_to_27ss():
    from src.service.mlb_qm_fitting_report.live_app import build_snapshot_payload

    settings = {"supabase_url": "http://x", "supabase_anon_key": "k"}
    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.resolve_as_of_date", return_value=date(2026, 8, 6)):
        payload = build_snapshot_payload(settings)

    weeks = payload["weeks"]
    assert len(weeks) == 1
    week = next(iter(weeks.values()))
    assert week["as_of_date"] == "2026-08-06"
    assert list(week["progress"].keys()) == ["27SS"]
    assert list(week["raw"].keys()) == ["27SS"]
    assert len(week["raw"]["27SS"]) == 1  # 26FW(S2)는 안 들어옴
    assert week["raw"]["27SS"][0]["style_code"] == "S1"


def test_root_endpoint_returns_html():
    from src.service.mlb_qm_fitting_report.live_app import app

    with patch("src.service.mlb_qm_fitting_report.live_app.fetch_styles", return_value=STYLES_FIXTURE), \
         patch("src.service.mlb_qm_fitting_report.live_app.fetch_fitting_records", return_value=RECORDS_FIXTURE):
        client = TestClient(app)
        resp = client.get("/")

    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    assert "MLB QM Weekly Analysis" in resp.text


if __name__ == "__main__":
    test_healthcheck()
    test_cache_returns_fresh_value_within_ttl()
    test_cache_falls_back_to_stale_on_fetch_error()
    test_cache_raises_when_no_prior_success()
    test_build_snapshot_payload_filters_to_27ss()
    test_root_endpoint_returns_html()
    print("OK: test_live_app")
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python tests/test_live_app.py`
Expected: `ImportError: cannot import name 'build_snapshot_payload'`

- [ ] **Step 3: 구현**

`live_app.py` 전체를 아래로 교체 (Task 1-2에서 만든 `SnapshotCache`/`healthz`는 유지):

```python
import time
from datetime import date
from typing import Callable

from fastapi import FastAPI, Response

from src.service.mlb_qm_fitting_report.config import load_settings, resolve_as_of_date, week_id_for
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records
from src.service.mlb_qm_fitting_report.aggregate import compute_progress, build_raw_rows
from src.service.mlb_qm_fitting_report.report_builder import build_report_html

SEASON = "27SS"

app = FastAPI()


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


def build_snapshot_payload(settings: dict) -> dict:
    """27SS만 걸러서 report_builder.build_report_html이 기대하는 snapshots shape으로 만든다."""
    as_of_date = resolve_as_of_date(settings, run_date=date.today())
    week_id = week_id_for(as_of_date)

    styles = [s for s in fetch_styles(settings) if s.get("season") == SEASON]
    records = fetch_fitting_records(settings)
    style_codes = {s["style_code"] for s in styles}
    records = [r for r in records if r["style_code"] in style_codes]

    progress = compute_progress(styles, records, as_of_date)
    raw = build_raw_rows(styles, records)

    return {
        "weeks": {
            week_id: {
                "as_of_date": as_of_date.isoformat(),
                "progress": progress,
                "warnings": [],
                "raw": raw,
            }
        }
    }


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
```

- [ ] **Step 4: 테스트 통과 확인**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python tests/test_live_app.py`
Expected: `OK: test_live_app`

- [ ] **Step 5: 기존 테스트 전부 재확인 (회귀 없는지)**

Run 각각 (모두 `PYTHONPATH=. .venv/Scripts/python tests/<file>.py`):
`test_aggregate.py`, `test_chase.py`, `test_config.py`, `test_overrides.py`, `test_snapshots.py`, `test_xlsx_source.py`, `test_live_app.py`
Expected: 전부 `OK: ...` — 하나라도 실패하면 Task 3의 구현이 기존 함수 시그니처를 건드린 것이니 원인 찾아 수정.

- [ ] **Step 6: 커밋**

```bash
git add src/service/mlb_qm_fitting_report/live_app.py tests/test_live_app.py
git commit -m "feat: serve live 27SS dashboard via GET / using existing report_builder"
```

---

### Task 4: 로컬 실행 확인 (수동 QA)

**Files:** 없음 (코드 변경 없음, 검증만)

- [ ] **Step 1: 로컬 서버 기동**

Run: `cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note" && PYTHONPATH=. .venv/Scripts/python -m uvicorn src.service.mlb_qm_fitting_report.live_app:app --port 8000`

- [ ] **Step 2: 브라우저로 확인**

`http://localhost:8000/` 접속. 확인 항목:
- 페이지가 로드되고 "MLB QM Weekly Analysis" 헤더가 보이는지
- 시즌이 27SS로 뜨는지, 진행률 표가 실제 값(0이 아닌 값 포함)으로 채워지는지
- 브라우저 개발자도구 콘솔에 JS 에러가 없는지
- "분석" 탭 눌러서 정상 렌더링되는지 (26FW 전용 로직이 없어졌으므로 27SS도 렌더링돼야 함)

- [ ] **Step 3: 캐시/fallback 수동 확인**

`config/report_settings.json`의 `supabase_url`을 일시적으로 오타난 값으로 바꾸고 서버 재기동 없이(캐시 살아있는 상태에서) 새로고침 → 이전 데이터가 그대로 보이고 응답 헤더에 `X-Data-Stale: true`가 있는지 확인(개발자도구 Network 탭). 확인 후 `supabase_url`을 원래 값으로 **반드시 되돌린다**.

- [ ] **Step 4: 서버 종료**

Ctrl+C로 uvicorn 종료.

---

### Task 5: 배포 (수동 게이트 — 조직 프로세스 필요)

이 태스크는 자동 실행이 아니라, `dcs-ai-common:embedded-app` 스킬의 `deployment/prep.md` 절차를 따라 **DCS AI 담당자에게 GitHub 저장소 생성을 요청**하는 것부터 시작한다. 요청·수령은 사용자가 직접 해야 하는 단계(Teams 채널 메시지 전송, 초대 수락)라 미리 자동화할 수 없다.

**Files:**
- Create (배포 준비 시): `.env` (커밋 안 함, `.gitignore`에 이미 포함되어 있는지 확인)
- Create (첫 배포 성공 후): `.dcsai.json`

- [ ] **Step 1: GitHub 사용자명 확인**

Run: `gh auth status && gh api user --jq .login`

- [ ] **Step 2: 요청 메시지 생성해서 사용자에게 제시**

`prep.md`의 형식대로 메시지 작성:

```
안녕하세요, MLB QM Fitting 27SS Live Dashboard 배포 요청드립니다.

📌 프로젝트 개요
  - 구성: FastAPI(Python) 백엔드 단독(별도 프론트엔드 빌드 없음, 서버가 HTML 직접 렌더링)
  - 기능: Supabase(styles/fitting_records)에서 27SS FIT/PP/TOP 진행률을 요청마다 실시간
    계산해서 보여주는 대시보드

📦 필요한 리소스
  - GitHub 저장소 생성 (fnf-deepHeading 조직) + 초대받을 GitHub 사용자명: <Step 1 결과>
```

사용자에게 위 메시지를 Teams DCS AI 채널에 전달하도록 안내하고, 저장소 링크를 받을 때까지 대기.

- [ ] **Step 3: (저장소 링크 수령 후) 원격 연결 및 push**

```bash
cd "C:\Users\AC1005\OneDrive - F&F\★JANE★\CODE\meeting_note"
git remote add origin <받은 저장소 링크>
git push -u origin master
```

(이 저장소는 브랜치명이 `master`다 — `main`으로 바꾸지 말고 그대로 push.)

- [ ] **Step 4: `.env` 작성**

Supabase 접속 정보는 이미 `config/report_settings.json`에 공개 anon key로 커밋돼 있어 별도 `.env` 불필요 — DCS AI 담당자가 다른 시크릿(예: `DCSAI_API_KEY`)을 요구하면 그때 `.env`에 추가.

- [ ] **Step 5: 배포**

`$SKILL/deployment/deploy.md` 절차대로:

```bash
dcs-ai-cli --version
dcs-ai-cli app deploy \
  --name mlb-qm-fitting-27ss-live \
  --repo <저장소 링크> \
  --start-command "uv run uvicorn src.service.mlb_qm_fitting_report.live_app:app --host 0.0.0.0 --port 3000" \
  --install-command "uv sync"
```

(정확한 플래그명은 `dcs-ai-cli app deploy --help`로 그 시점 버전 기준 재확인 — 스킬 문서 기준 플래그가 CLI 버전에 따라 달라질 수 있음.)

- [ ] **Step 6: 배포 후 확인**

발급된 `https://dcsai.fnf.co.kr/apps/<slug>` 접속해서 Task 4와 동일한 항목 재확인.

- [ ] **Step 7: `.dcsai.json` 커밋**

```bash
git add .dcsai.json
git commit -m "chore: record dcsai deployment slug"
git push
```

---

## Self-review notes

- Task 3의 `build_snapshot_payload`가 `records`를 `style_codes`로 필터링하는 이유: `fetch_fitting_records`는 시즌 구분 없이 전체를 가져오므로, 27SS 스타일에 속하지 않는 record가 섞여 있어도 `compute_progress`/`build_raw_rows`가 `styles`(이미 27SS로 필터됨)를 기준으로 순회하기 때문에 실제로는 안 섞이지만, 테스트에서 명시적으로 검증하고 코드에서도 명시적으로 필터링해 의도를 분명히 한다.
- `week_id_for`/`resolve_as_of_date`/`load_settings`는 기존 `run_weekly.py`와 동일하게 그대로 재사용 — 새 날짜 로직을 만들지 않는다.
- Task 5는 조직 프로세스(Teams 요청, 담당자 응답 대기)가 끼어있어 다른 태스크처럼 한 세션에서 끝까지 자동 진행되지 않는다. Task 1-4까지 완료되면 로컬에서 완전히 동작하는 백엔드가 이미 존재하므로, Task 5는 별도 시점에 진행해도 무방하다.
