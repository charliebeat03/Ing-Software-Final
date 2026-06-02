# modules/pedidos_chef.py - REESCRITO SEGÚN PATRÓN DE VENTAS
import traceback
import sqlite3
from datetime import datetime, date
from utils.db_operations import DBOperations
from utils.date_utils import get_current_date, format_date
from utils.calculos import actualizar_inventario_ingrediente
from utils.safe_output import safe_print as print

class PedidosChefManager:
    def __init__(self, db_path=None):
        try:
            self.db_path = db_path or 'data/inventario.db'
            print(f"✅ PedidosChefManager inicializado con db: {self.db_path}")
        except Exception as e:
            print(f"❌ Error inicializando PedidosChefManager: {e}")
            traceback.print_exc()
            self.db_path = db_path or 'data/inventario.db'
    
    # ========== MÉTODOS PRINCIPALES (PATRÓN VENTAS) ==========
    
    def cargar_ingredientes(self):
        """Carga ingredientes para formulario (igual que ventas carga productos)"""
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
                return [(row['id'], row['nombre'], row['unidad']) for row in resultados]
                
        except Exception as e:
            print(f"❌ Error cargando ingredientes: {e}")
            return []
    
    def agregar_pedido(self, ingrediente_id, cantidad, motivo=""):
        """Agrega un pedido del chef - MISMOS PRINCIPIOS QUE VENTAS"""
        try:
            print(f"📝 PedidosChefManager.agregar_pedido: {ingrediente_id}, {cantidad}")
            
            # Validar cantidad
            try:
                cantidad = float(cantidad)
                if cantidad <= 0:
                    raise ValueError("La cantidad debe ser mayor a 0")
            except (ValueError, TypeError):
                raise ValueError("Cantidad inválida")
            
            # Fecha actual en formato YYYY-MM-DD (IGUAL QUE VENTAS)
            fecha_actual = date.today()
            fecha_str = fecha_actual.strftime('%Y-%m-%d')
            
            # Hora actual en formato HH:MM:SS (IGUAL QUE VENTAS)
            hora_actual = datetime.now().strftime('%H:%M:%S')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Verificar si ya existe un pedido hoy para este ingrediente (ACUMULATIVO)
                cursor.execute('''
                    SELECT id, cantidad_total FROM pedidos_chef
                    WHERE fecha = ? AND ingrediente_id = ?
                ''', (fecha_str, ingrediente_id))
                pedido_existente = cursor.fetchone()
                
                if pedido_existente:
                    # Actualizar pedido existente (ACUMULAR)
                    nuevo_total = pedido_existente['cantidad_total'] + cantidad
                    cursor.execute('''
                        UPDATE pedidos_chef 
                        SET cantidad_total = ?
                        WHERE id = ?
                    ''', (nuevo_total, pedido_existente['id']))
                    pedido_id = pedido_existente['id']
                else:
                    # Crear nuevo pedido acumulativo
                    cursor.execute('''
                        INSERT INTO pedidos_chef (ingrediente_id, cantidad_total, fecha)
                        VALUES (?, ?, ?)
                    ''', (ingrediente_id, cantidad, fecha_str))
                    pedido_id = cursor.lastrowid
                
                # 2. Registrar en el detalle (HISTORIAL)
                cursor.execute('''
                    INSERT INTO pedidos_chef_detalle (pedido_id, cantidad, motivo, hora)
                    VALUES (?, ?, ?, ?)
                ''', (pedido_id, cantidad, motivo, hora_actual))
                
                conn.commit()
                
                # 3. Actualizar inventario (RESTAR del stock) - IGUAL QUE VENTAS
                try:
                    actualizar_inventario_ingrediente(ingrediente_id, cantidad, 'restar')
                except Exception as e:
                    print(f"⚠️ Error actualizando inventario: {e}")
                    # Continuar aunque falle el inventario
                
                print(f"✅ Pedido registrado: ID={pedido_id}, Hora={hora_actual}")
                return {
                    'success': True,
                    'pedido_id': pedido_id,
                    'hora': hora_actual,
                    'cantidad': cantidad
                }
                
        except Exception as e:
            print(f"❌ Error agregando pedido: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_pedidos_dia(self, fecha=None):
        """Obtiene pedidos acumulados del día - EXACTO COMO VENTAS"""
        try:
            if fecha is None:
                fecha = date.today()
            
            fecha_str = fecha.strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # CONSULTA SIMILAR A VENTAS - PEDIDOS ACUMULADOS POR DÍA
                cursor.execute('''
                    SELECT 
                        pc.id,
                        pc.ingrediente_id,
                        i.nombre as ingrediente_nombre,
                        pc.cantidad_total as cantidad,
                        um.abreviatura as unidad,
                        pc.fecha,
                        (SELECT COUNT(*) FROM pedidos_chef_detalle pcd WHERE pcd.pedido_id = pc.id) as pedidos_count,
                        (SELECT MAX(pcd.hora) FROM pedidos_chef_detalle pcd WHERE pcd.pedido_id = pc.id) as ultima_hora
                    FROM pedidos_chef pc
                    JOIN ingredientes i ON pc.ingrediente_id = i.id
                    LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE pc.fecha = ?
                    ORDER BY pc.cantidad_total DESC
                ''', (fecha_str,))
                
                resultados = cursor.fetchall()
                pedidos = []
                
                for row in resultados:
                    pedidos.append({
                        'id': row['id'],
                        'ingrediente_id': row['ingrediente_id'],
                        'ingrediente_nombre': row['ingrediente_nombre'],
                        'cantidad': row['cantidad'],
                        'unidad': row['unidad'],
                        'fecha': row['fecha'],
                        'pedidos_count': row['pedidos_count'],
                        'ultima_hora': row['ultima_hora']
                    })
                
                print(f"✅ {len(pedidos)} pedidos acumulados obtenidos")
                return pedidos
                
        except Exception as e:
            print(f"❌ Error obteniendo pedidos del día: {e}")
            return []
    
    def obtener_detalle_pedidos_dia(self, fecha=None):
        """Obtiene detalle histórico de pedidos - EXACTO COMO VENTAS"""
        try:
            if fecha is None:
                fecha = date.today()
            
            fecha_str = fecha.strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # CONSULTA SIMILAR A VENTAS_DETALLE
                cursor.execute('''
                    SELECT 
                        pcd.id as detalle_id,
                        pcd.pedido_id,
                        pcd.cantidad,
                        pcd.hora,
                        pcd.motivo,
                        i.nombre as ingrediente_nombre,
                        um.abreviatura as unidad
                    FROM pedidos_chef_detalle pcd
                    JOIN pedidos_chef pc ON pcd.pedido_id = pc.id
                    JOIN ingredientes i ON pc.ingrediente_id = i.id
                    LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                    WHERE pc.fecha = ?
                    ORDER BY pcd.hora DESC
                ''', (fecha_str,))
                
                resultados = cursor.fetchall()
                detalles = []
                
                for row in resultados:
                    detalles.append({
                        'detalle_id': row['detalle_id'],
                        'pedido_id': row['pedido_id'],
                        'ingrediente_nombre': row['ingrediente_nombre'],
                        'cantidad': row['cantidad'],
                        'hora': row['hora'],
                        'motivo': row['motivo'],
                        'unidad': row['unidad']
                    })
                
                print(f"✅ {len(detalles)} registros de detalle obtenidos")
                return detalles
                
        except Exception as e:
            print(f"❌ Error obteniendo detalle de pedidos: {e}")
            return []
    
    def cancelar_ultimo_pedido(self, ingrediente_id):
        """Cancela el último pedido - IGUAL QUE VENTAS CANCELA"""
        try:
            fecha_actual = date.today()
            fecha_str = fecha_actual.strftime('%Y-%m-%d')
            
            print(f"🔄 Cancelando último pedido del ingrediente: {ingrediente_id}")
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Buscar el último detalle de pedido de hoy para este ingrediente
                cursor.execute('''
                    SELECT pcd.id, pcd.cantidad, pcd.pedido_id
                    FROM pedidos_chef_detalle pcd
                    JOIN pedidos_chef pc ON pcd.pedido_id = pc.id
                    WHERE pc.ingrediente_id = ? AND pc.fecha = ?
                    ORDER BY pcd.hora DESC
                    LIMIT 1
                ''', (ingrediente_id, fecha_str))
                
                detalle = cursor.fetchone()
                
                if not detalle:
                    raise ValueError(f"No hay pedidos recientes para el ingrediente {ingrediente_id}")
                
                detalle_id = detalle['id']
                cantidad = detalle['cantidad']
                pedido_id = detalle['pedido_id']
                
                # 2. Eliminar del detalle
                cursor.execute('DELETE FROM pedidos_chef_detalle WHERE id = ?', (detalle_id,))
                
                # 3. Actualizar pedido acumulado
                cursor.execute('SELECT cantidad_total FROM pedidos_chef WHERE id = ?', (pedido_id,))
                pedido = cursor.fetchone()
                
                if pedido:
                    nueva_cantidad = pedido['cantidad_total'] - cantidad
                    
                    if nueva_cantidad <= 0:
                        # Si ya no hay pedidos, eliminar el registro acumulado
                        cursor.execute('DELETE FROM pedidos_chef WHERE id = ?', (pedido_id,))
                    else:
                        cursor.execute('''
                            UPDATE pedidos_chef 
                            SET cantidad_total = ?
                            WHERE id = ?
                        ''', (nueva_cantidad, pedido_id))
                
                # 4. DEVOLVER AL INVENTARIO - USANDO LA MISMA LÓGICA QUE EN VENTAS
                try:
                    # Primero buscar el inventario actual del ingrediente
                    cursor.execute('''
                        SELECT id, cantidad_actual FROM inventario_ingredientes 
                        WHERE ingrediente_id = ?
                    ''', (ingrediente_id,))
                    
                    inventario = cursor.fetchone()
                    
                    if inventario:
                        # Actualizar el inventario sumando la cantidad devuelta
                        nueva_cantidad_inventario = inventario['cantidad_actual'] + cantidad
                        cursor.execute('''
                            UPDATE inventario_ingredientes 
                            SET cantidad_actual = ?
                            WHERE ingrediente_id = ?
                        ''', (nueva_cantidad_inventario, ingrediente_id))
                    else:
                        # Si no existe registro de inventario, crear uno
                        cursor.execute('''
                            INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual)
                            VALUES (?, ?)
                        ''', (ingrediente_id, cantidad))
                    
                    print(f"✅ Se devolvieron {cantidad} al inventario del ingrediente {ingrediente_id}")
                    
                except Exception as e:
                    print(f"⚠️ Error actualizando inventario en cancelación: {e}")
                    # Si falla, intentar con la función externa
                    try:
                        actualizar_inventario_ingrediente(ingrediente_id, cantidad, 'sumar')
                    except Exception as e2:
                        print(f"⚠️ También falló la función externa: {e2}")
                
                conn.commit()
                
                print(f"✅ Pedido cancelado exitosamente (detalle_id: {detalle_id})")
                return {
                    'success': True,
                    'detalle_id': detalle_id,
                    'cantidad_devuelta': cantidad,
                    'ingrediente_id': ingrediente_id
                }
                
        except Exception as e:
            print(f"❌ Error cancelando pedido: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancelar_pedido_por_id(self, detalle_id):
        """Cancela un pedido específico por ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Obtener información del detalle a cancelar
                cursor.execute('''
                    SELECT pcd.cantidad, pcd.pedido_id, pc.ingrediente_id
                    FROM pedidos_chef_detalle pcd
                    JOIN pedidos_chef pc ON pcd.pedido_id = pc.id
                    WHERE pcd.id = ?
                ''', (detalle_id,))
                
                detalle = cursor.fetchone()
                
                if not detalle:
                    raise ValueError(f"No existe el detalle con ID {detalle_id}")
                
                cantidad = detalle['cantidad']
                pedido_id = detalle['pedido_id']
                ingrediente_id = detalle['ingrediente_id']
                
                # 2. Eliminar del detalle
                cursor.execute('DELETE FROM pedidos_chef_detalle WHERE id = ?', (detalle_id,))
                
                # 3. Actualizar pedido acumulado
                cursor.execute('SELECT cantidad_total FROM pedidos_chef WHERE id = ?', (pedido_id,))
                pedido = cursor.fetchone()
                
                if pedido:
                    nueva_cantidad = pedido['cantidad_total'] - cantidad
                    
                    if nueva_cantidad <= 0:
                        cursor.execute('DELETE FROM pedidos_chef WHERE id = ?', (pedido_id,))
                    else:
                        cursor.execute('''
                            UPDATE pedidos_chef 
                            SET cantidad_total = ?
                            WHERE id = ?
                        ''', (nueva_cantidad, pedido_id))
                
                # 4. Devolver al inventario - USANDO LA MISMA LÓGICA QUE EN VENTAS
                try:
                    # Buscar inventario actual
                    cursor.execute('''
                        SELECT id, cantidad_actual FROM inventario_ingredientes 
                        WHERE ingrediente_id = ?
                    ''', (ingrediente_id,))
                    
                    inventario = cursor.fetchone()
                    
                    if inventario:
                        # Actualizar sumando la cantidad devuelta
                        nueva_cantidad_inventario = inventario['cantidad_actual'] + cantidad
                        cursor.execute('''
                            UPDATE inventario_ingredientes 
                            SET cantidad_actual = ?
                            WHERE ingrediente_id = ?
                        ''', (nueva_cantidad_inventario, ingrediente_id))
                    else:
                        # Crear registro si no existe
                        cursor.execute('''
                            INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual)
                            VALUES (?, ?)
                        ''', (ingrediente_id, cantidad))
                    
                    print(f"✅ Se devolvieron {cantidad} al inventario")
                    
                except Exception as e:
                    print(f"⚠️ Error actualizando inventario: {e}")
                    # Intentar con la función externa
                    try:
                        actualizar_inventario_ingrediente(ingrediente_id, cantidad, 'sumar')
                    except Exception as e2:
                        print(f"⚠️ También falló la función externa: {e2}")
                
                conn.commit()
                
                return {
                    'success': True,
                    'detalle_id': detalle_id,
                    'cantidad_devuelta': cantidad,
                    'ingrediente_id': ingrediente_id
                }
                
        except Exception as e:
            print(f"❌ Error cancelando pedido por ID: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def obtener_total_pedidos_dia(self, fecha=None):
        """Obtiene total de pedidos del día"""
        try:
            pedidos = self.obtener_pedidos_dia(fecha)
            total = sum(float(p.get('cantidad', 0)) for p in pedidos)
            return total
        except Exception as e:
            print(f"❌ Error calculando total de pedidos: {e}")
            return 0
    
    # ========== MÉTODOS AUXILIARES ==========
    
    def _execute_query(self, query, params=(), commit=False):
        """Ejecuta consulta directa"""
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
