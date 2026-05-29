# modules/produccion_ui.py
import os
import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QFrame, QGridLayout,
    QSpinBox, QComboBox, QTextEdit, QSplitter, QSizePolicy,
    QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from modules.produccion import ProduccionManager
from modules.catalogos import CatalogoManager
from utils.date_utils import get_current_date, format_date

class ProduccionWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.produccion_manager = ProduccionManager()
        self.catalogos_manager = CatalogoManager()
        
        # Crear interfaz simplificada
        self.create_compact_ui()
        
        # Conectar señales
        self.connect_signals()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
        # Configurar tablas
        self.setup_tables()
        
        # Aplicar estilos
        self.apply_specific_styles()

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.produccion_manager = services.get("produccion")
            self.catalogos_manager = services.get("catalogos")
            try:
                self.actualizar_todo()
            except Exception:
                pass

    def refresh_data(self):
        self.actualizar_todo()
    
    def create_compact_ui(self):
        """Crea la interfaz compacta y funcional"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # ==================== ENCABEZADO ====================
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("Registro de producción")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setProperty("role", "title")
        
        self.fecha_label = QLabel()
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.fecha_label)
        
        main_layout.addWidget(header_frame)
        
        # ==================== SPLITTER PRINCIPAL ====================
        splitter = QSplitter(Qt.Horizontal)
        
        # ==================== PANEL IZQUIERDO - FORMULARIO ====================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(8)
        
        # Grupo: Nueva Producción
        nueva_produccion_group = QGroupBox("Nueva producción")
        nueva_produccion_layout = QVBoxLayout(nueva_produccion_group)
        nueva_produccion_layout.setSpacing(6)
        
        # Formulario en GRID
        form_grid = QGridLayout()
        form_grid.setVerticalSpacing(6)
        form_grid.setHorizontalSpacing(8)
        
        # Producto
        producto_label = QLabel("Producto:")
        producto_label.setMinimumWidth(70)
        producto_label.setProperty("role", "field")
        self.producto_combo = QComboBox()
        self.producto_combo.setMinimumHeight(28)
        form_grid.addWidget(producto_label, 0, 0)
        form_grid.addWidget(self.producto_combo, 0, 1, 1, 2)
        
        # Información del producto
        info_frame = QFrame()
        info_layout = QHBoxLayout(info_frame)
        info_layout.setContentsMargins(6, 4, 6, 4)
        info_layout.setSpacing(10)
        
        self.precio_label = QLabel("Precio: $0.00")
        self.unidad_label = QLabel("unidad")
        
        info_layout.addWidget(self.precio_label)
        info_layout.addStretch()
        info_layout.addWidget(self.unidad_label)
        
        form_grid.addWidget(info_frame, 1, 0, 1, 3)
        
        # Cantidad
        cantidad_label = QLabel("Cantidad:")
        cantidad_label.setProperty("role", "field")
        self.cantidad_input = QSpinBox()
        self.cantidad_input.setRange(1, 1000)
        self.cantidad_input.setValue(1)
        self.cantidad_input.setMinimumHeight(28)
        self.cantidad_input.setMinimumWidth(100)
        
        form_grid.addWidget(cantidad_label, 2, 0)
        form_grid.addWidget(self.cantidad_input, 2, 1)
        
        # Notas
        notas_label = QLabel("Notas:")
        notas_label.setProperty("role", "field")
        self.notas_input = QTextEdit()
        self.notas_input.setMaximumHeight(70)
        self.notas_input.setPlaceholderText("Opcional...")
        
        form_grid.addWidget(notas_label, 3, 0)
        form_grid.addWidget(self.notas_input, 3, 1, 1, 2)
        
        # Botones
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.registrar_btn = QPushButton("Registrar producción")
        self.registrar_btn.setMinimumHeight(28)
        self.registrar_btn.setMinimumWidth(130)
        
        self.cancelar_btn = QPushButton("Cancelar última")
        self.cancelar_btn.setMinimumHeight(28)
        self.cancelar_btn.setMinimumWidth(120)
        
        button_layout.addWidget(self.registrar_btn)
        button_layout.addWidget(self.cancelar_btn)
        button_layout.addStretch()
        
        form_grid.addLayout(button_layout, 4, 0, 1, 3)
        
        nueva_produccion_layout.addLayout(form_grid)
        left_layout.addWidget(nueva_produccion_group)
        
        # Estadísticas del día
        stats_group = QGroupBox("Resumen de hoy")
        stats_layout = QVBoxLayout(stats_group)
        
        self.produccion_hoy_label = QLabel("Producción hoy: 0 unidades")
        self.productos_producidos_label = QLabel("Productos producidos hoy: 0")
        
        stats_layout.addWidget(self.produccion_hoy_label)
        stats_layout.addWidget(self.productos_producidos_label)
        
        left_layout.addWidget(stats_group)
        left_layout.addStretch()
        
        # ==================== PANEL DERECHO - TABLAS ====================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(8)
        
        # Tabla de producción del día
        produccion_group = QGroupBox("Producción del día")
        produccion_layout = QVBoxLayout(produccion_group)
        
        self.produccion_table = QTableWidget()
        self.produccion_table.setColumnCount(5)
        self.produccion_table.setHorizontalHeaderLabels(["Hora", "Producto", "Cantidad", "Unidad", "Notas"])
        self.produccion_table.horizontalHeader().setStretchLastSection(True)
        
        produccion_layout.addWidget(self.produccion_table)
        right_layout.addWidget(produccion_group)
        
        # Botones de tabla
        table_buttons = QHBoxLayout()
        table_buttons.setSpacing(8)
        
        self.actualizar_btn = QPushButton("Actualizar")
        self.actualizar_btn.setMinimumHeight(28)
        
        self.limpiar_btn = QPushButton("Limpiar")
        self.limpiar_btn.setMinimumHeight(28)
        
        table_buttons.addWidget(self.actualizar_btn)
        table_buttons.addWidget(self.limpiar_btn)
        table_buttons.addStretch()
        
        right_layout.addLayout(table_buttons)
        
        # ==================== CONFIGURAR SPLITTER ====================
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([320, 520])
        
        main_layout.addWidget(splitter, 1)
        
        # Guardar referencia
        self.splitter = splitter
    
    def apply_specific_styles(self):
        """Aplica estilos específicos para este widget"""
        # Convertir a objectName/properties para QSS central
        self.setObjectName("produccionWidget")
        try:
            self.produccion_table.setObjectName("produccionTable")
        except Exception:
            pass

        self.fecha_label.setProperty("role", "muted")
        self.precio_label.setProperty("emphasis", "strong")
        self.unidad_label.setProperty("emphasis", "strong")
        self.produccion_hoy_label.setProperty("emphasis", "strong")
        self.productos_producidos_label.setProperty("role", "field")
    
    def connect_signals(self):
        """Conecta todas las señales"""
        self.producto_combo.currentIndexChanged.connect(self.actualizar_unidad)
        self.registrar_btn.clicked.connect(self.registrar_produccion)
        self.cancelar_btn.clicked.connect(self.cancelar_ultima_produccion)
        self.actualizar_btn.clicked.connect(self.actualizar_todo)
        self.limpiar_btn.clicked.connect(self.limpiar_formulario)
    
    def load_initial_data(self):
        """Carga los datos iniciales"""
        self.actualizar_fecha()
        self.cargar_productos()
        self.actualizar_todo()
    
    def setup_tables(self):
        """Configura las tablas"""
        # Tabla de producción
        header = self.produccion_table.horizontalHeader()
        header.setDefaultSectionSize(80)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Hora
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Producto
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unidad
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Notas
    
    def actualizar_fecha(self):
        """Actualiza la fecha en la interfaz"""
        try:
            fecha_actual = get_current_date()
            fecha_formateada = format_date(fecha_actual)
            self.fecha_label.setText(f"📅 {fecha_formateada}")
        except Exception as e:
            print(f"Error actualizando fecha: {e}")
            self.fecha_label.setText("📅 Fecha no disponible")
    
    def cargar_productos(self):
        """Carga TODOS los productos desde el catálogo"""
        try:
            print("🔄 ProduccionWidget.cargar_productos v2.0...")
            productos = self.catalogos_manager.obtener_productos()
            
            self.producto_combo.clear()
            
            if not productos:
                print("⚠️ No se encontraron productos")
                self.producto_combo.addItem("No hay productos disponibles", -1)
                return
            
            print(f"✅ {len(productos)} productos encontrados")
            
            for prod in productos:
                display_text = f"{prod['nombre']} (${prod.get('precio_venta', 0):.2f})"
                self.producto_combo.addItem(display_text, prod['id'])
            
            if self.producto_combo.count() > 0:
                self.producto_combo.setCurrentIndex(0)
                self.actualizar_unidad()
                
        except Exception as e:
            print(f"❌ ERROR cargando productos en producción: {str(e)}")
            import traceback
            traceback.print_exc()
            self.producto_combo.addItem("Error cargando productos", -1)
    
    def actualizar_unidad(self):
        """Actualiza la unidad de venta del producto seleccionado"""
        try:
            index = self.producto_combo.currentIndex()
            if index < 0:
                return
            
            producto_id = self.producto_combo.itemData(index)
            if not producto_id or producto_id == -1:
                self.unidad_label.setText("unidad")
                return
            
            # Obtener información del producto
            productos = self.catalogos_manager.obtener_productos()
            producto_actual = None
            
            for prod in productos:
                if prod['id'] == producto_id:
                    producto_actual = prod
                    break
            
            if producto_actual:
                precio = producto_actual.get('precio_venta', 0)
                self.precio_label.setText(f"Precio: ${precio:.2f}")
                self.unidad_label.setText(producto_actual.get('unidad_venta', 'unidad'))
            else:
                self.unidad_label.setText("unidad")
                
        except Exception as e:
            print(f"❌ Error actualizando unidad: {e}")
            self.unidad_label.setText("unidad")
    
    def actualizar_todo(self):
        """Actualiza los componentes de la interfaz."""
        try:
            print("🔄 Actualizando interfaz de producción v2.0...")
            
            self.actualizar_fecha()
            self.cargar_produccion_dia()
            self.cargar_estadisticas_dia()
            
        except Exception as e:
            print(f"❌ Error en actualización completa de producción: {e}")
    
    def cargar_produccion_dia(self):
        """Carga la producción del día en la tabla"""
        try:
            produccion = self.produccion_manager.obtener_produccion_dia()
            
            self.produccion_table.setRowCount(len(produccion))
            
            for i, prod in enumerate(produccion):
                hora = prod.get('hora', '--:--')
                if hora and len(hora) > 5:
                    hora = hora[11:16]  # Extraer HH:MM
                
                self.produccion_table.setItem(i, 0, QTableWidgetItem(hora))
                self.produccion_table.setItem(i, 1, QTableWidgetItem(prod.get('nombre', 'Desconocido')))
                self.produccion_table.setItem(i, 2, QTableWidgetItem(str(prod.get('cantidad', 0))))
                self.produccion_table.setItem(i, 3, QTableWidgetItem(prod.get('unidad_venta', 'unidad')))
                self.produccion_table.setItem(i, 4, QTableWidgetItem(prod.get('notas', '') or ''))
                
                # Centrar columnas
                for col in [0, 2, 3]:
                    item = self.produccion_table.item(i, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            
            # Ajustar alto de filas
            for i in range(self.produccion_table.rowCount()):
                self.produccion_table.setRowHeight(i, 24)
            
        except Exception as e:
            print(f"❌ Error cargando producción del día: {e}")
    
    def cargar_estadisticas_dia(self):
        """Carga las estadísticas de producción del día"""
        try:
            # Total producido hoy
            total_hoy = self.produccion_manager.obtener_total_produccion_dia()
            
            # Obtener producción del día para contar productos diferentes
            produccion = self.produccion_manager.obtener_produccion_dia()
            productos_count = len(set(p.get('nombre', '') for p in produccion)) if produccion else 0
            
            self.produccion_hoy_label.setText(f"Producción hoy: {total_hoy} unidades")
            self.productos_producidos_label.setText(f"Productos producidos hoy: {productos_count}")
                
        except Exception as e:
            print(f"❌ Error cargando estadísticas: {e}")
    
    def registrar_produccion(self):
        """Registra una nueva producción."""
        try:
            # Validar selección de producto
            if self.producto_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Validación", "Debe seleccionar un producto")
                return
            
            producto_id = self.producto_combo.itemData(self.producto_combo.currentIndex())
            if not producto_id or producto_id == -1:
                QMessageBox.warning(self, "Validación", "Producto no válido")
                return
            
            producto_nombre = self.producto_combo.currentText().split("(")[0].strip()
            
            # ✅ CORRECCIÓN: Obtener cantidad directamente del QSpinBox
            cantidad = self.cantidad_input.value()
            if cantidad <= 0:
                QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor a 0")
                return
            
            # Obtener notas
            notas = self.notas_input.toPlainText().strip()
            
            # Confirmar acción
            reply = QMessageBox.question(
                self, 'Confirmar producción',
                f'¿Registrar producción de {cantidad} {self.unidad_label.text()} '
                f'de "{producto_nombre}"?\n\n'
                f'• Inventario se actualizará automáticamente',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Registrar producción
                self.produccion_manager.registrar_produccion(
                    producto_id=producto_id,
                    cantidad=cantidad,
                    notas=notas
                )
                
                QMessageBox.information(
                    self, 
                    "Producción registrada", 
                    f"Producción registrada correctamente.\n\n"
                    f"<b>Detalles:</b>\n"
                    f"• Producto: {producto_nombre}\n"
                    f"• Cantidad: {cantidad} {self.unidad_label.text()}\n"
                    f"• Inventario actualizado"
                )
                
                # Limpiar campos
                self.limpiar_formulario()
                
                # Actualizar interfaz
                self.actualizar_todo()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la producción:\n{str(e)}")
    
    def cancelar_ultima_produccion(self):
        """Cancela la última producción del producto seleccionado"""
        try:
            if self.producto_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Validación", "Debe seleccionar un producto")
                return
            
            producto_id = self.producto_combo.itemData(self.producto_combo.currentIndex())
            if not producto_id or producto_id == -1:
                QMessageBox.warning(self, "Validación", "Producto no válido")
                return
            
            producto_nombre = self.producto_combo.currentText().split("(")[0].strip()
            
            # Verificar si hay producciones
            produccion = self.produccion_manager.obtener_produccion_dia()
            producciones_producto = [p for p in produccion if p.get('producto_id') == producto_id]
            
            if not producciones_producto:
                QMessageBox.warning(self, "Sin Producciones", f"No hay producciones de {producto_nombre} para cancelar")
                return
            
            # Confirmar cancelación
            reply = QMessageBox.question(
                self, 'Confirmar cancelación',
                f'¿Cancelar la última producción de "{producto_nombre}"?\n\n'
                f'• Cantidad: {producciones_producto[0].get("cantidad", 0)}\n'
                f'• Hora: {producciones_producto[0].get("hora", "")[:5]}\n\n'
                f'<b>Esta acción restará la cantidad del inventario</b>',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Cancelar producción
                resultado = self.produccion_manager.cancelar_ultima_produccion(producto_id)
                
                QMessageBox.information(
                    self, 
                    "Producción cancelada", 
                    f"Producción cancelada correctamente.\n\n"
                    f"<b>Detalles:</b>\n"
                    f"• Producto: {producto_nombre}\n"
                    f"• Cantidad cancelada: {resultado['cantidad']} unidades\n"
                    f"• Inventario actualizado"
                )
                
                # Actualizar interfaz
                self.actualizar_todo()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cancelar la producción:\n{str(e)}")
    
    def limpiar_formulario(self):
        """Limpia el formulario"""
        try:
            if self.producto_combo.count() > 0:
                self.producto_combo.setCurrentIndex(0)
            
            self.cantidad_input.setValue(1)
            self.notas_input.clear()
            
        except Exception as e:
            print(f"❌ Error limpiando formulario: {e}")
    
    def resizeEvent(self, event):
        """Maneja el redimensionamiento"""
        super().resizeEvent(event)
        
        if hasattr(self, 'splitter'):
            width = self.width()
            left_size = max(250, int(width * 0.3))
            right_size = max(400, int(width * 0.7))
            self.splitter.setSizes([left_size, right_size])
