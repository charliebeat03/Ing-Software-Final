# modules/excedentes.py - CORREGIDO v2.1
# 📝 Error: Incompatibilidad con database.py v2.0, métodos faltantes
# ✅ Cambios: Integración completa con database v2.0

import traceback
from datetime import datetime, date, timedelta
from database import db  # ✅ Usamos el singleton de database.py v2.0

class CierreDiarioManager:
    def __init__(self, db_path=None):
        try:
            # Usamos la instancia singleton de Database
            self.db = db
            print("✅ CierreDiarioManager v2.1 inicializado con Database v2.0")
            
            # Cache para consultas frecuentes
            self._cache = {
                'resumen_dia': None,
                'ingredientes_usados': None,
                'ventas_dia': None,
                'last_update': None
            }
                
        except Exception as e:
            print(f"❌ Error inicializando CierreDiarioManager: {e}")
            traceback.print_exc()
            self.db = None
            self._cache = {}
    
    def _clear_cache(self):
        """Limpia la cache para forzar actualización"""
        self._cache = {
            'resumen_dia': None,
            'ingredientes_usados': None,
            'ventas_dia': None,
            'last_update': None
        }
        print("🔄 Cache de cierre diario limpiado")
    
    # ====================================================
    # MÉTODOS PARA LA UI - IMPLEMENTADOS COMPLETAMENTE
    # ====================================================
    
    def obtener_resumen_ventas_dia(self, fecha=None):
        """Obtiene resumen de ventas del día"""
        try:
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            query = '''
                SELECT 
                    p.nombre as producto,
                    v.cantidad_total as cantidad,
                    p.precio_venta as precio_unitario,
                    v.total_ventas as total,
                    p.unidad_venta
                FROM ventas v
                JOIN productos p ON v.producto_id = p.id
                WHERE v.fecha = ?
                ORDER BY v.total_ventas DESC
            '''
            
            ventas = self.db.execute_query(query, (fecha_str,))
            
            # Convertir a lista de diccionarios
            ventas_dict = []
            total_dia = 0
            
            for row in ventas:
                venta_dict = dict(row)
                ventas_dict.append(venta_dict)
                total_dia += float(venta_dict.get('total', 0))
            
            return {
                'ventas': ventas_dict,
                'total_dia': total_dia,
                'total_items': len(ventas_dict)
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen ventas: {e}")
            traceback.print_exc()
            return {'ventas': [], 'total_dia': 0, 'total_items': 0}
    
    def obtener_resumen_produccion_dia(self, fecha=None):
        """Obtiene resumen de producción del día (mantenido por compatibilidad)"""
        try:
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            query = '''
                SELECT 
                    p.nombre as producto,
                    pr.cantidad,
                    p.unidad_venta
                FROM produccion pr
                JOIN productos p ON pr.producto_id = p.id
                WHERE pr.fecha = ?
                ORDER BY pr.cantidad DESC
            '''
            
            produccion = self.db.execute_query(query, (fecha_str,))
            
            produccion_dict = []
            total_produccion = 0
            
            for row in produccion:
                prod_dict = dict(row)
                produccion_dict.append(prod_dict)
                total_produccion += float(prod_dict.get('cantidad', 0))
            
            return {
                'produccion': produccion_dict,
                'total_produccion': total_produccion,
                'total_items': len(produccion_dict)
            }
            
        except Exception as e:
            print(f"❌ Error obteniendo resumen producción: {e}")
            return {'produccion': [], 'total_produccion': 0, 'total_items': 0}
    
    def obtener_pedidos_chef_dia(self, fecha=None):
        """Obtiene pedidos del chef del día para ajuste"""
        try:
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            query = '''
                SELECT 
                    pc.ingrediente_id,
                    i.nombre as ingrediente,
                    pc.cantidad_total as cantidad_pedida,
                    um.abreviatura as unidad,
                    COALESCE(ii.cantidad_actual, 0) as stock_actual
                FROM pedidos_chef pc
                JOIN ingredientes i ON pc.ingrediente_id = i.id
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                LEFT JOIN inventario_ingredientes ii ON i.id = ii.ingrediente_id
                WHERE pc.fecha = ?
                ORDER BY i.nombre
            '''
            
            pedidos = self.db.execute_query(query, (fecha_str,))
            
            pedidos_dict = []
            for row in pedidos:
                pedidos_dict.append(dict(row))
            
            return pedidos_dict
            
        except Exception as e:
            print(f"❌ Error obteniendo pedidos chef: {e}")
            traceback.print_exc()
            return []
    
    def obtener_excedentes_dia(self, fecha=None):
        """Calcula excedentes del día (producción - ventas)"""
        try:
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            # Obtener producción
            query_produccion = '''
                SELECT 
                    pr.producto_id,
                    p.nombre as producto,
                    SUM(pr.cantidad) as producido,
                    p.unidad_venta,
                    p.precio_venta
                FROM produccion pr
                JOIN productos p ON pr.producto_id = p.id
                WHERE pr.fecha = ?
                GROUP BY pr.producto_id
            '''
            
            produccion = self.db.execute_query(query_produccion, (fecha_str,))
            
            # Obtener ventas
            query_ventas = '''
                SELECT 
                    v.producto_id,
                    SUM(v.cantidad_total) as vendido
                FROM ventas v
                WHERE v.fecha = ?
                GROUP BY v.producto_id
            '''
            
            ventas = self.db.execute_query(query_ventas, (fecha_str,))
            
            # Crear diccionario de ventas
            ventas_dict = {v['producto_id']: v['vendido'] for v in ventas}
            
            # Calcular excedentes
            excedentes = []
            total_excedente = 0
            total_valor = 0
            
            for prod in produccion:
                producto_id = prod['producto_id']
                producido = float(prod['producido'])
                vendido = float(ventas_dict.get(producto_id, 0))
                excedente = producido - vendido
                
                if excedente > 0:
                    valor_excedente = excedente * float(prod['precio_venta'])
                    
                    excedentes.append({
                        'producto': prod['producto'],
                        'producido': producido,
                        'vendido': vendido,
                        'excedente': excedente,
                        'unidad_venta': prod['unidad_venta'],
                        'precio_venta': prod['precio_venta'],
                        'valor': valor_excedente
                    })
                    
                    total_excedente += excedente
                    total_valor += valor_excedente
            
            return {
                'excedentes': excedentes,
                'total_excedente': total_excedente,
                'total_valor': total_valor
            }
            
        except Exception as e:
            print(f"❌ Error calculando excedentes: {e}")
            traceback.print_exc()
            return {'excedentes': [], 'total_excedente': 0, 'total_valor': 0}
    
    def registrar_ajuste_ingrediente(self, ingrediente_id, cantidad_usada, cantidad_pedida, fecha):
        """Registra ajuste individual de ingrediente"""
        try:
            fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            diferencia = cantidad_pedida - cantidad_usada
            
            if diferencia <= 0:
                return {
                    'success': False,
                    'error': 'La cantidad usada no puede ser mayor o igual a la pedida'
                }
            
            # 1. Actualizar inventario
            update_query = '''
                UPDATE inventario_ingredientes
                SET cantidad_actual = cantidad_actual + ?,
                    fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE ingrediente_id = ?
            '''
            
            self.db.execute_query(update_query, (diferencia, ingrediente_id))
            
            # 2. Registrar ajuste en historial
            insert_query = '''
                INSERT INTO ajustes_inventario 
                (tipo, elemento_id, cantidad_anterior, cantidad_nueva, motivo)
                VALUES ('ingrediente', ?, ?, ?, ?)
            '''
            
            self.db.execute_query(insert_query, (
                ingrediente_id,
                cantidad_pedida,
                cantidad_usada,
                f'Ajuste diario {fecha_str} - Devuelto: {diferencia}'
            ))
            
            # 3. Obtener nuevo stock
            stock_query = '''
                SELECT cantidad_actual 
                FROM inventario_ingredientes 
                WHERE ingrediente_id = ?
            '''
            
            stock_result = self.db.execute_query(stock_query, (ingrediente_id,))
            stock_nuevo = stock_result[0]['cantidad_actual'] if stock_result else 0
            
            # Limpiar cache
            self._clear_cache()
            
            return {
                'success': True,
                'diferencia_devuelta': diferencia,
                'stock_nuevo': stock_nuevo
            }
            
        except Exception as e:
            print(f"❌ Error registrando ajuste: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    def cerrar_dia(self, ajustes, fecha=None):
        """Realiza el cierre completo del día"""
        try:
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            resultados = []
            errores = []
            
            # Procesar cada ajuste
            for ajuste in ajustes:
                ingrediente_id = ajuste.get('ingrediente_id')
                ingrediente_nombre = ajuste.get('ingrediente_nombre', 'Desconocido')
                cantidad_pedida = ajuste.get('cantidad_pedida', 0)
                cantidad_usada = ajuste.get('cantidad_usada', 0)
                
                if cantidad_usada > cantidad_pedida:
                    errores.append(f"{ingrediente_nombre}: La cantidad usada ({cantidad_usada}) excede lo pedido ({cantidad_pedida})")
                    continue
                
                resultado = self.registrar_ajuste_ingrediente(
                    ingrediente_id, cantidad_usada, cantidad_pedida, fecha_actual
                )
                
                if resultado['success']:
                    resultados.append({
                        'ingrediente': ingrediente_nombre,
                        'diferencia_devuelta': resultado['diferencia_devuelta']
                    })
                else:
                    errores.append(f"{ingrediente_nombre}: {resultado.get('error', 'Error desconocido')}")
            
            # Registrar cierre en tabla excedentes
            if resultados:
                cierre_query = '''
                    INSERT OR REPLACE INTO excedentes (fecha, notas_cierre)
                    VALUES (?, ?)
                '''
                
                notas = f"Cierre del día {fecha_str}. Ajustes: {len(resultados)}"
                self.db.execute_query(cierre_query, (fecha_str, notas))
            
            return {
                'success': len(errores) == 0,
                'fecha': fecha_str,
                'total_ajustes': len(resultados),
                'resultados': resultados,
                'errores': errores
            }
            
        except Exception as e:
            print(f"❌ Error en cierre diario: {e}")
            traceback.print_exc()
            return {
                'success': False,
                'errores': [str(e)]
            }
    
    # ====================================================
    # MÉTODOS AUXILIARES
    # ====================================================
    
    def obtener_ingredientes_usados_vs_pedidos(self, fecha=None):
        """Obtiene comparativa de ingredientes usados vs pedidos"""
        try:
            if fecha is None:
                fecha_actual = date.today()
                fecha_str = fecha_actual.strftime('%Y-%m-%d')
            else:
                fecha_str = fecha.strftime('%Y-%m-%d') if hasattr(fecha, 'strftime') else str(fecha)
            
            query = '''
                SELECT 
                    pc.ingrediente_id,
                    i.nombre as ingrediente,
                    pc.cantidad_total as pedido,
                    um.abreviatura as unidad,
                    COALESCE(ii.cantidad_actual, 0) as inventario_actual
                FROM pedidos_chef pc
                JOIN ingredientes i ON pc.ingrediente_id = i.id
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                LEFT JOIN inventario_ingredientes ii ON i.id = ii.ingrediente_id
                WHERE pc.fecha = ?
                ORDER BY i.nombre
            '''
            
            resultado = self.db.execute_query(query, (fecha_str,))
            return [dict(row) for row in resultado]
            
        except Exception as e:
            print(f"❌ Error obteniendo ingredientes usados: {e}")
            return []
    
    def obtener_historico_cierre(self, dias=7):
        """Obtiene histórico de cierres"""
        try:
            fecha_inicio = (date.today() - timedelta(days=dias)).strftime('%Y-%m-%d')
            
            query = '''
                SELECT 
                    fecha,
                    COUNT(DISTINCT v.producto_id) as productos_vendidos,
                    SUM(v.cantidad_total) as total_unidades,
                    SUM(v.total_ventas) as total_dinero
                FROM ventas v
                WHERE v.fecha >= ?
                GROUP BY v.fecha
                ORDER BY v.fecha DESC
            '''
            
            resultado = self.db.execute_query(query, (fecha_inicio,))
            return [dict(row) for row in resultado]
            
        except Exception as e:
            print(f"❌ Error obteniendo histórico de cierre: {e}")
            return []
    
    def cleanup(self):
        """Limpia recursos al cerrar el módulo"""
        self._clear_cache()
        print("✅ Recursos de CierreDiarioManager limpiados")