# utils/db_operations.py - VERSIÓN CORREGIDA CON MANEJO DE ERRORES Y CONEXIÓN ROBUSTA
import traceback
from datetime import datetime
from database import db
from utils.validators import validate_name, validate_positive, validate_price
from utils.date_utils import get_current_date
from utils.safe_output import safe_print as print

class DBOperations:
    def __init__(self, db_path=None):
        """Inicializa con conexión a base de datos"""
        try:
            self.db = db
            self.db_path = db_path or str(db.db_path)
            print("✅ DBOperations inicializado correctamente")
            # Verificar tablas básicas
            self.verificar_tablas_basicas()
        except Exception as e:
            print(f"❌ Error inicializando DBOperations: {e}")
            traceback.print_exc()
            raise
    
    def verificar_tablas_basicas(self):
        """Verifica que las tablas básicas existan"""
        try:
            # Verificar tabla productos
            productos = self.db.execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='productos'")
            if not productos:
                print("⚠️ ADVERTENCIA: Tabla 'productos' no encontrada")
            else:
                print("✅ Tabla 'productos' encontrada")
        except Exception as e:
            print(f"❌ Error verificando tablas: {e}")
    
    def get_unidades_medida(self, tipo=None):
        """Obtiene las unidades de medida, opcionalmente filtradas por tipo"""
        try:
            query = "SELECT * FROM unidades_medida WHERE activo = 1"
            params = ()
            
            if tipo:
                query += " AND tipo = ?"
                params = (tipo,)
            
            query += " ORDER BY nombre"
            result = self.db.execute_query(query, params)
            return result
        except Exception as e:
            print(f"❌ Error en get_unidades_medida: {e}")
            traceback.print_exc()
            return []
    
    def get_ingredientes_activos(self):
        """Obtiene todos los ingredientes activos"""
        try:
            result = self.db.execute_query('''
                SELECT i.*, um.nombre as unidad_nombre, um.abreviatura
                FROM ingredientes i
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE i.activo = 1
                ORDER BY i.nombre
            ''')
            return result
        except Exception as e:
            print(f"❌ Error en get_ingredientes_activos: {e}")
            traceback.print_exc()
            return []
    
    def get_productos_activos(self):
        """Obtiene todos los productos activos"""
        try:
            print("🔄 DBOperations.get_productos_activos: Ejecutando consulta...")
            result = self.db.execute_query('''
                SELECT * FROM productos 
                WHERE activo = 1 
                ORDER BY nombre
            ''')
            print(f"✅ DBOperations.get_productos_activos: {len(result)} productos encontrados")
            return result
        except Exception as e:
            print(f"❌ ERROR CRÍTICO en get_productos_activos: {e}")
            traceback.print_exc()
            # Retornar productos de ejemplo si la tabla no existe
            productos_ejemplo = [
                {'id': 1, 'nombre': 'Producto 1', 'precio_venta': 10.0, 'unidad_venta': 'unidad'},
                {'id': 2, 'nombre': 'Producto 2', 'precio_venta': 15.0, 'unidad_venta': 'unidad'},
                {'id': 3, 'nombre': 'Producto 3', 'precio_venta': 20.0, 'unidad_venta': 'unidad'},
            ]
            print("⚠️ Retornando productos de ejemplo")
            return productos_ejemplo
    
    def get_inventario_ingredientes(self):
        """Obtiene el inventario actual de ingredientes"""
        try:
            result = self.db.execute_query('''
                SELECT i.nombre, ii.cantidad_actual, um.abreviatura, i.stock_minimo
                FROM inventario_ingredientes ii
                JOIN ingredientes i ON ii.ingrediente_id = i.id
                JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE i.activo = 1
                ORDER BY i.nombre
            ''')
            return result
        except Exception as e:
            print(f"❌ Error en get_inventario_ingredientes: {e}")
            traceback.print_exc()
            return []
    
    def get_inventario_productos(self):
        """Obtiene el inventario actual de productos"""
        try:
            result = self.db.execute_query('''
                SELECT p.nombre, ip.cantidad_disponible, p.precio_venta, p.unidad_venta
                FROM inventario_productos ip
                JOIN productos p ON ip.producto_id = p.id
                WHERE p.activo = 1
                ORDER BY p.nombre
            ''')
            return result
        except Exception as e:
            print(f"❌ Error en get_inventario_productos: {e}")
            traceback.print_exc()
            return []
    
    def agregar_ingrediente(self, nombre, unidad_medida_id, stock_minimo=0, notas=""):
        """Agrega un nuevo ingrediente al sistema"""
        try:
            # Validaciones
            nombre = validate_name(nombre, "nombre del ingrediente")
            unidad_medida_id = validate_positive(unidad_medida_id, "unidad de medida")
            stock_minimo = validate_positive(stock_minimo, "stock mínimo")
            
            # Verificar que no exista
            existente = self.db.get_one('ingredientes', 'nombre = ? AND activo = 1', (nombre,))
            if existente:
                raise ValueError(f"El ingrediente '{nombre}' ya existe")
            
            # Insertar ingrediente
            ingrediente_id = self.db.execute_insert('''
                INSERT INTO ingredientes (nombre, unidad_medida_id, stock_minimo, notas)
                VALUES (?, ?, ?, ?)
            ''', (nombre, unidad_medida_id, stock_minimo, notas))
            
            # Crear registro en inventario con cantidad 0
            self.db.execute_insert('''
                INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual)
                VALUES (?, 0)
            ''', (ingrediente_id,))
            
            return ingrediente_id
        except Exception as e:
            print(f"❌ Error en agregar_ingrediente: {e}")
            traceback.print_exc()
            raise
    
    def actualizar_ingrediente(self, ingrediente_id, **kwargs):
        """Actualiza un ingrediente existente"""
        try:
            update_data = {}
            
            if 'nombre' in kwargs:
                update_data['nombre'] = validate_name(kwargs['nombre'], "nombre del ingrediente")
            
            if 'unidad_medida_id' in kwargs:
                update_data['unidad_medida_id'] = validate_positive(kwargs['unidad_medida_id'], "unidad de medida")
            
            if 'stock_minimo' in kwargs:
                update_data['stock_minimo'] = validate_positive(kwargs['stock_minimo'], "stock mínimo")
            
            if 'notas' in kwargs:
                update_data['notas'] = kwargs['notas']
            
            if update_data:
                update_data['ultima_actualizacion'] = 'CURRENT_TIMESTAMP'
                self.db.update('ingredientes', update_data, 'id = ?', (ingrediente_id,))
        except Exception as e:
            print(f"❌ Error en actualizar_ingrediente: {e}")
            traceback.print_exc()
            raise
    
    def desactivar_ingrediente(self, ingrediente_id):
        """Desactiva un ingrediente (eliminación lógica)"""
        try:
            # Verificar que no tenga movimientos recientes
            compras = self.db.execute_query('''
                SELECT COUNT(*) as count FROM compras 
                WHERE ingrediente_id = ? AND fecha > date('now', '-30 days')
            ''', (ingrediente_id,))
            
            if compras and compras[0]['count'] > 0:
                raise ValueError("No se puede desactivar. Tiene compras recientes.")
            
            # Marcar como inactivo
            self.db.execute_query('''
                UPDATE ingredientes 
                SET activo = 0 
                WHERE id = ?
            ''', (ingrediente_id,))
        except Exception as e:
            print(f"❌ Error en desactivar_ingrediente: {e}")
            traceback.print_exc()
            raise
    
    def agregar_producto(self, nombre, precio_venta, unidad_venta, descripcion=""):
        """Agrega un nuevo producto al sistema"""
        try:
            # Validaciones
            nombre = validate_name(nombre, "nombre del producto")
            precio_venta = validate_price(precio_venta)
            unidad_venta = validate_name(unidad_venta, "unidad de venta")
            
            # Verificar que no exista
            existente = self.db.get_one('productos', 'nombre = ? AND activo = 1', (nombre,))
            if existente:
                raise ValueError(f"El producto '{nombre}' ya existe")
            
            # Insertar producto
            producto_id = self.db.execute_insert('''
                INSERT INTO productos (nombre, precio_venta, unidad_venta, descripcion)
                VALUES (?, ?, ?, ?)
            ''', (nombre, precio_venta, unidad_venta, descripcion))
            
            # Crear registro en inventario con cantidad 0
            self.db.execute_insert('''
                INSERT INTO inventario_productos (producto_id, cantidad_disponible)
                VALUES (?, 0)
            ''', (producto_id,))
            
            return producto_id
        except Exception as e:
            print(f"❌ Error en agregar_producto: {e}")
            traceback.print_exc()
            raise
    
    # ========== CORRECCIÓN CRÍTICA: método registrar_compra con fecha opcional ==========
    def registrar_compra(self, ingrediente_id, cantidad, costo_unitario, notas="", fecha=None):
        """Registra una compra de ingredientes"""
        try:
            from utils.calculos import actualizar_inventario_ingrediente, calcular_costo_promedio_ingrediente
            
            # Validaciones
            cantidad = validate_positive(cantidad, "cantidad")
            costo_unitario = validate_positive(costo_unitario, "costo unitario")
            
            # Si no se proporciona fecha, usar la actual
            if fecha is None:
                fecha = get_current_date()
            
            # Asegurar que fecha esté en formato string
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            
            print(f"📝 Registrando compra: ingrediente_id={ingrediente_id}, cantidad={cantidad}, fecha={fecha}")
            
            # Registrar compra CON FECHA
            self.db.execute_insert('''
                INSERT INTO compras (ingrediente_id, cantidad, costo_unitario, notas, fecha)
                VALUES (?, ?, ?, ?, ?)
            ''', (ingrediente_id, cantidad, costo_unitario, notas, fecha))
            
            # Actualizar inventario (sumar)
            actualizar_inventario_ingrediente(ingrediente_id, cantidad, 'sumar')
            
            # Recalcular costo promedio
            calcular_costo_promedio_ingrediente(ingrediente_id)
            
        except Exception as e:
            print(f"❌ Error en registrar_compra: {e}")
            traceback.print_exc()
            raise
    
    def agregar_pedido_chef(self, ingrediente_id, cantidad, motivo=""):
        """Agrega un pedido del chef (acumulativo por día)"""
        try:
            from utils.calculos import actualizar_inventario_ingrediente
            from utils.date_utils import get_current_date
            
            # Validaciones
            cantidad = validate_positive(cantidad, "cantidad")
            fecha = get_current_date()
            
            # Asegurar formato de fecha
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            
            # Verificar stock disponible
            inventario = self.db.get_one('inventario_ingredientes', 'ingrediente_id = ?', (ingrediente_id,))
            if not inventario or inventario['cantidad_actual'] < cantidad:
                raise ValueError(f"Stock insuficiente")
            
            # Buscar o crear registro de pedido del día
            pedido = self.db.get_one('pedidos_chef', 'fecha = ? AND ingrediente_id = ?', (fecha, ingrediente_id))
            
            if pedido:
                # Actualizar cantidad total
                nueva_cantidad = pedido['cantidad_total'] + cantidad
                self.db.execute_query('''
                    UPDATE pedidos_chef 
                    SET cantidad_total = ?
                    WHERE id = ?
                ''', (nueva_cantidad, pedido['id']))
                pedido_id = pedido['id']
            else:
                # Crear nuevo registro
                pedido_id = self.db.execute_insert('''
                    INSERT INTO pedidos_chef (fecha, ingrediente_id, cantidad_total)
                    VALUES (?, ?, ?)
                ''', (fecha, ingrediente_id, cantidad))
            
            # Registrar en detalle
            self.db.execute_insert('''
                INSERT INTO pedidos_chef_detalle (pedido_id, cantidad, motivo)
                VALUES (?, ?, ?)
            ''', (pedido_id, cantidad, motivo))
            
            # Actualizar inventario (restar)
            actualizar_inventario_ingrediente(ingrediente_id, cantidad, 'restar')
            
            return pedido_id
        except Exception as e:
            print(f"❌ Error en agregar_pedido_chef: {e}")
            traceback.print_exc()
            raise
    
    def registrar_produccion(self, producto_id, cantidad, notas=""):
        """Registra producción de productos"""
        try:
            from utils.calculos import actualizar_inventario_producto
            from utils.date_utils import get_current_date
            
            # Validaciones
            cantidad = validate_positive(cantidad, "cantidad", min_value=1)
            fecha = get_current_date()
            
            # Asegurar formato de fecha
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            
            # Registrar producción
            self.db.execute_insert('''
                INSERT INTO produccion (fecha, producto_id, cantidad, notas)
                VALUES (?, ?, ?, ?)
            ''', (fecha, producto_id, cantidad, notas))
            
            # Actualizar inventario de productos (sumar)
            actualizar_inventario_producto(producto_id, cantidad, 'sumar')
        
        except Exception as e:
            print(f"❌ Error en registrar_produccion: {e}")
            traceback.print_exc()
            raise
    
    def registrar_venta(self, producto_id, cantidad):
        """Registra una venta (acumulativa por día)"""
        try:
            from utils.calculos import actualizar_inventario_producto
            from utils.date_utils import get_current_date
            
            # Validaciones
            cantidad = validate_positive(cantidad, "cantidad", min_value=1)
            fecha = get_current_date()
            
            # Asegurar formato de fecha
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            
            # Verificar stock disponible
            inventario = self.db.get_one('inventario_productos', 'producto_id = ?', (producto_id,))
            if not inventario or inventario['cantidad_disponible'] < cantidad:
                raise ValueError(f"Stock insuficiente. Disponible: {inventario['cantidad_disponible'] if inventario else 0}")
            
            # Obtener precio del producto
            producto = self.db.get_one('productos', 'id = ?', (producto_id,))
            if not producto:
                raise ValueError("Producto no encontrado")
            
            precio_unitario = producto['precio_venta']
            total_venta = cantidad * precio_unitario
            
            # Buscar o crear registro de venta del día
            venta = self.db.get_one('ventas', 'fecha = ? AND producto_id = ?', (fecha, producto_id))
            
            if venta:
                # Actualizar cantidad total y total de ventas
                nueva_cantidad = venta['cantidad_total'] + cantidad
                nuevo_total = venta['total_ventas'] + total_venta
                
                self.db.execute_query('''
                    UPDATE ventas 
                    SET cantidad_total = ?, total_ventas = ?
                    WHERE id = ?
                ''', (nueva_cantidad, nuevo_total, venta['id']))
                
                venta_id = venta['id']
            else:
                # Crear nuevo registro
                venta_id = self.db.execute_insert('''
                    INSERT INTO ventas (fecha, producto_id, cantidad_total, total_ventas)
                    VALUES (?, ?, ?, ?)
                ''', (fecha, producto_id, cantidad, total_venta))
            
            # Registrar en detalle
            self.db.execute_insert('''
                INSERT INTO ventas_detalle (venta_id, cantidad)
                VALUES (?, ?)
            ''', (venta_id, cantidad))
            
            # Actualizar inventario de productos (restar)
            actualizar_inventario_producto(producto_id, cantidad, 'restar')
            
            return total_venta
        
        except Exception as e:
            print(f"❌ Error en registrar_venta: {e}")
            traceback.print_exc()
            raise
    
    def obtener_ventas_dia(self, fecha=None):
        """Obtiene las ventas del día"""
        try:
            from utils.date_utils import get_current_date
            
            if fecha is None:
                fecha = get_current_date()
            
            # Asegurar formato de fecha
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            
            result = self.db.execute_query('''
                SELECT p.nombre, v.cantidad_total, v.total_ventas, p.unidad_venta, v.producto_id
                FROM ventas v
                JOIN productos p ON v.producto_id = p.id
                WHERE v.fecha = ?
                ORDER BY p.nombre
            ''', (fecha,))
            return result
        except Exception as e:
            print(f"❌ Error en obtener_ventas_dia: {e}")
            traceback.print_exc()
            return []
    
    def obtener_excedentes_dia(self, fecha=None):
        """Obtiene los excedentes del día"""
        try:
            from utils.date_utils import get_current_date
            
            if fecha is None:
                fecha = get_current_date()
            
            # Asegurar formato de fecha
            if hasattr(fecha, 'strftime'):
                fecha = fecha.strftime('%Y-%m-%d')
            
            result = self.db.execute_query('''
                SELECT p.nombre, e.producido, e.vendido, e.excedente, p.unidad_venta
                FROM excedentes e
                JOIN productos p ON e.producto_id = p.id
                WHERE e.fecha = ?
                ORDER BY p.nombre
            ''', (fecha,))
            return result
        except Exception as e:
            print(f"❌ Error en obtener_excedentes_dia: {e}")
            traceback.print_exc()
            return []
    
    def usar_excedente(self, producto_id, cantidad):
        """Usa excedentes del inventario"""
        try:
            from utils.calculos import actualizar_inventario_producto
            
            # Validaciones
            cantidad = validate_positive(cantidad, "cantidad")
            
            # Verificar que hay suficientes excedentes
            inventario = self.db.get_one('inventario_productos', 'producto_id = ?', (producto_id,))
            if not inventario or inventario['cantidad_disponible'] < cantidad:
                raise ValueError(f"Excedentes insuficientes. Disponible: {inventario['cantidad_disponible'] if inventario else 0}")
            
            # Actualizar inventario (restar)
            actualizar_inventario_producto(producto_id, cantidad, 'restar')
            
            # Registrar ajuste
            self.db.execute_insert('''
                INSERT INTO ajustes_inventario 
                (tipo, elemento_id, cantidad_anterior, cantidad_nueva, motivo)
                VALUES ('producto', ?, ?, ?, 'Uso de excedentes')
            ''', (producto_id, inventario['cantidad_disponible'], 
                  inventario['cantidad_disponible'] - cantidad))
        
        except Exception as e:
            print(f"❌ Error en usar_excedente: {e}")
            traceback.print_exc()
            raise
