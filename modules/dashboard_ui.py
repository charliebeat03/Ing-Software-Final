from __future__ import annotations

from datetime import date, timedelta

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

try:
    import pyqtgraph as pg
    from pyqtgraph import PlotWidget
    PG_AVAILABLE = True
except Exception:
    PG_AVAILABLE = False


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

        # Top metrics row
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.sales_card = self._create_metric_card("Ventas del dia")
        self.purchases_card = self._create_metric_card("Compras del dia")
        self.kitchen_card = self._create_metric_card("Pedidos de cocina")
        self.alerts_card = self._create_metric_card("Alertas activas")

        cards_layout.addWidget(self.sales_card["frame"])
        cards_layout.addWidget(self.purchases_card["frame"])
        cards_layout.addWidget(self.kitchen_card["frame"])
        cards_layout.addWidget(self.alerts_card["frame"])

        actions_frame = QFrame()
        actions_frame.setObjectName("dashboardCard")
        actions_layout = QVBoxLayout(actions_frame)
        actions_layout.setContentsMargins(14, 14, 14, 14)

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
        alerts_layout.setContentsMargins(14, 14, 14, 14)

        alerts_title = QLabel("Ingredientes con prioridad")
        alerts_title.setProperty("role", "title")

        # Alerts table (compact)
        self.alerts_table = QTableWidget(0, 4)
        self.alerts_table.setObjectName("alertsTable")
        self.alerts_table.setHorizontalHeaderLabels(["Ingrediente", "Disponible", "Minimo", "Estado"])
        self.alerts_table.verticalHeader().setVisible(False)
        self.alerts_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.alerts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.alerts_table.setAlternatingRowColors(True)
        self.alerts_table.setMinimumHeight(180)

        alerts_layout.addWidget(alerts_title)
        alerts_layout.addWidget(self.alerts_table)

        # Charts area (plots or graceful fallbacks)
        charts_frame = QFrame()
        charts_frame.setObjectName("chartsPlaceholder")
        charts_layout = QHBoxLayout(charts_frame)
        charts_layout.setContentsMargins(0, 8, 0, 0)
        charts_layout.setSpacing(12)

        if PG_AVAILABLE:
            # interactive lightweight plots
            self.sales_plot = PlotWidget()
            self.sales_plot.setObjectName("salesPlot")
            self.sales_plot.setBackground('w')
            # Title and axis labels so user knows what each chart shows
            try:
                self.sales_plot.getPlotItem().setTitle("Ventas — últimos 7 días")
                self.sales_plot.getPlotItem().setLabel('left', 'Total ($)')
                self.sales_plot.getPlotItem().setLabel('bottom', 'Día')
                self.sales_plot.addLegend(offset=(10, 10))
            except Exception:
                pass

            self.purchases_plot = PlotWidget()
            self.purchases_plot.setObjectName("purchasesPlot")
            self.purchases_plot.setBackground('w')
            try:
                self.purchases_plot.getPlotItem().setTitle("Compras — últimos 7 días")
                self.purchases_plot.getPlotItem().setLabel('left', 'Total ($)')
                self.purchases_plot.getPlotItem().setLabel('bottom', 'Día')
                self.purchases_plot.addLegend(offset=(10, 10))
            except Exception:
                pass

            charts_layout.addWidget(self.sales_plot, 1)
            charts_layout.addWidget(self.purchases_plot, 1)
        else:
            sales_chart = QFrame()
            sales_chart.setObjectName("chartPlaceholder")
            sales_chart.setMinimumHeight(120)
            sales_chart_layout = QVBoxLayout(sales_chart)
            self.sales_fallback_label = QLabel("Ventas: N/D")
            self.sales_fallback_label.setAlignment(Qt.AlignCenter)
            sales_chart_layout.addWidget(self.sales_fallback_label)

            purchases_chart = QFrame()
            purchases_chart.setObjectName("chartPlaceholder")
            purchases_chart.setMinimumHeight(120)
            purchases_chart_layout = QVBoxLayout(purchases_chart)
            self.purchases_fallback_label = QLabel("Compras: N/D")
            self.purchases_fallback_label.setAlignment(Qt.AlignCenter)
            purchases_chart_layout.addWidget(self.purchases_fallback_label)

            charts_layout.addWidget(sales_chart, 1)
            charts_layout.addWidget(purchases_chart, 1)

        layout.addLayout(cards_layout)
        layout.addWidget(actions_frame)
        layout.addWidget(charts_frame)
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
        # update small trend charts (7-day)
        try:
            xs_sales, ys_sales = self._gather_daily_series(ventas, kind='ventas', days=7)
            xs_comp, ys_comp = self._gather_daily_series(compras, kind='compras', days=7)
            self._update_charts(xs_sales, ys_sales, xs_comp, ys_comp)
        except Exception:
            # don't break the whole refresh if plotting fails
            pass

    def _gather_daily_series(self, service, kind: str = 'ventas', days: int = 7):
        xs = []
        ys = []
        for i in range(days - 1, -1, -1):
            d = date.today() - timedelta(days=i)
            dstr = d.strftime('%Y-%m-%d')
            if kind == 'ventas':
                val = getattr(service, 'obtener_total_ventas_dia', lambda *_: 0)(dstr)
            else:
                # compras expects (start, end)
                val = getattr(service, 'obtener_total_compras_periodo', lambda a, b: 0)(dstr, dstr)
            xs.append(d.strftime('%d/%m'))
            ys.append(float(val or 0))
        return xs, ys

    def _update_charts(self, xs_sales, ys_sales, xs_comp, ys_comp):
        if PG_AVAILABLE:
            try:
                self.sales_plot.clear()
                self.purchases_plot.clear()
                pen_sales = pg.mkPen('#157a6e', width=2)
                pen_comp = pg.mkPen('#2b8fbd', width=2)
                self.sales_plot.plot(list(range(len(ys_sales))), ys_sales, pen=pen_sales, symbol='o', symbolBrush='#157a6e', name='Ventas')
                self.purchases_plot.plot(list(range(len(ys_comp))), ys_comp, pen=pen_comp, symbol='o', symbolBrush='#2b8fbd', name='Compras')
                # set x axis ticks to day labels
                try:
                    self.sales_plot.getAxis('bottom').setTicks([list(enumerate(xs_sales))])
                    self.purchases_plot.getAxis('bottom').setTicks([list(enumerate(xs_comp))])
                except Exception:
                    pass
            except Exception:
                pass
        else:
            # fallback: show totals in labels
            try:
                self.sales_fallback_label.setText(f"Ventas (7d): {sum(ys_sales):,.2f}")
                self.purchases_fallback_label.setText(f"Compras (7d): {sum(ys_comp):,.2f}")
            except Exception:
                pass

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
