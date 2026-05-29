# modules/produccion.py - VERSIÓN CORREGIDA COMPLETA v2.0
import traceback
import sqlite3
from datetime import datetime
from utils.safe_output import safe_print as print

class ProduccionManager:
    def __init__(self, db_path=None):
        try:
            from database import db
            self.db = db
            self.db_path = 'data/inventario.db'
            print("✅ ProduccionManager v2.0 inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando ProduccionManager: {e}")
            self.db_path = db_path or 'data/inventario.db'
            self.db = None
    
    def _execute_query(self, query, params=(), commit=False):
        """Ejecuta consulta directa a la BD (backup si db falla)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                resultados = cursor.fetchall()
                return [dict(row) for row in resultados]
        except sqlite3.Error as e:
            print(f"❌ Error en consulta directa: {e}")
            return []
    
    def registrar_produccion(self, producto_id, cantidad, notas="", fecha=None):
        """Registra producción con hora actual (CORREGIDO v2.0)"""
        try:
            print(f"🔄 ProduccionManager.registrar_produccion v2.0: producto_id={producto_id}, cantidad={cantidad}")
            
            # ✅ CORRECCIÓN: Validar cantidad más robusta
            try:
                # Intentar convertir a entero
                cantidad_num = int(cantidad)
                if cantidad_num <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")
            except (ValueError, TypeError) as e:
                # Si falla, intentar convertir a float y luego a entero
                try:
                    cantidad_num = int(float(cantidad))
                    if cantidad_num <= 0:
                        raise ValueError("La cantidad debe ser mayor a 0")
                except:
                    raise ValueError(f"Cantidad inválida: '{cantidad}'. Debe ser un número entero positivo")
            
            # Usar fecha actual si no se proporciona
            if fecha is None:
                fecha = datetime.now().strftime('%Y-%m-%d')
            
            # Registrar en la base de datos
            if self.db and hasattr(self.db, 'execute_insert'):
                try:
                    produccion_id = self.db.execute_insert(
                        '''INSERT INTO produccion 
                           (fecha, hora, producto_id, cantidad, notas, fecha_registro) 
                           VALUES (?, CURRENT_TIME, ?, ?, ?, CURRENT_TIMESTAMP)''',
                        (fecha, producto_id, cantidad_num, notas)
                    )
                    print(f"✅ Producción registrada mediante Database: ID {produccion_id}")
                    
                    # Actualizar inventario
                    self.actualizar_inventario_produccion(producto_id, cantidad_num)
                    
                    return produccion_id
                except Exception as e:
                    print(f"⚠️ Error con Database.execute_insert: {e}, usando fallback")
            
            # FALLBACK: Inserción directa
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que el producto existe
                cursor.execute('SELECT id FROM productos WHERE id = ?', (producto_id,))
                producto = cursor.fetchone()
                
                if not producto:
                    raise ValueError(f"Producto con ID {producto_id} no encontrado")
                
                # Insertar producción (con columna hora)
                cursor.execute('''
                    INSERT INTO produccion 
                    (fecha, hora, producto_id, cantidad, notas, fecha_registro)
                    VALUES (?, CURRENT_TIME, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (fecha, producto_id, cantidad_num, notas))
                
                conn.commit()
                produccion_id = cursor.lastrowid
                
                # Actualizar inventario
                self.actualizar_inventario_produccion(producto_id, cantidad_num)
                
                print(f"✅ Producción registrada exitosamente: ID {produccion_id} para producto ID {producto_id}")
                return produccion_id
                
        except Exception as e:
            print(f"❌ Error registrando producción: {e}")
            traceback.print_exc()
            raise
    
    def obtener_produccion_dia(self, fecha=None):
        """Obtiene la producción de un día específico"""
        try:
            if fecha is None:
                fecha = datetime.now().strftime('%Y-%m-%d')
            
            query = '''
            SELECT 
                pr.id,
                pr.fecha,
                pr.hora,
                p.nombre,
                pr.cantidad,
                p.unidad_venta,
                pr.notas,
                p.precio_venta,
                pr.producto_id
            FROM produccion pr
            JOIN productos p ON pr.producto_id = p.id
            WHERE pr.fecha = ?
            ORDER BY pr.hora DESC
            '''
            
            if self.db:
                return self.db.execute_cached_query(query, (fecha,), cache_ttl=30)
            else:
                return self._execute_query(query, (fecha,))
            
        except Exception as e:
            print(f"❌ Error obteniendo producción del día: {e}")
            traceback.print_exc()
            return []
    
    def obtener_total_produccion_dia(self, fecha=None):
        """Obtiene el total de producción del día"""
        try:
            if fecha is None:
                fecha = datetime.now().strftime('%Y-%m-%d')
            
            query = '''
            SELECT SUM(cantidad) as total
            FROM produccion
            WHERE fecha = ?
            '''
            
            if self.db:
                result = self.db.execute_query(query, (fecha,))
            else:
                result = self._execute_query(query, (fecha,))
            
            return result[0]['total'] if result and result[0]['total'] else 0
            
        except Exception as e:
            print(f"❌ Error obteniendo total de producción: {e}")
            return 0
    
    def obtener_produccion_rango(self, fecha_inicio, fecha_fin):
        """Obtiene producción en un rango de fechas"""
        try:
            if self.db:
                query = '''
                SELECT pr.fecha, p.nombre, SUM(pr.cantidad) as total
                FROM produccion pr
                JOIN productos p ON pr.producto_id = p.id
                WHERE pr.fecha BETWEEN ? AND ?
                GROUP BY pr.fecha, pr.producto_id
                ORDER BY pr.fecha DESC
                '''
                return self.db.execute_cached_query(query, (fecha_inicio, fecha_fin), cache_ttl=300)
            else:
                return self._execute_query(query, (fecha_inicio, fecha_fin))
            
        except Exception as e:
            print(f"❌ Error obteniendo producción por rango: {e}")
            traceback.print_exc()
            return []
    
    def obtener_productos_activos(self):
        """Obtiene productos activos para producción"""
        try:
            if self.db and hasattr(self.db, 'get_all'):
                productos = self.db.get_all('productos', 'activo = 1')
                return [(p['id'], p['nombre'], p['precio_venta'], p['unidad_venta']) for p in productos]
            else:
                return self._execute_query('SELECT id, nombre, precio_venta, unidad_venta FROM productos WHERE activo = 1')
        except Exception as e:
            print(f"❌ Error obteniendo productos activos: {e}")
            return []
    
    def obtener_productos_mas_producidos(self, dias=30):
        """Obtiene los productos más producidos en un período"""
        try:
            query = '''
            SELECT 
                p.nombre,
                SUM(pr.cantidad) as total_producido,
                p.unidad_venta,
                COUNT(pr.id) as frecuencia
            FROM produccion pr
            JOIN productos p ON pr.producto_id = p.id
            WHERE pr.fecha >= date('now', ?)
            GROUP BY pr.producto_id
            ORDER BY total_producido DESC
            LIMIT 10
            '''
            
            days_param = f'-{dias} days'
            
            if self.db:
                return self.db.execute_cached_query(query, (days_param,), cache_ttl=300)
            else:
                return self._execute_query(query, (days_param,))
                
        except Exception as e:
            print(f"❌ Error obteniendo productos más producidos: {e}")
            return []
    
    def actualizar_inventario_produccion(self, producto_id, cantidad):
        """Actualiza el inventario después de producción"""
        try:
            print(f"🔄 Actualizando inventario por producción: producto_id={producto_id}, cantidad={cantidad}")
            
            if self.db and hasattr(self.db, 'execute_query'):
                # Verificar si ya existe registro en inventario
                inventario = self.db.execute_query(
                    'SELECT * FROM inventario_productos WHERE producto_id = ?', 
                    (producto_id,)
                )
                
                if inventario:
                    # Actualizar existente
                    self.db.execute_query(
                        '''UPDATE inventario_productos 
                           SET cantidad_disponible = cantidad_disponible + ?, 
                               fecha_actualizacion = CURRENT_TIMESTAMP 
                           WHERE producto_id = ?''',
                        (cantidad, producto_id)
                    )
                else:
                    # Insertar nuevo
                    self.db.execute_insert(
                        '''INSERT INTO inventario_productos 
                           (producto_id, cantidad_disponible, fecha_actualizacion) 
                           VALUES (?, ?, CURRENT_TIMESTAMP)''',
                        (producto_id, cantidad)
                    )
                
                print(f"✅ Inventario actualizado: +{cantidad} para producto ID {producto_id}")
                return True
            else:
                # Fallback directo
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT * FROM inventario_productos WHERE producto_id = ?', (producto_id,))
                    if cursor.fetchone():
                        cursor.execute(
                            '''UPDATE inventario_productos 
                               SET cantidad_disponible = cantidad_disponible + ?, 
                                   fecha_actualizacion = CURRENT_TIMESTAMP 
                               WHERE producto_id = ?''',
                            (cantidad, producto_id)
                        )
                    else:
                        cursor.execute(
                            '''INSERT INTO inventario_productos 
                               (producto_id, cantidad_disponible, fecha_actualizacion) 
                               VALUES (?, ?, CURRENT_TIMESTAMP)''',
                            (producto_id, cantidad)
                        )
                    
                    conn.commit()
                    print(f"✅ Inventario actualizado (fallback): +{cantidad} para producto ID {producto_id}")
                    return True
                    
        except Exception as e:
            print(f"❌ Error actualizando inventario por producción: {e}")
            traceback.print_exc()
            return False
    
    def cancelar_ultima_produccion(self, producto_id, fecha=None):
        """Cancela la última producción de un producto"""
        try:
            print(f"🔄 Cancelando última producción del producto: {producto_id}")
            
            if fecha is None:
                fecha = datetime.now().strftime('%Y-%m-%d')
            
            # Obtener la última producción del producto en la fecha
            query = '''
            SELECT id, cantidad
            FROM produccion
            WHERE producto_id = ? AND fecha = ?
            ORDER BY hora DESC
            LIMIT 1
            '''
            
            if self.db:
                producciones = self.db.execute_query(query, (producto_id, fecha))
            else:
                producciones = self._execute_query(query, (producto_id, fecha))
            
            if not producciones:
                raise ValueError(f"No hay producción para cancelar del producto {producto_id} en la fecha {fecha}")
            
            produccion_id = producciones[0]['id']
            cantidad = producciones[0]['cantidad']
            
            # Eliminar la producción
            delete_query = 'DELETE FROM produccion WHERE id = ?'
            
            if self.db:
                self.db.execute_query(delete_query, (produccion_id,))
            else:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(delete_query, (produccion_id,))
                    conn.commit()
            
            # Actualizar inventario (restar)
            self.actualizar_inventario_produccion(producto_id, -cantidad)
            
            print(f"✅ Producción cancelada exitosamente (ID: {produccion_id})")
            return {
                'produccion_id': produccion_id,
                'cantidad': cantidad,
                'producto_id': producto_id
            }
            
        except Exception as e:
            print(f"❌ Error cancelando producción: {e}")
            traceback.print_exc()
            raise
    
    # ========== NUEVOS MÉTODOS v2.0 ==========
    
    def agregar_produccion_a_ventas(self, produccion_id):
        """Agrega una producción específica a las ventas del día"""
        try:
            print(f"🔄 Agregando producción a ventas: ID {produccion_id}")
            
            # Obtener datos de la producción
            query = '''
            SELECT pr.cantidad, pr.producto_id, pr.fecha, p.precio_venta, p.nombre
            FROM produccion pr
            JOIN productos p ON pr.producto_id = p.id
            WHERE pr.id = ?
            '''
            
            if self.db:
                produccion = self.db.execute_query(query, (produccion_id,))
            else:
                produccion = self._execute_query(query, (produccion_id,))
            
            if not produccion:
                raise ValueError(f"Producción con ID {produccion_id} no encontrada")
            
            prod = produccion[0]
            cantidad = prod['cantidad']
            producto_id = prod['producto_id']
            fecha = prod['fecha']
            precio = prod['precio_venta']
            producto_nombre = prod['nombre']
            
            # Importar VentasManager
            from modules.ventas import VentasManager
            ventas_manager = VentasManager()
            
            # Agregar a ventas
            venta_id = ventas_manager.registrar_venta(producto_id, cantidad, precio, fecha)
            
            print(f"✅ Producción agregada a ventas: Venta ID {venta_id}")
            
            return {
                'venta_id': venta_id,
                'produccion_id': produccion_id,
                'producto_nombre': producto_nombre,
                'cantidad': cantidad,
                'precio': precio,
                'total_venta': cantidad * precio
            }
            
        except Exception as e:
            print(f"❌ Error agregando producción a ventas: {e}")
            traceback.print_exc()
            raise
