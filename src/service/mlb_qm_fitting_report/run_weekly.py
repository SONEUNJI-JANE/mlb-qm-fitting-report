# src/service/mlb_qm_fitting_report/run_weekly.py
from datetime import date

from src.service.mlb_qm_fitting_report.config import load_settings, resolve_as_of_date, week_id_for
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records, fetch_overrides, fetch_due_offsets
from src.service.mlb_qm_fitting_report.aggregate import compute_progress, build_raw_rows
from src.service.mlb_qm_fitting_report.xlsx_source import compute_progress_from_xlsx, read_fit_track_raw, resolve_due_dates
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
    raw = build_raw_rows(styles, records)

    raw_apparel_sources = settings.get("raw_apparel_sources", {})
    for season, xlsx_path in settings.get("legacy_xlsx_sources", {}).items():
        try:
            try:
                label_offsets = fetch_due_offsets(settings, season)
            except Exception:
                label_offsets = None  # Supabase 실패 시 xlsx_source.py의 코드 기본값 사용
            raw_rows = read_fit_track_raw(xlsx_path, raw_apparel_sources.get(season))
            raw[season] = raw_rows
            progress[season] = compute_progress_from_xlsx(resolve_due_dates(raw_rows, label_offsets), as_of_date)
        except Exception as e:
            # 로컬 엑셀 경로에만 접근 가능한 시즌이라, 그 파일이 없는 환경(예: 클라우드 cron)에서
            # 돌리면 여기서 실패한다. 그 시즌만 건너뛰고 나머지(Supabase 시즌)는 계속 진행.
            print(f"skip {season} (xlsx source unavailable): {e}")

    try:
        overrides = fetch_overrides(settings, week_id)
    except Exception:
        overrides = load_overrides(week_id)  # Supabase 실패 시 로컬 overrides/ 폴더로 fail open
    progress = apply_overrides(progress, overrides)

    snapshots = load_snapshots()
    # 이번 실행에서 못 만든 시즌(위에서 skip된 시즌)은 그 주차에 이미 있던 스냅샷 값을 그대로 유지한다.
    # 안 그러면 클라우드 cron이 26FW 없이 돌 때마다 같은 주차의 26FW 데이터가 사라져 버린다.
    existing_week = snapshots.get("weeks", {}).get(week_id, {})
    for season, prior_progress in existing_week.get("progress", {}).items():
        progress.setdefault(season, prior_progress)
    for season, prior_raw in existing_week.get("raw", {}).items():
        raw.setdefault(season, prior_raw)

    snapshots = append_snapshot(snapshots, week_id, as_of_date, progress, warnings=[], raw=raw)
    save_snapshots(snapshots)

    html = build_report_html(snapshots, settings)
    with open("src/output/dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"done: week={week_id} as_of={as_of_date.isoformat()}")


if __name__ == "__main__":
    main()
