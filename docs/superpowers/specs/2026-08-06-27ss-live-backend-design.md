# 27SS Live Backend — Design

## Background

MLB QM Fitting 대시보드는 지금 정적 HTML 한 장(`report_builder.py`가 만든
`src/output/dashboard/index.html`)에 주차별 스냅샷 JSON을 통째로 구워 넣는 구조다.
새 주차 데이터를 반영하려면 매번:

1. `run_weekly.py`로 스냅샷 재계산 + JSON 저장
2. `dcs-ai-cli app update`로 정적 파일 재배포

를 사람이 손으로 해야 한다. 26FW는 로컬 엑셀 파일(이 PC에만 있음)을 읽어야 해서
자동화가 어렵지만, 27SS는 Supabase(`styles`, `fitting_records`)만 쓰기 때문에
서버 쪽에서 완전히 자동화할 수 있다.

## Goal

27SS를 "배포 없이 항상 최신 데이터를 보여주는" 별도 앱으로 분리한다.
26FW는 지금 있는 그대로(정적 대시보드, 수동 배포) 손대지 않는다.

## Non-goals

- 26FW를 이 프로젝트에서 같이 옮기지 않는다(다음 프로젝트).
- 인증/권한 체계 변경 없음 — 지금 앱과 동일한 접근 방식 유지.
- 실시간 다중 사용자 협업 기능(동시 편집 등) 없음.

## Architecture

```
[브라우저] --fetch--> [FastAPI 백엔드] --REST--> [Supabase: styles, fitting_records]
```

- **백엔드**: Python FastAPI. `src/service/mlb_qm_fitting_report/`의 기존
  `supabase_client.py`, `aggregate.py`, `config.py`를 그대로 import해서 재사용한다
  (새로 안 만듦 — 검증된 로직 그대로 씀).
- **프론트**: 지금 `report_builder.py`가 만드는 HTML/CSS/JS를 거의 그대로 가져오되,
  `__SNAPSHOT_JSON__`을 파일에 굽는 대신 페이지 로드 시 `fetch('/api/summary?...')`로
  받아온다. 시즌 선택은 27SS 고정(드롭다운 없앰).

## Data flow — 스냅샷 저장을 없애는 이유

지금 구조는 "이번 주 as_of_date 기준으로 계산한 결과"를 주차별로 저장해서, 나중에
과거 주차를 다시 보여줄 때 그 저장된 값을 그대로 쓴다. 이건 매번 사람이 실행해야
만들어지는 값이라 자동화와 안 맞는다.

대신: `styles`/`fitting_records`의 모든 날짜 필드(due date, confirm_date)가 이미
실제 날짜로 저장돼 있으므로, **임의의 과거 as_of_date를 넣어도 그 시점 기준 진행률을
그 자리에서 재계산**할 수 있다(`aggregate.compute_progress`, `build_raw_rows`는
이미 `as_of_date` 인자를 받는 순수 함수라 그대로 재사용 가능). 그래서:

- 스냅샷 저장(JSON 누적) 완전히 제거
- "주차 선택" 드롭다운 → "기준일 선택"(날짜 입력, 기본값 = 오늘 기준 최근 금요일 등
  기존 `resolve_as_of_date` 로직 그대로 재사용)
- cron/스케줄 자체가 필요 없어짐 — 매 요청이 항상 최신

## API

```
GET /api/summary?as_of=YYYY-MM-DD
```

응답 형태는 지금 프론트 JS가 기대하는 `week.raw['27SS']` / `week.progress['27SS']`와
동일한 shape으로 맞춘다(프론트 JS 로직을 최대한 안 건드리기 위해).

```json
{
  "as_of_date": "2026-08-06",
  "progress": { "TD": {...}, "QA": {...} },
  "raw": [ {...}, {...} ]
}
```

- `as_of` 파라미터 생략 시 기존 `resolve_as_of_date(settings, run_date=today)` 로직으로
  기본값 계산.
- 잘못된 날짜 포맷 → 400 + 에러 메시지.

## Error handling

- Supabase 호출 실패(네트워크/타임아웃/5xx): 마지막 성공 응답을 짧게(예: 5분)
  in-memory 캐시해뒀다가 그대로 반환 + 응답에 `"stale": true` 플래그. 완전히 빈 화면
  대신 "몇 분 전 데이터"를 보여줘서 서비스 다운을 피한다.
- 캐시도 없는 첫 요청에서 Supabase 실패 시: 502 + 프론트에 에러 메시지 표시(빈 표
  대신 명확한 안내).
- 프론트에서 fetch 실패 시 재시도 1회 후 에러 배너 표시.

## Deployment

- `dcs-ai-common:embedded-app` 스킬의 K8s runtime-fetch 방식으로 배포
  (`dcs-ai-cli app deploy`). 새 slug/URL 발급됨.
- 첫 배포 후 `.dcsai.json` 커밋(스킬 가이드대로), 이후 재배포는 `dcs-ai-cli app redeploy`.

## Testing

- 기존 `tests/test_aggregate.py`, `tests/test_config.py`는 그대로 통과해야 함
  (로직 안 건드림 — import해서 재사용만 하므로).
- 새 테스트: `GET /api/summary` 엔드포인트 — 정상 응답 shape 검증 1개,
  Supabase 실패 시 캐시 fallback 동작 검증 1개.
- 배포 전 로컬에서 백엔드 띄우고 브라우저로 실제 데이터 렌더링 확인(수동 QA).

## Risks / open questions

- FastAPI 배포 환경에서 `config/report_settings.json`의 Supabase anon key를 그대로
  쓸 수 있는지(환경변수로 옮겨야 할 수도 있음) — 배포 단계에서 `embedded-app` 스킬의
  `postgres/setup.md` 또는 환경변수 가이드 참고해서 확인 필요.
- 지금 프론트 JS는 `WITHIN_STAGE_PIPELINE`에 '보정' 단계가 있는데, 27SS Supabase
  데이터에 '보정' 단계가 실제로 존재하는지 확인 필요(없으면 그 단계는 자연히
  빈 표로 나올 뿐, 에러는 아님).
