# modules/catalogos_ui.py
import os
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit,
    QMessageBox, QHeaderView, QFormLayout, QGroupBox,
    QSpinBox, QFrame, QScrollArea, QSplitter, QSizePolicy,
    QMenu, QAction, QInputDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QContextMenuEvent

class CatalogosWidget(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        
        # Variables de estado
        self.ingrediente_seleccionado_id = None
        self.producto_seleccionado_id = None
        self.modo_edicion = False
        
        # Inicializar managers
        try:
            from modules.catalogos import CatalogoManager
            self.catalogo_manager = CatalogoManager()
            print("Manager de catálogos inicializado")
        except Exception as e:
            print(f"Error inicializando catalogo_manager: {e}")
            self.catalogo_manager = None
        
        # Crear interfaz programáticamente
        print("Creando interfaz programáticamente...")
        self.create_ui_programmatically()
        
        # Configurar conexiones
        self.connect_signals()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
        # Configurar estilos
        self.setup_styles()

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.catalogo_manager = services.get("catalogos")
            try:
                self.load_initial_data()
            except Exception:
                pass

    def refresh_data(self):
        self.load_initial_data()
    
    def create_ui_programmatically(self):
        """Crea la interfaz programáticamente"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Título
        title_label = QLabel("Gestión de catálogos")
        title_label.setProperty("role", "title")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_label.setMinimumHeight(50)
        main_layout.addWidget(title_label)
        
        # Widget de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("catalogosTabWidget")
        
        # Pestaña 1: Ingredientes
        self.ingredientes_tab = QWidget()
        self.setup_ingredientes_tab_programmatically()
        self.tab_widget.addTab(self.ingredientes_tab, "Ingredientes")
        
        # Pestaña 2: Productos
        self.productos_tab = QWidget()
        self.setup_productos_tab_programmatically()
        self.tab_widget.addTab(self.productos_tab, "Productos")
        
        main_layout.addWidget(self.tab_widget, 1)
    
    def setup_ingredientes_tab_programmatically(self):
        """Configura la pestaña de ingredientes programáticamente"""
        main_layout = QVBoxLayout(self.ingredientes_tab)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Splitter horizontal para dividir formulario y tabla
        splitter = QSplitter(Qt.Vertical)
        
        # --- FORMULARIO (30% del espacio) ---
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(4, 4, 4, 4)
        form_layout.setSpacing(8)
        
        form_group = QGroupBox("Agregar/Editar Ingrediente")
        form_group.setObjectName("catalogosFormGroup")
        
        form_inner_layout = QFormLayout()
        form_inner_layout.setSpacing(10)
        form_inner_layout.setContentsMargins(12, 12, 12, 12)
        
        # Estilo para etiquetas de formulario
        label_style = """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2C3E50;
                min-height: 24px;
            }
        """
        
        # Nombre
        nombre_label = QLabel("Nombre:")
        nombre_label.setProperty("role", "field")
        self.ing_nombre_input = QLineEdit()
        self.ing_nombre_input.setPlaceholderText("Ej: Harina de Trigo")
        self.ing_nombre_input.setMinimumHeight(32)
        self.ing_nombre_input.setMaximumHeight(35)
        self.ing_nombre_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ing_nombre_input.setObjectName("ingNombreInput")
        
        # Unidad de medida
        unidad_label = QLabel("Unidad de medida:")
        unidad_label.setProperty("role", "field")
        self.ing_unidad_combo = QComboBox()
        self.ing_unidad_combo.setMinimumHeight(32)
        self.ing_unidad_combo.setMaximumHeight(35)
        self.ing_unidad_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ing_unidad_combo.setObjectName("ingUnidadCombo")
        
        # Stock mínimo
        stock_label = QLabel("Stock mínimo:")
        stock_label.setProperty("role", "field")
        self.ing_stock_min_spin = QDoubleSpinBox()
        self.ing_stock_min_spin.setRange(0, 10000)
        self.ing_stock_min_spin.setSuffix(" unidades")
        self.ing_stock_min_spin.setValue(10)
        self.ing_stock_min_spin.setDecimals(2)
        self.ing_stock_min_spin.setMinimumHeight(32)
        self.ing_stock_min_spin.setMaximumHeight(35)
        self.ing_stock_min_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ing_stock_min_spin.setObjectName("ingStockMinSpin")
        
        # Notas
        notas_label = QLabel("Notas:")
        notas_label.setProperty("role", "field")
        self.ing_notas_text = QTextEdit()
        self.ing_notas_text.setMinimumHeight(80)
        self.ing_notas_text.setMaximumHeight(100)
        self.ing_notas_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.ing_notas_text.setPlaceholderText("Notas adicionales sobre el ingrediente...")
        self.ing_notas_text.setObjectName("ingNotasText")
        
        form_inner_layout.addRow(nombre_label, self.ing_nombre_input)
        form_inner_layout.addRow(unidad_label, self.ing_unidad_combo)
        form_inner_layout.addRow(stock_label, self.ing_stock_min_spin)
        form_inner_layout.addRow(notas_label, self.ing_notas_text)
        
        # Botones del formulario
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.ing_agregar_btn = QPushButton("Guardar")
        self.ing_agregar_btn.setObjectName("btn_agregar")
        self.ing_agregar_btn.setMinimumHeight(35)
        self.ing_agregar_btn.setMaximumHeight(40)
        self.ing_agregar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ing_agregar_btn.setMinimumWidth(100)
        
        self.ing_actualizar_btn = QPushButton("Actualizar")
        self.ing_actualizar_btn.setObjectName("btn_actualizar")
        self.ing_actualizar_btn.setMinimumHeight(35)
        self.ing_actualizar_btn.setMaximumHeight(40)
        self.ing_actualizar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ing_actualizar_btn.setMinimumWidth(100)
        self.ing_actualizar_btn.setEnabled(False)
        
        self.ing_eliminar_btn = QPushButton("Eliminar")
        self.ing_eliminar_btn.setObjectName("btn_eliminar")
        self.ing_eliminar_btn.setMinimumHeight(35)
        self.ing_eliminar_btn.setMaximumHeight(40)
        self.ing_eliminar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ing_eliminar_btn.setMinimumWidth(100)
        self.ing_eliminar_btn.setEnabled(False)
        
        self.ing_limpiar_btn = QPushButton("Limpiar")
        self.ing_limpiar_btn.setMinimumHeight(35)
        self.ing_limpiar_btn.setMaximumHeight(40)
        self.ing_limpiar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ing_limpiar_btn.setMinimumWidth(100)
        
        self.ing_recargar_btn = QPushButton("Recargar")
        self.ing_recargar_btn.setMinimumHeight(35)
        self.ing_recargar_btn.setMaximumHeight(40)
        self.ing_recargar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.ing_recargar_btn.setMinimumWidth(100)
        
        button_layout.addWidget(self.ing_agregar_btn)
        button_layout.addWidget(self.ing_actualizar_btn)
        button_layout.addWidget(self.ing_eliminar_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ing_limpiar_btn)
        button_layout.addWidget(self.ing_recargar_btn)
        
        form_inner_layout.addRow(button_layout)
        form_group.setLayout(form_inner_layout)
        form_layout.addWidget(form_group)
        
        splitter.addWidget(form_container)
        
        # --- TABLA (70% del espacio) ---
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(4, 4, 4, 4)
        
        table_group = QGroupBox("Lista de Ingredientes")
        table_group.setObjectName("catalogosTableGroup")
        
        table_inner_layout = QVBoxLayout()
        table_inner_layout.setContentsMargins(4, 4, 4, 4)
        
        # Tabla de ingredientes
        self.ingredientes_table = QTableWidget()
        self.ingredientes_table.setColumnCount(6)
        self.ingredientes_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Unidad", "Stock Mín", "Notas", "Estado"
        ])
        
        # Configurar tabla
        self.setup_table_ingredientes()
        
        table_inner_layout.addWidget(self.ingredientes_table, 1)
        table_group.setLayout(table_inner_layout)
        table_layout.addWidget(table_group, 1)
        
        splitter.addWidget(table_container)
        
        # Configurar proporciones del splitter (30% formulario, 70% tabla)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter, 1)
    
    def setup_productos_tab_programmatically(self):
        """Configura la pestaña de productos programáticamente"""
        main_layout = QVBoxLayout(self.productos_tab)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # Splitter horizontal
        splitter = QSplitter(Qt.Vertical)
        
        # --- FORMULARIO (30% del espacio) ---
        form_container = QWidget()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(4, 4, 4, 4)
        form_layout.setSpacing(8)
        
        form_group = QGroupBox("Agregar/Editar Producto")
        form_group.setObjectName("catalogosProductFormGroup")
        
        form_inner_layout = QFormLayout()
        form_inner_layout.setSpacing(10)
        form_inner_layout.setContentsMargins(12, 12, 12, 12)
        
        # Estilo para etiquetas de formulario
        label_style = """
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #2C3E50;
                min-height: 24px;
            }
        """
        
        # Nombre
        nombre_label = QLabel("Nombre:")
        nombre_label.setProperty("role", "field")
        self.prod_nombre_input = QLineEdit()
        self.prod_nombre_input.setPlaceholderText("Ej: Empanada de Carne")
        self.prod_nombre_input.setMinimumHeight(32)
        self.prod_nombre_input.setMaximumHeight(35)
        self.prod_nombre_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prod_nombre_input.setObjectName("prodNombreInput")
        
        # Precio
        precio_label = QLabel("Precio:")
        precio_label.setProperty("role", "field")
        self.prod_precio_spin = QDoubleSpinBox()
        self.prod_precio_spin.setRange(0, 10000)
        self.prod_precio_spin.setPrefix("$ ")
        self.prod_precio_spin.setDecimals(2)
        self.prod_precio_spin.setValue(0)
        self.prod_precio_spin.setSingleStep(1.0)
        self.prod_precio_spin.setMinimumHeight(32)
        self.prod_precio_spin.setMaximumHeight(35)
        self.prod_precio_spin.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prod_precio_spin.setObjectName("prodPrecioSpin")
        
        # Unidad de venta
        unidad_label = QLabel("Unidad de venta:")
        unidad_label.setProperty("role", "field")
        self.prod_unidad_combo = QComboBox()
        self.prod_unidad_combo.setMinimumHeight(32)
        self.prod_unidad_combo.setMaximumHeight(35)
        self.prod_unidad_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prod_unidad_combo.setObjectName("prodUnidadCombo")
        
        # Descripción
        desc_label = QLabel("Descripción:")
        desc_label.setProperty("role", "field")
        self.prod_desc_text = QTextEdit()
        self.prod_desc_text.setMinimumHeight(80)
        self.prod_desc_text.setMaximumHeight(100)
        self.prod_desc_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prod_desc_text.setPlaceholderText("Descripción del producto...")
        self.prod_desc_text.setObjectName("prodDescText")
        
        form_inner_layout.addRow(nombre_label, self.prod_nombre_input)
        form_inner_layout.addRow(precio_label, self.prod_precio_spin)
        form_inner_layout.addRow(unidad_label, self.prod_unidad_combo)
        form_inner_layout.addRow(desc_label, self.prod_desc_text)
        
        # Botones del formulario
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.prod_agregar_btn = QPushButton("Guardar")
        self.prod_agregar_btn.setObjectName("btn_agregar")
        self.prod_agregar_btn.setMinimumHeight(35)
        self.prod_agregar_btn.setMaximumHeight(40)
        self.prod_agregar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prod_agregar_btn.setMinimumWidth(100)
        
        self.prod_actualizar_btn = QPushButton("Actualizar")
        self.prod_actualizar_btn.setObjectName("btn_actualizar")
        self.prod_actualizar_btn.setMinimumHeight(35)
        self.prod_actualizar_btn.setMaximumHeight(40)
        self.prod_actualizar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prod_actualizar_btn.setMinimumWidth(100)
        self.prod_actualizar_btn.setEnabled(False)
        
        self.prod_eliminar_btn = QPushButton("Eliminar")
        self.prod_eliminar_btn.setObjectName("btn_eliminar")
        self.prod_eliminar_btn.setMinimumHeight(35)
        self.prod_eliminar_btn.setMaximumHeight(40)
        self.prod_eliminar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prod_eliminar_btn.setMinimumWidth(100)
        self.prod_eliminar_btn.setEnabled(False)
        
        self.prod_limpiar_btn = QPushButton("Limpiar")
        self.prod_limpiar_btn.setMinimumHeight(35)
        self.prod_limpiar_btn.setMaximumHeight(40)
        self.prod_limpiar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prod_limpiar_btn.setMinimumWidth(100)
        
        self.prod_recargar_btn = QPushButton("Recargar")
        self.prod_recargar_btn.setMinimumHeight(35)
        self.prod_recargar_btn.setMaximumHeight(40)
        self.prod_recargar_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.prod_recargar_btn.setMinimumWidth(100)
        
        button_layout.addWidget(self.prod_agregar_btn)
        button_layout.addWidget(self.prod_actualizar_btn)
        button_layout.addWidget(self.prod_eliminar_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.prod_limpiar_btn)
        button_layout.addWidget(self.prod_recargar_btn)
        
        form_inner_layout.addRow(button_layout)
        form_group.setLayout(form_inner_layout)
        form_layout.addWidget(form_group)
        
        splitter.addWidget(form_container)
        
        # --- TABLA (70% del espacio) ---
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(4, 4, 4, 4)
        
        table_group = QGroupBox("Lista de Productos")
        table_group.setObjectName("catalogosProductsTableGroup")
        
        table_inner_layout = QVBoxLayout()
        table_inner_layout.setContentsMargins(4, 4, 4, 4)
        
        # Tabla de productos
        self.productos_table = QTableWidget()
        self.productos_table.setColumnCount(6)
        self.productos_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Precio", "Unidad", "Descripción", "Estado"
        ])
        
        # Configurar tabla
        self.setup_table_productos()
        
        table_inner_layout.addWidget(self.productos_table, 1)
        table_group.setLayout(table_inner_layout)
        table_layout.addWidget(table_group, 1)
        
        splitter.addWidget(table_container)
        
        # Configurar proporciones del splitter (30% formulario, 70% tabla)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter, 1)
    
    def setup_table_ingredientes(self):
        """Configura la tabla de ingredientes con CRUD completo"""
        if hasattr(self, 'ingredientes_table'):
            # Configurar comportamiento de selección
            self.ingredientes_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.ingredientes_table.setSelectionMode(QTableWidget.SingleSelection)
            self.ingredientes_table.setAlternatingRowColors(True)
            self.ingredientes_table.verticalHeader().setVisible(False)
            
            # Configurar header con buen contraste
            header = self.ingredientes_table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setDefaultAlignment(Qt.AlignLeft)
            
            # Configurar ancho de columnas
            if self.ingredientes_table.columnCount() >= 6:
                self.ingredientes_table.setColumnWidth(0, 50)   # ID
                self.ingredientes_table.setColumnWidth(1, 200)  # Nombre
                self.ingredientes_table.setColumnWidth(2, 80)   # Unidad
                self.ingredientes_table.setColumnWidth(3, 100)  # Stock Mín
                self.ingredientes_table.setColumnWidth(4, 200)  # Notas
                self.ingredientes_table.setColumnWidth(5, 80)   # Estado
            
            # Habilitar scroll suave
            self.ingredientes_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
            self.ingredientes_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
            
            # Estilo para la tabla con encabezados visibles
            table_style = """
                QTableWidget {
                    font-size: 12px;
                    alternate-background-color: #f8f9fa;
                    selection-background-color: #4a6fa5;
                    selection-color: white;
                    color: #2C3E50;
                    border: none;
                    gridline-color: #dee2e6;
                }
                QHeaderView::section {
                    background-color: #4a6fa5;
                    padding: 8px 4px;
                    border: 1px solid #3c5d8c;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }
                QTableWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid #ecf0f1;
                    color: #2C3E50;
                }
                QTableWidget::item:selected {
                    background-color: #4a6fa5;
                    color: #ffffff;
                    font-weight: bold;
                }
                QHeaderView::section:checked {
                    background-color: #3c5d8c;
                }
            """
            
            try:
                self.ingredientes_table.setObjectName("ingredientesTable")
            except Exception:
                pass
            
            # ✅ Habilitar doble clic para editar
            self.ingredientes_table.cellDoubleClicked.connect(self.on_ingrediente_double_clicked)
    
    def setup_table_productos(self):
        """Configura la tabla de productos con CRUD completo"""
        if hasattr(self, 'productos_table'):
            # Configurar comportamiento de selección
            self.productos_table.setSelectionBehavior(QTableWidget.SelectRows)
            self.productos_table.setSelectionMode(QTableWidget.SingleSelection)
            self.productos_table.setAlternatingRowColors(True)
            self.productos_table.verticalHeader().setVisible(False)
            
            # Configurar header con buen contraste
            header = self.productos_table.horizontalHeader()
            header.setStretchLastSection(True)
            header.setDefaultAlignment(Qt.AlignLeft)
            
            # Configurar ancho de columnas
            if self.productos_table.columnCount() >= 6:
                self.productos_table.setColumnWidth(0, 50)   # ID
                self.productos_table.setColumnWidth(1, 200)  # Nombre
                self.productos_table.setColumnWidth(2, 100)  # Precio
                self.productos_table.setColumnWidth(3, 80)   # Unidad
                self.productos_table.setColumnWidth(4, 200)  # Descripción
                self.productos_table.setColumnWidth(5, 80)   # Estado
            
            # Habilitar scroll suave
            self.productos_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
            self.productos_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
            
            # Estilo para la tabla con encabezados visibles
            table_style = """
                QTableWidget {
                    font-size: 12px;
                    alternate-background-color: #f8f9fa;
                    selection-background-color: #4a6fa5;
                    selection-color: white;
                    color: #2C3E50;
                    border: none;
                    gridline-color: #dee2e6;
                }
                QHeaderView::section {
                    background-color: #4a6fa5;
                    padding: 8px 4px;
                    border: 1px solid #3c5d8c;
                    font-size: 12px;
                    font-weight: bold;
                    color: white;
                }
                QTableWidget::item {
                    padding: 4px;
                    border-bottom: 1px solid #ecf0f1;
                    color: #2C3E50;
                }
                QTableWidget::item:selected {
                    background-color: #4a6fa5;
                    color: #ffffff;
                    font-weight: bold;
                }
                QHeaderView::section:checked {
                    background-color: #3c5d8c;
                }
            """
            
            try:
                self.productos_table.setObjectName("productosTable")
            except Exception:
                pass
            
            # ✅ CONEXIÓN NUEVA: Habilitar edición de precio al hacer doble clic
            self.productos_table.cellDoubleClicked.connect(self.on_producto_double_clicked)
    
    def connect_signals(self):
        """Conecta todas las señales y slots"""
        # Ingredientes
        if hasattr(self, 'ing_agregar_btn'):
            self.ing_agregar_btn.clicked.connect(self.agregar_ingrediente)
        if hasattr(self, 'ing_actualizar_btn'):
            self.ing_actualizar_btn.clicked.connect(self.actualizar_ingrediente)
        if hasattr(self, 'ing_eliminar_btn'):
            self.ing_eliminar_btn.clicked.connect(self.eliminar_ingrediente)
        if hasattr(self, 'ing_limpiar_btn'):
            self.ing_limpiar_btn.clicked.connect(self.limpiar_formulario_ingrediente)
        if hasattr(self, 'ing_recargar_btn'):
            self.ing_recargar_btn.clicked.connect(self.cargar_ingredientes)
        
        # Productos
        if hasattr(self, 'prod_agregar_btn'):
            self.prod_agregar_btn.clicked.connect(self.agregar_producto)
        if hasattr(self, 'prod_actualizar_btn'):
            self.prod_actualizar_btn.clicked.connect(self.actualizar_producto)
        if hasattr(self, 'prod_eliminar_btn'):
            self.prod_eliminar_btn.clicked.connect(self.eliminar_producto)
        if hasattr(self, 'prod_limpiar_btn'):
            self.prod_limpiar_btn.clicked.connect(self.limpiar_formulario_producto)
        if hasattr(self, 'prod_recargar_btn'):
            self.prod_recargar_btn.clicked.connect(self.cargar_productos)
        
        # Selección en tablas
        if hasattr(self, 'ingredientes_table'):
            self.ingredientes_table.itemSelectionChanged.connect(self.on_ingrediente_selected)
        if hasattr(self, 'productos_table'):
            self.productos_table.itemSelectionChanged.connect(self.on_producto_selected)
    
    def load_initial_data(self):
        """Carga los datos iniciales"""
        # Cargar unidades de medida
        self.cargar_unidades_medida()
        
        # Cargar listas
        self.cargar_ingredientes()
        self.cargar_productos()
    
    def cargar_unidades_medida(self):
        """Carga las unidades de medida REALES desde la base de datos"""
        try:
            print("Cargando unidades de medida REALES...")
            
            if not self.catalogo_manager:
                print("No hay manager de catálogo disponible")
                # Agregar unidades por defecto si no hay manager
                unidades_default = ["kg", "g", "l", "ml", "unidad", "docena"]
                if hasattr(self, 'ing_unidad_combo'):
                    self.ing_unidad_combo.clear()
                    for unidad in unidades_default:
                        self.ing_unidad_combo.addItem(unidad, unidad)
                
                if hasattr(self, 'prod_unidad_combo'):
                    self.prod_unidad_combo.clear()
                    for unidad in unidades_default:
                        self.prod_unidad_combo.addItem(unidad, unidad)
                return
            
            # Obtener unidades de medida REALES
            try:
                unidades = self.catalogo_manager.obtener_unidades_medida()
                if not unidades:
                    print("No se encontraron unidades de medida en la BD")
                    return
            except Exception as e:
                print(f"Error obteniendo unidades de medida: {e}")
                return
            
            # Unidades para ingredientes
            if hasattr(self, 'ing_unidad_combo'):
                self.ing_unidad_combo.clear()
                for unidad in unidades:
                    nombre = unidad.get('nombre', '')
                    abrev = unidad.get('abreviatura', '')
                    if nombre and abrev:
                        display_text = f"{nombre} ({abrev})"
                        self.ing_unidad_combo.addItem(display_text, abrev)
                if self.ing_unidad_combo.count() > 0:
                    self.ing_unidad_combo.setCurrentIndex(0)
            
            # Unidades para productos
            if hasattr(self, 'prod_unidad_combo'):
                self.prod_unidad_combo.clear()
                for unidad in unidades:
                    nombre = unidad.get('nombre', '')
                    abrev = unidad.get('abreviatura', '')
                    if nombre and abrev:
                        display_text = f"{nombre} ({abrev})"
                        self.prod_unidad_combo.addItem(display_text, abrev)
                if self.prod_unidad_combo.count() > 0:
                    self.prod_unidad_combo.setCurrentIndex(0)
                    
            print(f"{len(unidades)} unidades de medida cargadas")
                    
        except Exception as e:
            print(f"Error cargando unidades: {e}")
            traceback.print_exc()
    
    def cargar_ingredientes(self):
        """Carga la lista de ingredientes REALES desde la base de datos"""
        try:
            print("Cargando ingredientes REALES...")
            
            if not hasattr(self, 'ingredientes_table'):
                print("No hay tabla de ingredientes")
                return
            
            # Limpiar tabla primero
            self.ingredientes_table.setRowCount(0)
            
            # Si no hay manager, la tabla se queda vacía
            if not self.catalogo_manager:
                print("No hay manager de catálogo disponible")
                return
                
            # Obtener ingredientes REALES
            try:
                ingredientes = self.catalogo_manager.obtener_ingredientes()
                if not ingredientes:
                    print("No se encontraron ingredientes en la base de datos")
                    return
            except Exception as e:
                print(f"Error obteniendo ingredientes: {e}")
                return
            
            print(f"{len(ingredientes)} ingredientes REALES cargados")
            
            self.ingredientes_table.setRowCount(len(ingredientes))
            
            for i, ing in enumerate(ingredientes):
                # Extraer datos según estructura de la base de datos
                ing_id = ing.get('id', 0)
                nombre = ing.get('nombre', '')
                unidad = ing.get('abreviatura', ing.get('unidad', ''))
                stock_min = ing.get('stock_minimo', 0)
                notas = ing.get('notas', '')
                activo = ing.get('activo', 1)
                
                # Mostrar en tabla
                self.ingredientes_table.setItem(i, 0, QTableWidgetItem(str(ing_id)))
                self.ingredientes_table.setItem(i, 1, QTableWidgetItem(str(nombre)))
                self.ingredientes_table.setItem(i, 2, QTableWidgetItem(str(unidad)))
                
                # Stock mínimo con formato
                stock_item = QTableWidgetItem(f"{float(stock_min):.2f}" if stock_min else "0.00")
                stock_item.setTextAlignment(Qt.AlignCenter)
                self.ingredientes_table.setItem(i, 3, stock_item)
                
                # Notas truncadas
                notas_item = QTableWidgetItem(str(notas)[:50] + ("..." if len(str(notas)) > 50 else ""))
                self.ingredientes_table.setItem(i, 4, notas_item)
                
                # Estado
                estado_item = QTableWidgetItem('Activo' if activo else 'Inactivo')
                estado_item.setTextAlignment(Qt.AlignCenter)
                
                # Color para estado
                if activo:
                    estado_item.setBackground(QColor(220, 255, 220))
                    estado_item.setForeground(QColor(0, 0, 0))
                else:
                    estado_item.setBackground(QColor(255, 220, 220))
                    estado_item.setForeground(QColor(0, 0, 0))
                
                self.ingredientes_table.setItem(i, 5, estado_item)
                
                # Centrar algunas columnas
                for col in [0, 2, 3, 5]:
                    item = self.ingredientes_table.item(i, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            
            # Ajustar alto de filas
            for i in range(self.ingredientes_table.rowCount()):
                self.ingredientes_table.setRowHeight(i, 28)
            
            print("Tabla de ingredientes actualizada con datos REALES")
                    
        except Exception as e:
            print(f"Error cargando ingredientes: {e}")
            traceback.print_exc()
    
    def cargar_productos(self):
        """Carga la lista de productos REALES desde la base de datos"""
        try:
            print("Cargando productos REALES...")
            
            if not hasattr(self, 'productos_table'):
                print("No hay tabla de productos")
                return
            
            # Limpiar tabla primero
            self.productos_table.setRowCount(0)
            
            if not self.catalogo_manager:
                print("No hay manager de catálogo disponible")
                return
                
            # Obtener productos REALES
            try:
                productos = self.catalogo_manager.obtener_productos()
                if not productos:
                    print("No se encontraron productos en la base de datos")
                    return
            except Exception as e:
                print(f"Error obteniendo productos: {e}")
                return
            
            print(f"{len(productos)} productos REALES cargados")
            
            # Desactivar señales temporalmente para evitar eventos de celda cambiada
            self.productos_table.blockSignals(True)
            self.productos_table.setRowCount(len(productos))
            
            for i, prod in enumerate(productos):
                # Extraer datos según estructura de la base de datos
                prod_id = prod.get('id', 0)
                nombre = prod.get('nombre', '')
                precio = prod.get('precio_venta', 0)
                unidad = prod.get('unidad_venta', 'unidad')
                descripcion = prod.get('descripcion', '')
                activo = prod.get('activo', 1)
                
                # Mostrar en tabla
                self.productos_table.setItem(i, 0, QTableWidgetItem(str(prod_id)))
                self.productos_table.setItem(i, 1, QTableWidgetItem(str(nombre)))
                
                # ✅ PRECIO: hacer editable con formato
                precio_item = QTableWidgetItem(f"${float(precio):.2f}" if precio else "$0.00")
                precio_item.setData(Qt.UserRole, float(precio) if precio else 0.0)
                precio_item.setTextAlignment(Qt.AlignCenter)
                self.productos_table.setItem(i, 2, precio_item)
                
                self.productos_table.setItem(i, 3, QTableWidgetItem(str(unidad)))
                
                # Descripción truncada
                desc_item = QTableWidgetItem(str(descripcion)[:50] + ("..." if len(str(descripcion)) > 50 else ""))
                self.productos_table.setItem(i, 4, desc_item)
                
                # Estado
                estado_item = QTableWidgetItem('Activo' if activo else 'Inactivo')
                estado_item.setTextAlignment(Qt.AlignCenter)
                
                # Color para estado
                if activo:
                    estado_item.setBackground(QColor(220, 255, 220))
                    estado_item.setForeground(QColor(0, 0, 0))
                else:
                    estado_item.setBackground(QColor(255, 220, 220))
                    estado_item.setForeground(QColor(0, 0, 0))
                
                self.productos_table.setItem(i, 5, estado_item)
                
                # Centrar algunas columnas
                for col in [0, 2, 3, 5]:
                    item = self.productos_table.item(i, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            
            # Ajustar alto de filas
            for i in range(self.productos_table.rowCount()):
                self.productos_table.setRowHeight(i, 28)
            
            # Reactivar señales
            self.productos_table.blockSignals(False)
            
            print("Tabla de productos actualizada con datos REALES")
                    
        except Exception as e:
            print(f"Error cargando productos: {e}")
            traceback.print_exc()
            self.productos_table.blockSignals(False)
    
    # ========== EVENTOS DE TABLAS ==========
    
    def on_ingrediente_double_clicked(self, row, column):
        """Cuando se hace doble clic en un ingrediente"""
        if row >= 0 and column >= 0:
            self.on_ingrediente_selected()
            # Cambiar a modo edición
            self.ing_actualizar_btn.setEnabled(True)
            self.ing_eliminar_btn.setEnabled(True)
    
    def on_producto_double_clicked(self, row, column):
        """Cuando se hace doble clic en un producto"""
        if row >= 0 and column >= 0:
            if column == 2:  # Columna de precio
                item = self.productos_table.item(row, column)
                if item:
                    # Obtener el precio sin formato
                    precio_sin_formato = item.data(Qt.UserRole)
                    if precio_sin_formato is not None:
                        # Mostrar el precio sin símbolo de dólar para edición
                        nuevo_precio, ok = QInputDialog.getDouble(
                            self, "Editar Precio", 
                            "Nuevo precio del producto:", 
                            float(precio_sin_formato), 0, 10000, 2
                        )
                        if ok:
                            # Actualizar precio
                            id_item = self.productos_table.item(row, 0)
                            if id_item:
                                producto_id = int(id_item.text())
                                self.actualizar_precio_desde_tabla(producto_id, nuevo_precio)
            else:
                self.on_producto_selected()
                # Cambiar a modo edición
                self.prod_actualizar_btn.setEnabled(True)
                self.prod_eliminar_btn.setEnabled(True)
    
    def on_ingrediente_selected(self):
        """Cuando se selecciona un ingrediente en la tabla"""
        if hasattr(self, 'ingredientes_table') and hasattr(self, 'ing_nombre_input'):
            selected_row = self.ingredientes_table.currentRow()
            if selected_row >= 0:
                # Obtener ID del ingrediente
                id_item = self.ingredientes_table.item(selected_row, 0)
                if id_item:
                    self.ingrediente_seleccionado_id = int(id_item.text())
                    
                    # Cargar datos en formulario
                    nombre_item = self.ingredientes_table.item(selected_row, 1)
                    unidad_item = self.ingredientes_table.item(selected_row, 2)
                    stock_item = self.ingredientes_table.item(selected_row, 3)
                    notas_item = self.ingredientes_table.item(selected_row, 4)
                    
                    if nombre_item and unidad_item and stock_item and notas_item:
                        self.ing_nombre_input.setText(nombre_item.text())
                        
                        # Buscar unidad en combo
                        unidad_text = unidad_item.text()
                        index = self.ing_unidad_combo.findText(unidad_text, Qt.MatchContains)
                        if index >= 0:
                            self.ing_unidad_combo.setCurrentIndex(index)
                        
                        # Stock mínimo
                        try:
                            stock_text = stock_item.text().replace(" unidades", "")
                            self.ing_stock_min_spin.setValue(float(stock_text))
                        except:
                            self.ing_stock_min_spin.setValue(0)
                        
                        # Notas
                        self.ing_notas_text.setText(notas_item.text())
                        
                        # Activar botones de edición
                        self.ing_actualizar_btn.setEnabled(True)
                        self.ing_eliminar_btn.setEnabled(True)
                        
                        # Desactivar botón agregar
                        self.ing_agregar_btn.setEnabled(False)
    
    def on_producto_selected(self):
        """Cuando se selecciona un producto en la tabla"""
        if hasattr(self, 'productos_table') and hasattr(self, 'prod_nombre_input'):
            selected_row = self.productos_table.currentRow()
            if selected_row >= 0:
                # Obtener ID del producto
                id_item = self.productos_table.item(selected_row, 0)
                if id_item:
                    self.producto_seleccionado_id = int(id_item.text())
                    
                    # Cargar datos en formulario
                    nombre_item = self.productos_table.item(selected_row, 1)
                    precio_item = self.productos_table.item(selected_row, 2)
                    unidad_item = self.productos_table.item(selected_row, 3)
                    desc_item = self.productos_table.item(selected_row, 4)
                    
                    if nombre_item and precio_item and unidad_item and desc_item:
                        self.prod_nombre_input.setText(nombre_item.text())
                        
                        # Precio
                        try:
                            precio_text = precio_item.text().replace("$", "").strip()
                            self.prod_precio_spin.setValue(float(precio_text))
                        except:
                            self.prod_precio_spin.setValue(0)
                        
                        # Buscar unidad en combo
                        unidad_text = unidad_item.text()
                        index = self.prod_unidad_combo.findText(unidad_text, Qt.MatchContains)
                        if index >= 0:
                            self.prod_unidad_combo.setCurrentIndex(index)
                        
                        # Descripción
                        self.prod_desc_text.setText(desc_item.text())
                        
                        # Activar botones de edición
                        self.prod_actualizar_btn.setEnabled(True)
                        self.prod_eliminar_btn.setEnabled(True)
                        
                        # Desactivar botón agregar
                        self.prod_agregar_btn.setEnabled(False)
    
    # ========== FUNCIONES CRUD PARA INGREDIENTES ==========
    
    def agregar_ingrediente(self):
        """Agrega un nuevo ingrediente a la base de datos"""
        try:
            # Obtener datos del formulario
            nombre = self.ing_nombre_input.text().strip()
            unidad_text = self.ing_unidad_combo.currentText()
            unidad = unidad_text.split('(')[-1].replace(')', '').strip() if '(' in unidad_text else unidad_text
            stock_min = self.ing_stock_min_spin.value()
            notas = self.ing_notas_text.toPlainText().strip()
            
            # Validar
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre del ingrediente es obligatorio")
                return
            
            if not unidad:
                QMessageBox.warning(self, "Error", "Debe seleccionar una unidad de medida")
                return
            
            # Validar nombre
            if len(nombre) < 2:
                QMessageBox.warning(self, "Error", "El nombre debe tener al menos 2 caracteres")
                return
            
            # Validar stock mínimo
            if stock_min < 0:
                QMessageBox.warning(self, "Error", "El stock mínimo no puede ser negativo")
                return
            
            if not self.catalogo_manager:
                QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
                return
            
            # Agregar ingrediente a la base de datos
            try:
                # Obtener ID de la unidad de medida
                unidades = self.catalogo_manager.obtener_unidades_medida()
                unidad_id = None
                for u in unidades:
                    if u.get('abreviatura') == unidad or u.get('nombre') == unidad:
                        unidad_id = u.get('id')
                        break
                
                if not unidad_id:
                    QMessageBox.warning(self, "Error", f"Unidad de medida '{unidad}' no encontrada")
                    return
                
                # Llamar al método del catalogo_manager
                nuevo_id = self.catalogo_manager.agregar_ingrediente(
                    nombre=nombre,
                    unidad_medida_id=unidad_id,
                    stock_minimo=stock_min,
                    notas=notas
                )
                
                print(f"Ingrediente agregado con ID: {nuevo_id}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el ingrediente:\n{str(e)}")
                return
            
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", f"Ingrediente '{nombre}' agregado correctamente")
            
            # Limpiar formulario y actualizar lista
            self.limpiar_formulario_ingrediente()
            self.cargar_ingredientes()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo agregar el ingrediente:\n{str(e)}")
            traceback.print_exc()
    
    def actualizar_ingrediente(self):
        """Actualiza un ingrediente existente"""
        try:
            if self.ingrediente_seleccionado_id is None:
                QMessageBox.warning(self, "Error", "No hay ingrediente seleccionado para actualizar")
                return
            
            # Obtener datos del formulario
            nombre = self.ing_nombre_input.text().strip()
            unidad_text = self.ing_unidad_combo.currentText()
            unidad = unidad_text.split('(')[-1].replace(')', '').strip() if '(' in unidad_text else unidad_text
            stock_min = self.ing_stock_min_spin.value()
            notas = self.ing_notas_text.toPlainText().strip()
            
            # Validar
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre del ingrediente es obligatorio")
                return
            
            if not unidad:
                QMessageBox.warning(self, "Error", "Debe seleccionar una unidad de medida")
                return
            
            # Validar nombre
            if len(nombre) < 2:
                QMessageBox.warning(self, "Error", "El nombre debe tener al menos 2 caracteres")
                return
            
            # Validar stock mínimo
            if stock_min < 0:
                QMessageBox.warning(self, "Error", "El stock mínimo no puede ser negativo")
                return
            
            if not self.catalogo_manager:
                QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
                return
            
            # Obtener ID de la unidad de medida
            unidades = self.catalogo_manager.obtener_unidades_medida()
            unidad_id = None
            for u in unidades:
                if u.get('abreviatura') == unidad or u.get('nombre') == unidad:
                    unidad_id = u.get('id')
                    break
            
            if not unidad_id:
                QMessageBox.warning(self, "Error", f"Unidad de medida '{unidad}' no encontrada")
                return
            
            # Actualizar ingrediente
            self.catalogo_manager.actualizar_ingrediente(
                ingrediente_id=self.ingrediente_seleccionado_id,
                nombre=nombre,
                unidad_medida_id=unidad_id,
                stock_minimo=stock_min,
                notas=notas
            )
            
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", f"Ingrediente '{nombre}' actualizado correctamente")
            
            # Limpiar formulario y actualizar lista
            self.limpiar_formulario_ingrediente()
            self.cargar_ingredientes()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el ingrediente:\n{str(e)}")
            traceback.print_exc()
    
    def eliminar_ingrediente(self):
        """Elimina (desactiva) un ingrediente"""
        try:
            if self.ingrediente_seleccionado_id is None:
                QMessageBox.warning(self, "Error", "No hay ingrediente seleccionado para eliminar")
                return
            
            # Confirmar eliminación
            respuesta = QMessageBox.question(
                self, 
                "Confirmar eliminación", 
                "¿Está seguro de que desea eliminar este ingrediente?\n\nNota: Se marcará como inactivo, pero no se borrarán los registros históricos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.No:
                return
            
            # Eliminar ingrediente
            self.catalogo_manager.eliminar_ingrediente(self.ingrediente_seleccionado_id)
            
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", "Ingrediente eliminado correctamente")
            
            # Limpiar formulario y actualizar lista
            self.limpiar_formulario_ingrediente()
            self.cargar_ingredientes()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el ingrediente:\n{str(e)}")
            traceback.print_exc()
    
    # ========== FUNCIONES CRUD PARA PRODUCTOS ==========
    
    def agregar_producto(self):
        """Agrega un nuevo producto a la base de datos"""
        try:
            # Obtener datos del formulario
            nombre = self.prod_nombre_input.text().strip()
            precio = self.prod_precio_spin.value()
            unidad_text = self.prod_unidad_combo.currentText()
            unidad = unidad_text.split('(')[-1].replace(')', '').strip() if '(' in unidad_text else unidad_text
            descripcion = self.prod_desc_text.toPlainText().strip()
            
            # Validar
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio")
                return
            
            if not unidad:
                QMessageBox.warning(self, "Error", "Debe seleccionar una unidad de venta")
                return
            
            # Validar precio
            if precio <= 0:
                QMessageBox.warning(self, "Error", "El precio debe ser mayor a 0")
                return
            
            # Validar nombre
            if len(nombre) < 2:
                QMessageBox.warning(self, "Error", "El nombre debe tener al menos 2 caracteres")
                return
            
            if not self.catalogo_manager:
                QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
                return
            
            # Agregar producto a la base de datos
            try:
                # Llamar al método del catalogo_manager
                nuevo_id = self.catalogo_manager.agregar_producto(
                    nombre=nombre,
                    precio_venta=precio,
                    unidad_venta=unidad,
                    descripcion=descripcion
                )
                
                print(f"Producto agregado con ID: {nuevo_id}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo agregar el producto:\n{str(e)}")
                return
            
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", f"Producto '{nombre}' agregado correctamente")
            
            # Limpiar formulario y actualizar lista
            self.limpiar_formulario_producto()
            self.cargar_productos()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo agregar el producto:\n{str(e)}")
            traceback.print_exc()
    
    def actualizar_producto(self):
        """Actualiza un producto existente"""
        try:
            if self.producto_seleccionado_id is None:
                QMessageBox.warning(self, "Error", "No hay producto seleccionado para actualizar")
                return
            
            # Obtener datos del formulario
            nombre = self.prod_nombre_input.text().strip()
            precio = self.prod_precio_spin.value()
            unidad_text = self.prod_unidad_combo.currentText()
            unidad = unidad_text.split('(')[-1].replace(')', '').strip() if '(' in unidad_text else unidad_text
            descripcion = self.prod_desc_text.toPlainText().strip()
            
            # Validar
            if not nombre:
                QMessageBox.warning(self, "Error", "El nombre del producto es obligatorio")
                return
            
            if not unidad:
                QMessageBox.warning(self, "Error", "Debe seleccionar una unidad de venta")
                return
            
            # Validar precio
            if precio <= 0:
                QMessageBox.warning(self, "Error", "El precio debe ser mayor a 0")
                return
            
            # Validar nombre
            if len(nombre) < 2:
                QMessageBox.warning(self, "Error", "El nombre debe tener al menos 2 caracteres")
                return
            
            if not self.catalogo_manager:
                QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
                return
            
            # Actualizar producto
            self.catalogo_manager.actualizar_producto(
                producto_id=self.producto_seleccionado_id,
                nombre=nombre,
                precio_venta=precio,
                unidad_venta=unidad,
                descripcion=descripcion
            )
            
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", f"Producto '{nombre}' actualizado correctamente")
            
            # Limpiar formulario y actualizar lista
            self.limpiar_formulario_producto()
            self.cargar_productos()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el producto:\n{str(e)}")
            traceback.print_exc()
    
    def actualizar_precio_desde_tabla(self, producto_id, nuevo_precio):
        """Actualiza el precio desde la tabla (doble clic)"""
        try:
            if not self.catalogo_manager:
                QMessageBox.warning(self, "Error", "No hay conexión a la base de datos")
                return
            
            # Validar precio
            if nuevo_precio < 0:
                QMessageBox.warning(self, "Error", "El precio no puede ser negativo")
                return
            
            if nuevo_precio > 1000000:
                QMessageBox.warning(self, "Error", "El precio es demasiado alto")
                return
            
            # Actualizar precio
            self.catalogo_manager.actualizar_precio_producto(producto_id, nuevo_precio)
            
            # Recargar productos
            self.cargar_productos()
            
            # Mostrar mensaje
            QMessageBox.information(self, "Éxito", f"Precio actualizado a ${nuevo_precio:.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo actualizar el precio:\n{str(e)}")
            traceback.print_exc()
    
    def eliminar_producto(self):
        """Elimina (desactiva) un producto"""
        try:
            if self.producto_seleccionado_id is None:
                QMessageBox.warning(self, "Error", "No hay producto seleccionado para eliminar")
                return
            
            # Confirmar eliminación
            respuesta = QMessageBox.question(
                self, 
                "Confirmar eliminación", 
                "¿Está seguro de que desea eliminar este producto?\n\nNota: Se marcará como inactivo, pero no se borrarán los registros históricos.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if respuesta == QMessageBox.No:
                return
            
            # Eliminar producto
            self.catalogo_manager.eliminar_producto(self.producto_seleccionado_id)
            
            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", "Producto eliminado correctamente")
            
            # Limpiar formulario y actualizar lista
            self.limpiar_formulario_producto()
            self.cargar_productos()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el producto:\n{str(e)}")
            traceback.print_exc()
    
    # ========== FUNCIONES AUXILIARES ==========
    
    def limpiar_formulario_ingrediente(self):
        """Limpia el formulario de ingrediente"""
        if hasattr(self, 'ing_nombre_input'):
            self.ing_nombre_input.clear()
            self.ing_stock_min_spin.setValue(10.0)
            self.ing_notas_text.clear()
            if hasattr(self, 'ing_unidad_combo'):
                self.ing_unidad_combo.setCurrentIndex(0)
            
            # Deseleccionar tabla
            if hasattr(self, 'ingredientes_table'):
                self.ingredientes_table.clearSelection()
            
            # Desactivar botones de edición
            if hasattr(self, 'ing_actualizar_btn'):
                self.ing_actualizar_btn.setEnabled(False)
            if hasattr(self, 'ing_eliminar_btn'):
                self.ing_eliminar_btn.setEnabled(False)
            
            # Activar botón agregar
            if hasattr(self, 'ing_agregar_btn'):
                self.ing_agregar_btn.setEnabled(True)
            
            # Resetear ID seleccionado
            self.ingrediente_seleccionado_id = None
    
    def limpiar_formulario_producto(self):
        """Limpia el formulario de producto"""
        if hasattr(self, 'prod_nombre_input'):
            self.prod_nombre_input.clear()
            self.prod_precio_spin.setValue(0.0)
            self.prod_desc_text.clear()
            if hasattr(self, 'prod_unidad_combo'):
                self.prod_unidad_combo.setCurrentIndex(0)
            
            # Deseleccionar tabla
            if hasattr(self, 'productos_table'):
                self.productos_table.clearSelection()
            
            # Desactivar botones de edición
            if hasattr(self, 'prod_actualizar_btn'):
                self.prod_actualizar_btn.setEnabled(False)
            if hasattr(self, 'prod_eliminar_btn'):
                self.prod_eliminar_btn.setEnabled(False)
            
            # Activar botón agregar
            if hasattr(self, 'prod_agregar_btn'):
                self.prod_agregar_btn.setEnabled(True)
            
            # Resetear ID seleccionado
            self.producto_seleccionado_id = None
    
    def setup_styles(self):
        """Configura estilos adicionales"""
        # Estilo para botones
        button_style = """
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 12px;
                min-height: 35px;
                max-height: 40px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3c5d8c;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QPushButton#btn_agregar {
                background-color: #28a745;
            }
            QPushButton#btn_agregar:hover {
                background-color: #218838;
            }
            QPushButton#btn_actualizar {
                background-color: #ffc107;
                color: #212529;
            }
            QPushButton#btn_actualizar:hover {
                background-color: #e0a800;
            }
            QPushButton#btn_eliminar {
                background-color: #dc3545;
            }
            QPushButton#btn_eliminar:hover {
                background-color: #c82333;
            }
        """
        
        # Delegar estilos al QSS global: marcar widget para aplicar reglas por objeto
        self.setObjectName("catalogosWidget")
        
        # Configurar fuente global
        font = QFont("Segoe UI", 9)
        self.setFont(font)
    
    def contextMenuEvent(self, event):
        """Muestra menú contextual para las tablas"""
        # Implementar menú contextual si es necesario
        pass
