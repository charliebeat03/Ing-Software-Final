from __future__ import annotations

import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMessageBox

from app_core.auth import LoginDialog
from app_core.context import build_app_context
from app_core.theme import build_stylesheet
from app_core.style_guard import enforce_runtime_style_protection, find_inline_styles, format_findings
from config import APP_DISPLAY_NAME, APP_VERSION
from modules.main_window import MainWindow


def setup_environment() -> None:
    base_path = Path(__file__).resolve().parent
    base_str = str(base_path)
    if base_str not in sys.path:
        sys.path.insert(0, base_str)


def main() -> int:
    setup_environment()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_DISPLAY_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyleSheet(build_stylesheet())
    enforce_runtime_style_protection()

    try:
        # Static check: detect inline `setStyleSheet(` occurrences that
        # should be converted to the centralized `styles.qss` file.
        findings = find_inline_styles(Path(__file__).resolve().parent)
        if findings:
            summary = format_findings(findings[:50])
            reply = QMessageBox.warning(
                None,
                "Estilos inline detectados",
                "Se han detectado llamadas a setStyleSheet en el código fuente.\n"
                "Es recomendable centralizar estilos en styles.qss para mantener coherencia visual.\n\n"
                f"Muestras:\n{summary}\n\nContinuar de todas formas?",
                QMessageBox.Ok | QMessageBox.Cancel,
            )
            if reply == QMessageBox.Cancel:
                return 1

        login = LoginDialog()
        if login.exec_() != LoginDialog.Accepted or not login.authenticated_user:
            return 0

        context = build_app_context(login.authenticated_user)
        window = MainWindow(context=context)
        window.show()
        return app.exec_()
    except Exception as exc:  # pragma: no cover - defensive startup guard
        QMessageBox.critical(
            None,
            "Error de inicio",
            f"La aplicacion no pudo iniciar correctamente.\n\n{exc}",
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
