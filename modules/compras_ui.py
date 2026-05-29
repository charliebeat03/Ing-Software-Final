# modules/compras_ui.py - VERSIÓN PROFESIONAL PARA PYQT5
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLabel, QGroupBox,
    QHeaderView, QMessageBox, QFrame, QGridLayout,
    QDoubleSpinBox, QComboBox, QDateEdit, QTextEdit,
    QSpinBox, QSplitter, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont

from modules.compras import ComprasManager
from modules.catalogos import CatalogoManager
from utils.date_utils import get_current_date, format_date

class ComprasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Inicializar managers
        try:
            self.compras_manager = ComprasManager()
            self.catalogos_manager = CatalogoManager()
            print("Managers inicializados correctamente")
        except Exception as e:
            print(f"Error inicializando managers: {e}")
            raise
        
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

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.compras_manager = services.get("compras")
            self.catalogos_manager = services.get("catalogos")
            try:
                self.actualizar_todo()
            except Exception:
                pass
    
    def create_compact_ui(self):
        """Crea la interfaz compacta y funcional"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)
        
        # ==================== ENCABEZADO ====================
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        title_label = QLabel("REGISTRAR COMPRAS")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setProperty("role", "title")
        
        self.fecha_actual_label = QLabel()
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.fecha_actual_label)
        
        main_layout.addWidget(header_frame)
        
        # ==================== SPLITTER PRINCIPAL ====================
        splitter = QSplitter(Qt.Horizontal)
        
        # ==================== PANEL IZQUIERDO - FORMULARIO ====================
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(8)
        
        # Grupo: Nueva Compra
        nueva_compra_group = QGroupBox("NUEVA COMPRA")
        nueva_compra_layout = QVBoxLayout(nueva_compra_group)
        nueva_compra_layout.setSpacing(6)
        
        # Formulario en grid (NO QFormLayout)
        form_grid = QGridLayout()
        form_grid.setVerticalSpacing(6)
        form_grid.setHorizontalSpacing(8)
        
        # Fecha
        fecha_label = QLabel("Fecha:")
        fecha_label.setProperty("role", "field")
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        self.fecha_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_input.setMinimumHeight(26)
        form_grid.addWidget(fecha_label, 0, 0)
        form_grid.addWidget(self.fecha_input, 0, 1, 1, 2)
        
        # Ingrediente
        ingrediente_label = QLabel("Ingrediente:")
        ingrediente_label.setProperty("role", "field")
        self.ingrediente_combo = QComboBox()
        self.ingrediente_combo.setMinimumHeight(26)
        form_grid.addWidget(ingrediente_label, 1, 0)
        form_grid.addWidget(self.ingrediente_combo, 1, 1, 1, 2)
        
        # Cantidad
        cantidad_label = QLabel("Cantidad:")
        cantidad_label.setProperty("role", "field")
        cantidad_container = QWidget()
        cantidad_layout = QHBoxLayout(cantidad_container)
        cantidad_layout.setContentsMargins(0, 0, 0, 0)
        cantidad_layout.setSpacing(8)
        
        self.cantidad_input = QDoubleSpinBox()
        self.cantidad_input.setRange(0.01, 10000)
        self.cantidad_input.setDecimals(3)
        self.cantidad_input.setValue(1.0)
        self.cantidad_input.setMinimumHeight(26)
        self.cantidad_input.setMinimumWidth(100)
        
        self.unidad_label = QLabel("kg")
        self.unidad_label.setMinimumHeight(26)
        
        cantidad_layout.addWidget(self.cantidad_input)
        cantidad_layout.addWidget(self.unidad_label)
        cantidad_layout.addStretch()
        
        form_grid.addWidget(cantidad_label, 2, 0)
        form_grid.addWidget(cantidad_container, 2, 1, 1, 2)
        
        # Costo unitario
        costo_label = QLabel("Costo unitario:")
        costo_label.setProperty("role", "field")
        self.costo_input = QDoubleSpinBox()
        self.costo_input.setRange(0.01, 100000)
        self.costo_input.setDecimals(2)
        self.costo_input.setValue(1.0)
        self.costo_input.setMinimumHeight(26)
        self.costo_input.setMinimumWidth(100)
        
        form_grid.addWidget(costo_label, 3, 0)
        form_grid.addWidget(self.costo_input, 3, 1, 1, 2)
        
        # Total
        total_label = QLabel("Total:")
        total_label.setProperty("role", "field")
        self.total_label = QLabel("$0.00")
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.total_label.setMinimumHeight(26)
        
        form_grid.addWidget(total_label, 4, 0)
        form_grid.addWidget(self.total_label, 4, 1, 1, 2)
        
        # Notas
        notas_label = QLabel("Notas:")
        notas_label.setProperty("role", "field")
        self.notas_input = QTextEdit()
        self.notas_input.setMaximumHeight(60)
        self.notas_input.setPlaceholderText("Opcional...")
        
        form_grid.addWidget(notas_label, 5, 0)
        form_grid.addWidget(self.notas_input, 5, 1, 1, 2)
        
        nueva_compra_layout.addLayout(form_grid)
        
        # Botones - SOLO BOTÓN REGISTRAR
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        self.registrar_btn = QPushButton("Registrar")
        self.registrar_btn.setMinimumHeight(26)
        self.registrar_btn.setMinimumWidth(100)
        
        button_layout.addWidget(self.registrar_btn)
        button_layout.addStretch()
        
        nueva_compra_layout.addLayout(button_layout)
        left_layout.addWidget(nueva_compra_group)
        
        # Resumen rápido
        resumen_group = QGroupBox("Resumen Rápido")
        resumen_layout = QVBoxLayout(resumen_group)
        
        self.compras_hoy_label = QLabel("Hoy: $0.00")
        self.compras_mes_label = QLabel("Este mes: $0.00")
        
        resumen_layout.addWidget(self.compras_hoy_label)
        resumen_layout.addWidget(self.compras_mes_label)
        
        left_layout.addWidget(resumen_group)
        left_layout.addStretch()
        
        # ==================== PANEL DERECHO - TABLAS ====================
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(8)
        
        # Filtros
        filtros_frame = QFrame()
        filtros_layout = QHBoxLayout(filtros_frame)
        
        filtros_label = QLabel("Mostrar últimos:")
        filtros_label.setProperty("role", "field")
        self.filtro_dias_spin = QSpinBox()
        self.filtro_dias_spin.setRange(1, 365)
        self.filtro_dias_spin.setValue(7)
        self.filtro_dias_spin.setSuffix(" días")
        self.filtro_dias_spin.setMinimumHeight(26)
        
        self.filtrar_btn = QPushButton("Filtrar")
        self.filtrar_btn.setMinimumHeight(26)
        
        self.actualizar_btn = QPushButton("Actualizar")
        self.actualizar_btn.setMinimumHeight(26)
        
        filtros_layout.addWidget(filtros_label)
        filtros_layout.addWidget(self.filtro_dias_spin)
        filtros_layout.addStretch()
        filtros_layout.addWidget(self.filtrar_btn)
        filtros_layout.addWidget(self.actualizar_btn)
        
        right_layout.addWidget(filtros_frame)
        
        # Tabla de compras
        compras_group = QGroupBox("HISTORIAL")
        compras_layout = QVBoxLayout(compras_group)
        
        self.compras_table = QTableWidget()
        self.compras_table.setColumnCount(7)
        self.compras_table.setHorizontalHeaderLabels(["Fecha", "Ingrediente", "Cantidad", "Unidad", "Costo", "Total", "Notas"])
        self.compras_table.horizontalHeader().setStretchLastSection(True)
        
        compras_layout.addWidget(self.compras_table)
        right_layout.addWidget(compras_group)
        
        # Botones de tabla
        table_buttons = QHBoxLayout()
        table_buttons.setSpacing(8)
        
        self.exportar_btn = QPushButton("Exportar")
        self.exportar_btn.setMinimumHeight(26)
        
        table_buttons.addWidget(self.exportar_btn)
        table_buttons.addStretch()
        
        right_layout.addLayout(table_buttons)
        
        # ==================== CONFIGURAR SPLITTER ====================
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 550])
        
        main_layout.addWidget(splitter, 1)
        
        # Guardar referencia
        self.splitter = splitter
    
    def apply_specific_styles(self):
        """Aplica estilos específicos para este widget"""
        # Estilo para botones
        button_style = """
            QPushButton {
                background-color: #4a6fa5;
                color: white;
                border: 1px solid #3c5d8c;
                border-radius: 3px;
                padding: 4px 10px;
                font-size: 11px;
                min-height: 26px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #3c5d8c;
                border-color: #2c3e50;
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
        """
        
        # Estilo para campos
        field_style = """
            QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 3px 6px;
                font-size: 11px;
                min-height: 26px;
                background-color: white;
                color: #000000;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QTextEdit {
                min-height: 50px;
                color: #000000;
            }
            QSpinBox, QDoubleSpinBox {
                color: #000000;
            }
        """
        
        # Estilo para etiquetas
        label_style = """
            QLabel {
                font-size: 11px;
                color: #000000;
                padding: 2px;
            }
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #4a6fa5;
                border-radius: 4px;
                margin-top: 6px;
                color: #000000;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #000000;
                background-color: #4a6fa5;
                color: white;
                border-radius: 2px;
                padding: 2px 8px;
            }
        """
        
        # Delegar a QSS global; asignar objectName para este módulo
        self.setObjectName("comprasWidget")
        try:
            self.compras_table.setObjectName("comprasTable")
        except Exception:
            pass

        # Botones y badges usan propiedades para aplicar estilos desde styles.qss
        self.registrar_btn.setProperty("role", "action")
        
        # Estilos específicos
        self.fecha_actual_label.setProperty("role", "muted")
        self.total_label.setProperty("emphasis", "strong")
        self.compras_hoy_label.setProperty("emphasis", "strong")
        self.compras_mes_label.setProperty("emphasis", "strong")
        
        # Estilo para tablas - PROFESIONAL CON ENCABEZADOS VISIBLES
        table_style = """
            QTableWidget {
                font-size: 11px;
                alternate-background-color: #f8f9fa;
                selection-background-color: #4a6fa5;
                selection-color: white;
                color: #000000;
                border: 1px solid #dee2e6;
                gridline-color: #dee2e6;
            }
            QHeaderView::section {
                background-color: #4a6fa5;
                padding: 6px 4px;
                border: 1px solid #3c5d8c;
                font-size: 11px;
                font-weight: bold;
                color: white;
            }
            QTableWidget::item {
                color: #000000;
                border-bottom: 1px solid #ecf0f1;
            }
            QTableWidget::item:selected {
                background-color: #4a6fa5;
                color: #ffffff;
            }
            QHeaderView::section:checked {
                background-color: #3c5d8c;
            }
        """
        
        # tablas estiladas desde styles.qss por objectName
        try:
            self.compras_table.setObjectName("comprasTable")
        except Exception:
            pass
    
    def connect_signals(self):
        """Conecta todas las señales"""
        self.cantidad_input.valueChanged.connect(self.calcular_total)
        self.costo_input.valueChanged.connect(self.calcular_total)
        self.ingrediente_combo.currentIndexChanged.connect(self.actualizar_unidad)
        self.registrar_btn.clicked.connect(self.registrar_compra)
        self.actualizar_btn.clicked.connect(self.actualizar_todo)
        self.filtrar_btn.clicked.connect(self.filtrar_compras)
        self.exportar_btn.clicked.connect(self.exportar_compras)
    
    def load_initial_data(self):
        """Carga los datos iniciales"""
        self.actualizar_fecha()
        self.cargar_ingredientes()
        self.calcular_total()
        self.actualizar_todo()
    
    def setup_tables(self):
        """Configura las tablas"""
        # Tabla de compras
        header = self.compras_table.horizontalHeader()
        header.setDefaultSectionSize(100)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Fecha
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Ingrediente
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Unidad
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Costo
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Total
        header.setSectionResizeMode(6, QHeaderView.Stretch)  # Notas
    
    def actualizar_fecha(self):
        """Actualiza la fecha en la interfaz"""
        try:
            fecha_actual = get_current_date()
            fecha_formateada = format_date(fecha_actual)
            self.fecha_actual_label.setText(fecha_formateada)
        except Exception as e:
            print(f"Error actualizando fecha: {e}")
            self.fecha_actual_label.setText("Fecha no disponible")
    
    def cargar_ingredientes(self):
        """Carga TODOS los ingredientes desde el catálogo"""
        try:
            ingredientes = self.catalogos_manager.obtener_ingredientes()
            
            self.ingrediente_combo.clear()
            
            if not ingredientes:
                self.ingrediente_combo.addItem("No hay ingredientes disponibles", -1)
                return
            
            for ing in ingredientes:
                display_text = f"{ing['nombre']} ({ing.get('abreviatura', '')})"
                self.ingrediente_combo.addItem(display_text, ing['id'])
            
            if self.ingrediente_combo.count() > 0:
                self.ingrediente_combo.setCurrentIndex(0)
                self.actualizar_unidad()
                
        except Exception as e:
            print(f"ERROR cargando ingredientes: {str(e)}")
            import traceback
            traceback.print_exc()
            self.ingrediente_combo.addItem("Error cargando ingredientes", -1)
    
    def actualizar_unidad(self):
        """Actualiza la etiqueta de unidad según el ingrediente seleccionado"""
        try:
            index = self.ingrediente_combo.currentIndex()
            if index < 0:
                return
            
            texto = self.ingrediente_combo.itemText(index)
            
            # Extraer unidad entre paréntesis
            if "(" in texto and ")" in texto:
                unidad = texto.split("(")[1].split(")")[0]
                self.unidad_label.setText(unidad)
            else:
                self.unidad_label.setText("unidad")
                
        except Exception as e:
            print(f"Error actualizando unidad: {e}")
            self.unidad_label.setText("unidad")
    
    def calcular_total(self):
        """Calcula el total de la compra"""
        try:
            cantidad = self.cantidad_input.value()
            costo = self.costo_input.value()
            total = cantidad * costo
            self.total_label.setText(f"${total:.2f}")
            
        except Exception as e:
            print(f"Error calculando total: {e}")
            self.total_label.setText("$0.00")
    
    def cargar_compras(self):
        """Carga las compras en la tabla según el filtro de días"""
        try:
            # Obtener número de días para filtrar
            dias = self.filtro_dias_spin.value()
            
            # Calcular fechas
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=dias)
            
            # Obtener compras del período
            compras = self.compras_manager.obtener_compras_por_fecha(
                fecha_inicio.isoformat(), fecha_fin.isoformat()
            )
            
            self.compras_table.setRowCount(len(compras))
            
            for i, compra in enumerate(compras):
                # Formatear fecha
                try:
                    fecha = datetime.strptime(compra['fecha'], '%Y-%m-%d %H:%M:%S')
                    fecha_str = fecha.strftime('%d/%m/%Y %H:%M')
                except:
                    fecha_str = compra.get('fecha', 'N/A')
                
                self.compras_table.setItem(i, 0, QTableWidgetItem(fecha_str))
                self.compras_table.setItem(i, 1, QTableWidgetItem(compra.get('ingrediente_nombre', 'Desconocido')))
                self.compras_table.setItem(i, 2, QTableWidgetItem(f"{compra.get('cantidad', 0):.3f}"))
                self.compras_table.setItem(i, 3, QTableWidgetItem(compra.get('abreviatura', '')))
                self.compras_table.setItem(i, 4, QTableWidgetItem(f"${compra.get('costo_unitario', 0):.2f}"))
                self.compras_table.setItem(i, 5, QTableWidgetItem(f"${compra.get('total', 0):.2f}"))
                self.compras_table.setItem(i, 6, QTableWidgetItem(compra.get('notas', '') or ""))
                
                # Centrar columnas numéricas
                for col in [2, 3, 4, 5]:
                    item = self.compras_table.item(i, col)
                    if item:
                        item.setTextAlignment(Qt.AlignCenter)
            
            # Ajustar alto de filas
            for i in range(self.compras_table.rowCount()):
                self.compras_table.setRowHeight(i, 24)
            
        except Exception as e:
            print(f"Error cargando compras: {e}")
    
    def cargar_resumen(self):
        """Carga el resumen de compras"""
        try:
            # Total de hoy
            fecha_hoy = datetime.now().date().isoformat()
            total_hoy = self.compras_manager.obtener_total_compras_periodo(fecha_hoy, fecha_hoy)
            
            # Total del mes (últimos 30 días)
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=30)
            total_mes = self.compras_manager.obtener_total_compras_periodo(
                fecha_inicio.isoformat(), fecha_fin.isoformat()
            )
            
            self.compras_hoy_label.setText(f"Hoy: ${total_hoy:.2f}")
            self.compras_mes_label.setText(f"Este mes: ${total_mes:.2f}")
                
        except Exception as e:
            print(f"Error cargando resumen: {e}")
    
    def filtrar_compras(self):
        """Filtra las compras según los días seleccionados"""
        try:
            dias = self.filtro_dias_spin.value()
            self.actualizar_btn.setText(f"Filtrado ({dias} días)")
            self.cargar_compras()
            
        except Exception as e:
            print(f"Error filtrando compras: {e}")
    
    def actualizar_todo(self):
        """Actualiza TODOS los componentes de la interfaz"""
        try:
            print("Actualizando interfaz de compras...")
            
            self.actualizar_fecha()
            self.cargar_compras()
            self.cargar_resumen()
            
            # Restaurar texto del botón de actualizar
            self.actualizar_btn.setText("Actualizar")
            
        except Exception as e:
            print(f"Error en actualización completa: {e}")
    
    def registrar_compra(self):
        """Registra una nueva compra"""
        try:
            # Validar selección de ingrediente
            if self.ingrediente_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Validación", "Debe seleccionar un ingrediente")
                return
            
            ingrediente_id = self.ingrediente_combo.itemData(self.ingrediente_combo.currentIndex())
            if not ingrediente_id or ingrediente_id == -1:
                QMessageBox.warning(self, "Validación", "Ingrediente no válido")
                return
            
            ingrediente_nombre = self.ingrediente_combo.currentText().split("(")[0].strip()
            
            # Validar cantidad
            cantidad = self.cantidad_input.value()
            if cantidad <= 0:
                QMessageBox.warning(self, "Validación", "La cantidad debe ser mayor a 0")
                return
            
            # Validar costo
            costo = self.costo_input.value()
            if costo <= 0:
                QMessageBox.warning(self, "Validación", "El costo debe ser mayor a 0")
                return
            
            # Obtener fecha
            fecha = self.fecha_input.date().toString("yyyy-MM-dd")
            
            # Obtener notas
            notas = self.notas_input.toPlainText().strip()
            
            # Calcular total para confirmación
            total = cantidad * costo
            
            # Confirmar acción
            reply = QMessageBox.question(
                self, 'Confirmar Compra',
                f'¿Registrar compra de {cantidad} {self.unidad_label.text()} '
                f'de "{ingrediente_nombre}"?\n\n'
                f'• Total: ${total:.2f}',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Registrar compra en la base de datos
                self.compras_manager.registrar_compra(
                    ingrediente_id=ingrediente_id,
                    cantidad=cantidad,
                    costo_unitario=costo,
                    notas=notas,
                    fecha=fecha
                )
                
                QMessageBox.information(
                    self, 
                    "Compra Registrada", 
                    f"Compra registrada correctamente.\nTotal: ${total:.2f}"
                )
                
                # Limpiar formulario
                self.limpiar_formulario()
                
                # Actualizar interfaz
                self.actualizar_todo()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la compra:\n{str(e)}")
    
    def limpiar_formulario(self):
        """Limpia el formulario de compra"""
        try:
            self.fecha_input.setDate(QDate.currentDate())
            
            if self.ingrediente_combo.count() > 0:
                self.ingrediente_combo.setCurrentIndex(0)
            
            self.cantidad_input.setValue(1.0)
            self.costo_input.setValue(1.0)
            self.notas_input.clear()
            
            self.calcular_total()
            
        except Exception as e:
            print(f"Error limpiando formulario: {e}")
    
    def exportar_compras(self):
        """Exporta las compras a un archivo CSV"""
        try:
            # Obtener número de días para filtrar
            dias = self.filtro_dias_spin.value()
            
            # Calcular fechas
            fecha_fin = datetime.now().date()
            fecha_inicio = fecha_fin - timedelta(days=dias)
            
            # Obtener compras del período
            compras = self.compras_manager.obtener_compras_por_fecha(
                fecha_inicio.isoformat(), fecha_fin.isoformat()
            )
            
            if not compras:
                QMessageBox.information(self, "Exportar", "No hay compras para exportar")
                return
            
            # Crear un archivo CSV
            from pathlib import Path
            import csv
            
            base_dir = Path(__file__).parent.parent
            export_dir = base_dir / "exportaciones"
            export_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = export_dir / f"compras_{timestamp}.csv"
            
            with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Fecha', 'Ingrediente', 'Cantidad', 'Unidad', 'Costo Unitario', 'Total', 'Notas']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for compra in compras:
                    writer.writerow({
                        'Fecha': compra.get('fecha', ''),
                        'Ingrediente': compra.get('ingrediente_nombre', ''),
                        'Cantidad': compra.get('cantidad', 0),
                        'Unidad': compra.get('abreviatura', ''),
                        'Costo Unitario': compra.get('costo_unitario', 0),
                        'Total': compra.get('total', 0),
                        'Notas': compra.get('notas', '')
                    })
            
            QMessageBox.information(
                self, 
                "Exportación Exitosa", 
                f"Se exportaron {len(compras)} compras a:\n\n{export_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", f"No se pudo exportar las compras:\n{str(e)}")
    
    def resizeEvent(self, event):
        """Maneja el redimensionamiento de la ventana"""
        super().resizeEvent(event)
        
        if hasattr(self, 'splitter'):
            width = self.width()
            left_size = max(300, int(width * 0.4))
            right_size = max(400, int(width * 0.6))
            self.splitter.setSizes([left_size, right_size])
