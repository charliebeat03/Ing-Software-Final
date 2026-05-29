from __future__ import annotations

from datetime import date

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class DashboardWidget(QWidget):
    def __init__(self, context: dict | None = None):
        super().__init__()
        self.context = context or {}
        self._build_ui()
        self.refresh_data()

    def setup(self, context: dict) -> None:
        self.context = context or {}
        self.refresh_data()

    def set_context(self, context: dict) -> None:
        self.setup(context)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        cards_layout = QGridLayout()
        cards_layout.setSpacing(14)

        self.sales_card = self._create_metric_card("Ventas del dia")
        self.purchases_card = self._create_metric_card("Compras del dia")
        self.kitchen_card = self._create_metric_card("Pedidos de cocina")
        self.alerts_card = self._create_metric_card("Alertas activas")

        cards_layout.addWidget(self.sales_card["frame"], 0, 0)
        cards_layout.addWidget(self.purchases_card["frame"], 0, 1)
        cards_layout.addWidget(self.kitchen_card["frame"], 1, 0)
        cards_layout.addWidget(self.alerts_card["frame"], 1, 1)

        actions_frame = QFrame()
        actions_frame.setObjectName("dashboardCard")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(18, 18, 18, 18)

        actions_title = QLabel("Accesos rapidos")
        actions_title.setProperty("role", "title")

        button_row = QHBoxLayout()
        for label, module_id in (
            ("Ir a Ventas", "ventas"),
            ("Ir a Compras", "compras"),
            ("Ver Inventario", "inventario"),
            ("Abrir Cierre", "excedentes"),
        ):
            button = QPushButton(label)
            button.setObjectName("quickActionButton")
            button.clicked.connect(lambda checked=False, target=module_id: self.navigate(target))
            button_row.addWidget(button)

        actions_layout.addWidget(actions_title)
        actions_layout.addLayout(button_row)

        alerts_frame = QFrame()
        alerts_frame.setObjectName("dashboardCard")
        alerts_layout = QVBoxLayout(alerts_frame)
        alerts_layout.setContentsMargins(18, 18, 18, 18)

        alerts_title = QLabel("Ingredientes con prioridad")
        alerts_title.setProperty("role", "title")

        self.alerts_table = QTableWidget(0, 4)
        self.alerts_table.setHorizontalHeaderLabels(["Ingrediente", "Disponible", "Minimo", "Estado"])
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.alerts_table.setAlternatingRowColors(True)

        alerts_layout.addWidget(alerts_title)
        alerts_layout.addWidget(self.alerts_table)

        layout.addLayout(cards_layout)
        layout.addWidget(actions_frame)
        layout.addWidget(alerts_frame, 1)

    def _create_metric_card(self, title: str) -> dict:
        frame = QFrame()
        frame.setObjectName("dashboardCard")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("metricLabel")
        value_label = QLabel("0")
        value_label.setObjectName("metricValue")
        detail_label = QLabel("Sin datos cargados.")
        detail_label.setProperty("role", "muted")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        layout.addStretch(1)

        return {
            "frame": frame,
            "value": value_label,
            "detail": detail_label,
        }

    def navigate(self, module_id: str) -> None:
        callback = self.context.get("navigate_module")
        if callable(callback):
            callback(module_id)

    def refresh_data(self) -> None:
        services = (self.context or {}).get("services")
        if services is None:
            return

        today = date.today()
        today_str = today.strftime("%Y-%m-%d")

        ventas = services.get("ventas")
        compras = services.get("compras")
        inventario = services.get("inventario")
        pedidos = services.get("pedidos_chef")

        total_ventas = getattr(ventas, "obtener_total_ventas_dia", lambda *_: 0)(today_str)
        total_compras = getattr(compras, "obtener_total_compras_periodo", lambda *_: 0)(today_str, today_str)
        pedidos_dia = getattr(pedidos, "obtener_pedidos_dia", lambda *_: [])(today)
        ingredientes_bajos = getattr(inventario, "obtener_ingredientes_bajo_stock", lambda: [])()
        productos_bajos = getattr(inventario, "obtener_productos_bajo_stock", lambda *_: [])()

        total_alertas = len(ingredientes_bajos) + len(productos_bajos)

        self.sales_card["value"].setText(f"${float(total_ventas):,.2f}")
        self.sales_card["detail"].setText("Ventas acumuladas del dia actual.")

        self.purchases_card["value"].setText(f"${float(total_compras):,.2f}")
        self.purchases_card["detail"].setText("Compras registradas hoy.")

        self.kitchen_card["value"].setText(str(len(pedidos_dia)))
        self.kitchen_card["detail"].setText("Ingredientes pedidos por cocina.")

        self.alerts_card["value"].setText(str(total_alertas))
        self.alerts_card["detail"].setText("Ingredientes o productos con stock comprometido.")

        self._fill_alerts_table(ingredientes_bajos)

    def _fill_alerts_table(self, rows: list[dict]) -> None:
        self.alerts_table.setRowCount(0)
        for row_index, item in enumerate(rows[:8]):
            self.alerts_table.insertRow(row_index)
            values = [
                item.get("nombre", item.get("ingrediente_nombre", "")),
                f"{float(item.get('cantidad_actual', 0)):.2f}",
                f"{float(item.get('stock_minimo', 0)):.2f}",
                "Bajo stock",
            ]
            for col_index, value in enumerate(values):
                table_item = QTableWidgetItem(str(value))
                if col_index in (1, 2):
                    table_item.setTextAlignment(Qt.AlignCenter)
                self.alerts_table.setItem(row_index, col_index, table_item)
        self.alerts_table.resizeColumnsToContents()
