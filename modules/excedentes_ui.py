# modules/excedentes_ui.py
import os
import sys
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QFrame, QFormLayout,
    QLineEdit, QSpinBox, QComboBox, QTextEdit,
    QSplitter, QCheckBox, QDialog, QDialogButtonBox,
    QInputDialog, QSizePolicy, QDoubleSpinBox, QDateEdit,
    QTabWidget, QScrollArea, QProgressBar, QGridLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor

from modules.excedentes import CierreDiarioManager

class CierreDiarioWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Inicializar manager
        self.cierre_manager = CierreDiarioManager()
        
        # Variables
        self.fecha_actual = date.today()
        self.ajustes_pendientes = []
        
        # Crear interfaz
        self.create_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Cargar datos iniciales
        self.load_initial_data()

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.cierre_manager = services.get("excedentes")
            try:
                self.load_initial_data()
            except Exception:
                pass

    def refresh_data(self):
        self.load_initial_data()
    
    def create_ui(self):
        """Crea la interfaz de cierre diario."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # ==================== ENCABEZADO ====================
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(8, 6, 8, 6)
        
        # Título
        title_label = QLabel("CIERRE DIARIO")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        
        # Selector de fecha
        fecha_layout = QHBoxLayout()
        fecha_layout.setSpacing(6)
        
        fecha_label = QLabel("Fecha:")
        self.fecha_input = QDateEdit()
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setMinimumHeight(26)
        self.fecha_input.setMaximumWidth(110)
        
        self.cargar_btn = QPushButton("Cargar día")
        self.cargar_btn.setMinimumHeight(26)
        self.cargar_btn.setMinimumWidth(90)
        
        fecha_layout.addWidget(fecha_label)
        fecha_layout.addWidget(self.fecha_input)
        fecha_layout.addWidget(self.cargar_btn)
        fecha_layout.addStretch()
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addLayout(fecha_layout)
        
        main_layout.addWidget(header_frame)
        
        # ==================== PESTAÑAS ====================
        self.tabs = QTabWidget()
        
        # Pestaña 1: Resumen del Día
        self.tab_resumen = QWidget()
        self.create_tab_resumen()
        self.tabs.addTab(self.tab_resumen, "Resumen")
        
        # Pestaña 2: Ajuste de Ingredientes
        self.tab_ajuste = QWidget()
        self.create_tab_ajuste()
        self.tabs.addTab(self.tab_ajuste, "Ajuste de cocina")
        
        main_layout.addWidget(self.tabs, 1)
        
        # ==================== BARRA INFERIOR ====================
        footer_frame = QFrame()
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(6, 6, 6, 6)
        
        # Información
        self.info_label = QLabel("Seleccione fecha y cargue los datos del día")
        self.info_label.setProperty("role", "hint")
        
        # Botones de acción
        self.btn_calcular_cierre = QPushButton("Calcular cierre")
        self.btn_calcular_cierre.setMinimumHeight(30)
        self.btn_calcular_cierre.setMinimumWidth(100)
        
        self.btn_guardar_cierre = QPushButton("Guardar cierre")
        self.btn_guardar_cierre.setMinimumHeight(30)
        self.btn_guardar_cierre.setMinimumWidth(100)
        self.btn_guardar_cierre.setEnabled(False)
        
        footer_layout.addWidget(self.info_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_calcular_cierre)
        footer_layout.addWidget(self.btn_guardar_cierre)
        
        main_layout.addWidget(footer_frame)
        
        # Delegar estilos al QSS global y asignar objectName para este módulo
        self.setObjectName("excedentesWidget")
        self.btn_guardar_cierre.setObjectName("btn_guardar_cierre")
        self.btn_calcular_cierre.setObjectName("btn_calcular_cierre")
    
    def create_tab_resumen(self):
        """Crea la pestaña de resumen con instrucciones y ventas"""
        layout = QVBoxLayout(self.tab_resumen)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # ===== INSTRUCCIONES =====
        instrucciones_frame = QFrame()
        instrucciones_frame.setObjectName("excedentesInstructions")
        
        instrucciones_layout = QVBoxLayout(instrucciones_frame)
        
        instrucciones_titulo = QLabel("Instrucciones para el cierre diario")
        instrucciones_titulo.setProperty("role", "title")
        
        instrucciones_texto = QLabel(
            "1. Seleccione la fecha del día a cerrar en el selector superior.\n"
            "2. Haga clic en 'Cargar Día' para obtener los datos de ventas y pedidos.\n"
            "3. Revise las ventas del día en esta tabla.\n"
            "4. Vaya a la pestaña 'Ajuste Chef' para registrar ingredientes sobrantes.\n"
            "5. Después de registrar todos los ajustes, calcule el cierre.\n"
            "6. Finalmente, guarde el cierre para actualizar el inventario."
        )
        instrucciones_texto.setProperty("role", "hint")
        instrucciones_texto.setWordWrap(True)
        
        instrucciones_layout.addWidget(instrucciones_titulo)
        instrucciones_layout.addWidget(instrucciones_texto)
        
        layout.addWidget(instrucciones_frame)
        
        # ===== VENTAS DEL DÍA =====
        ventas_group = QGroupBox("VENTAS DEL DÍA")
        ventas_group.setObjectName("excedentesVentasGroup")
        
        ventas_layout = QVBoxLayout(ventas_group)
        ventas_layout.setContentsMargins(6, 12, 6, 6)
        ventas_layout.setSpacing(4)
        
        # Tabla de ventas - más compacta
        self.ventas_table = QTableWidget()
        self.ventas_table.setColumnCount(4)
        self.ventas_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Precio Unit.", "Total"])
        self.ventas_table.setMinimumHeight(200)
        self.ventas_table.setMaximumHeight(350)
        
        # Configurar header oscuro
        header = self.ventas_table.horizontalHeader()
        header.setDefaultSectionSize(100)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        ventas_layout.addWidget(self.ventas_table)
        
        # Totales
        totales_layout = QHBoxLayout()
        
        self.lbl_total_ventas = QLabel("Total Ventas: $0.00")
        self.lbl_total_ventas.setProperty("emphasis", "strong")
        self.lbl_total_ventas.setProperty("intent", "success")

        self.lbl_total_productos = QLabel("Productos Vendidos: 0")
        self.lbl_total_productos.setProperty("emphasis", "strong")
        self.lbl_total_productos.setProperty("intent", "info")
        
        totales_layout.addWidget(self.lbl_total_ventas)
        totales_layout.addStretch()
        totales_layout.addWidget(self.lbl_total_productos)
        
        ventas_layout.addLayout(totales_layout)
        
        layout.addWidget(ventas_group, 1)
    
    def create_tab_ajuste(self):
        """Crea la pestaña de ajuste de ingredientes"""
        layout = QVBoxLayout(self.tab_ajuste)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # ===== FORMULARIO PARA REGISTRAR DEVOLUCIÓN =====
        form_frame = QFrame()
        form_frame.setObjectName("excedentesFormFrame")
        
        form_layout = QGridLayout(form_frame)
        form_layout.setVerticalSpacing(6)
        form_layout.setHorizontalSpacing(8)
        
        # Título del formulario
        form_titulo = QLabel("REGISTRAR DEVOLUCIÓN DE INGREDIENTE")
        form_titulo.setProperty("role", "title")
        form_layout.addWidget(form_titulo, 0, 0, 1, 4)
        
        # Ingrediente
        form_layout.addWidget(QLabel("Ingrediente:"), 1, 0)
        self.combo_ingrediente = QComboBox()
        self.combo_ingrediente.setMinimumHeight(26)
        form_layout.addWidget(self.combo_ingrediente, 1, 1)
        
        # Cantidad pedida
        form_layout.addWidget(QLabel("Cantidad Pedida:"), 1, 2)
        self.lbl_cantidad_pedida = QLabel("0")
        self.lbl_cantidad_pedida.setMinimumHeight(26)
        self.lbl_cantidad_pedida.setProperty("role", "badge")
        form_layout.addWidget(self.lbl_cantidad_pedida, 1, 3)
        
        # Cantidad sobrante
        form_layout.addWidget(QLabel("Cantidad Sobrante:"), 2, 0)
        self.spin_sobrante = QDoubleSpinBox()
        self.spin_sobrante.setMinimum(0)
        self.spin_sobrante.setMaximum(9999)
        self.spin_sobrante.setDecimals(2)
        self.spin_sobrante.setMinimumHeight(26)
        form_layout.addWidget(self.spin_sobrante, 2, 1)
        
        # Unidad
        form_layout.addWidget(QLabel("Unidad:"), 2, 2)
        self.lbl_unidad = QLabel("")
        self.lbl_unidad.setMinimumHeight(26)
        self.lbl_unidad.setProperty("role", "badge")
        form_layout.addWidget(self.lbl_unidad, 2, 3)
        
        # Botones del formulario
        btn_layout = QHBoxLayout()
        self.btn_agregar_ajuste = QPushButton("Agregar Ajuste")
        self.btn_agregar_ajuste.setMinimumHeight(26)
        self.btn_limpiar = QPushButton("Limpiar")
        self.btn_limpiar.setMinimumHeight(26)
        
        btn_layout.addWidget(self.btn_agregar_ajuste)
        btn_layout.addWidget(self.btn_limpiar)
        btn_layout.addStretch()
        
        form_layout.addLayout(btn_layout, 3, 0, 1, 4)
        
        layout.addWidget(form_frame)
        
        # ===== TABLA DE INGREDIENTES PEDIDOS =====
        ingredientes_label = QLabel("INGREDIENTES PEDIDOS EN EL DÍA:")
        ingredientes_label.setProperty("role", "sectionTitle")
        layout.addWidget(ingredientes_label)
        
        self.tabla_ingredientes_dia = QTableWidget()
        self.tabla_ingredientes_dia.setColumnCount(4)
        self.tabla_ingredientes_dia.setHorizontalHeaderLabels([
            "Ingrediente", "Cantidad Pedida", "Unidad", "Stock Actual"
        ])
        self.tabla_ingredientes_dia.setMinimumHeight(150)
        self.tabla_ingredientes_dia.setMaximumHeight(250)
        
        # Configurar header
        header_ingredientes = self.tabla_ingredientes_dia.horizontalHeader()
        header_ingredientes.setDefaultSectionSize(120)
        header_ingredientes.setSectionResizeMode(0, QHeaderView.Stretch)
        header_ingredientes.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_ingredientes.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_ingredientes.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla_ingredientes_dia)
        
        # ===== TABLA DE AJUSTES PENDIENTES =====
        ajustes_label = QLabel("AJUSTES PENDIENTES:")
        ajustes_label.setProperty("role", "sectionTitle")
        layout.addWidget(ajustes_label)
        
        self.tabla_ajustes_pendientes = QTableWidget()
        self.tabla_ajustes_pendientes.setColumnCount(5)
        self.tabla_ajustes_pendientes.setHorizontalHeaderLabels([
            "Ingrediente", "Cant. Pedida", "Cant. Usada", "A Devolver", "Eliminar"
        ])
        self.tabla_ajustes_pendientes.setMinimumHeight(150)
        
        # Configurar header
        header_ajustes = self.tabla_ajustes_pendientes.horizontalHeader()
        header_ajustes.setDefaultSectionSize(100)
        header_ajustes.setSectionResizeMode(0, QHeaderView.Stretch)
        header_ajustes.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header_ajustes.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header_ajustes.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header_ajustes.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.tabla_ajustes_pendientes, 1)
    
    def get_styles(self):
        """Retorna los estilos CSS para la aplicación"""
        return """
            /* Estilos generales */
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }
            
            /* Tablas - Headers oscuros */
            QHeaderView::section {
                background-color: #495057;
                color: white;
                padding: 4px 8px;
                border: 1px solid #6c757d;
                font-weight: bold;
                font-size: 9pt;
            }
            
            QHeaderView::section:hover {
                background-color: #343a40;
            }
            
            /* Tablas - Celdas */
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
                font-size: 9pt;
            }
            
            QTableWidget::item {
                padding: 2px 4px;
                border-bottom: 1px solid #e9ecef;
            }
            
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            
            /* Botones discretos en tablas */
            QPushButton.table-action {
                background-color: transparent;
                border: none;
                color: #dc3545;
                font-size: 9pt;
                padding: 2px 6px;
                text-decoration: underline;
            }
            
            QPushButton.table-action:hover {
                color: #c82333;
                background-color: #f8d7da;
                border-radius: 2px;
            }
            
            /* Botones normales */
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: 1px solid #545b62;
                border-radius: 3px;
                padding: 5px 12px;
                font-size: 9pt;
                font-weight: normal;
            }
            
            QPushButton:hover {
                background-color: #5a6268;
                border-color: #4e555b;
            }
            
            QPushButton:pressed {
                background-color: #545b62;
            }
            
            /* Botones principales */
            QPushButton#btn_guardar_cierre {
                background-color: #28a745;
                border-color: #1e7e34;
            }
            
            QPushButton#btn_guardar_cierre:hover {
                background-color: #218838;
                border-color: #1e7e34;
            }
            
            QPushButton#btn_calcular_cierre {
                background-color: #17a2b8;
                border-color: #117a8b;
            }
            
            QPushButton#btn_calcular_cierre:hover {
                background-color: #138496;
                border-color: #117a8b;
            }
            
            /* Campos de entrada */
            QComboBox, QDateEdit, QDoubleSpinBox {
                border: 1px solid #ced4da;
                border-radius: 3px;
                padding: 3px 6px;
                background-color: white;
                min-height: 26px;
            }
            
            QComboBox:editable, QDateEdit:editable, QDoubleSpinBox:editable {
                background-color: white;
            }
            
            /* Labels */
            QLabel {
                color: #212529;
                font-size: 9pt;
            }
            
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                background-color: white;
            }
            
            QTabBar::tab {
                background-color: #e9ecef;
                padding: 6px 12px;
                margin-right: 2px;
                border: 1px solid #dee2e6;
                border-bottom: none;
                border-top-left-radius: 3px;
                border-top-right-radius: 3px;
                color: #495057;
                font-size: 9pt;
            }
            
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #007bff;
                font-weight: bold;
                color: #007bff;
            }
            
            QTabBar::tab:hover {
                background-color: #dee2e6;
            }
        """
    
    def connect_signals(self):
        """Conecta todas las señales"""
        self.cargar_btn.clicked.connect(self.cargar_dia)
        self.combo_ingrediente.currentIndexChanged.connect(self.actualizar_formulario)
        self.btn_agregar_ajuste.clicked.connect(self.agregar_ajuste)
        self.btn_limpiar.clicked.connect(self.limpiar_formulario)
        self.btn_calcular_cierre.clicked.connect(self.calcular_cierre)
        self.btn_guardar_cierre.clicked.connect(self.guardar_cierre)
    
    def load_initial_data(self):
        """Carga los datos iniciales"""
        self.cargar_dia()
    
    def cargar_dia(self):
        """Carga los datos del día seleccionado"""
        try:
            fecha = self.fecha_input.date().toPyDate()
            self.fecha_actual = fecha
            
            # Limpiar datos anteriores
            self.ajustes_pendientes = []
            self.tabla_ajustes_pendientes.setRowCount(0)
            self.btn_guardar_cierre.setEnabled(False)
            
            # 1. Cargar ventas del día
            resumen_ventas = self.cierre_manager.obtener_resumen_ventas_dia(fecha)
            self.cargar_resumen_ventas(resumen_ventas)
            
            # 2. Cargar ingredientes pedidos
            ingredientes = self.cierre_manager.obtener_pedidos_chef_dia(fecha)
            self.cargar_ingredientes_dia(ingredientes)
            
            # 3. Actualizar combo de ingredientes
            self.combo_ingrediente.clear()
            for ingrediente in ingredientes:
                self.combo_ingrediente.addItem(
                    ingrediente['ingrediente'],
                    ingrediente  # Guardar datos completos
                )
            
            if ingredientes:
                self.combo_ingrediente.setCurrentIndex(0)
            
            self.info_label.setText(f"Datos cargados para {fecha.strftime('%d/%m/%Y')}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{str(e)}")
    
    def cargar_resumen_ventas(self, resumen):
        """Carga el resumen de ventas en la tabla"""
        try:
            ventas = resumen['ventas']
            self.ventas_table.setRowCount(len(ventas))
            
            for i, venta in enumerate(ventas):
                # Producto
                item_producto = QTableWidgetItem(venta.get('producto', ''))
                item_producto.setFlags(item_producto.flags() & ~Qt.ItemIsEditable)
                self.ventas_table.setItem(i, 0, item_producto)
                
                # Cantidad
                item_cantidad = QTableWidgetItem(str(venta.get('cantidad', 0)))
                item_cantidad.setTextAlignment(Qt.AlignCenter)
                item_cantidad.setFlags(item_cantidad.flags() & ~Qt.ItemIsEditable)
                self.ventas_table.setItem(i, 1, item_cantidad)
                
                # Precio unitario
                item_precio = QTableWidgetItem(f"${venta.get('precio_unitario', 0):.2f}")
                item_precio.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_precio.setFlags(item_precio.flags() & ~Qt.ItemIsEditable)
                self.ventas_table.setItem(i, 2, item_precio)
                
                # Total
                item_total = QTableWidgetItem(f"${venta.get('total', 0):.2f}")
                item_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item_total.setFlags(item_total.flags() & ~Qt.ItemIsEditable)
                self.ventas_table.setItem(i, 3, item_total)
                
                # Alternar colores de fila
                if i % 2 == 0:
                    for col in range(4):
                        self.ventas_table.item(i, col).setBackground(QColor(248, 249, 250))
            
            # Ajustar alto de filas (más compacto)
            for i in range(self.ventas_table.rowCount()):
                self.ventas_table.setRowHeight(i, 22)
            
            # Actualizar totales
            self.lbl_total_ventas.setText(f"Total Ventas: ${resumen['total_dia']:.2f}")
            self.lbl_total_productos.setText(f"Productos Vendidos: {resumen['total_items']}")
            
        except Exception as e:
            print(f"Error cargando resumen ventas: {e}")
    
    def cargar_ingredientes_dia(self, ingredientes):
        """Carga los ingredientes pedidos en el día"""
        try:
            self.tabla_ingredientes_dia.setRowCount(len(ingredientes))
            
            for i, ing in enumerate(ingredientes):
                # Ingrediente
                item_ingrediente = QTableWidgetItem(ing.get('ingrediente', ''))
                item_ingrediente.setFlags(item_ingrediente.flags() & ~Qt.ItemIsEditable)
                self.tabla_ingredientes_dia.setItem(i, 0, item_ingrediente)
                
                # Cantidad pedida
                item_pedida = QTableWidgetItem(str(ing.get('cantidad_pedida', 0)))
                item_pedida.setTextAlignment(Qt.AlignCenter)
                item_pedida.setFlags(item_pedida.flags() & ~Qt.ItemIsEditable)
                self.tabla_ingredientes_dia.setItem(i, 1, item_pedida)
                
                # Unidad
                item_unidad = QTableWidgetItem(ing.get('unidad', ''))
                item_unidad.setTextAlignment(Qt.AlignCenter)
                item_unidad.setFlags(item_unidad.flags() & ~Qt.ItemIsEditable)
                self.tabla_ingredientes_dia.setItem(i, 2, item_unidad)
                
                # Stock actual
                item_stock = QTableWidgetItem(str(ing.get('stock_actual', 0)))
                item_stock.setTextAlignment(Qt.AlignCenter)
                item_stock.setFlags(item_stock.flags() & ~Qt.ItemIsEditable)
                self.tabla_ingredientes_dia.setItem(i, 3, item_stock)
                
                # Alternar colores de fila
                if i % 2 == 0:
                    for col in range(4):
                        self.tabla_ingredientes_dia.item(i, col).setBackground(QColor(248, 249, 250))
            
            # Ajustar alto de filas
            for i in range(self.tabla_ingredientes_dia.rowCount()):
                self.tabla_ingredientes_dia.setRowHeight(i, 22)
                
        except Exception as e:
            print(f"Error cargando ingredientes: {e}")
    
    def actualizar_formulario(self):
        """Actualiza el formulario cuando cambia el ingrediente seleccionado"""
        try:
            index = self.combo_ingrediente.currentIndex()
            if index >= 0:
                ingrediente = self.combo_ingrediente.itemData(index)
                if ingrediente:
                    self.lbl_cantidad_pedida.setText(str(ingrediente.get('cantidad_pedida', 0)))
                    self.lbl_unidad.setText(ingrediente.get('unidad', ''))
                    self.spin_sobrante.setMaximum(float(ingrediente.get('cantidad_pedida', 0)))
                    self.spin_sobrante.setValue(0)
        except Exception as e:
            print(f"Error actualizando formulario: {e}")
    
    def agregar_ajuste(self):
        """Agrega un ajuste a la lista de pendientes"""
        try:
            index = self.combo_ingrediente.currentIndex()
            if index < 0:
                QMessageBox.warning(self, "Advertencia", "Seleccione un ingrediente")
                return
            
            ingrediente = self.combo_ingrediente.itemData(index)
            if not ingrediente:
                return
            
            ingrediente_id = ingrediente.get('ingrediente_id')
            ingrediente_nombre = ingrediente.get('ingrediente', '')
            cantidad_pedida = float(ingrediente.get('cantidad_pedida', 0))
            cantidad_sobrante = self.spin_sobrante.value()
            
            if cantidad_sobrante < 0:
                QMessageBox.warning(self, "Advertencia", "La cantidad sobrante no puede ser negativa")
                return
            
            if cantidad_sobrante > cantidad_pedida:
                QMessageBox.warning(self, "Advertencia", 
                    "La cantidad sobrante no puede ser mayor que la pedida")
                return
            
            cantidad_usada = cantidad_pedida - cantidad_sobrante
            a_devolver = cantidad_sobrante
            
            # Verificar si ya existe ajuste para este ingrediente
            for i in range(self.tabla_ajustes_pendientes.rowCount()):
                if self.tabla_ajustes_pendientes.item(i, 0).text() == ingrediente_nombre:
                    QMessageBox.warning(self, "Advertencia", 
                        f"Ya existe un ajuste para {ingrediente_nombre}")
                    return
            
            # Agregar a la tabla de ajustes pendientes
            row = self.tabla_ajustes_pendientes.rowCount()
            self.tabla_ajustes_pendientes.insertRow(row)
            
            # Ingrediente
            item_ingrediente = QTableWidgetItem(ingrediente_nombre)
            item_ingrediente.setFlags(item_ingrediente.flags() & ~Qt.ItemIsEditable)
            self.tabla_ajustes_pendientes.setItem(row, 0, item_ingrediente)
            
            # Cantidad pedida
            item_pedida = QTableWidgetItem(str(cantidad_pedida))
            item_pedida.setTextAlignment(Qt.AlignCenter)
            item_pedida.setFlags(item_pedida.flags() & ~Qt.ItemIsEditable)
            self.tabla_ajustes_pendientes.setItem(row, 1, item_pedida)
            
            # Cantidad usada
            item_usada = QTableWidgetItem(str(cantidad_usada))
            item_usada.setTextAlignment(Qt.AlignCenter)
            item_usada.setFlags(item_usada.flags() & ~Qt.ItemIsEditable)
            self.tabla_ajustes_pendientes.setItem(row, 2, item_usada)
            
            # A devolver
            item_devolver = QTableWidgetItem(str(a_devolver))
            item_devolver.setTextAlignment(Qt.AlignCenter)
            item_devolver.setFlags(item_devolver.flags() & ~Qt.ItemIsEditable)
            
            # Colorear según cantidad a devolver
            if a_devolver > 0:
                item_devolver.setBackground(QColor(200, 230, 201))  # Verde claro
            else:
                item_devolver.setBackground(QColor(255, 205, 210))  # Rojo claro
            
            self.tabla_ajustes_pendientes.setItem(row, 3, item_devolver)
            
            # Botón discreto para eliminar (texto subrayado, no botón)
            btn_eliminar = QPushButton("✕")
            btn_eliminar.setObjectName("table-action")
            btn_eliminar.setToolTip("Eliminar ajuste")
            btn_eliminar.clicked.connect(lambda checked, r=row: self.eliminar_ajuste(r))
            self.tabla_ajustes_pendientes.setCellWidget(row, 4, btn_eliminar)
            
            # Alternar colores de fila
            if row % 2 == 0:
                for col in range(4):
                    item = self.tabla_ajustes_pendientes.item(row, col)
                    if item:
                        item.setBackground(QColor(248, 249, 250))
            
            # Ajustar alto de fila
            self.tabla_ajustes_pendientes.setRowHeight(row, 22)
            
            # Guardar en lista de ajustes
            self.ajustes_pendientes.append({
                'ingrediente_id': ingrediente_id,
                'ingrediente_nombre': ingrediente_nombre,
                'cantidad_pedida': cantidad_pedida,
                'cantidad_usada': cantidad_usada
            })
            
            # Habilitar botón de guardar
            self.btn_guardar_cierre.setEnabled(True)
            
            # Limpiar formulario
            self.limpiar_formulario()
            
            self.info_label.setText(f"Ajuste agregado: {ingrediente_nombre}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo agregar el ajuste:\n{str(e)}")
    
    def eliminar_ajuste(self, row):
        """Elimina un ajuste de la lista de pendientes"""
        try:
            ingrediente_nombre = self.tabla_ajustes_pendientes.item(row, 0).text()
            
            self.tabla_ajustes_pendientes.removeRow(row)
            
            # Eliminar de la lista de ajustes
            self.ajustes_pendientes = [
                a for a in self.ajustes_pendientes 
                if a['ingrediente_nombre'] != ingrediente_nombre
            ]
            
            # Deshabilitar botón si no hay ajustes
            if not self.ajustes_pendientes:
                self.btn_guardar_cierre.setEnabled(False)
            
            # Re-indexar los botones de eliminar (opcional, ya que se elimina la fila)
            # Pero podemos actualizar las conexiones para las filas restantes
            for i in range(self.tabla_ajustes_pendientes.rowCount()):
                widget = self.tabla_ajustes_pendientes.cellWidget(i, 4)
                if widget:
                    # Desconectar todas las conexiones anteriores
                    try:
                        widget.clicked.disconnect()
                    except:
                        pass
                    # Conectar con nuevo índice
                    widget.clicked.connect(lambda checked, r=i: self.eliminar_ajuste(r))
            
            self.info_label.setText(f"Ajuste eliminado: {ingrediente_nombre}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el ajuste:\n{str(e)}")
    
    def limpiar_formulario(self):
        """Limpia el formulario de ajuste"""
        self.spin_sobrante.setValue(0)
    
    def calcular_cierre(self):
        """Calcula el resumen del cierre del día"""
        try:
            fecha_str = self.fecha_actual.strftime('%d/%m/%Y')
            
            if not self.ajustes_pendientes:
                QMessageBox.warning(self, "Advertencia", 
                    "No hay ajustes pendientes. Registre al menos un ajuste antes de calcular el cierre.")
                return
            
            # Calcular totales
            total_ventas = 0
            total_ingredientes_ajustados = len(self.ajustes_pendientes)
            total_a_devolver = 0
            
            # Sumar total de ventas
            resumen_ventas = self.cierre_manager.obtener_resumen_ventas_dia(self.fecha_actual)
            total_ventas = resumen_ventas['total_dia']
            
            # Calcular total a devolver
            for i in range(self.tabla_ajustes_pendientes.rowCount()):
                a_devolver = float(self.tabla_ajustes_pendientes.item(i, 3).text())
                total_a_devolver += a_devolver
            
            # Mostrar resumen
            mensaje = f"<b>RESUMEN DEL CIERRE - {fecha_str}</b><br><br>"
            mensaje += f"<b>Ventas Totales:</b> ${total_ventas:.2f}<br>"
            mensaje += f"<b>Ingredientes Ajustados:</b> {total_ingredientes_ajustados}<br>"
            mensaje += f"<b>Total a Devolver al Inventario:</b> {total_a_devolver:.2f} unidades<br><br>"
            
            mensaje += "<b>Detalle de Ajustes:</b><br>"
            for ajuste in self.ajustes_pendientes:
                a_devolver = ajuste['cantidad_pedida'] - ajuste['cantidad_usada']
                mensaje += f"• {ajuste['ingrediente_nombre']}: "
                mensaje += f"Pedido={ajuste['cantidad_pedida']}, "
                mensaje += f"Usado={ajuste['cantidad_usada']}, "
                mensaje += f"Devolver={a_devolver:.2f}<br>"
            
            mensaje += "<br><i>Revise los datos antes de guardar el cierre.</i>"
            
            QMessageBox.information(self, "Cierre Calculado", mensaje)
            
            self.info_label.setText(f"Cierre calculado para {fecha_str}. Listo para guardar.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo calcular el cierre:\n{str(e)}")
    
    def guardar_cierre(self):
        """Guarda el cierre completo del día en la base de datos"""
        try:
            if not self.ajustes_pendientes:
                QMessageBox.warning(self, "Advertencia", 
                    "No hay ajustes pendientes para guardar.")
                return
            
            fecha_str = self.fecha_actual.strftime('%d/%m/%Y')
            
            # Explicación de lo que hace "Guardar Cierre"
            explicacion = (
                "¿ESTÁ SEGURO DE GUARDAR EL CIERRE?\n\n"
                "Esta acción realizará lo siguiente:\n"
                "1. Actualizará el inventario con las cantidades devueltas\n"
                "2. Registrará los ajustes en el historial\n"
                "3. Guardará el cierre en la base de datos\n\n"
                "Esta acción NO se puede deshacer.\n\n"
                f"Se procesarán {len(self.ajustes_pendientes)} ajustes."
            )
            
            reply = QMessageBox.question(
                self, 'Confirmar Guardado de Cierre',
                explicacion,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Mostrar progreso
                progress = QMessageBox(self)
                progress.setWindowTitle("Guardando Cierre")
                progress.setText("Procesando ajustes y actualizando inventario...")
                progress.setStandardButtons(QMessageBox.NoButton)
                progress.show()
                
                # Procesar cierre
                resultado = self.cierre_manager.cerrar_dia(
                    self.ajustes_pendientes, self.fecha_actual
                )
                
                progress.close()
                
                if resultado['success']:
                    mensaje = f"<b>CIERRE GUARDADO EXITOSAMENTE</b><br><br>"
                    mensaje += f"<b>Fecha:</b> {resultado['fecha']}<br>"
                    mensaje += f"<b>Ajustes Procesados:</b> {resultado['total_ajustes']}<br>"
                    
                    if resultado['resultados']:
                        total_devuelto = sum(r.get('diferencia_devuelta', 0) 
                                          for r in resultado['resultados'])
                        mensaje += f"<b>Total Devuelto al Inventario:</b> {total_devuelto:.2f} unidades<br>"
                    
                    mensaje += "<br>El inventario ha sido actualizado automáticamente."
                    
                    QMessageBox.information(self, "Cierre Completado", mensaje)
                    
                    # Limpiar interfaz
                    self.tabla_ajustes_pendientes.setRowCount(0)
                    self.ajustes_pendientes = []
                    self.btn_guardar_cierre.setEnabled(False)
                    self.info_label.setText(f"Cierre guardado - {datetime.now().strftime('%H:%M:%S')}")
                    
                else:
                    errores = "<br>".join(resultado.get('errores', []))
                    QMessageBox.critical(self, "Error en Cierre",
                        f"<b>NO SE PUDO COMPLETAR EL CIERRE</b><br><br>{errores}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el cierre:\n{str(e)}")
