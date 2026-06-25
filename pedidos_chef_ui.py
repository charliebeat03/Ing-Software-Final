# modules/pedidos_chef_ui.py - Copia corregida
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QFrame, QGridLayout,
    QComboBox, QTextEdit, QSplitter, QSizePolicy,
    QApplication, QDoubleSpinBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from modules.pedidos_chef import PedidosChefManager
from modules.catalogos import CatalogoManager
from modules.inventario import InventarioManager
from utils.date_utils import get_current_date, format_date

class PedidosChefWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Variables para seguimiento
        self.total_pedidos = 0.0
        self.ingrediente_actual = None
        
        self.pedidos_manager = PedidosChefManager()
        self.catalogos_manager = CatalogoManager()
        self.inventario_manager = InventarioManager()
        
        # Crear interfaz compacta
        self.create_compact_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
        # Configurar tablas
        self.setup_tables()
        
        # Aplicar estilos
        self.apply_specific_styles()
        
        # Timer para actualización periódica
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.force_refresh_all)
        self.update_timer.start(15000)

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.pedidos_manager = services.get("pedidos_chef")
            self.catalogos_manager = services.get("catalogos")
            self.inventario_manager = services.get("inventario")
            try:
                self.force_refresh_all()
            except Exception:
                pass

    def refresh_data(self):
        self.force_refresh_all()
    
    def create_compact_ui(self):
        """Crea la interfaz compacta y funcional"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # ==================== ENCABEZADO ====================
        header_frame = QFrame()
        header_frame.setObjectName("pedidosHeader")
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Pedidos de cocina")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setProperty("role", "title")
        
        self.fecha_label = QLabel()
        self.fecha_label.setProperty("role", "muted")
        
        # Indicador de actualización automática
        self.auto_update_label = QLabel("Actualización automática cada 15 s")
        self.auto_update_label.setProperty("role", "indicator")
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.fecha_label)
        header_layout.addWidget(self.auto_update_label)
        
        main_layout.addWidget(header_frame)
        
        # ==================== SPLITTER PRINCIPAL ====================
        splitter = QSplitter(Qt.Horizontal)
        
        # ==================== PANEL IZQUIERDO - FORMULARIO ====================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(8)
        
        # Grupo: Nuevo Pedido
        nuevo_pedido_group = QGroupBox("Nuevo pedido")
        nuevo_pedido_layout = QVBoxLayout(nuevo_pedido_group)
        nuevo_pedido_layout.setSpacing(6)
        
        # Formulario en GRID
        form_grid = QGridLayout()
        form_grid.setVerticalSpacing(6)
        form_grid.setHorizontalSpacing(8)
        
        # Ingrediente
        ingrediente_label = QLabel("Ingrediente:")
        ingrediente_label.setMinimumWidth(70)
        ingrediente_label.setProperty("role", "field")
        self.ingrediente_combo = QComboBox()
        self.ingrediente_combo.setMinimumHeight(32)
        form_grid.addWidget(ingrediente_label, 0, 0)
        form_grid.addWidget(self.ingrediente_combo, 0, 1, 1, 2)
        
        # Información de stock
        stock_label = QLabel("Stock:")
        stock_label.setProperty("role", "field")
        self.stock_info_label = QLabel("Disponible: -")
        self.stock_info_label.setMinimumHeight(24)
        self.stock_info_label.setProperty("emphasis", "strong")
        form_grid.addWidget(stock_label, 1, 0)
        form_grid.addWidget(self.stock_info_label, 1, 1, 1, 2)
        
        # Cantidad
        cantidad_label = QLabel("Cantidad:")
        cantidad_label.setProperty("role", "field")
        self.cantidad_input = QDoubleSpinBox()
        self.cantidad_input.setRange(0.01, 10000)
        self.cantidad_input.setDecimals(3)
        self.cantidad_input.setValue(0.5)
        self.cantidad_input.setMinimumHeight(32)
        self.cantidad_input.setMinimumWidth(100)
        
        self.unidad_label = QLabel("kg")
        self.unidad_label.setMinimumWidth(30)
        self.unidad_label.setProperty("emphasis", "strong")
        
        form_grid.addWidget(cantidad_label, 2, 0)
        form_grid.addWidget(self.cantidad_input, 2, 1)
        form_grid.addWidget(self.unidad_label, 2, 2)
        
        # Motivo
        motivo_label = QLabel("Motivo:")
        motivo_label.setProperty("role", "field")
        self.motivo_input = QTextEdit()
        self.motivo_input.setMaximumHeight(70)
        self.motivo_input.setPlaceholderText("Opcional...")
        
        form_grid.addWidget(motivo_label, 3, 0)
        form_grid.addWidget(self.motivo_input, 3, 1, 1, 2)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.agregar_btn = QPushButton("Registrar pedido")
        self.agregar_btn.setMinimumHeight(32)
        self.agregar_btn.setMinimumWidth(100)
        self.agregar_btn.setProperty("role", "action")
        
        self.cancelar_btn = QPushButton("Cancelar último")
        self.cancelar_btn.setMinimumHeight(32)
        self.cancelar_btn.setMinimumWidth(120)
        self.cancelar_btn.setProperty("role", "action")
        
        button_layout.addWidget(self.agregar_btn)
        button_layout.addWidget(self.cancelar_btn)
        button_layout.addStretch()
        
        form_grid.addLayout(button_layout, 4, 0, 1, 3)
        
        nuevo_pedido_layout.addLayout(form_grid)
        left_layout.addWidget(nuevo_pedido_group)
        
        # Información
        info_group = QGroupBox("Información")
        info_group_layout = QVBoxLayout(info_group)
        info_text = QLabel(
            "• Los pedidos se acumulan por día.\n"
            "• El stock se descuenta automáticamente.\n"
            "• Puede cancelar el último pedido.\n"
            "• La vista se actualiza cada 15 segundos."
        )
        info_text.setWordWrap(True)
        info_text.setProperty("role", "hint")
        info_group_layout.addWidget(info_text)
        
        left_layout.addWidget(info_group)
        left_layout.addStretch()
        
        # ==================== PANEL DERECHO - TABLAS ====================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(8)
        
        # Panel de totales
        totales_frame = QFrame()
        totales_frame.setObjectName("totalesFrame")
        totales_layout = QHBoxLayout(totales_frame)
        
        self.total_ingredientes_label = QLabel("Total hoy: 0.000")
        self.total_ingredientes_label.setProperty("role", "metricBadge")
        
        self.actualizar_btn = QPushButton("Actualizar")
        self.actualizar_btn.setMinimumHeight(32)
        self.actualizar_btn.setMinimumWidth(120)
        self.actualizar_btn.setProperty("role", "action")
        
        totales_layout.addWidget(self.total_ingredientes_label)
        totales_layout.addStretch()
        totales_layout.addWidget(self.actualizar_btn)
        
        right_layout.addWidget(totales_frame)
        
        # Tabla de pedidos acumulados del día (TABLA SUPERIOR)
        pedidos_group = QGroupBox("Pedidos acumulados del día")
        pedidos_layout = QVBoxLayout(pedidos_group)
        
        self.pedidos_table = QTableWidget()
        self.pedidos_table.setColumnCount(6)
        self.pedidos_table.setHorizontalHeaderLabels(["Ingrediente", "Cantidad", "Unidad", "Pedidos", "Última Hora", "ID"])
        self.pedidos_table.horizontalHeader().setStretchLastSection(True)
        
        pedidos_layout.addWidget(self.pedidos_table)
        right_layout.addWidget(pedidos_group)
        
        # Botones de tabla
        table_buttons = QHBoxLayout()
        table_buttons.setSpacing(8)
        
        self.detalle_btn = QPushButton("Ver Detalle")
        self.detalle_btn.setMinimumHeight(32)
        self.detalle_btn.setProperty("role", "action")
        
        self.limpiar_btn = QPushButton("Limpiar Selección")
        self.limpiar_btn.setMinimumHeight(32)
        self.limpiar_btn.setProperty("role", "action")
        
        table_buttons.addWidget(self.detalle_btn)
        table_buttons.addWidget(self.limpiar_btn)
        table_buttons.addStretch()
        
        right_layout.addLayout(table_buttons)
        
        # Tabla de historial detallado (TABLA INFERIOR)
        historial_group = QGroupBox("HISTORIAL DETALLADO")
        historial_layout = QVBoxLayout(historial_group)
        
        self.historial_table = QTableWidget()
        # SOLO 6 COLUMNAS VISIBLES - quitamos la columna "Acción" del display
        self.historial_table.setColumnCount(6)
        self.historial_table.setHorizontalHeaderLabels(["ID", "Hora", "Ingrediente", "Cantidad", "Unidad", "Motivo"])
        
        historial_layout.addWidget(self.historial_table)
        right_layout.addWidget(historial_group)
        
        # ==================== CONFIGURAR SPLITTER ====================
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])
        
        main_layout.addWidget(splitter, 1)
        
        # Guardar referencia
        self.splitter = splitter

    def apply_specific_styles(self):
        """Aplica estilos específicos"""
        self.setObjectName("pedidosChefWidget")
        try:
            self.pedidos_table.setObjectName("pedidosTable")
            self.historial_table.setObjectName("historialTable")
        except Exception:
            pass
        self.total_ingredientes_label.setProperty("role", "metricBadge")
        self.actualizar_btn.setProperty("role", "action")
        self.detalle_btn.setProperty("role", "action")
        self.limpiar_btn.setProperty("role", "action")
        self.pedidos_table.setAlternatingRowColors(True)
        self.historial_table.setAlternatingRowColors(True)

    def connect_signals(self):
        """Conecta todas las señales"""
        self.ingrediente_combo.currentIndexChanged.connect(self.actualizar_stock_info)
        self.agregar_btn.clicked.connect(self.agregar_pedido)
        self.cancelar_btn.clicked.connect(self.cancelar_ultimo_pedido)
        self.actualizar_btn.clicked.connect(self.force_refresh_all)
        self.detalle_btn.clicked.connect(self.cargar_historial_detalle)
        self.limpiar_btn.clicked.connect(self.limpiar_seleccion)

    def load_initial_data(self):
        """Carga los datos iniciales"""
        self.actualizar_fecha()
        self.cargar_ingredientes()
        self.force_refresh_all()

    def setup_tables(self):
        """Configura las tablas"""
        header = self.pedidos_table.horizontalHeader()
        header.setDefaultSectionSize(100)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)

        header = self.historial_table.horizontalHeader()
        header.setDefaultSectionSize(80)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.Stretch)

    def actualizar_fecha(self):
        try:
            fecha_actual = datetime.now().date()
            fecha_formateada = fecha_actual.strftime("%d/%m/%Y")
            self.fecha_label.setText(f"Fecha: {fecha_formateada}")
        except Exception as e:
            print(f"Error actualizando fecha: {e}")
            self.fecha_label.setText("Fecha: No disponible")

    def cargar_ingredientes(self):
        try:
            print("🔄 PedidosChefWidget.cargar_ingredientes...")
            ingredientes_data = self.pedidos_manager.cargar_ingredientes()
            self.ingrediente_combo.clear()
            
            if not ingredientes_data:
                print("⚠️ No se encontraron ingredientes")
                self.ingrediente_combo.addItem("No hay ingredientes disponibles", -1)
                return
            
            print(f"✅ {len(ingredientes_data)} ingredientes encontrados")
            
            for ing_id, nombre, unidad in ingredientes_data:
                display_text = f"{nombre} ({unidad})"
                self.ingrediente_combo.addItem(display_text, ing_id)
            
            if self.ingrediente_combo.count() > 0:
                self.ingrediente_combo.setCurrentIndex(0)
                self.actualizar_stock_info()
                
        except Exception as e:
            print(f"❌ ERROR cargando ingredientes: {str(e)}")
            self.ingrediente_combo.addItem("Error cargando ingredientes", -1)

    def actualizar_stock_info(self):
        try:
            index = self.ingrediente_combo.currentIndex()
            if index < 0:
                return
            
            ingrediente_id = self.ingrediente_combo.itemData(index)
            if ingrediente_id is None or ingrediente_id == -1:
                self.stock_info_label.setText("Disponible: -")
                self.unidad_label.setText("kg")
                return
            
            ingredientes_data = self.pedidos_manager.cargar_ingredientes()
            ingrediente_actual = None
            
            for ing_id, nombre, unidad in ingredientes_data:
                if ing_id == ingrediente_id:
                    ingrediente_actual = {'id': ing_id, 'nombre': nombre, 'unidad': unidad}
                    break
            
            if not ingrediente_actual:
                self.stock_info_label.setText("Disponible: -")
                self.unidad_label.setText("kg")
                return
            
            stock_disponible = 0
            try:
                inventario = self.inventario_manager.obtener_inventario_ingredientes()
                for item in inventario:
                    if item.get('id') == ingrediente_id or item.get('nombre') == ingrediente_actual['nombre']:
                        stock_disponible = item.get('cantidad_actual', 0)
                        break
            except Exception as e:
                print(f"⚠️ Error obteniendo inventario: {e}")
            
            self.unidad_label.setText(ingrediente_actual.get('unidad', 'kg'))
            self.stock_info_label.setText(f"Disponible: {stock_disponible} {ingrediente_actual.get('unidad', 'kg')}")
            
        except Exception as e:
            print(f"❌ Error actualizando stock: {e}")
            self.stock_info_label.setText("Disponible: Error")

    def cargar_pedidos_dia(self):
        try:
            print("🔄 PedidosChefWidget.cargar_pedidos_dia()...")
            pedidos = self.pedidos_manager.obtener_pedidos_dia()
            
            print(f"📊 Pedidos acumulados obtenidos: {len(pedidos)} registros")
            
            self.pedidos_table.setRowCount(0)
            
            total_cantidad = 0.0
            
            for i, pedido in enumerate(pedidos):
                ingrediente_nombre = pedido.get('ingrediente_nombre', 'Desconocido')
                cantidad = pedido.get('cantidad', 0)
                unidad = pedido.get('unidad', 'unidad')
                pedidos_count = pedido.get('pedidos_count', 0)
                ultima_hora = pedido.get('ultima_hora', '--:--')
                pedido_id = pedido.get('id', '')
                
                try:
                    cantidad_num = float(cantidad)
                except (ValueError, TypeError):
                    cantidad_num = 0
                
                self.pedidos_table.insertRow(i)
                
                self.pedidos_table.setItem(i, 0, QTableWidgetItem(str(ingrediente_nombre)))
                self.pedidos_table.setItem(i, 1, QTableWidgetItem(f"{cantidad_num:.3f}"))
                self.pedidos_table.setItem(i, 2, QTableWidgetItem(str(unidad)))
                self.pedidos_table.setItem(i, 3, QTableWidgetItem(str(pedidos_count)))
                self.pedidos_table.setItem(i, 4, QTableWidgetItem(str(ultima_hora)))
                self.pedidos_table.setItem(i, 5, QTableWidgetItem(str(pedido_id)))
                
                for col in [1, 2, 3, 4, 5]:
                    item = self.pedidos_table.item(i, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
                
                total_cantidad += cantidad_num
            
            self.total_ingredientes_label.setText(f"Total hoy: {total_cantidad:.3f}")
            
            for i in range(self.pedidos_table.rowCount()):
                self.pedidos_table.setRowHeight(i, 24)
            
            if len(pedidos) == 0:
                print("ℹ️ No hay pedidos para mostrar hoy")
                self.pedidos_table.setRowCount(1)
                self.pedidos_table.setItem(0, 0, QTableWidgetItem("No hay pedidos registrados hoy"))
                self.pedidos_table.item(0, 0).setTextAlignment(Qt.AlignCenter)
                self.pedidos_table.setSpan(0, 0, 1, 6)
            
            print(f"✅ Tabla de pedidos actualizada. Total: {total_cantidad:.3f}")
            
        except Exception as e:
            print(f"❌ Error cargando pedidos del día: {e}")
            import traceback
            traceback.print_exc()

    def cargar_historial_detalle(self):
        try:
            print("🔄 PedidosChefWidget.cargar_historial_detalle()...")
            detalles = self.pedidos_manager.obtener_detalle_pedidos_dia()
            
            print(f"📊 Historial obtenido: {len(detalles)} registros")
            
            self.historial_table.setRowCount(0)
            
            for i, item in enumerate(detalles):
                detalle_id = item.get('detalle_id', '')
                hora = item.get('hora', '--:--')
                ingrediente_nombre = item.get('ingrediente_nombre', 'Desconocido')
                cantidad = item.get('cantidad', 0)
                unidad = item.get('unidad', 'unidad')
                motivo = item.get('motivo', 'Sin motivo')
                
                try:
                    cantidad_num = float(cantidad)
                except (ValueError, TypeError):
                    cantidad_num = 0
                
                if isinstance(hora, str) and len(hora) > 8:
                    hora = hora[:8]
                
                self.historial_table.insertRow(i)
                
                self.historial_table.setItem(i, 0, QTableWidgetItem(str(detalle_id)))
                self.historial_table.setItem(i, 1, QTableWidgetItem(str(hora)))
                self.historial_table.setItem(i, 2, QTableWidgetItem(str(ingrediente_nombre)))
                self.historial_table.setItem(i, 3, QTableWidgetItem(f"{cantidad_num:.3f}"))
                self.historial_table.setItem(i, 4, QTableWidgetItem(str(unidad)))
                self.historial_table.setItem(i, 5, QTableWidgetItem(str(motivo)))
                
                for col in [0, 1, 3, 4]:
                    item_widget = self.historial_table.item(i, col)
                    if item_widget:
                        item_widget.setTextAlignment(Qt.AlignCenter)
            
            for i in range(self.historial_table.rowCount()):
                self.historial_table.setRowHeight(i, 24)
            
            if len(detalles) == 0:
                print("ℹ️ No hay historial para mostrar hoy")
                self.historial_table.setRowCount(1)
                self.historial_table.setItem(0, 2, QTableWidgetItem("No hay historial de pedidos hoy"))
                self.historial_table.item(0, 2).setTextAlignment(Qt.AlignCenter)
                self.historial_table.setSpan(0, 2, 1, 4)
            
            print(f"✅ Historial actualizado con {len(detalles)} registros")
            
        except Exception as e:
            print(f"❌ Error cargando historial: {e}")
            import traceback
            traceback.print_exc()

    def limpiar_seleccion(self):
        self.pedidos_table.clearSelection()
        self.historial_table.clearSelection()

    def force_refresh_all(self):
        print("🔄 FORZANDO ACTUALIZACIÓN COMPLETA...")
        
        try:
            self.cargar_pedidos_dia()
            self.cargar_historial_detalle()
            
            if self.ingrediente_combo.currentIndex() >= 0:
                self.actualizar_stock_info()
            
            self.actualizar_fecha()
            
            print("✅ Actualización completa exitosa")
            
        except Exception as e:
            print(f"❌ Error en actualización forzada: {e}")

    def agregar_pedido(self):
        try:
            if self.ingrediente_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Validación", "Debe seleccionar un ingrediente")
                return
            
            ingrediente_id = self.ingrediente_combo.itemData(self.ingrediente_combo.currentIndex())
            if ingrediente_id is None or ingrediente_id == -1:
                QMessageBox.warning(self, "Validación", "Ingrediente no válido")
                return
            
            ingrediente_nombre = self.ingrediente_combo.currentText().split("(")[0].strip()
            
            cantidad = self.cantidad_input.value()
            if cantidad <= 0:
                QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor a 0")
                return
            
            motivo = self.motivo_input.toPlainText().strip()
            
            reply = QMessageBox.question(
                self, 'Confirmar Pedido',
                f'¿Agregar pedido de {cantidad} {self.unidad_label.text()} '
                f'de "{ingrediente_nombre}"?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.agregar_btn.setEnabled(False)
                QApplication.processEvents()
                
                resultado = self.pedidos_manager.agregar_pedido(ingrediente_id, cantidad, motivo)
                
                if resultado['success']:
                    hora_actual = datetime.now().strftime('%H:%M:%S')
                    
                    QMessageBox.information(
                        self, 
                         "Pedido registrado", 
                        f"Pedido registrado correctamente a las {hora_actual}."
                    )
                    
                    self.motivo_input.clear()
                    self.cantidad_input.setValue(0.5)
                    
                    self.force_refresh_all()
                    
                else:
                    QMessageBox.critical(self, "Error", 
                        f"No se pudo registrar el pedido:\n{resultado.get('error', 'Error desconocido')}")
                
                self.agregar_btn.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el pedido:\n{str(e)}")
            self.agregar_btn.setEnabled(True)

    def cancelar_ultimo_pedido(self):
        try:
            if self.ingrediente_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Validación", "Debe seleccionar un ingrediente")
                return
            
            ingrediente_id = self.ingrediente_combo.itemData(self.ingrediente_combo.currentIndex())
            if ingrediente_id is None or ingrediente_id == -1:
                QMessageBox.warning(self, "Validación", "Ingrediente no válido")
                return
            
            ingrediente_nombre = self.ingrediente_combo.currentText().split("(")[0].strip()
            
            try:
                detalles = self.pedidos_manager.obtener_detalle_pedidos_dia()
                pedidos_ingrediente = [p for p in detalles if p.get('ingrediente_nombre') == ingrediente_nombre]
            except Exception as e:
                print(f"⚠️ Error obteniendo detalle para cancelar: {e}")
                pedidos_ingrediente = []
            
            if not pedidos_ingrediente:
                QMessageBox.warning(self, "Sin Pedidos", f"No hay pedidos de {ingrediente_nombre} para cancelar")
                return
            
            reply = QMessageBox.question(
                self, 'Confirmar Cancelación',
                f'¿Cancelar el último pedido de "{ingrediente_nombre}"?\n\n'
                f'• Cantidad: {pedidos_ingrediente[0].get("cantidad", 0)}\n'
                f'• Hora: {pedidos_ingrediente[0].get("hora", "")}',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.cancelar_btn.setEnabled(False)
                QApplication.processEvents()
                
                resultado = self.pedidos_manager.cancelar_ultimo_pedido(ingrediente_id)
                
                if resultado['success']:
                    QMessageBox.information(
                        self, 
                        "Pedido cancelado", 
                        f"Se canceló el último pedido de {ingrediente_nombre}.\n"
                        f"Se devolvieron {resultado['cantidad_devuelta']} al inventario."
                    )
                    
                    self.force_refresh_all()
                    
                else:
                    QMessageBox.critical(self, "Error", 
                        f"No se pudo cancelar el pedido:\n{resultado.get('error', 'Error desconocido')}")
                
                self.cancelar_btn.setEnabled(True)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cancelar el pedido:\n{str(e)}")
            self.cancelar_btn.setEnabled(True)

    def cancelar_pedido_por_id(self, detalle_id):
        try:
            selected_items = self.historial_table.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Selección", "Seleccione un pedido de la tabla para cancelar")
                return
            
            row = selected_items[0].row()
            detalle_id_item = self.historial_table.item(row, 0)
            if not detalle_id_item:
                QMessageBox.warning(self, "Error", "No se pudo obtener el ID del pedido seleccionado")
                return
            
            detalle_id = int(detalle_id_item.text())
            ingrediente_nombre = self.historial_table.item(row, 2).text()
            cantidad = self.historial_table.item(row, 3).text()
            hora = self.historial_table.item(row, 1).text()
            
            reply = QMessageBox.question(
                self, 'Confirmar Cancelación',
                f'¿Cancelar el pedido de {ingrediente_nombre} a las {hora}?\n\n'
                f'• Cantidad: {cantidad}',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                resultado = self.pedidos_manager.cancelar_pedido_por_id(detalle_id)
                
                if resultado['success']:
                    QMessageBox.information(
                        self, 
                        "Pedido cancelado", 
                        f"Pedido cancelado correctamente.\n"
                        f"Se devolvieron {resultado['cantidad_devuelta']} al inventario."
                    )
                    
                    self.force_refresh_all()
                    
                else:
                    QMessageBox.critical(self, "Error", 
                        f"No se pudo cancelar el pedido:\n{resultado.get('error', 'Error desconocido')}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cancelar el pedido:\n{str(e)}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        
        if hasattr(self, 'splitter'):
            width = self.width()
            left_size = max(250, int(width * 0.3))
            right_size = max(400, int(width * 0.7))
            self.splitter.setSizes([left_size, right_size])

    def closeEvent(self, event):
        if hasattr(self, 'update_timer') and self.update_timer.isActive():
            self.update_timer.stop()
            print("✅ Timer de actualización detenido")
        super().closeEvent(event)
