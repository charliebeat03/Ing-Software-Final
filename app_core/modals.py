from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)


class ConfirmDialog(QDialog):
    def __init__(self, parent: QWidget | None, title: str, message: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName("confirmDialog")
        self._build_ui(message)

    def _build_ui(self, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        frame = QFrame()
        frame.setObjectName("modalCard")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setObjectName("modalMessage")

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setObjectName("modalCancel")
        ok_btn = QPushButton("Confirmar")
        ok_btn.setObjectName("modalConfirm")

        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(ok_btn)

        frame_layout.addWidget(lbl)
        frame_layout.addLayout(btn_row)

        layout.addWidget(frame)

    def exec_(self) -> bool:
        return super().exec_() == QDialog.Accepted


class InfoDialog(QDialog):
    def __init__(self, parent: QWidget | None, title: str, message: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setObjectName("infoDialog")
        self._build_ui(message)

    def _build_ui(self, message: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        frame = QFrame()
        frame.setObjectName("modalCard")
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)

        lbl = QLabel(message)
        lbl.setWordWrap(True)
        lbl.setObjectName("modalMessage")

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        ok_btn = QPushButton("Ok")
        ok_btn.setObjectName("modalConfirm")
        ok_btn.clicked.connect(self.accept)

        btn_row.addWidget(ok_btn)

        frame_layout.addWidget(lbl)
        frame_layout.addLayout(btn_row)

        layout.addWidget(frame)

    def exec_(self) -> bool:
        return super().exec_() == QDialog.Accepted
