# modules/historial_ui.py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QDateEdit, 
                             QComboBox, QPushButton, QSplitter, QGroupBox,
                             QFormLayout, QFrame, QHeaderView, QMessageBox,
                             QTabWidget, QProgressBar, QGridLayout)
from PyQt5.QtCore import Qt, QDate, pyqtSlot
from PyQt5.QtGui import QFont, QColor, QBrush
from datetime import datetime
import locale

try:
    locale.setlocale(locale.LC_ALL, 'es_MX.UTF-8')
except:
    pass

from modules.historial import HistorialManager

class HistorialWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.tabla_datos = None
        self.lbl_estado = None
        self.lbl_total_valor = None
        self.lbl_productos_valor = None
        self.lbl_promedio_valor = None
        self.lbl_ultima_actualizacion = None
        self.combo_vista = None
        self.date_edit = None
        self.combo_anio = None
        self.combo_mes = None
        self.btn_actualizar = None
        self.btn_exportar = None
        self.lbl_total_titulo = None
        self.lbl_productos_titulo = None
        self.lbl_promedio_titulo = None
        self._actualizando = False
        
        self.historial_manager = HistorialManager()
        self.setup_ui()
        self.cargar_datos_iniciales()
        self.conectar_señales()

    def set_context(self, context):
        self.context = context or {}
        services = self.context.get("services")
        if services:
            self.historial_manager = services.get("historial")
            try:
                self.actualizar_datos()
            except Exception:
                pass

    def refresh_data(self):
        self.actualizar_datos()
    
    def setup_ui(self):
        """Configura la interfaz gráfica para el historial y reportes."""
        self.setWindowTitle("Historial y Reportes")
        self.setMinimumSize(900, 700)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ===== TÍTULO PRINCIPAL =====
        titulo_frame = QFrame()
        titulo_frame.setObjectName("historialTitleFrame")
        titulo_layout = QVBoxLayout(titulo_frame)

        titulo_label = QLabel("Historial de ventas")
        titulo_label.setAlignment(Qt.AlignCenter)
        titulo_font = QFont()
        titulo_font.setBold(True)
        titulo_font.setPointSize(14)
        titulo_label.setFont(titulo_font)
        titulo_label.setProperty("role", "title")

        subtitulo_label = QLabel("Consulta y exportación de ventas por rango de fechas")
        subtitulo_label.setAlignment(Qt.AlignCenter)
        subtitulo_label.setProperty("role", "hint")

        titulo_layout.addWidget(titulo_label)
        titulo_layout.addWidget(subtitulo_label)
        main_layout.addWidget(titulo_frame)

        # ===== BARRA DE HERRAMIENTAS =====
        toolbar_frame = QFrame()
        toolbar_frame.setObjectName("historialToolbar")
        toolbar_layout = QHBoxLayout(toolbar_frame)

        # Selector de vista
        self.combo_vista = QComboBox()
        self.combo_vista.addItem("Vista diaria", "dia")
        self.combo_vista.addItem("Vista mensual", "mes")
        self.combo_vista.currentIndexChanged.connect(self.cambiar_vista)
        self.combo_vista.setMinimumHeight(30)

        toolbar_layout.addWidget(QLabel("Vista:"))
        toolbar_layout.addWidget(self.combo_vista)

        # Selector de fecha para vista diaria
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setMaximumWidth(120)
        self.date_edit.setMinimumHeight(30)
        self.date_edit.dateChanged.connect(self.cargar_datos_dia)
        toolbar_layout.addWidget(QLabel("Fecha:"))
        toolbar_layout.addWidget(self.date_edit)

        # Selectores para vista mensual
        self.combo_anio = QComboBox()
        self.combo_mes = QComboBox()
        self.combo_anio.currentIndexChanged.connect(self.cargar_datos_mes)
        self.combo_mes.currentIndexChanged.connect(self.cargar_datos_mes)
        self.combo_anio.setMinimumHeight(30)
        self.combo_mes.setMinimumHeight(30)

        anio_actual = QDate.currentDate().year()
        for anio in range(anio_actual - 2, anio_actual + 1):
            self.combo_anio.addItem(str(anio), anio)
        self.combo_anio.setCurrentText(str(anio_actual))

        meses = [
            ("Enero", 1), ("Febrero", 2), ("Marzo", 3), ("Abril", 4),
            ("Mayo", 5), ("Junio", 6), ("Julio", 7), ("Agosto", 8),
            ("Septiembre", 9), ("Octubre", 10), ("Noviembre", 11), ("Diciembre", 12)
        ]
        for nombre, numero in meses:
            self.combo_mes.addItem(nombre, numero)
        self.combo_mes.setCurrentIndex(QDate.currentDate().month() - 1)

        toolbar_layout.addWidget(QLabel("Año:"))
        toolbar_layout.addWidget(self.combo_anio)
        toolbar_layout.addWidget(QLabel("Mes:"))
        toolbar_layout.addWidget(self.combo_mes)

        self.combo_anio.setVisible(False)
        self.combo_mes.setVisible(False)

        toolbar_layout.addStretch()

        # Botones de acción
        self.btn_actualizar = QPushButton("Actualizar")
        self.btn_actualizar.clicked.connect(self.actualizar_datos)
        self.btn_actualizar.setMaximumWidth(100)
        self.btn_actualizar.setMinimumHeight(30)
        self.btn_actualizar.setProperty("role", "action")

        self.btn_exportar = QPushButton("Exportar CSV")
        self.btn_exportar.setMaximumWidth(100)
        self.btn_exportar.setMinimumHeight(30)
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setProperty("role", "action")

        toolbar_layout.addWidget(self.btn_actualizar)
        toolbar_layout.addWidget(self.btn_exportar)
        main_layout.addWidget(toolbar_frame)

        # ===== PANEL DE ESTADÍSTICAS =====
        stats_frame = QFrame()
        stats_frame.setObjectName("historialStats")
        stats_layout = QHBoxLayout(stats_frame)

        # Total del día/mes
        self.lbl_total_titulo = QLabel("TOTAL DEL DÍA:")
        self.lbl_total_titulo.setFont(QFont("Arial", 10, QFont.Bold))
        self.lbl_total_titulo.setProperty("role", "field")

        self.lbl_total_valor = QLabel("$0.00")
        self.lbl_total_valor.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_total_valor.setProperty("intent", "success")

        # Productos vendidos
        self.lbl_productos_titulo = QLabel("PRODUCTOS VENDIDOS:")
        self.lbl_productos_titulo.setFont(QFont("Arial", 10, QFont.Bold))
        self.lbl_productos_titulo.setProperty("role", "field")

        self.lbl_productos_valor = QLabel("0")
        self.lbl_productos_valor.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_productos_valor.setProperty("intent", "info")

        # Promedio por producto
        self.lbl_promedio_titulo = QLabel("PROMEDIO POR PRODUCTO:")
        self.lbl_promedio_titulo.setFont(QFont("Arial", 10, QFont.Bold))
        self.lbl_promedio_titulo.setProperty("role", "field")

        self.lbl_promedio_valor = QLabel("$0.00")
        self.lbl_promedio_valor.setFont(QFont("Arial", 16, QFont.Bold))
        self.lbl_promedio_valor.setProperty("intent", "accent")

        grid_stats = QGridLayout()
        grid_stats.addWidget(self.lbl_total_titulo, 0, 0)
        grid_stats.addWidget(self.lbl_total_valor, 1, 0, Qt.AlignCenter)
        grid_stats.addWidget(self.lbl_productos_titulo, 0, 1)
        grid_stats.addWidget(self.lbl_productos_valor, 1, 1, Qt.AlignCenter)
        grid_stats.addWidget(self.lbl_promedio_titulo, 0, 2)
        grid_stats.addWidget(self.lbl_promedio_valor, 1, 2, Qt.AlignCenter)

        stats_layout.addLayout(grid_stats)
        main_layout.addWidget(stats_frame)

        # ===== TABLA DE DATOS =====
        self.tabla_datos = QTableWidget()
        self.tabla_datos.setAlternatingRowColors(True)
        self.tabla_datos.setObjectName("historialTable")
        self.configurar_tabla_dia()
        main_layout.addWidget(self.tabla_datos)

        # ===== BARRA DE ESTADO =====
        status_frame = QFrame()
        status_layout = QHBoxLayout(status_frame)

        self.lbl_estado = QLabel("Listo")
        self.lbl_estado.setProperty("role", "muted")

        self.lbl_ultima_actualizacion = QLabel("Última actualización: --:--:--")
        self.lbl_ultima_actualizacion.setProperty("role", "muted")

        status_layout.addWidget(self.lbl_estado)
        status_layout.addStretch()
        status_layout.addWidget(self.lbl_ultima_actualizacion)

        main_layout.addWidget(status_frame)

        self.setLayout(main_layout)
    
    def configurar_tabla_dia(self):
        """Configura la tabla para vista por día."""
        if self.tabla_datos is None:
            return
            
        self.tabla_datos.setColumnCount(5)
        headers = ["Producto", "Cantidad", "Precio Unitario", "Total", "% del Total"]
        self.tabla_datos.setHorizontalHeaderLabels(headers)
        
        header = self.tabla_datos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
    
    def configurar_tabla_mes(self):
        """Configura la tabla para vista por mes."""
        if self.tabla_datos is None:
            return
            
        self.tabla_datos.setColumnCount(4)
        headers = ["Producto", "Cantidad Total", "Total Dinero", "% del Total"]
        self.tabla_datos.setHorizontalHeaderLabels(headers)
        
        header = self.tabla_datos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
    
    def conectar_señales(self):
        """Conecta las señales del manager."""
        pass
    
    def cargar_datos_iniciales(self):
        """Carga los datos iniciales al mostrar la ventana."""
        self.cargar_rango_fechas()
        self.cargar_datos_dia()
    
    def cargar_rango_fechas(self):
        """Carga el rango de fechas disponibles."""
        try:
            fecha_min, fecha_max = self.historial_manager.obtener_rango_fechas_disponibles()
            if fecha_min and fecha_max:
                fecha_min = QDate.fromString(fecha_min, "yyyy-MM-dd")
                fecha_max = QDate.fromString(fecha_max, "yyyy-MM-dd")
                self.date_edit.setDateRange(fecha_min, fecha_max)
        except Exception as e:
            print(f"Error cargando rango de fechas: {e}")
    
    def cargar_datos_dia(self):
        """Carga las ventas del día seleccionado."""
        if self._actualizando:
            return

        if self.tabla_datos is None:
            return
             
        self._actualizando = True
        fecha = self.date_edit.date().toPyDate()
        
        try:
            ventas = self.historial_manager.obtener_ventas_por_dia(fecha)
            total = float(self.historial_manager.obtener_total_dia(fecha) or 0)
            
            self.tabla_datos.setRowCount(len(ventas))
            
            for i, venta in enumerate(ventas):
                cantidad_total = float(venta.get('cantidad_total', 0) or 0)
                precio_unitario = float(venta.get('precio_unitario', 0) or 0)
                total_dinero = float(venta.get('total_dinero', 0) or 0)
                porcentaje = (total_dinero / total * 100) if total > 0 else 0
                
                self.tabla_datos.setItem(i, 0, QTableWidgetItem(str(venta['producto_nombre'])))
                self.tabla_datos.setItem(i, 1, QTableWidgetItem(str(cantidad_total)))
                self.tabla_datos.setItem(i, 2, QTableWidgetItem(f"${precio_unitario:.2f}"))
                self.tabla_datos.setItem(i, 3, QTableWidgetItem(f"${total_dinero:.2f}"))
                self.tabla_datos.setItem(i, 4, QTableWidgetItem(f"{porcentaje:.1f}%"))
                
                # Alternar colores de fila
                if i % 2 == 0:
                    for col in range(5):
                        item = self.tabla_datos.item(i, col)
                        if item:
                            item.setBackground(QColor(248, 249, 250))
            
            self.actualizar_estadisticas_dia(ventas, total)
            self.lbl_estado.setText(f"Datos cargados para {fecha.strftime('%d/%m/%Y')}")
            self.lbl_ultima_actualizacion.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            error_msg = str(e)
            self.lbl_estado.setText(f"Error: {error_msg}")
            self.lbl_total_valor.setText("$0.00")
            self.tabla_datos.setRowCount(0)
            print(f"❌ Error en cargar_datos_dia: {error_msg}")
        finally:
            self._actualizando = False
    
    def cargar_datos_mes(self):
        """Carga las ventas del mes seleccionado."""
        if self._actualizando:
            return

        if self.tabla_datos is None:
            return
             
        self._actualizando = True
        anio = self.combo_anio.currentData() or QDate.currentDate().year()
        mes = self.combo_mes.currentData() or QDate.currentDate().month()
        
        try:
            ventas_mes = self.historial_manager.obtener_ventas_por_mes(anio, mes)
            total_mes = float(self.historial_manager.obtener_total_mes(anio, mes) or 0)
                 
            self.tabla_datos.setRowCount(len(ventas_mes))
            
            for i, venta in enumerate(ventas_mes):
                cantidad_total = float(venta.get('cantidad_total', 0) or 0)
                total_dinero = float(venta.get('total_dinero', 0) or 0)
                porcentaje = (total_dinero / total_mes * 100) if total_mes > 0 else 0
                
                self.tabla_datos.setItem(i, 0, QTableWidgetItem(str(venta['producto_nombre'])))
                self.tabla_datos.setItem(i, 1, QTableWidgetItem(str(cantidad_total)))
                self.tabla_datos.setItem(i, 2, QTableWidgetItem(f"${total_dinero:.2f}"))
                self.tabla_datos.setItem(i, 3, QTableWidgetItem(f"{porcentaje:.1f}%"))
                
                # Alternar colores de fila
                if i % 2 == 0:
                    for col in range(4):
                        item = self.tabla_datos.item(i, col)
                        if item:
                            item.setBackground(QColor(248, 249, 250))
            
            self.actualizar_estadisticas_mes(ventas_mes, total_mes)
            
            if self.lbl_estado is not None:
                nombre_mes = self.combo_mes.currentText()
                self.lbl_estado.setText(f"Datos cargados para {nombre_mes} {anio}")
                
            if self.lbl_ultima_actualizacion is not None:
                self.lbl_ultima_actualizacion.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"❌ {error_msg}")
            
            try:
                if self.lbl_estado is not None:
                    self.lbl_estado.setText(error_msg)
                if self.lbl_total_valor is not None:
                    self.lbl_total_valor.setText("$0.00")
                if self.tabla_datos is not None:
                    self.tabla_datos.setRowCount(0)
            except:
                pass
        finally:
            self._actualizando = False
    
    def actualizar_estadisticas_dia(self, ventas, total):
        """Actualiza las estadísticas para vista diaria."""
        if self.lbl_total_valor is None or self.lbl_productos_valor is None or self.lbl_promedio_valor is None:
            return

        total = float(total or 0)
             
        self.lbl_total_valor.setText(f"${total:.2f}")
        
        total_productos = sum(float(item.get('cantidad_total', 0) or 0) for item in ventas)
        self.lbl_productos_valor.setText(str(int(total_productos)))
        
        promedio = total / len(ventas) if ventas else 0
        self.lbl_promedio_valor.setText(f"${promedio:.2f}")
    
    def actualizar_estadisticas_mes(self, ventas_mes, total_mes):
        """Actualiza las estadísticas para vista mensual."""
        if self.lbl_total_valor is None or self.lbl_productos_valor is None or self.lbl_promedio_valor is None:
            return

        total_mes = float(total_mes or 0)
             
        self.lbl_total_valor.setText(f"${total_mes:.2f}")
        
        total_productos = sum(float(item.get('cantidad_total', 0) or 0) for item in ventas_mes)
        self.lbl_productos_valor.setText(str(int(total_productos)))
        
        promedio = total_mes / len(ventas_mes) if ventas_mes else 0
        self.lbl_promedio_valor.setText(f"${promedio:.2f}")
    
    @pyqtSlot()
    def actualizar_datos(self):
        """Actualiza todos los datos mostrados."""
        if self._actualizando:
            return
            
        self.historial_manager.limpiar_cache()
        
        if self.combo_vista.currentData() == "dia":
            self.cargar_datos_dia()
        else:
            self.cargar_datos_mes()
    
    def cambiar_vista(self):
        """Cambia entre vista diaria y mensual."""
        vista = self.combo_vista.currentData()
        
        if vista == "dia":
            self.configurar_tabla_dia()
            self.date_edit.setVisible(True)
            self.combo_anio.setVisible(False)
            self.combo_mes.setVisible(False)
            self.cargar_datos_dia()
        else:
            self.configurar_tabla_mes()
            self.date_edit.setVisible(False)
            self.combo_anio.setVisible(True)
            self.combo_mes.setVisible(True)
            self.cargar_datos_mes()
    
    @pyqtSlot()
    def actualizar_ui(self):
        """Actualiza la UI cuando hay nuevos datos."""
        pass
    
    def mostrar_contexto(self, pos):
        """Muestra menú contextual para la tabla."""
        pass
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        self.historial_manager.limpiar_cache()
        event.accept()
