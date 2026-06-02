from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "A Tu Gusto"
APP_DISPLAY_NAME = "A Tu Gusto | Gestion Operativa"
APP_VERSION = "3.0.0"
APP_COMPANY = "A Tu Gusto"


def get_base_path() -> Path:
    """Return the project base path in development or frozen mode."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_path()
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = DATA_DIR / "backups"
REPORTS_DIR = DATA_DIR / "reportes"
ARCHIVE_DIR = BASE_DIR / "archive"
DOCS_DIR = BASE_DIR / "docs"
TOOLS_DIR = BASE_DIR / "tools"

for directory in (DATA_DIR, BACKUP_DIR, REPORTS_DIR, ARCHIVE_DIR, DOCS_DIR, TOOLS_DIR):
    directory.mkdir(parents=True, exist_ok=True)


DB_PATH = DATA_DIR / "inventario.db"
STYLE_PATH = BASE_DIR / "styles.qss"
ICON_PATH = BASE_DIR / "icon.ico"
ROOT_PATH = BASE_DIR


def as_posix_path(path: Path | str) -> str:
    return str(Path(path))


if not getattr(sys, "frozen", False):
    print(f"[DEBUG] BASE_DIR: {BASE_DIR}")
    print(f"[DEBUG] DATA_DIR: {DATA_DIR}")
    print(f"[DEBUG] DB_PATH: {DB_PATH}")
