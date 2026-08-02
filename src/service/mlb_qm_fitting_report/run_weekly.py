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
            label_offsets = fetch_due_offsets(settings, season)
        except Exception:
            label_offsets = None  # Supabase 실패 시 xlsx_source.py의 코드 기본값 사용
        raw_rows = read_fit_track_raw(xlsx_path, raw_apparel_sources.get(season))
        raw[season] = raw_rows
        progress[season] = compute_progress_from_xlsx(resolve_due_dates(raw_rows, label_offsets), as_of_date)

    try:
        overrides = fetch_overrides(settings, week_id)
    except Exception:
        overrides = load_overrides(week_id)  # Supabase 실패 시 로컬 overrides/ 폴더로 fail open
    progress = apply_overrides(progress, overrides)

    snapshots = load_snapshots()
    snapshots = append_snapshot(snapshots, week_id, as_of_date, progress, warnings=[], raw=raw)
    save_snapshots(snapshots)

    html = build_report_html(snapshots, settings)
    with open("src/output/dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"done: week={week_id} as_of={as_of_date.isoformat()}")


if __name__ == "__main__":
    main()
