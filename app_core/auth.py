from __future__ import annotations

from dataclasses import dataclass

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QFrame,
)

from database import db
from .security import verify_password


@dataclass
class AuthResult:
    success: bool
    user: dict | None = None
    error: str | None = None


class AuthService:
    def authenticate(self, username: str, password: str) -> AuthResult:
        username = (username or "").strip().lower()
        if not username or not password:
            return AuthResult(False, error="Debe escribir usuario y contrasena.")

        user = db.get_one(
            "usuarios",
            "LOWER(username) = ? AND activo = 1",
            (username,),
        )
        if not user:
            return AuthResult(False, error="Usuario no encontrado o inactivo.")

        if not verify_password(password, user["password_salt"], user["password_hash"]):
            return AuthResult(False, error="Contrasena incorrecta.")

        return AuthResult(
            True,
            user={
                "id": user["id"],
                "username": user["username"],
                "nombre_completo": user["nombre_completo"],
                "rol": user["rol"],
            },
        )


class LoginDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.auth_service = AuthService()
        self.authenticated_user: dict | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        self.setWindowTitle("Iniciar sesion")
        self.setModal(True)
        self.setMinimumWidth(520)
        self.resize(560, 380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Card container to give a consistent framed login area
        card = QFrame()
        card.setObjectName("loginCard")
        card.setMinimumWidth(420)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(14)

        # Logo + title row
        header_row = QHBoxLayout()
        logo = QLabel("ATG")
        logo.setObjectName("loginLogo")
        logo.setFixedSize(54, 54)
        logo.setAlignment(Qt.AlignCenter)

        header = QLabel("A Tu Gusto")
        header.setObjectName("loginTitle")
        header.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        header_row.addWidget(logo)
        header_row.addSpacing(8)
        header_row.addWidget(header)

        subtitle = QLabel("Gestion integrada para compras, cocina, ventas y cierres.")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("loginSubtitle")

        form_layout = QFormLayout()
        form_layout.setSpacing(12)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Usuario")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contrasena")
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Usuario", self.username_input)
        form_layout.addRow("Contrasena", self.password_input)

        hint = QLabel(
            "Usuarios iniciales: admin/admin123, recepcion/recepcion123, "
            "chef/chef123, gerente/gerente123."
        )
        hint.setWordWrap(True)
        hint.setObjectName("loginHint")

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        self.cancel_button = QPushButton("Salir")
        self.login_button = QPushButton("Entrar")
        self.login_button.setDefault(True)
        self.login_button.setObjectName("primaryButton")

        self.cancel_button.clicked.connect(self.reject)
        self.login_button.clicked.connect(self.handle_login)
        self.password_input.returnPressed.connect(self.handle_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)

        button_row.addWidget(self.cancel_button)
        button_row.addWidget(self.login_button)

        # assemble card
        # header row (logo + title)
        card_layout.addLayout(header_row)
        card_layout.addWidget(subtitle)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(hint)
        card_layout.addLayout(button_row)

        layout.addWidget(card, alignment=Qt.AlignCenter)

        # focus and UX
        self.username_input.setFocus()

    def handle_login(self) -> None:
        result = self.auth_service.authenticate(
            self.username_input.text(),
            self.password_input.text(),
        )
        if not result.success:
            QMessageBox.warning(self, "Acceso denegado", result.error or "No fue posible autenticar.")
            return

        self.authenticated_user = result.user
        self.accept()

    def accept(self) -> None:
        """Only accept dialog if authentication succeeded."""
        if not self.authenticated_user:
            QMessageBox.warning(self, "Acceso denegado", "Credenciales inválidas. Verifique usuario y contraseña.")
            return
        super().accept()

    def keyPressEvent(self, event) -> None:
        # Intercept Enter/Return to avoid accidental dialog close and force handle_login
        from PyQt5.QtCore import Qt
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.handle_login()
            return
        super().keyPressEvent(event)
