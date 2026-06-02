from __future__ import annotations

from pathlib import Path

from config import STYLE_PATH


def build_stylesheet() -> str:
    """Load and return the global stylesheet.

    Prefers the external `styles.qss` defined by `config.STYLE_PATH` so the
    visual design is centralized. If the file is missing, return a small
    fallback stylesheet to keep the UI usable.
    """
    try:
        path = Path(STYLE_PATH)
        if path.exists():
            return path.read_text(encoding="utf-8")
    except Exception:
        pass

    # Minimal fallback stylesheet (used only if styles.qss is missing).
    return """
QWidget {
    background-color: #f8f9fa;
    color: #2c3e50;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 11px;
}

QPushButton#primaryButton {
    background-color: #3498db;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 600;
}

QPushButton#primaryButton:hover { background-color: #2e86c1; }

QFrame#loginCard { background: white; border: 1px solid #e9ecef; border-radius: 10px; padding: 16px; }
QLabel#loginTitle { font-size: 22px; font-weight: 700; color: #2c3e50; }
QLabel#moduleTitle { font-size: 20px; font-weight: 700; color: #2c3e50; }
QLabel#moduleSubtitle, QLabel#loginSubtitle { color: #6b7e86; }
"""
