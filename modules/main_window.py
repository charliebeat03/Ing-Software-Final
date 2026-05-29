from __future__ import annotations

from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAction,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from app_core.module_registry import ModuleSpec, default_module, get_module_spec, grouped_modules
from database import db
from modules.module_loader import ModuleLoader


class MainWindow(QMainWindow):
    def __init__(self, context: dict | None = None):
        super().__init__()
        self.context = context or {}
        self.context["navigate_module"] = self.show_module
        self.module_loader = ModuleLoader(self.context)
        self.module_widgets: dict[str, QWidget] = {}
        self.nav_buttons: dict[str, QPushButton] = {}
        self.current_module_id: str | None = None

        self.setWindowTitle(self.context.get("display_name", "A Tu Gusto"))
        self.resize(1440, 860)
        self.setMinimumSize(1180, 760)

        self._build_ui()
        self._build_menu()
        self._start_clock()
        self.show_module(default_module().module_id)

    def _build_ui(self) -> None:
        central = QWidget()
        central_layout = QHBoxLayout(central)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        self.setCentralWidget(central)

        self.sidebar = self._build_sidebar()
        content = self._build_content_area()

        central_layout.addWidget(self.sidebar)
        central_layout.addWidget(content, 1)

        status_bar = QStatusBar()
        status_bar.showMessage("Sistema listo para operar.")
        self.setStatusBar(status_bar)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("shellSidebar")
        sidebar.setMinimumWidth(250)
        sidebar.setMaximumWidth(290)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel("A Tu Gusto")
        title.setObjectName("brandTitle")

        subtitle = QLabel("Compras, cocina, ventas, inventario y cierre diario.")
        subtitle.setObjectName("brandSubtitle")
        subtitle.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(subtitle)

        for group_name, specs in grouped_modules().items():
            section = QLabel(group_name)
            section.setObjectName("sectionTitle")
            layout.addWidget(section)
            for spec in specs:
                button = QPushButton(spec.title)
                button.setObjectName("sidebarButton")
                button.setCheckable(True)
                button.clicked.connect(lambda checked=False, module_id=spec.module_id: self.show_module(module_id))
                self.nav_buttons[spec.module_id] = button
                layout.addWidget(button)

        layout.addStretch(1)

        footer = QLabel(f"Version {self.context.get('version', '3.0.0')}")
        footer.setObjectName("brandSubtitle")
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)
        return sidebar

    def _build_content_area(self) -> QFrame:
        content = QFrame()
        content.setObjectName("shellContent")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("shellHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 14, 20, 14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.module_title_label = QLabel("Panel General")
        self.module_title_label.setObjectName("moduleTitle")
        self.module_subtitle_label = QLabel("Resumen operativo del restaurante.")
        self.module_subtitle_label.setObjectName("moduleSubtitle")
        title_box.addWidget(self.module_title_label)
        title_box.addWidget(self.module_subtitle_label)

        self.date_label = QLabel("")
        self.date_label.setObjectName("moduleDate")

        current_user = self.context.get("current_user", {})
        user_name = current_user.get("nombre_completo", "Usuario")
        user_role = current_user.get("rol", "Sin rol")
        self.user_label = QLabel(f"{user_name} | {user_role}")
        self.user_label.setObjectName("userLabel")

        self.backup_button = QPushButton("Crear respaldo")
        self.backup_button.setObjectName("quickActionButton")
        self.backup_button.clicked.connect(self.trigger_backup)

        # Sidebar toggle button
        self.toggle_sidebar_button = QPushButton("❮")
        self.toggle_sidebar_button.setObjectName("sidebarToggleButton")
        self.toggle_sidebar_button.setFixedSize(36, 36)
        self.toggle_sidebar_button.clicked.connect(self.toggle_sidebar)

        right_box = QVBoxLayout()
        right_box.setSpacing(4)
        right_box.addWidget(self.user_label, alignment=Qt.AlignRight)
        right_box.addWidget(self.date_label, alignment=Qt.AlignRight)

        header_layout.addLayout(title_box, 1)
        header_layout.addWidget(self.toggle_sidebar_button)
        header_layout.addWidget(self.backup_button)
        header_layout.addSpacing(12)
        header_layout.addLayout(right_box)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout.addWidget(header)
        layout.addWidget(self.stacked_widget, 1)
        return content

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        archivo_menu = menu_bar.addMenu("Archivo")
        refrescar_action = QAction("Refrescar modulo actual", self)
        refrescar_action.triggered.connect(self.refresh_current_module)
        respaldo_action = QAction("Crear respaldo ahora", self)
        respaldo_action.triggered.connect(self.trigger_backup)
        salir_action = QAction("Salir", self)
        salir_action.triggered.connect(self.close)

        archivo_menu.addAction(refrescar_action)
        archivo_menu.addAction(respaldo_action)
        archivo_menu.addSeparator()
        archivo_menu.addAction(salir_action)

        modulos_menu = menu_bar.addMenu("Modulos")
        for group_name, specs in grouped_modules().items():
            group_menu = modulos_menu.addMenu(group_name)
            for spec in specs:
                action = QAction(spec.title, self)
                action.triggered.connect(lambda checked=False, module_id=spec.module_id: self.show_module(module_id))
                group_menu.addAction(action)

        ayuda_menu = menu_bar.addMenu("Ayuda")
        info_action = QAction("Acerca de", self)
        info_action.triggered.connect(self.show_about)
        ayuda_menu.addAction(info_action)

    def _start_clock(self) -> None:
        self._update_clock()
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(60_000)

    def _update_clock(self) -> None:
        self.date_label.setText(datetime.now().strftime("%d/%m/%Y %I:%M %p"))

    def load_module(self, module_id: str) -> QWidget:
        if module_id in self.module_widgets:
            return self.module_widgets[module_id]

        spec = get_module_spec(module_id)
        widget = self.module_loader.load(spec)
        self.module_widgets[module_id] = widget
        self.stacked_widget.addWidget(widget)
        return widget

    def show_module(self, module_id: str) -> None:
        spec = get_module_spec(module_id)
        widget = self.load_module(module_id)
        self.stacked_widget.setCurrentWidget(widget)
        self.current_module_id = module_id
        self.module_title_label.setText(spec.title)
        self.module_subtitle_label.setText(spec.description)

        for current_id, button in self.nav_buttons.items():
            button.setChecked(current_id == module_id)

        self.statusBar().showMessage(f"{spec.title}: {spec.description}")

        refresh_method = getattr(widget, "refresh_data", None)
        if callable(refresh_method):
            refresh_method()
            return
        update_method = getattr(widget, "actualizar_todo", None)
        if callable(update_method):
            update_method()

    def refresh_current_module(self) -> None:
        if not self.current_module_id:
            return
        widget = self.module_widgets.get(self.current_module_id)
        for method_name in ("refresh_data", "actualizar_todo", "load_initial_data", "load_data"):
            method = getattr(widget, method_name, None)
            if callable(method):
                method()
                self.statusBar().showMessage("Modulo actualizado.")
                return
        self.statusBar().showMessage("Este modulo no expone una rutina de recarga.")

    def trigger_backup(self) -> None:
        backup_path = db.create_daily_backup()
        QMessageBox.information(
            self,
            "Respaldo creado",
            f"El respaldo actual se encuentra en:\n{backup_path}",
        )

    def show_about(self) -> None:
        QMessageBox.information(
            self,
            "Acerca de A Tu Gusto",
            "Aplicacion modular para inventario, compras, cocina, ventas y cierre diario.",
        )

    def closeEvent(self, event) -> None:
        reply = QMessageBox.question(
            self,
            "Salir",
            "Desea cerrar la aplicacion?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            event.ignore()
            return

        for widget in self.module_widgets.values():
            cleanup = getattr(widget, "cleanup", None)
            if callable(cleanup):
                cleanup()
        event.accept()

    def toggle_sidebar(self) -> None:
        """Show or hide the left sidebar."""
        if not hasattr(self, "sidebar") or self.sidebar is None:
            return
        if self.sidebar.isVisible():
            self.sidebar.hide()
            self.toggle_sidebar_button.setText("❯")
            self.statusBar().showMessage("Barra lateral oculta.")
        else:
            self.sidebar.show()
            self.toggle_sidebar_button.setText("❮")
            self.statusBar().showMessage("Barra lateral mostrada.")
