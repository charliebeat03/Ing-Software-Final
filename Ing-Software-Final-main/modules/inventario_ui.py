# modules/inventario_ui.py
import os
import traceback
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QFrame, QSplitter,
    QScrollArea, QGridLayout, QSizePolicy, QStackedWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5 import uic

class InventarioWidget(QWidget):
    def __init__(self, db_manager=None):
        super().__init__()
        
        # Inicializar managers
        try:
            from modules.inventario import InventarioManager
            from modules.catalogos import CatalogoManager
            
            self.inventario_manager = InventarioManager()
            self.catalogo_manager = CatalogoManager()
            print("Managers de inventario y catálogos inicializados")
        except Exception as e:
            print(f"Error inicializando managers: {e}")
            self.inventario_manager = None
            self.catalogo_manager = None
        
        # Cargar interfaz desde archivo .ui
        ui_path = os.path.join("ui", "inventario.ui")
        if os.path.exists(ui_path):
            try:
                uic.loadUi(ui_path, self)
                self.setup_ui_loaded()
                self.apply_windows_standard_fixes()
            except Exception as e:
                print(f"Error cargando UI: {e}")
                self.create_responsive_ui()
        else:
            self.create_responsive_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Cargar datos iniciales
        self.load_data()
        
        # Aplicar estilos
        self.apply_specific_styles()

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.inventario_manager = services.get("inventario")
            self.catalogo_manager = services.get("catalogos")
            try:
                self.load_data()
            except Exception:
                pass

    def refresh_data(self):
        self.load_data()
    
    def apply_windows_standard_fixes(self):
        """Aplica correcciones de estilo Windows a elementos cargados desde .ui"""
        # Reducir botones a 30px
        for btn in self.findChildren(QPushButton):
            btn.setMinimumHeight(30)
            btn.setMaximumHeight(32)
        
        # Ajustar altura de filas de tabla para mostrar más filas
        if hasattr(self, 'ingredientes_table'):
            self.ingredientes_table.verticalHeader().setDefaultSectionSize(24)
            # Asegurar que las columnas se expandan
            header = self.ingredientes_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
        
        if hasattr(self, 'productos_table'):
            self.productos_table.verticalHeader().setDefaultSectionSize(24)
            header = self.productos_table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.Stretch)
        
        # Reducir tamaño de paneles de alertas y resumen
        for group in self.findChildren(QGroupBox):
            if "ALERTAS" in group.title() or "RESUMEN" in group.title():
                group.setMaximumHeight(200)
    
    def create_responsive_ui(self):
        """Crea la interfaz responsiva"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # Título
        title_label = QLabel("Estado del inventario")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        title_label.setMinimumHeight(40)
        title_label.setProperty("role", "title")
        main_layout.addWidget(title_label)
        
        # Splitter principal (horizontal para las dos tablas)
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(3)
        
        # --- PANEL IZQUIERDO: Ingredientes ---
        ingredientes_panel = QWidget()
        ingredientes_layout = QVBoxLayout(ingredientes_panel)
        ingredientes_layout.setContentsMargins(6, 6, 6, 6)
        ingredientes_layout.setSpacing(6)
        
        # Grupo de ingredientes
        ingredientes_group = QGroupBox("Ingredientes")
        ingredientes_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        ingredientes_inner = QVBoxLayout(ingredientes_group)
        ingredientes_inner.setSpacing(6)
        ingredientes_inner.setContentsMargins(8, 8, 8, 8)
        
        # Tabla de ingredientes
        self.ingredientes_table = QTableWidget()
        self.ingredientes_table.setColumnCount(5)
        self.ingredientes_table.setHorizontalHeaderLabels(["Nombre", "Stock", "Unidad", "Mínimo", "Estado"])
        self.ingredientes_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configurar tabla para expandirse
        header = self.ingredientes_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Stock
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Unidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Mínimo
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Estado
        
        self.ingredientes_table.verticalHeader().setDefaultSectionSize(24)  # Altura de fila reducida
        
        ingredientes_inner.addWidget(self.ingredientes_table, 1)
        
        # Botones para ingredientes
        ingredientes_buttons = QHBoxLayout()
        ingredientes_buttons.setSpacing(8)
        
        self.ing_refresh_btn = QPushButton("Actualizar")
        self.ing_refresh_btn.setMinimumHeight(30)
        self.ing_refresh_btn.setMinimumWidth(100)
        
        self.ing_export_btn = QPushButton("Exportar")
        self.ing_export_btn.setMinimumHeight(30)
        self.ing_export_btn.setMinimumWidth(100)
        
        ingredientes_buttons.addWidget(self.ing_refresh_btn)
        ingredientes_buttons.addStretch()
        ingredientes_buttons.addWidget(self.ing_export_btn)
        
        ingredientes_inner.addLayout(ingredientes_buttons)
        ingredientes_layout.addWidget(ingredientes_group, 1)
        
        # Agregar al splitter
        main_splitter.addWidget(ingredientes_panel)
        
        # --- PANEL DERECHO: Productos ---
        productos_panel = QWidget()
        productos_layout = QVBoxLayout(productos_panel)
        productos_layout.setContentsMargins(6, 6, 6, 6)
        productos_layout.setSpacing(6)
        
        # Grupo de productos
        productos_group = QGroupBox("Productos")
        productos_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        productos_inner = QVBoxLayout(productos_group)
        productos_inner.setSpacing(6)
        productos_inner.setContentsMargins(8, 8, 8, 8)
        
        # Tabla de productos
        self.productos_table = QTableWidget()
        self.productos_table.setColumnCount(5)
        self.productos_table.setHorizontalHeaderLabels(["Nombre", "Disponible", "Unidad", "Precio", "Valor"])
        self.productos_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Configurar tabla para expandirse
        header = self.productos_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Nombre
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Disponible
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Unidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Precio
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Valor
        
        self.productos_table.verticalHeader().setDefaultSectionSize(24)  # Altura de fila reducida
        
        productos_inner.addWidget(self.productos_table, 1)
        
        # Botones para productos
        productos_buttons = QHBoxLayout()
        productos_buttons.setSpacing(8)
        
        self.prod_refresh_btn = QPushButton("Actualizar")
        self.prod_refresh_btn.setMinimumHeight(30)
        self.prod_refresh_btn.setMinimumWidth(100)
        
        self.prod_export_btn = QPushButton("Exportar")
        self.prod_export_btn.setMinimumHeight(30)
        self.prod_export_btn.setMinimumWidth(100)
        
        productos_buttons.addWidget(self.prod_refresh_btn)
        productos_buttons.addStretch()
        productos_buttons.addWidget(self.prod_export_btn)
        
        productos_inner.addLayout(productos_buttons)
        productos_layout.addWidget(productos_group, 1)
        
        # Agregar al splitter
        main_splitter.addWidget(productos_panel)
        
        # Configurar tamaños del splitter (50% cada uno)
        main_splitter.setSizes([400, 400])
        main_layout.addWidget(main_splitter, 1)
        
        # --- PANEL INFERIOR: Alertas y Resumen (COMPACTO) ---
        bottom_splitter = QSplitter(Qt.Horizontal)
        bottom_splitter.setHandleWidth(3)
        
        # Panel de alertas (COMPACTO)
        alertas_panel = QWidget()
        alertas_layout = QVBoxLayout(alertas_panel)
        alertas_layout.setContentsMargins(6, 6, 6, 6)
        alertas_layout.setSpacing(6)
        
        alertas_group = QGroupBox("Alertas")
        alertas_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        alertas_group.setMaximumHeight(150)  # REDUCIDO
        
        alertas_inner = QVBoxLayout(alertas_group)
        alertas_inner.setSpacing(6)
        alertas_inner.setContentsMargins(8, 8, 8, 8)
        
        # Área de scroll para alertas
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("inventarioAlertsScroll")
        scroll_area.setMaximumHeight(100)
        
        self.alertas_widget = QWidget()
        self.alertas_layout = QVBoxLayout(self.alertas_widget)
        self.alertas_layout.setSpacing(6)
        self.alertas_layout.setContentsMargins(4, 4, 4, 4)
        
        scroll_area.setWidget(self.alertas_widget)
        alertas_inner.addWidget(scroll_area)
        alertas_layout.addWidget(alertas_group)
        bottom_splitter.addWidget(alertas_panel)
        
        # Panel de resumen (COMPACTO)
        resumen_panel = QWidget()
        resumen_layout = QVBoxLayout(resumen_panel)
        resumen_layout.setContentsMargins(6, 6, 6, 6)
        resumen_layout.setSpacing(6)
        
        resumen_group = QGroupBox("Resumen")
        resumen_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        resumen_group.setMaximumHeight(150)  # REDUCIDO
        
        resumen_inner = QVBoxLayout(resumen_group)
        resumen_inner.setSpacing(6)
        resumen_inner.setContentsMargins(8, 8, 8, 8)
        
        # Grid para métricas (COMPACTO)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        self.resumen_indicadores = {}
        
        metricas = [
            ("Ingredientes", "0", 0, 0),
            ("Productos", "0", 0, 1),
            ("Valor Total", "$0", 1, 0),
            ("Alertas", "0", 1, 1)
        ]
        
        for texto, valor, fila, columna in metricas:
            indicador = QLabel(valor)
            indicador.setAlignment(Qt.AlignCenter)
            indicador.setProperty("role", "metricBadge")

            titulo = QLabel(texto)
            titulo.setAlignment(Qt.AlignCenter)
            titulo.setProperty("role", "field")
            
            grid_layout.addWidget(indicador, fila*2, columna)
            grid_layout.addWidget(titulo, fila*2+1, columna)
            self.resumen_indicadores[texto] = indicador
        
        resumen_inner.addLayout(grid_layout)
        resumen_layout.addWidget(resumen_group)
        bottom_splitter.addWidget(resumen_panel)
        
        # Configurar tamaños del splitter inferior (60% alertas, 40% resumen)
        bottom_splitter.setSizes([180, 120])  # REDUCIDO
        main_layout.addWidget(bottom_splitter)
    
    def apply_specific_styles(self):
        """Aplica estilos específicos para este widget"""
        # Convertir estilos inline a objectName/property para QSS global
        self.setObjectName("inventarioWidget")
        try:
            self.ingredientes_table.setObjectName("ingredientesTable")
            self.productos_table.setObjectName("productosTable")
        except Exception:
            pass

        # Botones de acción usan el estilo global de módulos
        self.ing_refresh_btn.setProperty("role", "action")
        self.ing_export_btn.setProperty("role", "action")
        self.prod_refresh_btn.setProperty("role", "action")
        self.prod_export_btn.setProperty("role", "action")
    
    def setup_ui_loaded(self):
        """Configurar interfaz cuando se carga desde .ui"""
        # Configurar tablas si existen
        if hasattr(self, 'ingredientes_table'):
            self.ingredientes_table.verticalHeader().setDefaultSectionSize(24)
            # Forzar que las tablas se expandan
            self.ingredientes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        if hasattr(self, 'productos_table'):
            self.productos_table.verticalHeader().setDefaultSectionSize(24)
            self.productos_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def connect_signals(self):
        """Conecta todas las señales"""
        # CORRECCIÓN DEL BUG: Ambos botones de actualizar llaman a load_data() para refrescar todo
        self.ing_refresh_btn.clicked.connect(self.load_data)
        self.ing_export_btn.clicked.connect(self.exportar_ingredientes)
        
        self.prod_refresh_btn.clicked.connect(self.load_data)
        self.prod_export_btn.clicked.connect(self.exportar_productos)
    
    def load_data(self):
        """Carga todos los datos - CORREGIDO PARA ACTUALIZAR ALERTAS"""
        print("🔄 Cargando todos los datos de inventario...")
        self.cargar_ingredientes()
        self.cargar_productos()
        # CORRECCIÓN: Asegurar que las alertas se actualicen siempre
        self.cargar_alertas()
        self.cargar_resumen()
    
    def cargar_ingredientes(self):
        """Carga los ingredientes REALES desde la base de datos - CORREGIDO"""
        try:
            print("Cargando ingredientes REALES desde BD...")
            
            if not self.inventario_manager:
                QMessageBox.warning(self, "Error", "No se pudo inicializar el manager de inventario")
                return
            
            # Obtener datos REALES de inventario de ingredientes
            try:
                ingredientes = self.inventario_manager.obtener_inventario_ingredientes()
            except Exception as e:
                print(f"Error con inventario_manager.obtener_inventario_ingredientes: {e}")
                # Intentar obtener datos directamente de la base de datos
                ingredientes = self._obtener_ingredientes_directo()
            
            if not ingredientes:
                print("No se encontraron ingredientes en la base de datos")
                self.ingredientes_table.setRowCount(1)
                self.ingredientes_table.setItem(0, 0, QTableWidgetItem("No hay ingredientes en la base de datos"))
                self.ingredientes_table.item(0, 0).setTextAlignment(Qt.AlignCenter)
                self.ingredientes_table.setSpan(0, 0, 1, 5)
                self.resumen_indicadores["Ingredientes"].setText("0")
                return
            
            print(f"{len(ingredientes)} ingredientes REALES cargados")
            
            self.ingredientes_table.setRowCount(len(ingredientes))
            
            alertas_bajas = 0
            
            for i, ingrediente in enumerate(ingredientes):
                # Extraer datos con nombres de campo CORREGIDOS
                nombre = ingrediente.get('nombre', ingrediente.get('ingrediente_nombre', 'Desconocido'))
                stock = ingrediente.get('cantidad_actual', ingrediente.get('stock', ingrediente.get('cantidad_disponible', 0)))
                unidad = ingrediente.get('unidad', ingrediente.get('abreviatura', ingrediente.get('unidad_medida', 'unidad')))
                minimo = ingrediente.get('cantidad_minima', ingrediente.get('minimo', ingrediente.get('stock_minimo', 0)))
                
                # Convertir a números
                try:
                    stock_num = float(stock) if stock is not None else 0
                    minimo_num = float(minimo) if minimo is not None else 0
                except (ValueError, TypeError):
                    stock_num = 0
                    minimo_num = 0
                
                # Determinar estado
                if stock_num >= minimo_num:
                    estado = "OK"
                elif stock_num > minimo_num * 0.5:
                    estado = "BAJO"
                    alertas_bajas += 1
                else:
                    estado = "CRÍTICO"
                    alertas_bajas += 1
                
                # Mostrar en tabla
                self.ingredientes_table.setItem(i, 0, QTableWidgetItem(str(nombre)))
                self.ingredientes_table.setItem(i, 1, QTableWidgetItem(f"{stock_num:.2f}" if isinstance(stock_num, float) else str(stock_num)))
                self.ingredientes_table.setItem(i, 2, QTableWidgetItem(str(unidad)))
                self.ingredientes_table.setItem(i, 3, QTableWidgetItem(f"{minimo_num:.2f}" if isinstance(minimo_num, float) else str(minimo_num)))
                
                estado_item = QTableWidgetItem(estado)
                estado_item.setTextAlignment(Qt.AlignCenter)
                
                # Colorear según estado
                if estado == 'OK':
                    estado_item.setBackground(QColor(220, 255, 220))
                    estado_item.setForeground(QColor(0, 0, 0))
                elif estado == 'BAJO':
                    estado_item.setBackground(QColor(255, 255, 200))
                    estado_item.setForeground(QColor(0, 0, 0))
                else:  # CRÍTICO
                    estado_item.setBackground(QColor(255, 220, 220))
                    estado_item.setForeground(QColor(0, 0, 0))
                
                self.ingredientes_table.setItem(i, 4, estado_item)
                
                # Centrar columnas numéricas
                for col in [1, 2, 3]:
                    cell_item = self.ingredientes_table.item(i, col)
                    if cell_item:
                        cell_item.setTextAlignment(Qt.AlignCenter)
            
            # Actualizar resumen
            self.resumen_indicadores["Ingredientes"].setText(str(len(ingredientes)))
            # NOTA: No actualizamos "Alertas" aquí, se actualizará en cargar_alertas()
            
            print(f"Inventario de ingredientes actualizado. Alertas: {alertas_bajas}")
            
        except Exception as e:
            print(f"Error cargando ingredientes REALES: {e}")
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los ingredientes:\n{str(e)}")
    
    def _obtener_ingredientes_directo(self):
        """Obtiene ingredientes directamente desde la BD cuando el manager falla"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('data/inventario.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Consulta que une ingredientes con su inventario (columnas reales)
            cursor.execute('''
                SELECT 
                    i.id,
                    i.nombre,
                    COALESCE(inv.cantidad_actual, 0) as cantidad_actual,
                    um.abreviatura as unidad,
                    i.stock_minimo,
                    i.activo
                FROM ingredientes i
                LEFT JOIN inventario_ingredientes inv ON i.id = inv.ingrediente_id
                LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE i.activo = 1
                ORDER BY i.nombre
            ''')
            
            resultados = cursor.fetchall()
            conn.close()
            
            ingredientes = []
            for row in resultados:
                ingredientes.append({
                    'id': row['id'],
                    'nombre': row['nombre'],
                    'cantidad_actual': row['cantidad_actual'],
                    'unidad': row['unidad'],
                    'stock_minimo': row['stock_minimo'],
                    'activo': row['activo']
                })
            
            return ingredientes
        except Exception as e:
            print(f"Error en consulta directa de ingredientes: {e}")
            return []
    
    def cargar_productos(self):
        """Carga los productos REALES desde la base de datos"""
        try:
            print("Cargando productos REALES desde BD...")
            
            if not self.inventario_manager:
                QMessageBox.warning(self, "Error", "No se pudo inicializar el manager de inventario")
                return
            
            # Obtener datos REALES de inventario de productos
            try:
                productos = self.inventario_manager.obtener_inventario_productos()
            except Exception as e:
                print(f"Error con inventario_manager.obtener_inventario_productos: {e}")
                # Intentar obtener datos directamente
                productos = self._obtener_productos_directo()
            
            if not productos:
                print("No se encontraron productos en la base de datos")
                self.productos_table.setRowCount(1)
                self.productos_table.setItem(0, 0, QTableWidgetItem("No hay productos en la base de datos"))
                self.productos_table.item(0, 0).setTextAlignment(Qt.AlignCenter)
                self.productos_table.setSpan(0, 0, 1, 5)
                self.resumen_indicadores["Productos"].setText("0")
                self.resumen_indicadores["Valor Total"].setText("$0.00")
                return
            
            print(f"{len(productos)} productos REALES cargados")
            
            self.productos_table.setRowCount(len(productos))
            
            valor_total = 0
            
            for i, producto in enumerate(productos):
                # Extraer datos con nombres de campo CORREGIDOS
                nombre = producto.get('nombre', producto.get('producto_nombre', 'Desconocido'))
                disponible = producto.get('cantidad_disponible', producto.get('disponible', producto.get('stock', 0)))
                unidad = producto.get('unidad_venta', producto.get('unidad', 'unidad'))
                precio = producto.get('precio_venta', producto.get('precio', 0))
                
                # Convertir a números
                try:
                    disponible_num = float(disponible) if disponible is not None else 0
                    precio_num = float(precio) if precio is not None else 0
                except (ValueError, TypeError):
                    disponible_num = 0
                    precio_num = 0
                
                valor = disponible_num * precio_num
                valor_total += valor
                
                # Mostrar en tabla
                self.productos_table.setItem(i, 0, QTableWidgetItem(str(nombre)))
                self.productos_table.setItem(i, 1, QTableWidgetItem(str(int(disponible_num)) if disponible_num.is_integer() else f"{disponible_num:.2f}"))
                self.productos_table.setItem(i, 2, QTableWidgetItem(str(unidad)))
                self.productos_table.setItem(i, 3, QTableWidgetItem(f"${precio_num:.2f}"))
                self.productos_table.setItem(i, 4, QTableWidgetItem(f"${valor:.2f}"))
                
                # Centrar columnas numéricas
                for col in [1, 2, 3, 4]:
                    cell_item = self.productos_table.item(i, col)
                    if cell_item:
                        cell_item.setTextAlignment(Qt.AlignCenter)
            
            # Actualizar resumen
            self.resumen_indicadores["Productos"].setText(str(len(productos)))
            self.resumen_indicadores["Valor Total"].setText(f"${valor_total:.2f}")
            
            print(f"Inventario de productos actualizado. Valor total: ${valor_total:.2f}")
            
        except Exception as e:
            print(f"Error cargando productos REALES: {e}")
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los productos:\n{str(e)}")
    
    def _obtener_productos_directo(self):
        """Obtiene productos directamente desde la BD cuando el manager falla"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect('data/inventario.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Consulta que une productos con su inventario
            cursor.execute('''
                SELECT 
                    p.id,
                    p.nombre,
                    COALESCE(ip.cantidad_disponible, 0) as cantidad_disponible,
                    p.unidad_venta as unidad,
                    p.precio_venta,
                    p.activo
                FROM productos p
                LEFT JOIN inventario_productos ip ON p.id = ip.producto_id
                WHERE p.activo = 1
                ORDER BY p.nombre
            ''')
            
            resultados = cursor.fetchall()
            conn.close()
            
            productos = []
            for row in resultados:
                productos.append({
                    'id': row['id'],
                    'nombre': row['nombre'],
                    'cantidad_disponible': row['cantidad_disponible'],
                    'unidad_venta': row['unidad'],
                    'precio_venta': row['precio_venta'],
                    'activo': row['activo']
                })
            
            return productos
        except Exception as e:
            print(f"Error en consulta directa de productos: {e}")
            return []
    
    def cargar_alertas(self):
        """Carga las alertas REALES de stock bajo - CORREGIDO PARA ACTUALIZARSE"""
        try:
            print("Cargando alertas REALES...")
            
            # Limpiar alertas anteriores
            for i in reversed(range(self.alertas_layout.count())):
                widget = self.alertas_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            
            if not self.inventario_manager:
                print("No hay manager de inventario")
                return
            
            # Obtener alertas REALES de inventario
            try:
                alertas = self.inventario_manager.obtener_alertas_inventario()
            except Exception as e:
                print(f"Error obteniendo alertas: {e}")
                # Generar alertas basadas en los datos cargados en las tablas
                alertas = self._generar_alertas_desde_tablas()
            
            if not alertas:
                # Mostrar mensaje de que no hay alertas
                alerta_widget = QFrame()
                alerta_widget.setFrameStyle(QFrame.Box)
                alerta_widget.setObjectName("inventarioAlertFrame")
                alerta_widget.setProperty("alertType", "ok")
                alerta_widget.setMinimumHeight(30)
                
                alerta_layout = QHBoxLayout(alerta_widget)
                alerta_layout.setSpacing(8)
                
                icono = QLabel("✓")
                icono.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                
                mensaje = QLabel("No hay alertas de inventario")
                mensaje.setProperty("role", "alertText")
                mensaje.setProperty("emphasis", "medium")
                mensaje.setWordWrap(True)
                
                alerta_layout.addWidget(icono)
                alerta_layout.addWidget(mensaje, 1)
                
                self.alertas_layout.addWidget(alerta_widget)
                # Actualizar contador de alertas en resumen
                self.resumen_indicadores["Alertas"].setText("0")
                return
            
            print(f"{len(alertas)} alertas REALES cargadas")
            
            for alerta in alertas:
                alerta_widget = QFrame()
                alerta_widget.setFrameStyle(QFrame.Box)
                tipo = alerta.get('tipo', 'ADVERTENCIA')
                mensaje_texto = alerta.get('mensaje', 'Alerta de stock')
                alerta_widget.setObjectName("inventarioAlertFrame")
                alerta_widget.setProperty("alertType", "critical" if tipo == 'CRÍTICO' else "warning")
                alerta_widget.setMinimumHeight(30)
                
                alerta_layout = QHBoxLayout(alerta_widget)
                alerta_layout.setSpacing(8)
                
                icono = QLabel("!" if tipo == 'CRÍTICO' else "!")
                icono.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                
                mensaje = QLabel(mensaje_texto)
                mensaje.setProperty("role", "alertText")
                mensaje.setProperty("emphasis", "medium")
                mensaje.setWordWrap(True)
                
                alerta_layout.addWidget(icono)
                alerta_layout.addWidget(mensaje, 1)
                
                self.alertas_layout.addWidget(alerta_widget)
            
            # CORRECCIÓN: Actualizar resumen con el número real de alertas
            self.resumen_indicadores["Alertas"].setText(str(len(alertas)))
            
        except Exception as e:
            print(f"Error cargando alertas: {e}")
    
    def _generar_alertas_desde_tablas(self):
        """Genera alertas basadas en los datos de las tablas - UTILIZADA COMO FALLBACK"""
        alertas = []
        
        # Revisar tabla de ingredientes
        for row in range(self.ingredientes_table.rowCount()):
            estado_item = self.ingredientes_table.item(row, 4)
            if estado_item and estado_item.text() in ['BAJO', 'CRÍTICO']:
                nombre_item = self.ingredientes_table.item(row, 0)
                stock_item = self.ingredientes_table.item(row, 1)
                minimo_item = self.ingredientes_table.item(row, 3)
                unidad_item = self.ingredientes_table.item(row, 2)
                
                if nombre_item and stock_item and minimo_item and unidad_item:
                    tipo = 'CRÍTICO' if estado_item.text() == 'CRÍTICO' else 'ADVERTENCIA'
                    mensaje = f"{nombre_item.text()} {tipo.lower()} ({stock_item.text()}/{minimo_item.text()} {unidad_item.text()})"
                    alertas.append({'tipo': tipo, 'mensaje': mensaje})
        
        return alertas
    
    def cargar_resumen(self):
        """Carga el resumen REAL del inventario"""
        # Los indicadores ya se actualizan en los otros métodos
        pass
    
    def exportar_ingredientes(self):
        """Exporta el inventario REAL de ingredientes a CSV"""
        try:
            from datetime import datetime
            
            if self.ingredientes_table.rowCount() == 0:
                QMessageBox.warning(self, "Sin datos", "No hay datos de ingredientes para exportar")
                return
            
            # Nombre del archivo
            fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nombre_archivo = f"inventario_ingredientes_{fecha_actual}.csv"
            
            # Crear contenido CSV
            contenido = "Nombre,Stock,Unidad,Mínimo,Estado\n"
            
            for row in range(self.ingredientes_table.rowCount()):
                fila = []
                for col in range(self.ingredientes_table.columnCount()):
                    item = self.ingredientes_table.item(row, col)
                    if item:
                        fila.append(item.text())
                contenido += ",".join(fila) + "\n"
            
            # Guardar archivo
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            QMessageBox.information(self, "Exportación Exitosa",
                f"Inventario de ingredientes REAL exportado a:\n\n{nombre_archivo}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación",
                f"No se pudo exportar el inventario:\n{str(e)}")
    
    def exportar_productos(self):
        """Exporta el inventario REAL de productos a CSV"""
        try:
            from datetime import datetime
            
            if self.productos_table.rowCount() == 0:
                QMessageBox.warning(self, "Sin datos", "No hay datos de productos para exportar")
                return
            
            # Nombre del archivo
            fecha_actual = datetime.now().strftime("%Y-%m-%d_%H-%M")
            nombre_archivo = f"inventario_productos_{fecha_actual}.csv"
            
            # Crear contenido CSV
            contenido = "Nombre,Disponible,Unidad,Precio,Valor\n"
            
            for row in range(self.productos_table.rowCount()):
                fila = []
                for col in range(self.productos_table.columnCount()):
                    item = self.productos_table.item(row, col)
                    if item:
                        fila.append(item.text())
                contenido += ",".join(fila) + "\n"
            
            # Guardar archivo
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            QMessageBox.information(self, "Exportación Exitosa",
                f"Inventario de productos REAL exportado a:\n\n{nombre_archivo}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación",
                f"No se pudo exportar el inventario:\n{str(e)}")
