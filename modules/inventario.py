# modules/inventario.py - VERSIÓN v2.0 COMPATIBLE CON database.py OPTIMIZADA
import traceback
from datetime import datetime
from utils.date_utils import get_current_date
from utils.safe_output import safe_print as print

# Importar desde la nueva database.py optimizada
try:
    from database import get_connection, get_cached_data, execute_query
except ImportError:
    print("⚠️ No se pudo importar database.py optimizada, usando fallback")
    get_connection = None
    get_cached_data = None
    execute_query = None

class InventarioManager:
    def __init__(self, db_path=None):
        try:
            self.db_path = db_path or 'data/inventario.db'
            print("✅ InventarioManager v2.0 inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando InventarioManager: {e}")
            traceback.print_exc()
            self.db_path = db_path or 'data/inventario.db'
    
    # ========== FUNCIONES PRINCIPALES OPTIMIZADAS (v2.0) ==========
    
    def obtener_inventario_ingredientes(self):
        """Obtiene el inventario actual de ingredientes usando database.py optimizada"""
        try:
            print("🔄 InventarioManager.obtener_inventario_ingredientes() v2.0...")
            
            if get_connection and execute_query:
                # Usar la nueva database.py optimizada
                conn = get_connection()
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        i.id, 
                        i.nombre, 
                        COALESCE(ii.cantidad_actual, 0) as cantidad_actual,
                        i.stock_minimo, 
                        um.abreviatura as unidad,
                        um.nombre as unidad_nombre,
                        i.notas,
                        CASE 
                            WHEN COALESCE(ii.cantidad_actual, 0) < i.stock_minimo THEN 'BAJO'
                            ELSE 'OK'
                        END as estado_stock
                    FROM ingredientes i
                    LEFT JOIN inventario_ingredientes ii ON i.id = ii.ingrediente_id
                    LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE i.activo = 1
                    ORDER BY i.nombre
                '''
                
                cursor.execute(query)
                resultados = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                inventario = []
                for row in resultados:
                    inventario.append({
                        'id': row[0],
                        'nombre': row[1],
                        'cantidad_actual': float(row[2]) if row[2] else 0.0,
                        'stock_minimo': float(row[3]) if row[3] else 0.0,
                        'unidad': row[4],
                        'unidad_nombre': row[5],
                        'notas': row[6],
                        'estado_stock': row[7]
                    })
                
                cursor.close()
                print(f"✅ {len(inventario)} ingredientes obtenidos (con database.py v2.0)")
                return inventario
            else:
                # Fallback a conexión directa
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT i.id, i.nombre, 
                           COALESCE(ii.cantidad_actual, 0) as cantidad_actual,
                           i.stock_minimo, um.abreviatura as unidad
                    FROM ingredientes i
                    LEFT JOIN inventario_ingredientes ii ON i.id = ii.ingrediente_id
                    LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE i.activo = 1
                    ORDER BY i.nombre
                ''')
                
                resultados = cursor.fetchall()
                inventario = [dict(row) for row in resultados]
                cursor.close()
                conn.close()
                
                print(f"✅ {len(inventario)} ingredientes obtenidos (fallback)")
                return inventario
            
        except Exception as e:
            print(f"❌ Error obteniendo inventario de ingredientes: {e}")
            traceback.print_exc()
            return []
    
    def obtener_inventario_productos(self):
        """Obtiene el inventario actual de productos usando database.py optimizada"""
        try:
            print("🔄 InventarioManager.obtener_inventario_productos() v2.0...")
            
            if get_connection and execute_query:
                # Usar la nueva database.py optimizada
                conn = get_connection()
                cursor = conn.cursor()
                
                query = '''
                    SELECT 
                        p.id, 
                        p.nombre, 
                        COALESCE(ip.cantidad_disponible, 0) as cantidad_disponible,
                        p.precio_venta, 
                        p.unidad_venta,
                        p.descripcion,
                        CASE 
                            WHEN COALESCE(ip.cantidad_disponible, 0) < 5 THEN 'BAJO'
                            ELSE 'OK'
                        END as estado_stock
                    FROM productos p
                    LEFT JOIN inventario_productos ip ON p.id = ip.producto_id
                    WHERE p.activo = 1
                    ORDER BY p.nombre
                '''
                
                cursor.execute(query)
                resultados = cursor.fetchall()
                
                # Convertir a lista de diccionarios
                inventario = []
                for row in resultados:
                    inventario.append({
                        'id': row[0],
                        'nombre': row[1],
                        'cantidad_disponible': float(row[2]) if row[2] else 0.0,
                        'precio_venta': float(row[3]) if row[3] else 0.0,
                        'unidad_venta': row[4],
                        'descripcion': row[5],
                        'estado_stock': row[6]
                    })
                
                cursor.close()
                print(f"✅ {len(inventario)} productos obtenidos (con database.py v2.0)")
                return inventario
            else:
                # Fallback a conexión directa
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT p.id, p.nombre, 
                           COALESCE(ip.cantidad_disponible, 0) as cantidad_disponible,
                           p.precio_venta, p.unidad_venta
                    FROM productos p
                    LEFT JOIN inventario_productos ip ON p.id = ip.producto_id
                    WHERE p.activo = 1
                    ORDER BY p.nombre
                ''')
                
                resultados = cursor.fetchall()
                inventario = [dict(row) for row in resultados]
                cursor.close()
                conn.close()
                
                print(f"✅ {len(inventario)} productos obtenidos (fallback)")
                return inventario
            
        except Exception as e:
            print(f"❌ Error obteniendo inventario de productos: {e}")
            traceback.print_exc()
            return []
    
    def obtener_ingredientes_bajo_stock(self):
        """Obtiene ingredientes con stock por debajo del mínimo"""
        try:
            print("🔄 InventarioManager.obtener_ingredientes_bajo_stock() v2.0...")
            
            inventario = self.obtener_inventario_ingredientes()
            if not inventario:
                return []
            
            bajo_stock = []
            for item in inventario:
                cantidad_actual = item.get('cantidad_actual', 0)
                stock_minimo = item.get('stock_minimo', 0)
                
                try:
                    if float(cantidad_actual) < float(stock_minimo):
                        # Agregar información adicional
                        item['diferencia'] = float(stock_minimo) - float(cantidad_actual)
                        item['porcentaje'] = (float(cantidad_actual) / float(stock_minimo) * 100) if stock_minimo > 0 else 0
                        bajo_stock.append(item)
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Error comparando stock para {item.get('nombre', 'desconocido')}: {e}")
                    continue
            
            print(f"✅ {len(bajo_stock)} ingredientes con bajo stock encontrados")
            return bajo_stock
            
        except Exception as e:
            print(f"❌ Error obteniendo ingredientes bajo stock: {e}")
            traceback.print_exc()
            return []
    
    def obtener_productos_bajo_stock(self, minimo=5):
        """Obtiene productos con stock bajo"""
        try:
            print(f"🔄 InventarioManager.obtener_productos_bajo_stock(minimo={minimo}) v2.0...")
            
            inventario = self.obtener_inventario_productos()
            if not inventario:
                return []
            
            bajo_stock = []
            for item in inventario:
                cantidad_disponible = item.get('cantidad_disponible', 0)
                try:
                    if float(cantidad_disponible) < float(minimo):
                        # Agregar información adicional
                        item['diferencia'] = float(minimo) - float(cantidad_disponible)
                        item['porcentaje'] = (float(cantidad_disponible) / float(minimo) * 100) if minimo > 0 else 0
                        bajo_stock.append(item)
                except (ValueError, TypeError) as e:
                    print(f"⚠️ Error comparando stock para {item.get('nombre', 'desconocido')}: {e}")
                    continue
            
            print(f"✅ {len(bajo_stock)} productos con bajo stock encontrados")
            return bajo_stock
            
        except Exception as e:
            print(f"❌ Error obteniendo productos bajo stock: {e}")
            traceback.print_exc()
            return []

    def obtener_alertas_inventario(self):
        """Genera alertas combinadas de ingredientes y productos con stock comprometido."""
        alertas = []

        try:
            for item in self.obtener_ingredientes_bajo_stock():
                disponible = float(item.get('cantidad_actual', 0) or 0)
                minimo = float(item.get('stock_minimo', 0) or 0)
                nombre = item.get('nombre', 'Ingrediente')
                tipo = 'CRÍTICO' if disponible <= 0 or (minimo and disponible / minimo < 0.5) else 'ADVERTENCIA'
                alertas.append({
                    'tipo': tipo,
                    'mensaje': f"{nombre}: disponible {disponible:.2f} / mínimo {minimo:.2f}",
                    'nombre': nombre,
                    'disponible': disponible,
                    'minimo': minimo,
                    'unidad': item.get('unidad', ''),
                })

            for item in self.obtener_productos_bajo_stock():
                disponible = float(item.get('cantidad_disponible', 0) or 0)
                nombre = item.get('nombre', 'Producto')
                tipo = 'CRÍTICO' if disponible <= 0 else 'ADVERTENCIA'
                alertas.append({
                    'tipo': tipo,
                    'mensaje': f"{nombre}: quedan {disponible:.0f} unidades listas para venta",
                    'nombre': nombre,
                    'disponible': disponible,
                    'minimo': 5,
                    'unidad': item.get('unidad_venta', ''),
                })
        except Exception as exc:
            print(f"❌ Error generando alertas de inventario: {exc}")
            traceback.print_exc()

        return alertas
    
    def obtener_resumen_dia(self, fecha=None):
        """Obtiene un resumen del día usando database.py optimizada"""
        try:
            print(f"🔄 InventarioManager.obtener_resumen_dia(fecha={fecha}) v2.0...")
            
            if fecha is None:
                fecha = get_current_date()
            
            # Asegurar formato de fecha
            if hasattr(fecha, 'strftime'):
                fecha_str = fecha.strftime('%Y-%m-%d')
            else:
                fecha_str = str(fecha)
            
            if get_connection:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Obtener pedidos del chef
                cursor.execute('''
                    SELECT pc.*, i.nombre as ingrediente_nombre, um.abreviatura
                    FROM pedidos_chef pc
                    JOIN ingredientes i ON pc.ingrediente_id = i.id
                    JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE pc.fecha = ?
                ''', (fecha_str,))
                
                pedidos = []
                for row in cursor.fetchall():
                    pedidos.append({
                        'id': row[0],
                        'ingrediente_id': row[1],
                        'ingrediente_nombre': row[6],
                        'cantidad_total': float(row[3]) if row[3] else 0.0,
                        'unidad': row[7],
                        'fecha': row[2]
                    })
                
                # Obtener producción
                cursor.execute('''
                    SELECT p.id, p.nombre, pr.cantidad, pr.fecha, pr.notas
                    FROM produccion pr
                    JOIN productos p ON pr.producto_id = p.id
                    WHERE date(pr.fecha) = ?
                ''', (fecha_str,))
                
                produccion = []
                for row in cursor.fetchall():
                    produccion.append({
                        'id': row[0],
                        'producto_nombre': row[1],
                        'cantidad': float(row[2]) if row[2] else 0.0,
                        'fecha': row[3],
                        'notas': row[4]
                    })
                
                # Obtener ventas usando vista optimizada si existe
                try:
                    cursor.execute('''
                        SELECT vd.producto_id, p.nombre, 
                               SUM(vd.cantidad) as cantidad_total,
                               SUM(vd.cantidad * vd.precio_unitario) as total_dinero,
                               p.unidad_venta
                        FROM ventas_detalle vd
                        JOIN productos p ON vd.producto_id = p.id
                        JOIN ventas v ON vd.venta_id = v.id
                        WHERE date(v.fecha_hora) = ?
                        GROUP BY vd.producto_id, p.nombre, p.unidad_venta
                    ''', (fecha_str,))
                except:
                    # Fallback si hay error en la vista
                    cursor.execute('''
                        SELECT v.producto_id, p.nombre, 
                               v.cantidad_total, v.total_ventas, p.unidad_venta
                        FROM ventas v
                        JOIN productos p ON v.producto_id = p.id
                        WHERE v.fecha = ?
                    ''', (fecha_str,))
                
                ventas = []
                for row in cursor.fetchall():
                    ventas.append({
                        'producto_id': row[0],
                        'producto_nombre': row[1],
                        'cantidad_total': float(row[2]) if row[2] else 0.0,
                        'total_dinero': float(row[3]) if row[3] else 0.0,
                        'unidad_venta': row[4]
                    })
                
                cursor.close()
                
                # Calcular totales
                total_pedidos = sum(p.get('cantidad_total', 0) for p in pedidos)
                total_produccion = sum(p.get('cantidad', 0) for p in produccion)
                total_ventas_cantidad = sum(v.get('cantidad_total', 0) for v in ventas)
                total_ventas_dinero = sum(v.get('total_dinero', 0) for v in ventas)
                
                # Obtener excedentes si existen
                try:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT e.*, i.nombre as ingrediente_nombre
                        FROM excedentes e
                        JOIN ingredientes i ON e.ingrediente_id = i.id
                        WHERE e.fecha = ?
                    ''', (fecha_str,))
                    
                    excedentes = []
                    for row in cursor.fetchall():
                        excedentes.append({
                            'id': row[0],
                            'ingrediente_id': row[1],
                            'ingrediente_nombre': row[6],
                            'cantidad_excedente': float(row[3]) if row[3] else 0.0,
                            'fecha': row[2],
                            'motivo': row[4]
                        })
                    cursor.close()
                except:
                    excedentes = []
                
                total_excedentes = sum(e.get('cantidad_excedente', 0) for e in excedentes)
                
                resumen = {
                    'fecha': fecha_str,
                    'pedidos': {
                        'total': total_pedidos,
                        'detalle': pedidos,
                        'count': len(pedidos)
                    },
                    'produccion': {
                        'total': total_produccion,
                        'detalle': produccion,
                        'count': len(produccion)
                    },
                    'ventas': {
                        'total_cantidad': total_ventas_cantidad,
                        'total_dinero': total_ventas_dinero,
                        'detalle': ventas,
                        'count': len(ventas),
                        'promedio_por_venta': total_ventas_dinero / len(ventas) if ventas else 0
                    },
                    'excedentes': {
                        'total': total_excedentes,
                        'detalle': excedentes,
                        'count': len(excedentes)
                    }
                }
                
                print(f"✅ Resumen del día {fecha_str} generado (v2.0)")
                return resumen
            else:
                # Fallback a la versión anterior
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Similar a la lógica anterior pero con sqlite3 directo
                cursor.execute('''
                    SELECT pc.*, i.nombre as ingrediente_nombre, um.abreviatura
                    FROM pedidos_chef pc
                    JOIN ingredientes i ON pc.ingrediente_id = i.id
                    JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE pc.fecha = ?
                ''', (fecha_str,))
                pedidos = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute('''
                    SELECT SUM(cantidad) as total FROM produccion WHERE fecha = ?
                ''', (fecha_str,))
                produccion_result = cursor.fetchone()
                total_produccion = produccion_result['total'] if produccion_result and produccion_result['total'] else 0
                
                cursor.execute('''
                    SELECT v.*, p.nombre as producto_nombre, p.unidad_venta
                    FROM ventas v
                    JOIN productos p ON v.producto_id = p.id
                    WHERE v.fecha = ?
                ''', (fecha_str,))
                ventas = [dict(row) for row in cursor.fetchall()]
                
                cursor.close()
                conn.close()
                
                total_pedidos = sum(p.get('cantidad_total', 0) for p in pedidos)
                total_ventas_cantidad = sum(v.get('cantidad_total', 0) for v in ventas)
                total_ventas_dinero = sum(v.get('total_ventas', 0) for v in ventas)
                
                resumen = {
                    'fecha': fecha_str,
                    'pedidos': {'total': total_pedidos, 'detalle': pedidos},
                    'produccion': {'total': total_produccion, 'detalle': []},
                    'ventas': {'total_cantidad': total_ventas_cantidad, 'total_dinero': total_ventas_dinero, 'detalle': ventas},
                    'excedentes': {'total': 0, 'detalle': []}
                }
                
                print(f"✅ Resumen del día {fecha_str} generado (fallback)")
                return resumen
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen del día: {e}")
            traceback.print_exc()
            return {
                'fecha': fecha_str if 'fecha_str' in locals() else get_current_date(),
                'pedidos': {'total': 0, 'detalle': [], 'count': 0},
                'produccion': {'total': 0, 'detalle': [], 'count': 0},
                'ventas': {'total_cantidad': 0, 'total_dinero': 0, 'detalle': [], 'count': 0, 'promedio_por_venta': 0},
                'excedentes': {'total': 0, 'detalle': [], 'count': 0}
            }
    
    def ajustar_inventario_ingrediente(self, ingrediente_id, nueva_cantidad, motivo):
        """Ajusta manualmente el inventario de un ingrediente"""
        try:
            print(f"🔄 Ajustando inventario ingrediente {ingrediente_id} a {nueva_cantidad}...")
            
            if get_connection:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Obtener cantidad actual
                cursor.execute('''
                    SELECT cantidad_actual FROM inventario_ingredientes 
                    WHERE ingrediente_id = ?
                ''', (ingrediente_id,))
                resultado = cursor.fetchone()
                
                if resultado:
                    cantidad_anterior = float(resultado[0]) if resultado[0] else 0.0
                else:
                    cantidad_anterior = 0.0
                
                # Actualizar o insertar inventario
                if resultado:
                    cursor.execute('''
                        UPDATE inventario_ingredientes 
                        SET cantidad_actual = ?, ultima_actualizacion = CURRENT_TIMESTAMP
                        WHERE ingrediente_id = ?
                    ''', (nueva_cantidad, ingrediente_id))
                else:
                    cursor.execute('''
                        INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual, ultima_actualizacion)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (ingrediente_id, nueva_cantidad))
                
                # Registrar ajuste
                cursor.execute('''
                    INSERT INTO ajustes_inventario 
                    (tipo, elemento_id, cantidad_anterior, cantidad_nueva, motivo, fecha)
                    VALUES ('ingrediente', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (ingrediente_id, cantidad_anterior, nueva_cantidad, motivo))
                
                conn.commit()
                cursor.close()
            else:
                # Fallback
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT cantidad_actual FROM inventario_ingredientes 
                    WHERE ingrediente_id = ?
                ''', (ingrediente_id,))
                resultado = cursor.fetchone()
                
                if resultado:
                    cantidad_anterior = float(resultado[0]) if resultado[0] else 0.0
                else:
                    cantidad_anterior = 0.0
                
                if resultado:
                    cursor.execute('''
                        UPDATE inventario_ingredientes 
                        SET cantidad_actual = ?, ultima_actualizacion = CURRENT_TIMESTAMP
                        WHERE ingrediente_id = ?
                    ''', (nueva_cantidad, ingrediente_id))
                else:
                    cursor.execute('''
                        INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual, ultima_actualizacion)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (ingrediente_id, nueva_cantidad))
                
                cursor.execute('''
                    INSERT INTO ajustes_inventario 
                    (tipo, elemento_id, cantidad_anterior, cantidad_nueva, motivo, fecha)
                    VALUES ('ingrediente', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (ingrediente_id, cantidad_anterior, nueva_cantidad, motivo))
                
                conn.commit()
                cursor.close()
                conn.close()
            
            print(f"✅ Inventario de ingrediente ajustado: {cantidad_anterior} -> {nueva_cantidad}")
            return True
            
        except Exception as e:
            print(f"❌ Error ajustando inventario de ingrediente: {e}")
            traceback.print_exc()
            return False
    
    def ajustar_inventario_producto(self, producto_id, nueva_cantidad, motivo):
        """Ajusta manualmente el inventario de un producto"""
        try:
            print(f"🔄 Ajustando inventario producto {producto_id} a {nueva_cantidad}...")
            
            if get_connection:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Obtener cantidad actual
                cursor.execute('''
                    SELECT cantidad_disponible FROM inventario_productos 
                    WHERE producto_id = ?
                ''', (producto_id,))
                resultado = cursor.fetchone()
                
                if resultado:
                    cantidad_anterior = float(resultado[0]) if resultado[0] else 0.0
                else:
                    cantidad_anterior = 0.0
                
                # Actualizar o insertar inventario
                if resultado:
                    cursor.execute('''
                        UPDATE inventario_productos 
                        SET cantidad_disponible = ?, ultima_actualizacion = CURRENT_TIMESTAMP
                        WHERE producto_id = ?
                    ''', (nueva_cantidad, producto_id))
                else:
                    cursor.execute('''
                        INSERT INTO inventario_productos (producto_id, cantidad_disponible, ultima_actualizacion)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (producto_id, nueva_cantidad))
                
                # Registrar ajuste
                cursor.execute('''
                    INSERT INTO ajustes_inventario 
                    (tipo, elemento_id, cantidad_anterior, cantidad_nueva, motivo, fecha)
                    VALUES ('producto', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (producto_id, cantidad_anterior, nueva_cantidad, motivo))
                
                conn.commit()
                cursor.close()
            else:
                # Fallback
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT cantidad_disponible FROM inventario_productos 
                    WHERE producto_id = ?
                ''', (producto_id,))
                resultado = cursor.fetchone()
                
                if resultado:
                    cantidad_anterior = float(resultado[0]) if resultado[0] else 0.0
                else:
                    cantidad_anterior = 0.0
                
                if resultado:
                    cursor.execute('''
                        UPDATE inventario_productos 
                        SET cantidad_disponible = ?, ultima_actualizacion = CURRENT_TIMESTAMP
                        WHERE producto_id = ?
                    ''', (nueva_cantidad, producto_id))
                else:
                    cursor.execute('''
                        INSERT INTO inventario_productos (producto_id, cantidad_disponible, ultima_actualizacion)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    ''', (producto_id, nueva_cantidad))
                
                cursor.execute('''
                    INSERT INTO ajustes_inventario 
                    (tipo, elemento_id, cantidad_anterior, cantidad_nueva, motivo, fecha)
                    VALUES ('producto', ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (producto_id, cantidad_anterior, nueva_cantidad, motivo))
                
                conn.commit()
                cursor.close()
                conn.close()
            
            print(f"✅ Inventario de producto ajustado: {cantidad_anterior} -> {nueva_cantidad}")
            return True
            
        except Exception as e:
            print(f"❌ Error ajustando inventario de producto: {e}")
            traceback.print_exc()
            return False
    
    # ========== FUNCIONES DE LIMPIEZA (MANTENIDAS) ==========
    
    def limpiar_datos_prueba_ingredientes(self):
        """Elimina ingredientes de prueba marcados como tales"""
        try:
            print("🗑️ Limpiando ingredientes de prueba...")
            
            eliminados = 0
            if get_connection:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Buscar ingredientes de prueba
                cursor.execute('''
                    SELECT id, nombre FROM ingredientes 
                    WHERE (LOWER(nombre) LIKE '%prueba%' 
                       OR LOWER(notas) LIKE '%prueba%'
                       OR LOWER(nombre) LIKE '%test%'
                       OR LOWER(notas) LIKE '%test%')
                       AND activo = 1
                ''')
                
                ingredientes_prueba = cursor.fetchall()
                
                for ingrediente in ingredientes_prueba:
                    ingrediente_id, nombre = ingrediente
                    try:
                        # Marcar como inactivo
                        cursor.execute('UPDATE ingredientes SET activo = 0 WHERE id = ?', (ingrediente_id,))
                        # Eliminar del inventario
                        cursor.execute('DELETE FROM inventario_ingredientes WHERE ingrediente_id = ?', (ingrediente_id,))
                        eliminados += 1
                        print(f"✅ Eliminado: {nombre}")
                    except Exception as e:
                        print(f"⚠️ Error eliminando {nombre}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
            else:
                # Fallback
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, nombre FROM ingredientes 
                    WHERE (LOWER(nombre) LIKE '%prueba%' 
                       OR LOWER(notas) LIKE '%prueba%'
                       OR LOWER(nombre) LIKE '%test%'
                       OR LOWER(notas) LIKE '%test%')
                       AND activo = 1
                ''')
                
                ingredientes_prueba = cursor.fetchall()
                
                for ingrediente in ingredientes_prueba:
                    ingrediente_id, nombre = ingrediente
                    try:
                        cursor.execute('UPDATE ingredientes SET activo = 0 WHERE id = ?', (ingrediente_id,))
                        cursor.execute('DELETE FROM inventario_ingredientes WHERE ingrediente_id = ?', (ingrediente_id,))
                        eliminados += 1
                        print(f"✅ Eliminado: {nombre}")
                    except Exception as e:
                        print(f"⚠️ Error eliminando {nombre}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
                conn.close()
            
            print(f"✅ Total eliminados: {eliminados} ingredientes de prueba")
            return eliminados
            
        except Exception as e:
            print(f"❌ Error limpiando datos de prueba de ingredientes: {e}")
            traceback.print_exc()
            return 0
    
    def limpiar_datos_prueba_productos(self):
        """Elimina productos de prueba marcados como tales"""
        try:
            print("🗑️ Limpiando productos de prueba...")
            
            eliminados = 0
            if get_connection:
                conn = get_connection()
                cursor = conn.cursor()
                
                # Buscar productos de prueba
                cursor.execute('''
                    SELECT id, nombre FROM productos 
                    WHERE (LOWER(nombre) LIKE '%prueba%' 
                       OR LOWER(descripcion) LIKE '%prueba%'
                       OR LOWER(nombre) LIKE '%test%'
                       OR LOWER(descripcion) LIKE '%test%')
                       AND activo = 1
                ''')
                
                productos_prueba = cursor.fetchall()
                
                for producto in productos_prueba:
                    producto_id, nombre = producto
                    try:
                        # Marcar como inactivo
                        cursor.execute('UPDATE productos SET activo = 0 WHERE id = ?', (producto_id,))
                        # Eliminar del inventario
                        cursor.execute('DELETE FROM inventario_productos WHERE producto_id = ?', (producto_id,))
                        eliminados += 1
                        print(f"✅ Eliminado: {nombre}")
                    except Exception as e:
                        print(f"⚠️ Error eliminando {nombre}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
            else:
                # Fallback
                import sqlite3
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT id, nombre FROM productos 
                    WHERE (LOWER(nombre) LIKE '%prueba%' 
                       OR LOWER(descripcion) LIKE '%prueba%'
                       OR LOWER(nombre) LIKE '%test%'
                       OR LOWER(descripcion) LIKE '%test%')
                       AND activo = 1
                ''')
                
                productos_prueba = cursor.fetchall()
                
                for producto in productos_prueba:
                    producto_id, nombre = producto
                    try:
                        cursor.execute('UPDATE productos SET activo = 0 WHERE id = ?', (producto_id,))
                        cursor.execute('DELETE FROM inventario_productos WHERE producto_id = ?', (producto_id,))
                        eliminados += 1
                        print(f"✅ Eliminado: {nombre}")
                    except Exception as e:
                        print(f"⚠️ Error eliminando {nombre}: {e}")
                        continue
                
                conn.commit()
                cursor.close()
                conn.close()
            
            print(f"✅ Total eliminados: {eliminados} productos de prueba")
            return eliminados
            
        except Exception as e:
            print(f"❌ Error limpiando datos de prueba de productos: {e}")
            traceback.print_exc()
            return 0
    
    def limpiar_todos_datos_prueba(self):
        """Limpia todos los datos de prueba del sistema"""
        try:
            print("🧹 LIMPIANDO TODOS LOS DATOS DE PRUEBA v2.0...")
            
            total_eliminados = 0
            
            # Limpiar ingredientes de prueba
            eliminados_ingredientes = self.limpiar_datos_prueba_ingredientes()
            total_eliminados += eliminados_ingredientes
            
            # Limpiar productos de prueba
            eliminados_productos = self.limpiar_datos_prueba_productos()
            total_eliminados += eliminados_productos
            
            print(f"🧹 TOTAL ELIMINADO v2.0: {total_eliminados} elementos de prueba")
            return total_eliminados
            
        except Exception as e:
            print(f"❌ Error limpiando todos los datos de prueba: {e}")
            traceback.print_exc()
            return 0
    
    # ========== FUNCIONES AUXILIARES PARA MÓDULOS CONSUMIDORES ==========
    
    def obtener_ingredientes_para_compras(self):
        """✅ Función específica para módulo de compras - v2.0"""
        try:
            inventario = self.obtener_inventario_ingredientes()
            # Formatear para combobox: (id, nombre, unidad, cantidad_actual, stock_minimo)
            resultado = []
            for ing in inventario:
                resultado.append((
                    ing['id'],
                    ing['nombre'],
                    ing['unidad'],
                    ing['cantidad_actual'],
                    ing['stock_minimo']
                ))
            return resultado
        except Exception as e:
            print(f"❌ Error en obtener_ingredientes_para_compras: {e}")
            return []
    
    def obtener_productos_para_ventas(self):
        """✅ Función específica para módulo de ventas - v2.0"""
        try:
            inventario = self.obtener_inventario_productos()
            # Formatear para combobox: (id, nombre, precio, unidad, cantidad_disponible)
            resultado = []
            for prod in inventario:
                resultado.append((
                    prod['id'],
                    prod['nombre'],
                    prod['precio_venta'],
                    prod['unidad_venta'],
                    prod['cantidad_disponible']
                ))
            return resultado
        except Exception as e:
            print(f"❌ Error en obtener_productos_para_ventas: {e}")
            return []
