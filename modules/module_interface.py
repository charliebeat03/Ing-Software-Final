from __future__ import annotations

from PyQt5.QtWidgets import QWidget


class BaseModule(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context: dict | None = None

    def setup(self, context: dict) -> None:
        self.context = context or {}

    def set_context(self, context: dict) -> None:
        self.setup(context)

    def cleanup(self) -> None:
        return None
