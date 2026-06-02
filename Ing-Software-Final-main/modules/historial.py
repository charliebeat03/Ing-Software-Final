"""
Módulo de Historial y Reportes para el sistema "A TU GUSTO"
v2.0 - Integrado con database.py optimizado
"""

from datetime import datetime, timedelta
from PyQt5.QtCore import QObject, pyqtSignal
from database import db

class HistorialManager(QObject):
    """Gestor principal de historial y reportes de ventas."""
    
    # Señal para actualización de datos
    datos_actualizados = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.cache_reportes = {}
        self.cache_tiempo = {}
    
    def obtener_ventas_por_dia(self, fecha):
        """
        Obtiene ventas detalladas para una fecha específica.
        
        Args:
            fecha (datetime.date): Fecha a consultar
            
        Returns:
            list: Lista de diccionarios con:
                - producto_nombre
                - cantidad_total
                - precio_unitario
                - total_dinero
        """
        # Usar cache si está disponible
        if isinstance(fecha, datetime):
            fecha_str = fecha.strftime('%Y-%m-%d')
        else:
            fecha_str = str(fecha)
            
        cache_key = f"ventas_dia_{fecha_str}"
        if cache_key in self.cache_reportes:
            if datetime.now() - self.cache_tiempo[cache_key] < timedelta(minutes=5):
                return self.cache_reportes[cache_key]
        
        try:
            # Consulta optimizada
            query = """
            SELECT 
                p.nombre as producto_nombre,
                v.cantidad_total,
                p.precio_venta as precio_unitario,
                v.total_ventas as total_dinero
            FROM ventas v
            INNER JOIN productos p ON v.producto_id = p.id
            WHERE v.fecha = ?
            ORDER BY v.total_ventas DESC
            """
            
            resultados = db.execute_query(query, (fecha_str,))
            
            ventas = []
            for row in resultados:
                venta_dict = dict(row)
                # Manejo seguro de valores None
                cantidad = venta_dict.get('cantidad_total')
                precio = venta_dict.get('precio_unitario')
                total = venta_dict.get('total_dinero')
                
                ventas.append({
                    'producto_nombre': str(venta_dict.get('producto_nombre', '')),
                    'cantidad_total': float(cantidad) if cantidad is not None else 0.0,
                    'precio_unitario': float(precio) if precio is not None else 0.0,
                    'total_dinero': float(total) if total is not None else 0.0
                })
            
            # Actualizar cache
            self.cache_reportes[cache_key] = ventas
            self.cache_tiempo[cache_key] = datetime.now()
            
            return ventas
            
        except Exception as e:
            print(f"❌ Error en obtener_ventas_por_dia: {e}")
            return []
    
    def obtener_total_dia(self, fecha):
        """
        Obtiene el total monetario de ventas para una fecha.
        
        Args:
            fecha (datetime.date): Fecha a consultar
            
        Returns:
            float: Total del día
        """
        ventas = self.obtener_ventas_por_dia(fecha)
        total = sum(item.get('total_dinero', 0) for item in ventas)
        return float(total)
    
    def obtener_ventas_por_mes(self, año, mes):
        """
        Obtiene resumen de ventas por producto para un mes específico.
        
        Args:
            año (int): Año a consultar
            mes (int): Mes a consultar (1-12)
            
        Returns:
            list: Lista de diccionarios con:
                - producto_nombre
                - cantidad_total
                - total_dinero
        """
        cache_key = f"ventas_mes_{año}_{mes:02d}"
        if cache_key in self.cache_reportes:
            if datetime.now() - self.cache_tiempo[cache_key] < timedelta(minutes=10):
                return self.cache_reportes[cache_key]
        
        try:
            query = """
            SELECT 
                p.nombre as producto_nombre,
                SUM(v.cantidad_total) as cantidad_total,
                SUM(v.total_ventas) as total_dinero
            FROM ventas v
            INNER JOIN productos p ON v.producto_id = p.id
            WHERE strftime('%Y', v.fecha) = ? 
              AND strftime('%m', v.fecha) = ?
            GROUP BY v.producto_id
            ORDER BY total_dinero DESC
            """
            
            resultados = db.execute_query(query, (str(año), f"{mes:02d}"))
            
            ventas_mes = []
            for row in resultados:
                venta_dict = dict(row)
                # Manejo seguro de valores None
                cantidad = venta_dict.get('cantidad_total')
                total = venta_dict.get('total_dinero')
                
                ventas_mes.append({
                    'producto_nombre': str(venta_dict.get('producto_nombre', '')),
                    'cantidad_total': float(cantidad) if cantidad is not None else 0.0,
                    'total_dinero': float(total) if total is not None else 0.0
                })
            
            # Actualizar cache
            self.cache_reportes[cache_key] = ventas_mes
            self.cache_tiempo[cache_key] = datetime.now()
            
            return ventas_mes
            
        except Exception as e:
            print(f"❌ Error en obtener_ventas_por_mes: {e}")
            return []
    
    def obtener_total_mes(self, año, mes):
        """
        Obtiene el total monetario de ventas para un mes.
        
        Args:
            año (int): Año a consultar
            mes (int): Mes a consultar (1-12)
            
        Returns:
            float: Total del mes
        """
        ventas_mes = self.obtener_ventas_por_mes(año, mes)
        total = sum(item.get('total_dinero', 0) for item in ventas_mes)
        return float(total)
    
    def obtener_productos_mas_vendidos(self, dias=7):
        """
        Obtiene los productos más vendidos en los últimos N días.
        
        Args:
            dias (int): Número de días hacia atrás
            
        Returns:
            list: Lista de productos ordenados por ventas
        """
        fecha_inicio = datetime.now() - timedelta(days=dias)
        fecha_str = fecha_inicio.strftime('%Y-%m-%d')
        
        try:
            query = """
            SELECT 
                p.nombre as producto_nombre,
                SUM(v.cantidad_total) as cantidad_total,
                SUM(v.total_ventas) as total_dinero
            FROM ventas v
            INNER JOIN productos p ON v.producto_id = p.id
            WHERE v.fecha >= ?
            GROUP BY p.nombre
            ORDER BY cantidad_total DESC
            LIMIT 10
            """
            
            resultados = db.execute_query(query, (fecha_str,))
            
            productos = []
            for row in resultados:
                venta_dict = dict(row)
                cantidad = venta_dict.get('cantidad_total')
                total = venta_dict.get('total_dinero')
                
                productos.append({
                    'producto_nombre': str(venta_dict.get('producto_nombre', '')),
                    'cantidad_total': float(cantidad) if cantidad is not None else 0.0,
                    'total_dinero': float(total) if total is not None else 0.0
                })
            
            return productos
            
        except Exception as e:
            print(f"❌ Error en obtener_productos_mas_vendidos: {e}")
            return []
    
    def limpiar_cache(self):
        """Limpia el cache de reportes."""
        self.cache_reportes.clear()
        self.cache_tiempo.clear()
        # NO emitir señal aquí para evitar recursión
        # self.datos_actualizados.emit()
    
    def obtener_rango_fechas_disponibles(self):
        """
        Obtiene el rango de fechas con datos disponibles.
        
        Returns:
            tuple: (fecha_minima, fecha_maxima)
        """
        try:
            query = "SELECT MIN(fecha), MAX(fecha) FROM ventas"
            resultados = db.execute_query(query)
            
            if resultados and resultados[0]:
                fecha_min, fecha_max = resultados[0][0], resultados[0][1]
                if fecha_min and fecha_max:
                    return fecha_min, fecha_max
            return None, None
            
        except Exception as e:
            print(f"❌ Error en obtener_rango_fechas_disponibles: {e}")
            return None, None