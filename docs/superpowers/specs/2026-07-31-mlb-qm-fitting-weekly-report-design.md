# MLB QM Fitting 주간 미팅노트 자동 생성 — 설계

## 배경 / 목적

MLB QM Fitting 인증 진행 상황(FIT/PP/TOP 완료율)을 매주 수기로 작성해온 주간 업무 보고(예: "7/27 주간 업무 보고")를, `dcsai.fnf.co.kr/apps/mlb-qm-fitting` 뒤의 Supabase DB에서 자동 집계해 생성한다. 매주 실행 시 과거 주차 기록은 보존하고 새 주차만 누적 추가한다. 계산값이 실제와 다를 때는 원본 DB를 건드리지 않고 표시값 산출에 쓰인 입력(분자/분모)만 오버라이드할 수 있어야 한다.

## 데이터 소스

Supabase 프로젝트 `ppeedhejhbgshdjnlrha` (읽기 전용, anon key 사용).

- `styles`: style_code, item, quarter, season, td, qa, co, qc_due, pp_due, top_due 등
- `fitting_records`: style_code, stage(`보정`/`FIT`/`PP`/`TOP`), round, status(`Go to FIT`/`Rejected`/`Int Rej`/`Approved`), fitting_date 등
- `settings`: 체이스 경고 기준일수 등 (현재 DB엔 `warn_fit_cfm_due` 등 일부만 존재 — 스크린샷의 세분화된 단계별 임계값은 앱 내 설정 UI 값이며 DB에 완전히 반영 안 돼 있을 수 있음. 1차 구현은 스크린샷에 보이는 값을 상수로 코드에 반영하고, 추후 DB 연동값이 갖춰지면 그쪽을 우선한다)

이번 스코프: **FIT / PP / TOP** 3단계만. CAD 지표(요척 협의, PP GRADING CFM)는 데이터 소스가 없어 제외.

## 진척률 정의

스타일별 해당 단계 최신 round의 status가 `Approved`면 완료로 집계.

- **총량 대비 %** = 완료 스타일 수 / 전체 대상 스타일 수 (기존 수기 보고 방식과 동일)
- **기준대비 %** = (기준일 ≤ due date인 스타일 중 완료 수) / (기준일 ≤ due date인 전체 스타일 수)
  - FIT은 `styles.qc_due`, PP는 `pp_due`, TOP은 `top_due` 기준
  - due date가 null인 스타일은 기준대비 계산에서 제외 (총량 대비에는 포함)
  - 100% 초과 표기 없음(분자 ≤ 분모 항상 성립하므로), 100% 미달이면 지연

두 지표를 표에 함께 표시한다.

### 기준일(as_of_date)

리포트는 매주 월요일 오전 실행되지만, 집계 대상은 "그 실행 시점"이 아니라 직전 주 금요일까지다. 기준일은 하드코딩하지 않고 설정 파일로 뺀다.

```jsonc
// config/report_settings.json
{
  "as_of_weekday": "FRI",       // 기준 요일 (기본: 금요일)
  "as_of_date_override": null   // 특정 주만 수동 지정 (YYYY-MM-DD). 평소 null
}
```

- `as_of_date_override`가 null이면: 실행일 기준 직전 해당 요일을 자동 계산
- 공휴일 등으로 기준일이 달라지는 주는 이 값을 그 주만 수동 지정
- 스냅샷에는 실제 사용된 `as_of_date`를 함께 기록해 나중에 혼동 방지

## 아키텍처 / 데이터 흐름

```
[Supabase: styles + fitting_records + settings]  (읽기 전용)
        │  매주 1회, schedule 스킬로 등록된 cron
        ▼
[fetch_and_aggregate.py]
   - as_of_date 결정 (config/report_settings.json)
   - styles + fitting_records 조회
   - 시즌 × TD/QA × 단계(FIT/PP/TOP)별 총량대비/기준대비 % 계산
   - overrides/{week}.json 있으면 해당 분자/분모로 교체
        │
        ▼
[data/weekly_snapshots.json]  ← 이번 주 계산결과 append (과거 주 그대로 유지)
        │
        ▼
[build_report.py] → snapshots.json 읽어 report.html 생성
        │
        ▼
[dcs-ai-cli dashboard deploy] → Quick Dashboard URL 갱신
```

### 폴더 구조

```
src/service/mlb-qm-fitting-report/
  fetch_and_aggregate.py
  build_report.py
config/
  report_settings.json
overrides/
  2026-W31.json              # 주차별 수동 오버라이드 (있는 주만 존재)
src/output/
  weekly_snapshots.json      # 누적 주차 데이터 (append-only)
  report.html                # 배포 산출물
```

## 화면 구조 (report.html)

단일 정적 HTML, `weekly_snapshots.json`을 fetch해 클라이언트에서 렌더링. Supabase는 직접 물지 않음(원본 접근은 python 스크립트만).

```
┌─────────────────────────────────────────────┐
│ MLB QM Fitting 주간 보고        [주차 드롭다운▾]│  ← 기본: 최신 주
├─────────────────────────────────────────────┤
│ 시즌 → 담당(TD/QA) → 단계별 총량대비%/기준대비% │
│   (기존 수기 보고 표 레이아웃 그대로 유지)       │
│                                               │
│ ⚠ 마감 임박/지연 스타일 (chase 경고 기준 초과) │
├─────────────────────────────────────────────┤
│ [수정] 최신 주만 활성 — 계산 입력값(분자/분모) │
│        오버라이드, 과거 주는 잠금              │
└─────────────────────────────────────────────┘
```

## 오버라이드 동작

- 표시 텍스트를 직접 고치는 게 아니라 **집계 입력값(분자/분모)** 을 재정의
- `overrides/{week}.json`: `[{season, stage, owner_type, override_numerator, override_denominator}, ...]`
- 해당 주 재실행/재조회 시 override 존재하면 계산값 대신 사용, 두 % 다 재계산
- 다음 주는 override 파일이 없으므로 자동 재계산으로 복귀 (해당 주만 고정)
- 과거(확정된) 주차는 UI에서 수정 버튼 비활성화

## 에러 처리

- Supabase 조회 실패 → 스크립트 중단, 직전 스냅샷/배포본 유지 (빈 데이터로 덮어쓰기 금지)
- due_date null → 기준대비 계산 제외, 총량 대비엔 포함
- 배포 전 JSON 검증: 주차 키 형식(`YYYY-Www`), % 값 0~100 범위 체크

## 테스트

- `fetch_and_aggregate.py`: 총량대비/기준대비 % 계산 함수에 대해 알려진 입력(작은 fixture: 스타일 N개, due date 섞음, round별 status 섞음)으로 assert 기반 self-check
- override 병합 로직: override 있을 때/없을 때 결과 분기 확인
- as_of_date 계산: `as_of_date_override` null/지정 두 케이스, 요일 계산 경계값(월요일 실행 시 정확히 직전 금요일 나오는지)

## 배포 자동화

`schedule` 스킬로 주간 cron 클라우드 에이전트 등록:
1. `fetch_and_aggregate.py` 실행 (snapshots.json 갱신)
2. `build_report.py` 실행 (report.html 갱신)
3. `dcs-ai-cli dashboard deploy`로 Quick Dashboard 재배포
