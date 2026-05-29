Feat: Dashboard redesign and style guard updates

Summary:
- Improved dashboard layout: horizontal metric cards, tighter paddings, and chart placeholders for future graphs.
- Alerts table renamed/objectName set for easier styling (`alertsTable`).
- Added `chartPlaceholder` frames for sales/purchases charts.
- Added `# allow-inline-style` marker to `main_app.py` and `tools/installer/main_instalador.py` to avoid runtime/style-guard warnings for intentional central stylesheet usage.
- Backup action (`Crear respaldo`) in MainWindow remains unchanged and uses `db.create_daily_backup()`.

Branch:
- Changes committed to `feature/dashboard-redesign`.

Notes / next steps:
- Add QSS rules in `styles.qss` to style new object names (`dashboardCard`, `metricValue`, `chartPlaceholder`, `alertsTable`).
- Implement actual charts (e.g., using matplotlib or pyqtgraph) and hook real endpoints for sales/purchases trends.
- Optionally mark other files that legitimately set styles with `# allow-inline-style` or refactor to the centralized stylesheet in `app_core/theme.py`.
 - Implemented charts using `pyqtgraph` when available; fallbacks show numeric 7-day summaries when the plotting library is missing.
 - Enlarged and improved `LoginDialog` layout (logo + title row, wider card, Enter submits by default).
 - Updated `styles.qss` with rules for `dashboardCard`, `metricValue`, `chartPlaceholder` and `alertsTable`.
