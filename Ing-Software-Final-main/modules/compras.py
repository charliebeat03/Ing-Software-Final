# modules/compras.py - VERSIÓN CORREGIDA DEFINITIVA
import traceback
import sqlite3
from utils.db_operations import DBOperations
from utils.date_utils import get_current_date, format_date
from utils.validators import validate_positive
from utils.safe_output import safe_print as print

class ComprasManager:
    def __init__(self, db_path=None):
        try:
            self.db_ops = DBOperations(db_path) if db_path else DBOperations()
            # Obtener ruta de la BD
            if hasattr(self.db_ops, 'db') and hasattr(self.db_ops.db, 'db_path'):
                self.db_path = self.db_ops.db.db_path
            else:
                self.db_path = db_path or 'data/inventario.db'
            print("✅ ComprasManager inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando ComprasManager: {e}")
            traceback.print_exc()
            self.db_path = db_path or 'data/inventario.db'
            self.db_ops = None
    
    # ========== ✅ FUNCIÓN DE CARGA DE INGREDIENTES (REQUERIDA) ==========
    
    def cargar_ingredientes(self):
        """✅ CARGA INGREDIENTES PARA FORMULARIO DE COMPRAS
        Devuelve: [(id, nombre, unidad), ...] para combobox
        """
        try:
            print("🔄 ComprasManager.cargar_ingredientes() - Cargando para formulario...")
            
            # Importar dinámicamente para evitar circular imports
            from modules.catalogos import CatalogoManager
            
            catalogo = CatalogoManager(self.db_path)
            ingredientes = catalogo.obtener_ingredientes_activos()
            
            if not ingredientes:
                print("⚠️ No se pudieron cargar ingredientes desde catálogo, intentando directo...")
                # FALLBACK: Consulta directa
                ingredientes = self._cargar_ingredientes_directo()
            
            print(f"✅ {len(ingredientes)} ingredientes cargados para compras")
            return ingredientes
            
        except Exception as e:
            print(f"❌ Error en cargar_ingredientes: {e}")
            traceback.print_exc()
            # Último recurso: devolver lista vacía
            return []
    
    def _cargar_ingredientes_directo(self):
        """Carga ingredientes directamente desde BD"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT i.id, i.nombre, um.abreviatura as unidad
                    FROM ingredientes i
                    LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE i.activo = 1
                    ORDER BY i.nombre
                ''')
                resultados = cursor.fetchall()
                # ✅ CORRECCIÓN: Usar acceso por índice en lugar de .get()
                return [(row['id'], row['nombre'], row['unidad']) for row in resultados]
        except sqlite3.Error as e:
            print(f"❌ Error en carga directa de ingredientes: {e}")
            return []
    
    # ========== MANTENER FUNCIONES EXISTENTES (con mejoras) ==========
    
    def registrar_compra(self, ingrediente_id, cantidad, costo_unitario, notas="", fecha=None):
        """Registra una compra de ingredientes"""
        try:
            print(f"📝 ComprasManager.registrar_compra: ingrediente_id={ingrediente_id}, cantidad={cantidad}")
            
            if self.db_ops and hasattr(self.db_ops, 'registrar_compra'):
                # Pasar fecha a db_ops.registrar_compra
                return self.db_ops.registrar_compra(ingrediente_id, cantidad, costo_unitario, notas, fecha)
            
            # FALLBACK: Registro directo
            if fecha is None:
                fecha = get_current_date()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO compras (ingrediente_id, cantidad, costo_unitario, notas, fecha)
                    VALUES (?, ?, ?, ?, ?)
                ''', (ingrediente_id, cantidad, costo_unitario, notas, fecha))
                conn.commit()
                
                # Actualizar stock del ingrediente
                cursor.execute('''
                    UPDATE ingredientes 
                    SET stock_actual = COALESCE(stock_actual, 0) + ? 
                    WHERE id = ?
                ''', (cantidad, ingrediente_id))
                conn.commit()
                
                print(f"✅ Compra registrada exitosamente (ID: {cursor.lastrowid})")
                return cursor.lastrowid
                
        except Exception as e:
            print(f"❌ Error en ComprasManager.registrar_compra: {e}")
            traceback.print_exc()
            raise
    
    def obtener_compras_recientes(self, limite=50):
        """Obtiene las compras más recientes"""
        try:
            if self.db_ops:
                compras = self.db_ops.db.execute_query('''
                    SELECT c.*, i.nombre as ingrediente_nombre, um.abreviatura
                    FROM compras c
                    JOIN ingredientes i ON c.ingrediente_id = i.id
                    JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    ORDER BY c.fecha DESC
                    LIMIT ?
                ''', (limite,))
                if compras:
                    # ✅ CORRECCIÓN CRÍTICA: Convertir sqlite3.Row a diccionario
                    if isinstance(compras, list) and len(compras) > 0 and hasattr(compras[0], '__getitem__'):
                        compras = [dict(row) for row in compras]
                    return compras
            
            # FALLBACK: Consulta directa
            return self._execute_query('''
                SELECT c.*, i.nombre as ingrediente_nombre, um.abreviatura
                FROM compras c
                JOIN ingredientes i ON c.ingrediente_id = i.id
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                ORDER BY c.fecha DESC
                LIMIT ?
            ''', (limite,))
                
        except Exception as e:
            print(f"❌ Error obteniendo compras recientes: {e}")
            traceback.print_exc()
            return []
    
    def obtener_compras_por_fecha(self, fecha_inicio, fecha_fin=None):
        """Obtiene compras en un rango de fechas"""
        try:
            if fecha_fin is None:
                fecha_fin = get_current_date()
            
            # Asegurar formato de fechas
            if hasattr(fecha_inicio, 'strftime'):
                fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
            if hasattr(fecha_fin, 'strftime'):
                fecha_fin = fecha_fin.strftime('%Y-%m-%d')
            
            if self.db_ops:
                compras = self.db_ops.db.execute_query('''
                    SELECT c.*, i.nombre as ingrediente_nombre, um.abreviatura
                    FROM compras c
                    JOIN ingredientes i ON c.ingrediente_id = i.id
                    JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE date(c.fecha) BETWEEN ? AND ?
                    ORDER BY c.fecha DESC
                ''', (fecha_inicio, fecha_fin))
                if compras:
                    # ✅ CORRECCIÓN CRÍTICA: Convertir sqlite3.Row a diccionario
                    if isinstance(compras, list) and len(compras) > 0 and hasattr(compras[0], '__getitem__'):
                        compras = [dict(row) for row in compras]
                    return compras
            
            # FALLBACK: Consulta directa
            return self._execute_query('''
                SELECT c.*, i.nombre as ingrediente_nombre, um.abreviatura
                FROM compras c
                JOIN ingredientes i ON c.ingrediente_id = i.id
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE date(c.fecha) BETWEEN ? AND ?
                ORDER BY c.fecha DESC
            ''', (fecha_inicio, fecha_fin))
                
        except Exception as e:
            print(f"❌ Error obteniendo compras por fecha: {e}")
            traceback.print_exc()
            return []
    
    def obtener_total_compras_periodo(self, fecha_inicio, fecha_fin=None):
        """Obtiene el total de compras en un período"""
        try:
            if fecha_fin is None:
                fecha_fin = get_current_date()
            
            # Asegurar formato de fechas
            if hasattr(fecha_inicio, 'strftime'):
                fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
            if hasattr(fecha_fin, 'strftime'):
                fecha_fin = fecha_fin.strftime('%Y-%m-%d')
            
            if self.db_ops:
                resultado = self.db_ops.db.execute_query('''
                    SELECT SUM(cantidad * costo_unitario) as total_compras
                    FROM compras
                    WHERE date(fecha) BETWEEN ? AND ?
                ''', (fecha_inicio, fecha_fin))
                
                # ✅ CORRECCIÓN: Acceder correctamente al resultado
                if resultado:
                    # Convertir sqlite3.Row si es necesario
                    if hasattr(resultado[0], '__getitem__'):
                        row = dict(resultado[0])
                        total = row.get('total_compras', 0)
                    else:
                        total = resultado[0].get('total_compras', 0)
                    return float(total) if total else 0
            
            # FALLBACK: Consulta directa
            resultado = self._execute_query('''
                SELECT SUM(cantidad * costo_unitario) as total_compras
                FROM compras
                WHERE date(fecha) BETWEEN ? AND ?
            ''', (fecha_inicio, fecha_fin))
            
            if resultado and resultado[0]['total_compras'] is not None:
                return float(resultado[0]['total_compras'])
            else:
                return 0
                
        except Exception as e:
            print(f"❌ Error obteniendo total compras período: {e}")
            traceback.print_exc()
            return 0
    
    def obtener_ingredientes_mas_comprados(self, limite=10):
        """Obtiene los ingredientes más comprados"""
        try:
            if self.db_ops:
                resultado = self.db_ops.db.execute_query('''
                    SELECT i.nombre, SUM(c.cantidad) as total_cantidad, 
                           SUM(c.cantidad * c.costo_unitario) as total_costo, um.abreviatura
                    FROM compras c
                    JOIN ingredientes i ON c.ingrediente_id = i.id
                    JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    GROUP BY c.ingrediente_id
                    ORDER BY total_costo DESC
                    LIMIT ?
                ''', (limite,))
                if resultado:
                    # ✅ CORRECCIÓN CRÍTICA: Convertir sqlite3.Row a diccionario
                    if isinstance(resultado, list) and len(resultado) > 0 and hasattr(resultado[0], '__getitem__'):
                        resultado = [dict(row) for row in resultado]
                    return resultado
            
            # FALLBACK: Consulta directa
            return self._execute_query('''
                SELECT i.nombre, SUM(c.cantidad) as total_cantidad, 
                       SUM(c.cantidad * c.costo_unitario) as total_costo, um.abreviatura
                FROM compras c
                JOIN ingredientes i ON c.ingrediente_id = i.id
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                GROUP BY c.ingrediente_id
                ORDER BY total_costo DESC
                LIMIT ?
            ''', (limite,))
                
        except Exception as e:
            print(f"❌ Error obteniendo ingredientes más comprados: {e}")
            traceback.print_exc()
            return []
    
    def _execute_query(self, query, params=()):
        """Método helper para ejecutar consultas directas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                resultados = cursor.fetchall()
                # ✅ CORRECCIÓN CRÍTICA: Convertir sqlite3.Row a diccionario
                return [dict(row) for row in resultados]
        except sqlite3.Error as e:
            print(f"❌ Error en consulta directa (compras): {e}")
            return []
