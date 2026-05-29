from __future__ import annotations

import re
from datetime import datetime

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from modules.catalogos import CatalogoManager
from modules.inventario import InventarioManager
from modules.ventas import VentasManager
from utils.date_utils import format_date, get_current_date


class VentasWidget(QWidget):
    def __init__(self, context: dict | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.context = context or {}
        self.total_ventas_dinero = 0.0
        self.producto_actual: dict | None = None
        self.productos: list[dict] = []
        self.stock_por_producto: dict[int, float] = {}
        self.seleccion_detalle_ids: list[int] = []
        self.ultima_actualizacion: datetime | None = None

        self._configure_managers()
        self._build_ui()
        self.connect_signals()
        self.setup_tables()
        self.load_initial_data()

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.actualizar_todo)
        self.update_timer.start(15000)

    def _configure_managers(self) -> None:
        services = (self.context or {}).get("services")
        if services:
            self.ventas_manager = services.get("ventas")
            self.catalogos_manager = services.get("catalogos")
            self.inventario_manager = services.get("inventario")
            return

        self.ventas_manager = VentasManager()
        self.catalogos_manager = CatalogoManager()
        self.inventario_manager = InventarioManager()

    def setup(self, context: dict) -> None:
        self.context = context or {}
        self._configure_managers()
        self.actualizar_todo()

    def set_context(self, context: dict) -> None:
        self.setup(context)

    def refresh_data(self) -> None:
        self.actualizar_todo()

    def _build_ui(self) -> None:
        self.setObjectName("ventasWidget")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("pageHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(22, 18, 22, 18)

        hero_copy = QVBoxLayout()
        hero_copy.setSpacing(4)

        hero_title = QLabel("Ventas del dia")
        hero_title.setObjectName("heroTitle")
        hero_subtitle = QLabel(
            "Registra salidas, revisa movimientos recientes y controla el ritmo comercial del turno."
        )
        hero_subtitle.setObjectName("heroSubtitle")
        hero_subtitle.setWordWrap(True)

        hero_copy.addWidget(hero_title)
        hero_copy.addWidget(hero_subtitle)

        hero_status = QVBoxLayout()
        hero_status.setSpacing(8)

        self.fecha_label = QLabel("--/--/----")
        self.fecha_label.setObjectName("statusPill")
        self.fecha_label.setAlignment(Qt.AlignCenter)

        self.update_indicator = QLabel("Pendiente")
        self.update_indicator.setProperty("role", "indicator")
        self.update_indicator.setAlignment(Qt.AlignCenter)

        hero_status.addWidget(self.fecha_label)
        hero_status.addWidget(self.update_indicator)

        hero_layout.addLayout(hero_copy, 1)
        hero_layout.addLayout(hero_status)

        main_layout.addWidget(hero)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        left_panel = QFrame()
        left_panel.setObjectName("pagePanel")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(14)

        form_group = QGroupBox("Registrar venta")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(12)

        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(10)
        form_grid.setVerticalSpacing(10)

        producto_label = QLabel("Producto")
        producto_label.setProperty("role", "field")
        self.producto_combo = QComboBox()
        self.producto_combo.setMinimumHeight(38)

        cantidad_label = QLabel("Cantidad")
        cantidad_label.setProperty("role", "field")
        self.cantidad_input = QDoubleSpinBox()
        self.cantidad_input.setRange(0.01, 10000)
        self.cantidad_input.setDecimals(2)
        self.cantidad_input.setValue(1.0)
        self.cantidad_input.setMinimumHeight(38)

        self.unidad_label = QLabel("unidad")
        self.unidad_label.setObjectName("inlineInfo")
        self.unidad_label.setAlignment(Qt.AlignCenter)

        form_grid.addWidget(producto_label, 0, 0)
        form_grid.addWidget(self.producto_combo, 1, 0, 1, 3)
        form_grid.addWidget(cantidad_label, 2, 0)
        form_grid.addWidget(self.cantidad_input, 3, 0, 1, 2)
        form_grid.addWidget(self.unidad_label, 3, 2)

        form_layout.addLayout(form_grid)

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(10)
        info_grid.setVerticalSpacing(10)

        price_card, self.precio_label = self._create_info_card("Precio unitario", "$0.00")
        stock_card, self.stock_label = self._create_info_card("Disponible", "0")
        total_card, self.venta_actual_label = self._create_info_card("Venta actual", "$0.00")

        info_grid.addWidget(price_card, 0, 0)
        info_grid.addWidget(stock_card, 0, 1)
        info_grid.addWidget(total_card, 1, 0, 1, 2)

        form_layout.addLayout(info_grid)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self.agregar_btn = QPushButton("Registrar venta")
        self.agregar_btn.setObjectName("primaryButton")
        self.agregar_btn.setMinimumHeight(38)

        self.cancelar_btn = QPushButton("Cancelar ultima")
        self.cancelar_btn.setMinimumHeight(38)

        self.actualizar_btn = QPushButton("Actualizar")
        self.actualizar_btn.setMinimumHeight(38)

        action_row.addWidget(self.agregar_btn)
        action_row.addWidget(self.cancelar_btn)
        action_row.addWidget(self.actualizar_btn)

        form_layout.addLayout(action_row)
        left_layout.addWidget(form_group)

        support_group = QGroupBox("Flujo sugerido")
        support_layout = QVBoxLayout(support_group)
        support_layout.setSpacing(10)

        support_text = QLabel(
            "1. Selecciona el producto.\n"
            "2. Confirma la cantidad despachada.\n"
            "3. Registra la venta y revisa el historial inmediato.\n"
            "4. Si hubo un error, cancela la ultima venta o varias desde la tabla."
        )
        support_text.setWordWrap(True)
        support_text.setProperty("role", "hint")

        self.last_refresh_label = QLabel("Sin sincronizacion reciente")
        self.last_refresh_label.setProperty("role", "muted")

        support_layout.addWidget(support_text)
        support_layout.addWidget(self.last_refresh_label)
        support_layout.addStretch(1)

        left_layout.addWidget(support_group)
        left_layout.addStretch(1)

        right_panel = QFrame()
        right_panel.setObjectName("pagePanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(14)

        summary_row = QHBoxLayout()
        summary_row.setSpacing(10)

        _, self.total_dia_label = self._create_summary_card("Ingresos del dia", "$0.00")
        _, self.total_unidades_label = self._create_summary_card("Unidades", "0")
        _, self.total_transacciones_label = self._create_summary_card("Transacciones", "0")
        _, self.ultima_venta_label = self._create_summary_card("Ultima venta", "--:--")
        _, self.promedio_venta_label = self._create_summary_card("Ticket promedio", "$0.00")

        for frame, _label in (
            self._create_summary_card("Ingresos del dia", "$0.00"),
            self._create_summary_card("Unidades", "0"),
        ):
            frame.deleteLater()

        summary_cards = [
            self._create_summary_card("Ingresos del dia", "$0.00"),
            self._create_summary_card("Unidades", "0"),
            self._create_summary_card("Transacciones", "0"),
            self._create_summary_card("Ultima venta", "--:--"),
            self._create_summary_card("Ticket promedio", "$0.00"),
        ]

        self.total_dia_label = summary_cards[0][1]
        self.total_unidades_label = summary_cards[1][1]
        self.total_transacciones_label = summary_cards[2][1]
        self.ultima_venta_label = summary_cards[3][1]
        self.promedio_venta_label = summary_cards[4][1]

        for frame, _label in summary_cards:
            summary_row.addWidget(frame)

        right_layout.addLayout(summary_row)

        ventas_group = QGroupBox("Ventas acumuladas")
        ventas_layout = QVBoxLayout(ventas_group)
        ventas_layout.setSpacing(10)

        self.ventas_table = QTableWidget(0, 4)
        self.ventas_table.setObjectName("ventasTable")
        self.ventas_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio", "Total"])
        self.ventas_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ventas_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ventas_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ventas_table.setAlternatingRowColors(True)
        self.ventas_table.verticalHeader().setVisible(False)

        ventas_layout.addWidget(self.ventas_table)
        right_layout.addWidget(ventas_group, 1)

        toolbar = QFrame()
        toolbar.setObjectName("toolbarCard")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 10, 14, 10)
        toolbar_layout.setSpacing(8)

        toolbar_title = QLabel("Movimientos del turno")
        toolbar_title.setProperty("role", "title")

        self.detalle_btn = QPushButton("Refrescar historial")
        self.detalle_btn.setMinimumHeight(34)

        self.cancelar_seleccionadas_btn = QPushButton("Cancelar seleccionadas")
        self.cancelar_seleccionadas_btn.setMinimumHeight(34)
        self.cancelar_seleccionadas_btn.setEnabled(False)

        toolbar_layout.addWidget(toolbar_title)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.detalle_btn)
        toolbar_layout.addWidget(self.cancelar_seleccionadas_btn)

        right_layout.addWidget(toolbar)

        historial_group = QGroupBox("Historial detallado")
        historial_layout = QVBoxLayout(historial_group)
        historial_layout.setSpacing(10)

        self.historial_table = QTableWidget(0, 6)
        self.historial_table.setObjectName("historialTable")
        self.historial_table.setHorizontalHeaderLabels(["ID", "Hora", "Producto", "Cantidad", "Precio", "Total"])
        self.historial_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.historial_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.historial_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.historial_table.setAlternatingRowColors(True)
        self.historial_table.verticalHeader().setVisible(False)

        historial_layout.addWidget(self.historial_table)
        right_layout.addWidget(historial_group, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([360, 980])

        left_panel.setMinimumWidth(340)
        left_panel.setMaximumWidth(420)
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main_layout.addWidget(splitter, 1)
        self.splitter = splitter

    def _create_info_card(self, caption: str, value: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setObjectName("summaryCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        caption_label = QLabel(caption)
        caption_label.setObjectName("summaryCaption")
        value_label = QLabel(value)
        value_label.setObjectName("summaryValue")

        layout.addWidget(caption_label)
        layout.addWidget(value_label)
        return frame, value_label

    def _create_summary_card(self, caption: str, value: str) -> tuple[QFrame, QLabel]:
        frame = QFrame()
        frame.setObjectName("summaryCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        caption_label = QLabel(caption)
        caption_label.setObjectName("summaryCaption")
        value_label = QLabel(value)
        value_label.setObjectName("summaryValue")

        layout.addWidget(caption_label)
        layout.addWidget(value_label)
        layout.addStretch(1)
        return frame, value_label

    def connect_signals(self) -> None:
        self.producto_combo.currentIndexChanged.connect(self.actualizar_info_producto)
        self.cantidad_input.valueChanged.connect(self.calcular_venta_actual)
        self.agregar_btn.clicked.connect(self.agregar_venta)
        self.cancelar_btn.clicked.connect(self.cancelar_ultima_venta)
        self.actualizar_btn.clicked.connect(self.actualizar_todo)
        self.detalle_btn.clicked.connect(self.cargar_historial_detalle)
        self.cancelar_seleccionadas_btn.clicked.connect(self.cancelar_ventas_seleccionadas)
        self.historial_table.itemSelectionChanged.connect(self.actualizar_seleccion_historial)
        self.historial_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.historial_table.customContextMenuRequested.connect(self.mostrar_menu_contextual)

    def load_initial_data(self) -> None:
        self.actualizar_fecha()
        self.cargar_productos()
        self.actualizar_todo()

    def setup_tables(self) -> None:
        ventas_header = self.ventas_table.horizontalHeader()
        ventas_header.setSectionResizeMode(0, QHeaderView.Stretch)
        ventas_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        ventas_header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        ventas_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        historial_header = self.historial_table.horizontalHeader()
        historial_header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        historial_header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        historial_header.setSectionResizeMode(2, QHeaderView.Stretch)
        historial_header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        historial_header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        historial_header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

    def actualizar_fecha(self) -> None:
        try:
            self.fecha_label.setText(format_date(get_current_date()))
        except Exception:
            self.fecha_label.setText(datetime.now().strftime("%d/%m/%Y"))

    def cargar_productos(self) -> None:
        productos: list[dict] = []

        try:
            raw_rows = []
            if hasattr(self.catalogos_manager, "obtener_productos"):
                raw_rows = self.catalogos_manager.obtener_productos()

            if not raw_rows and hasattr(self.catalogos_manager, "obtener_productos_activos"):
                raw_rows = self.catalogos_manager.obtener_productos_activos()

            for row in raw_rows or []:
                normalized = self._normalize_producto(row)
                if normalized:
                    productos.append(normalized)
        except Exception:
            productos = []

        self.productos = sorted(productos, key=lambda item: item["nombre"].lower())
        self.producto_combo.blockSignals(True)
        self.producto_combo.clear()

        if not self.productos:
            self.producto_combo.addItem("No hay productos disponibles", -1)
            self.producto_combo.blockSignals(False)
            self.producto_actual = None
            self.reset_info_producto()
            return

        for producto in self.productos:
            display = f"{producto['nombre']}  |  {self._format_money(producto['precio_venta'])}"
            self.producto_combo.addItem(display, producto["id"])

        self.producto_combo.setCurrentIndex(0)
        self.producto_combo.blockSignals(False)
        self.actualizar_info_producto()

    def _normalize_producto(self, row) -> dict | None:
        if isinstance(row, dict):
            if not row.get("id"):
                return None
            return {
                "id": int(row["id"]),
                "nombre": str(row.get("nombre", "Producto")),
                "precio_venta": self._to_float(row.get("precio_venta", 0)),
                "unidad_venta": str(row.get("unidad_venta", "unidad") or "unidad"),
            }

        if isinstance(row, (list, tuple)) and len(row) >= 4:
            return {
                "id": int(row[0]),
                "nombre": str(row[1]),
                "precio_venta": self._to_float(row[2]),
                "unidad_venta": str(row[3] or "unidad"),
            }

        return None

    def actualizar_info_producto(self, *_) -> None:
        producto_id = self.producto_combo.currentData()
        if producto_id in (None, -1):
            self.producto_actual = None
            self.reset_info_producto()
            return

        self.producto_actual = next((item for item in self.productos if item["id"] == int(producto_id)), None)
        if not self.producto_actual:
            self.reset_info_producto()
            return

        self.precio_label.setText(self._format_money(self.producto_actual.get("precio_venta", 0)))
        self.unidad_label.setText(self.producto_actual.get("unidad_venta", "unidad"))
        stock_actual = self.stock_por_producto.get(int(producto_id), 0.0)
        self.stock_label.setText(f"{stock_actual:,.2f}")
        self.calcular_venta_actual()

    def reset_info_producto(self) -> None:
        self.precio_label.setText("$0.00")
        self.stock_label.setText("0")
        self.unidad_label.setText("unidad")
        self.venta_actual_label.setText("$0.00")

    def calcular_venta_actual(self, *_) -> None:
        precio = 0.0
        if self.producto_actual:
            precio = self._to_float(self.producto_actual.get("precio_venta", 0))
        else:
            match = re.search(r"\$([\d\.,]+)", self.producto_combo.currentText())
            if match:
                precio = self._to_float(match.group(1).replace(",", ""))

        total = self.cantidad_input.value() * precio
        self.venta_actual_label.setText(self._format_money(total))

    def actualizar_todo(self) -> None:
        try:
            self.actualizar_fecha()
            self._actualizar_cache_stock()
            self.cargar_ventas_dia()
            self.cargar_historial_detalle()
            self.cargar_estadisticas_dia()
            self.actualizar_info_producto()

            self.ultima_actualizacion = datetime.now()
            hora = self.ultima_actualizacion.strftime("%H:%M:%S")
            self.update_indicator.setText(f"Sincronizado {hora}")
            self.update_indicator.setToolTip(f"Ultima actualizacion: {hora}")
            self.last_refresh_label.setText(f"Ultima sincronizacion completada a las {hora}.")
        except Exception as exc:
            self.update_indicator.setText("Revision requerida")
            self.update_indicator.setToolTip(str(exc))
            self.last_refresh_label.setText(f"No fue posible actualizar todo: {exc}")

    def _actualizar_cache_stock(self) -> None:
        self.stock_por_producto.clear()
        try:
            inventario = self.inventario_manager.obtener_inventario_productos()
        except Exception:
            inventario = []

        for item in inventario or []:
            producto_id = item.get("id")
            if producto_id is None:
                continue
            self.stock_por_producto[int(producto_id)] = self._to_float(item.get("cantidad_disponible", 0))

    def cargar_ventas_dia(self) -> None:
        try:
            ventas = self.ventas_manager.obtener_ventas_dia()
        except Exception:
            ventas = []

        self.ventas_table.clearSpans()
        self.ventas_table.setRowCount(0)
        self.total_ventas_dinero = 0.0

        if not ventas:
            self._set_empty_message(self.ventas_table, 4, "No hay ventas registradas hoy.")
            self.total_dia_label.setText("$0.00")
            return

        self.ventas_table.setRowCount(len(ventas))

        for row_index, venta in enumerate(ventas):
            nombre = venta.get("nombre") or venta.get("producto_nombre") or "Producto"
            cantidad = self._to_float(venta.get("cantidad", venta.get("cantidad_total", 0)))
            precio = self._to_float(venta.get("precio", venta.get("precio_venta", 0)))
            total = self._to_float(venta.get("total", venta.get("total_ventas", 0)))
            unidad = venta.get("unidad_venta", "")

            cantidad_text = f"{cantidad:,.2f} {unidad}".strip()
            row_values = [
                str(nombre),
                cantidad_text,
                self._format_money(precio),
                self._format_money(total),
            ]

            for col_index, value in enumerate(row_values):
                item = QTableWidgetItem(value)
                if col_index:
                    item.setTextAlignment(Qt.AlignCenter)
                self.ventas_table.setItem(row_index, col_index, item)

            self.ventas_table.setRowHeight(row_index, 34)
            self.total_ventas_dinero += total

        self.total_dia_label.setText(self._format_money(self.total_ventas_dinero))

    def cargar_estadisticas_dia(self) -> None:
        try:
            detalle = self.ventas_manager.obtener_detalle_ventas_dia()
        except Exception:
            detalle = []

        total_transacciones = len(detalle)
        total_unidades = 0.0
        ultima_hora = "--:--"

        for item in detalle:
            total_unidades += self._to_float(item.get("cantidad", 0))
            hora = str(item.get("hora", "") or "")
            if hora and hora > ultima_hora:
                ultima_hora = hora

        promedio = self.total_ventas_dinero / total_transacciones if total_transacciones else 0.0

        self.total_unidades_label.setText(f"{total_unidades:,.2f}")
        self.total_transacciones_label.setText(str(total_transacciones))
        self.ultima_venta_label.setText(ultima_hora)
        self.promedio_venta_label.setText(self._format_money(promedio))

    def cargar_historial_detalle(self) -> None:
        try:
            detalle = self.ventas_manager.obtener_detalle_ventas_dia()
        except Exception:
            detalle = []

        self.historial_table.clearSpans()
        self.historial_table.setRowCount(0)
        self.seleccion_detalle_ids.clear()
        self.cancelar_seleccionadas_btn.setEnabled(False)

        if not detalle:
            self._set_empty_message(self.historial_table, 6, "No hay historial de ventas hoy.")
            return

        self.historial_table.setRowCount(len(detalle))

        for row_index, row in enumerate(detalle):
            detalle_id = row.get("detalle_id", 0)
            hora = row.get("hora", "--:--")
            nombre = row.get("nombre") or row.get("producto_nombre") or "Producto"
            cantidad = self._to_float(row.get("cantidad", 0))
            precio = self._to_float(row.get("precio", row.get("precio_venta", 0)))
            total = self._to_float(row.get("total", row.get("total_venta", 0)))

            values = [
                str(detalle_id),
                str(hora),
                str(nombre),
                f"{cantidad:,.2f}",
                self._format_money(precio),
                self._format_money(total),
            ]

            for col_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                if col_index != 2:
                    item.setTextAlignment(Qt.AlignCenter)
                self.historial_table.setItem(row_index, col_index, item)

            self.historial_table.setRowHeight(row_index, 34)

    def _set_empty_message(self, table: QTableWidget, columns: int, message: str) -> None:
        table.setRowCount(1)
        item = QTableWidgetItem(message)
        item.setTextAlignment(Qt.AlignCenter)
        table.setItem(0, 0, item)
        table.setSpan(0, 0, 1, columns)
        table.setRowHeight(0, 38)

    def actualizar_seleccion_historial(self) -> None:
        selected_rows = {item.row() for item in self.historial_table.selectedItems()}
        self.seleccion_detalle_ids = []

        for row in selected_rows:
            id_item = self.historial_table.item(row, 0)
            if not id_item:
                continue
            try:
                self.seleccion_detalle_ids.append(int(id_item.text()))
            except ValueError:
                continue

        self.cancelar_seleccionadas_btn.setEnabled(bool(self.seleccion_detalle_ids))

    def mostrar_menu_contextual(self, pos) -> None:
        menu = QMenu(self)

        if self.seleccion_detalle_ids:
            cancelar_action = menu.addAction("Cancelar venta seleccionada")
            cancelar_action.triggered.connect(self.cancelar_venta_contextual)

            if len(self.seleccion_detalle_ids) > 1:
                cancelar_multiples = menu.addAction(
                    f"Cancelar {len(self.seleccion_detalle_ids)} ventas"
                )
                cancelar_multiples.triggered.connect(self.cancelar_ventas_seleccionadas)

            menu.addSeparator()

        actualizar_action = menu.addAction("Actualizar historial")
        actualizar_action.triggered.connect(self.actualizar_todo)
        menu.exec_(self.historial_table.mapToGlobal(pos))

    def cancelar_venta_contextual(self) -> None:
        filas = {item.row() for item in self.historial_table.selectedItems()}
        if not filas:
            return

        row = next(iter(filas))
        detalle_id_item = self.historial_table.item(row, 0)
        producto_item = self.historial_table.item(row, 2)
        cantidad_item = self.historial_table.item(row, 3)
        total_item = self.historial_table.item(row, 5)
        hora_item = self.historial_table.item(row, 1)

        if not detalle_id_item:
            return

        detalle_id = int(detalle_id_item.text())
        producto = producto_item.text() if producto_item else "Producto"
        cantidad = cantidad_item.text() if cantidad_item else "0"
        total = total_item.text() if total_item else "$0.00"
        hora = hora_item.text() if hora_item else "--:--"

        reply = QMessageBox.question(
            self,
            "Confirmar cancelacion",
            f"Cancelar la venta de {producto} registrada a las {hora}?\n\n"
            f"Cantidad: {cantidad}\n"
            f"Total: {total}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            resultado = self.ventas_manager.cancelar_venta_por_id(detalle_id)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo cancelar la venta.\n\n{exc}")
            return

        QMessageBox.information(
            self,
            "Venta cancelada",
            f"Movimiento revertido correctamente.\nTotal devuelto: {self._format_money(resultado['total_devuelto'])}",
        )
        self.actualizar_todo()

    def cancelar_ventas_seleccionadas(self) -> None:
        if not self.seleccion_detalle_ids:
            QMessageBox.warning(self, "Sin seleccion", "Selecciona al menos una venta del historial.")
            return

        cantidad = len(self.seleccion_detalle_ids)
        reply = QMessageBox.question(
            self,
            "Confirmar cancelacion",
            f"Cancelar {cantidad} ventas seleccionadas?\n\nEsta accion no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            resultado = self.ventas_manager.cancelar_ventas_seleccionadas(self.seleccion_detalle_ids)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudieron cancelar las ventas.\n\n{exc}")
            return

        QMessageBox.information(
            self,
            "Ventas canceladas",
            f"Se cancelaron {resultado['ventas_canceladas']} movimientos.\n"
            f"Total devuelto: {self._format_money(resultado['total_dinero_devuelto'])}",
        )
        self.actualizar_todo()

    def agregar_venta(self) -> None:
        producto_id = self.producto_combo.currentData()
        if producto_id in (None, -1):
            QMessageBox.warning(self, "Validacion", "Debes seleccionar un producto valido.")
            return

        cantidad = self.cantidad_input.value()
        if cantidad <= 0:
            QMessageBox.warning(self, "Validacion", "La cantidad debe ser mayor que cero.")
            return

        producto_nombre = self.producto_actual.get("nombre", "Producto") if self.producto_actual else "Producto"
        total_venta = self._to_float(cantidad) * self._to_float(
            self.producto_actual.get("precio_venta", 0) if self.producto_actual else 0
        )

        reply = QMessageBox.question(
            self,
            "Confirmar venta",
            f"Registrar {cantidad:,.2f} {self.unidad_label.text()} de {producto_nombre}?\n\n"
            f"Total estimado: {self._format_money(total_venta)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            total_registrado = self.ventas_manager.registrar_venta(int(producto_id), cantidad)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la venta.\n\n{exc}")
            return

        QMessageBox.information(
            self,
            "Venta registrada",
            f"Venta guardada correctamente.\nTotal: {self._format_money(total_registrado)}",
        )
        self.cantidad_input.setValue(1.0)
        self.actualizar_todo()

    def cancelar_ultima_venta(self) -> None:
        producto_id = self.producto_combo.currentData()
        if producto_id in (None, -1):
            QMessageBox.warning(self, "Validacion", "Selecciona un producto valido.")
            return

        producto_nombre = self.producto_actual.get("nombre", "Producto") if self.producto_actual else "Producto"

        try:
            detalle = self.ventas_manager.obtener_detalle_ventas_dia()
            ventas_producto = [row for row in detalle if row.get("id_producto") == int(producto_id)]
        except Exception:
            ventas_producto = []

        if not ventas_producto:
            QMessageBox.warning(
                self,
                "Sin ventas",
                f"No hay movimientos de {producto_nombre} para cancelar.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirmar cancelacion",
            f"Cancelar la ultima venta registrada de {producto_nombre}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        try:
            resultado = self.ventas_manager.cancelar_ultima_venta(int(producto_id))
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"No se pudo cancelar la ultima venta.\n\n{exc}")
            return

        QMessageBox.information(
            self,
            "Venta cancelada",
            f"Movimiento revertido correctamente.\nTotal devuelto: {self._format_money(resultado['total_devuelto'])}",
        )
        self.actualizar_todo()

    def cleanup(self) -> None:
        if hasattr(self, "update_timer") and self.update_timer.isActive():
            self.update_timer.stop()

    def _format_money(self, value) -> str:
        return f"${self._to_float(value):,.2f}"

    def _to_float(self, value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0
