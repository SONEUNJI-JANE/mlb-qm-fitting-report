# src/service/mlb_qm_fitting_report/run_weekly.py
from datetime import date

from src.service.mlb_qm_fitting_report.config import load_settings, resolve_as_of_date, week_id_for
from src.service.mlb_qm_fitting_report.supabase_client import fetch_styles, fetch_fitting_records
from src.service.mlb_qm_fitting_report.aggregate import compute_progress
from src.service.mlb_qm_fitting_report.xlsx_source import read_fit_track_rows, compute_progress_from_xlsx
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

    for season, xlsx_path in settings.get("legacy_xlsx_sources", {}).items():
        rows = read_fit_track_rows(xlsx_path)
        progress[season] = compute_progress_from_xlsx(rows, as_of_date)

    overrides = load_overrides(week_id)
    progress = apply_overrides(progress, overrides)

    snapshots = load_snapshots()
    snapshots = append_snapshot(snapshots, week_id, as_of_date, progress, warnings=[])
    save_snapshots(snapshots)

    html = build_report_html(snapshots)
    with open("src/output/dashboard/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"done: week={week_id} as_of={as_of_date.isoformat()}")


if __name__ == "__main__":
    main()
