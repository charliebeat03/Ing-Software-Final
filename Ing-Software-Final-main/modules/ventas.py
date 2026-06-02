# modules/ventas.py - Módulo de ventas corregido y optimizado v2.0
import traceback
import sqlite3
from datetime import datetime, date
from utils.db_operations import DBOperations
from utils.calculos import calcular_excedentes_dia
from utils.safe_output import safe_print as print

class VentasManager:
    def __init__(self, db_path=None):
        try:
            self.db_path = db_path or 'data/inventario.db'
            print(f"✅ VentasManager v2.0 inicializado con db_path: {self.db_path}")
            
            # Cache para evitar consultas repetidas (OPTIMIZACIÓN v2.0)
            self._cache = {
                'ventas_dia': None,
                'detalle_dia': None,
                'productos': None,
                'last_update': None
            }
            
            # Usar DBOperations optimizado
            try:
                self.db_ops = DBOperations(self.db_path)
                print("✅ DBOperations inicializado correctamente")
            except Exception as e:
                print(f"⚠️ DBOperations no pudo inicializarse: {e}")
                self.db_ops = None
                
        except Exception as e:
            print(f"❌ Error inicializando VentasManager: {e}")
            traceback.print_exc()
            self.db_path = db_path or 'data/inventario.db'
            self.db_ops = None
            self._cache = {}
    
    def _clear_cache(self):
        """Limpia la cache para forzar actualización"""
        self._cache = {
            'ventas_dia': None,
            'detalle_dia': None,
            'productos': None,
            'last_update': None
        }
        print("🔄 Cache de ventas limpiado")
    
    def cargar_productos(self):
        """Carga productos para formulario de ventas"""
        try:
            # Verificar cache primero
            if self._cache.get('productos') and self._cache.get('last_update'):
                tiempo_transcurrido = (datetime.now() - self._cache['last_update']).total_seconds()
                if tiempo_transcurrido < 60:  # 1 minuto de cache
                    print("✅ Productos obtenidos desde cache")
                    return self._cache['productos']
            
            print("🔄 VentasManager.cargar_productos() - Cargando desde BD...")
            
            try:
                from modules.catalogos import CatalogoManager
                catalogo = CatalogoManager(self.db_path)
                productos = catalogo.obtener_productos_activos()
            except Exception as e:
                print(f"⚠️ Error importando CatalogoManager: {e}")
                productos = self._cargar_productos_directo()
            
            if not productos:
                print("⚠️ No se pudieron cargar productos desde catálogo, intentando directo...")
                productos = self._cargar_productos_directo()
            
            # Actualizar cache
            self._cache['productos'] = productos
            self._cache['last_update'] = datetime.now()
            
            print(f"✅ {len(productos)} productos cargados para ventas")
            return productos
            
        except Exception as e:
            print(f"❌ Error en cargar_productos: {e}")
            traceback.print_exc()
            return []
    
    def _cargar_productos_directo(self):
        """Carga productos directamente desde BD"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, nombre, precio_venta, unidad_venta
                    FROM productos
                    WHERE activo = 1
                    ORDER BY nombre
                ''')
                resultados = cursor.fetchall()
                return [(row['id'], row['nombre'], row['precio_venta'], row['unidad_venta']) 
                       for row in resultados]
        except sqlite3.Error as e:
            print(f"❌ Error en carga directa de productos: {e}")
            return []
    
    def registrar_venta(self, producto_id, cantidad):
        """Registra una venta - CORREGIDO v2.0 (sin desfase)"""
        try:
            print(f"📝 VentasManager.registrar_venta v2.0: producto_id={producto_id}, cantidad={cantidad}")
            
            # Validación
            try:
                cantidad_num = float(cantidad)
                if cantidad_num <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")
                if cantidad_num > 10000:
                    raise ValueError("La cantidad es demasiado grande")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cantidad inválida: {str(e)}")
            
            # Usar una sola transacción para evitar desfase
            fecha_actual = date.today().isoformat()
            hora_actual = datetime.now().strftime('%H:%M:%S')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Obtener precio del producto
                cursor.execute('SELECT precio_venta FROM productos WHERE id = ?', (producto_id,))
                producto = cursor.fetchone()
                
                if not producto:
                    raise ValueError(f"Producto con ID {producto_id} no encontrado")
                
                precio = producto['precio_venta']
                total_venta = cantidad_num * precio
                
                # Buscar si ya existe una venta hoy para este producto
                cursor.execute('''
                    SELECT id, cantidad_total, total_ventas FROM ventas
                    WHERE fecha = ? AND producto_id = ?
                ''', (fecha_actual, producto_id))
                venta_existente = cursor.fetchone()
                
                if venta_existente:
                    # Actualizar venta existente
                    nueva_cantidad = venta_existente['cantidad_total'] + cantidad_num
                    nuevo_total = venta_existente['total_ventas'] + total_venta
                    
                    cursor.execute('''
                        UPDATE ventas 
                        SET cantidad_total = ?, total_ventas = ?
                        WHERE id = ?
                    ''', (nueva_cantidad, nuevo_total, venta_existente['id']))
                    venta_id = venta_existente['id']
                else:
                    # Insertar nueva venta
                    cursor.execute('''
                        INSERT INTO ventas (producto_id, cantidad_total, total_ventas, fecha)
                        VALUES (?, ?, ?, ?)
                    ''', (producto_id, cantidad_num, total_venta, fecha_actual))
                    venta_id = cursor.lastrowid
                
                # Registrar detalle con hora actual
                cursor.execute('''
                    INSERT INTO ventas_detalle (venta_id, cantidad, hora)
                    VALUES (?, ?, ?)
                ''', (venta_id, cantidad_num, hora_actual))
                
                # Actualizar inventario en la misma transacción
                self._actualizar_inventario_producto(cursor, producto_id, cantidad_num, 'restar')
                
                conn.commit()
                
                # Calcular excedentes
                try:
                    calcular_excedentes_dia(fecha_actual)
                except Exception as e:
                    print(f"⚠️ Error calculando excedentes: {e}")
                
                # Limpiar cache para forzar actualización
                self._clear_cache()
                
                print(f"✅ Venta registrada exitosamente (ID: {venta_id}) en una sola transacción")
                return total_venta
                
        except Exception as e:
            print(f"❌ Error registrando venta: {e}")
            traceback.print_exc()
            raise
    
    def _actualizar_inventario_producto(self, cursor, producto_id, cantidad, operacion):
        """Actualiza el inventario del producto"""
        try:
            cursor.execute('''
                SELECT id, cantidad_disponible FROM inventario_productos 
                WHERE producto_id = ?
            ''', (producto_id,))
            
            inventario = cursor.fetchone()
            
            if inventario:
                cantidad_actual = inventario['cantidad_disponible']
                
                if operacion == 'restar':
                    nueva_cantidad = cantidad_actual - cantidad
                else:  # sumar
                    nueva_cantidad = cantidad_actual + cantidad
                
                if nueva_cantidad < 0:
                    nueva_cantidad = 0
                    print(f"⚠️ Atención: Inventario quedaría negativo, se establece a 0")
                
                cursor.execute('''
                    UPDATE inventario_productos 
                    SET cantidad_disponible = ?
                    WHERE producto_id = ?
                ''', (nueva_cantidad, producto_id))
            else:
                if operacion == 'restar':
                    cursor.execute('''
                        INSERT INTO inventario_productos (producto_id, cantidad_disponible)
                        VALUES (?, 0)
                    ''', (producto_id,))
                    print(f"⚠️ Producto {producto_id} creado con inventario 0. No se puede restar.")
                else:
                    cursor.execute('''
                        INSERT INTO inventario_productos (producto_id, cantidad_disponible)
                        VALUES (?, ?)
                    ''', (producto_id, cantidad))
            
        except Exception as e:
            print(f"❌ Error actualizando inventario: {e}")
            raise
    
    def obtener_ventas_dia(self, fecha=None, force_refresh=False):
        """Obtiene las ventas acumuladas del día - CORREGIDO v2.0"""
        try:
            # Verificar cache si no se fuerza refresco
            if not force_refresh and self._cache.get('ventas_dia'):
                tiempo_transcurrido = (datetime.now() - self._cache['last_update']).total_seconds()
                if tiempo_transcurrido < 5:  # 5 segundos de cache
                    print("✅ Ventas obtenidas desde cache")
                    return self._cache['ventas_dia']
            
            print("🔄 VentasManager.obtener_ventas_dia() v2.0...")
            
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            # Usar conexión dedicada para consistencia
            ventas = self._execute_query('''
                SELECT 
                    p.nombre,
                    v.cantidad_total as cantidad,
                    p.precio_venta as precio,
                    v.total_ventas as total,
                    p.unidad_venta,
                    v.id as venta_id,
                    p.id as producto_id
                FROM ventas v
                JOIN productos p ON v.producto_id = p.id
                WHERE v.fecha = ?
                ORDER BY v.id DESC
            ''', (fecha_str,))
            
            # Actualizar cache
            self._cache['ventas_dia'] = ventas
            self._cache['last_update'] = datetime.now()
            
            print(f"✅ {len(ventas)} ventas obtenidas (consistente)")
            return ventas
            
        except Exception as e:
            print(f"❌ Error obteniendo ventas del día: {e}")
            traceback.print_exc()
            return []
    
    def obtener_detalle_ventas_dia(self, fecha=None, force_refresh=False):
        """Obtiene el detalle histórico de ventas del día - CORREGIDO v2.0"""
        try:
            # Verificar cache si no se fuerza refresco
            if not force_refresh and self._cache.get('detalle_dia'):
                tiempo_transcurrido = (datetime.now() - self._cache['last_update']).total_seconds()
                if tiempo_transcurrido < 5:  # 5 segundos de cache
                    print("✅ Detalle obtenido desde cache")
                    return self._cache['detalle_dia']
            
            print("🔄 VentasManager.obtener_detalle_ventas_dia() v2.0...")
            
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            # Misma lógica de fecha que obtener_ventas_dia para consistencia
            detalle = self._execute_query('''
                SELECT 
                    vd.hora,
                    p.nombre,
                    vd.cantidad,
                    p.precio_venta as precio,
                    (vd.cantidad * p.precio_venta) as total,
                    p.id as id_producto,
                    p.unidad_venta,
                    vd.id as detalle_id,
                    vd.venta_id
                FROM ventas_detalle vd
                JOIN ventas v ON vd.venta_id = v.id
                JOIN productos p ON v.producto_id = p.id
                WHERE v.fecha = ?
                ORDER BY vd.hora DESC
            ''', (fecha_str,))
            
            # Actualizar cache
            self._cache['detalle_dia'] = detalle
            self._cache['last_update'] = datetime.now()
            
            print(f"✅ {len(detalle)} registros de detalle obtenidos (consistente)")
            return detalle
            
        except Exception as e:
            print(f"❌ Error obteniendo detalle de ventas: {e}")
            traceback.print_exc()
            return []
    
    def obtener_total_ventas_dia(self, fecha=None):
        """Obtiene el total de ventas del día en dinero"""
        try:
            ventas = self.obtener_ventas_dia(fecha)
            total = sum(float(v.get('total', 0)) for v in ventas)
            return total
        except Exception as e:
            print(f"❌ Error calculando total ventas día: {e}")
            return 0
    
    def obtener_cantidad_ventas_dia(self, fecha=None):
        """Obtiene la cantidad total de productos vendidos en el día"""
        try:
            ventas = self.obtener_ventas_dia(fecha)
            cantidad = sum(float(v.get('cantidad', 0)) for v in ventas)
            return cantidad
        except Exception as e:
            print(f"❌ Error calculando cantidad ventas día: {e}")
            return 0
    
    def obtener_productos_mas_vendidos(self, dias=30):
        """Obtiene los productos más vendidos en un período"""
        try:
            print(f"🔄 Obteniendo productos más vendidos (últimos {dias} días)...")
            
            fecha_inicio_result = self._execute_query(
                "SELECT date('now', ?) as fecha", (f'-{dias} days',)
            )
            
            if not fecha_inicio_result:
                fecha_inicio = date.today().isoformat()
            else:
                fecha_inicio = fecha_inicio_result[0]['fecha']
            
            productos = self._execute_query('''
                SELECT 
                    p.nombre,
                    SUM(v.cantidad_total) as total_vendido,
                    SUM(v.total_ventas) as total_ingresos,
                    p.unidad_venta
                FROM ventas v
                JOIN productos p ON v.producto_id = p.id
                WHERE v.fecha >= ?
                GROUP BY v.producto_id
                ORDER BY total_vendido DESC
                LIMIT 10
            ''', (fecha_inicio,))
            
            return productos
            
        except Exception as e:
            print(f"❌ Error obteniendo productos más vendidos: {e}")
            traceback.print_exc()
            return []
    
    # ====================================================
    # NUEVAS FUNCIONES v2.0: CANCELACIÓN DE VENTAS
    # ====================================================
    
    def cancelar_venta_por_id(self, detalle_id):
        """Cancela una venta específica por ID del detalle - NUEVO v2.0"""
        try:
            print(f"🔄 Cancelando venta con detalle_id: {detalle_id}")
            
            # Obtener información de la venta a cancelar
            detalle = self._execute_query('''
                SELECT 
                    vd.venta_id,
                    vd.cantidad,
                    v.producto_id,
                    v.fecha,
                    p.precio_venta
                FROM ventas_detalle vd
                JOIN ventas v ON vd.venta_id = v.id
                JOIN productos p ON v.producto_id = p.id
                WHERE vd.id = ?
            ''', (detalle_id,))
            
            if not detalle:
                raise ValueError(f"No se encontró la venta con detalle_id: {detalle_id}")
            
            venta_info = detalle[0]
            venta_id = venta_info['venta_id']
            cantidad = venta_info['cantidad']
            producto_id = venta_info['producto_id']
            fecha = venta_info['fecha']
            precio = venta_info['precio_venta']
            total_a_devolver = cantidad * precio
            
            # Usar una sola transacción para mantener consistencia
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Eliminar el detalle
                cursor.execute('DELETE FROM ventas_detalle WHERE id = ?', (detalle_id,))
                
                # 2. Actualizar la venta acumulada
                cursor.execute('''
                    SELECT cantidad_total, total_ventas FROM ventas WHERE id = ?
                ''', (venta_id,))
                venta_actual = cursor.fetchone()
                
                if venta_actual:
                    nueva_cantidad = venta_actual['cantidad_total'] - cantidad
                    nuevo_total = venta_actual['total_ventas'] - total_a_devolver
                    
                    if nueva_cantidad <= 0:
                        # Si no quedan ventas, eliminar el registro acumulado
                        cursor.execute('DELETE FROM ventas WHERE id = ?', (venta_id,))
                    else:
                        cursor.execute('''
                            UPDATE ventas 
                            SET cantidad_total = ?, total_ventas = ?
                            WHERE id = ?
                        ''', (nueva_cantidad, nuevo_total, venta_id))
                
                # 3. Actualizar inventario (devolver al stock)
                self._actualizar_inventario_producto(cursor, producto_id, cantidad, 'sumar')
                
                # 4. Recalcular excedentes
                try:
                    calcular_excedentes_dia(fecha)
                except Exception as e:
                    print(f"⚠️ Error recalculando excedentes: {e}")
                
                conn.commit()
                
                # Limpiar cache
                self._clear_cache()
                
                print(f"✅ Venta cancelada exitosamente (detalle_id: {detalle_id})")
                return {
                    'detalle_id': detalle_id,
                    'cantidad_devuelta': cantidad,
                    'total_devuelto': total_a_devolver,
                    'producto_id': producto_id
                }
                
        except Exception as e:
            print(f"❌ Error cancelando venta por ID: {e}")
            traceback.print_exc()
            raise
    
    def cancelar_ventas_seleccionadas(self, detalle_ids):
        """Cancela múltiples ventas seleccionadas - NUEVO v2.0"""
        try:
            print(f"🔄 Cancelando {len(detalle_ids)} ventas seleccionadas...")
            
            if not detalle_ids:
                return {
                    'ventas_canceladas': 0,
                    'total_cantidad_devuelta': 0,
                    'total_dinero_devuelto': 0,
                    'detalles': []
                }
            
            resultados = []
            for detalle_id in detalle_ids:
                try:
                    resultado = self.cancelar_venta_por_id(detalle_id)
                    resultados.append(resultado)
                except Exception as e:
                    print(f"⚠️ Error cancelando venta {detalle_id}: {e}")
            
            # Resumen de la operación
            total_cantidad = sum(r['cantidad_devuelta'] for r in resultados)
            total_dinero = sum(r['total_devuelto'] for r in resultados)
            
            print(f"✅ {len(resultados)} ventas canceladas. Total devuelto: ${total_dinero:.2f}")
            
            return {
                'ventas_canceladas': len(resultados),
                'total_cantidad_devuelta': total_cantidad,
                'total_dinero_devuelto': total_dinero,
                'detalles': resultados
            }
            
        except Exception as e:
            print(f"❌ Error cancelando ventas seleccionadas: {e}")
            traceback.print_exc()
            raise
    
    def cancelar_ultima_venta(self, producto_id, fecha=None):
        """Cancela la última venta de un producto - CORREGIDO v2.0"""
        try:
            print(f"🔄 Cancelando última venta del producto: {producto_id}")
            
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            # Obtener el último detalle de venta del producto en la fecha
            detalle = self._execute_query('''
                SELECT vd.id
                FROM ventas_detalle vd
                JOIN ventas v ON vd.venta_id = v.id
                WHERE v.producto_id = ? AND v.fecha = ?
                ORDER BY vd.hora DESC
                LIMIT 1
            ''', (producto_id, fecha_str))
            
            if not detalle:
                raise ValueError(f"No hay ventas para cancelar del producto {producto_id} en la fecha {fecha_str}")
            
            detalle_id = detalle[0]['id']
            
            # Usar la nueva función cancelar_venta_por_id
            return self.cancelar_venta_por_id(detalle_id)
            
        except Exception as e:
            print(f"❌ Error cancelando última venta: {e}")
            traceback.print_exc()
            raise
    
    # ====================================================
    # FUNCIONES AUXILIARES
    # ====================================================
    
    def _execute_query(self, query, params=(), commit=False):
        """Ejecuta consulta directa a la BD"""
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
            print(f"❌ Error en consulta directa (ventas): {e}")
            return []
    
    def _get_one(self, table, condition, params):
        """Obtiene un registro de una tabla"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(f'SELECT * FROM {table} WHERE {condition}', params)
                resultado = cursor.fetchone()
                return dict(resultado) if resultado else None
        except sqlite3.Error as e:
            print(f"❌ Error obteniendo registro: {e}")
            return None
