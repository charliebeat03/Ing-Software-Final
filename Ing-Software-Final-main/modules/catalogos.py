# modules/catalogos.py - VERSIÓN CORREGIDA DEFINITIVA
import traceback
import sqlite3
from utils.db_operations import DBOperations
from utils.validators import validate_name, validate_positive, validate_price
from utils.safe_output import safe_print as print

class CatalogoManager:
    def __init__(self, db_path=None):
        try:
            self.db_ops = DBOperations(db_path) if db_path else DBOperations()
            # Obtener ruta de la BD desde db_ops si está disponible
            if hasattr(self.db_ops, 'db') and hasattr(self.db_ops.db, 'db_path'):
                self.db_path = self.db_ops.db.db_path
            else:
                self.db_path = db_path or 'data/inventario.db'
            print("✅ CatalogoManager inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando CatalogoManager: {e}")
            traceback.print_exc()
            self.db_path = db_path or 'data/inventario.db'
            self.db_ops = None
    
    # ========== FUNCIONES DE CONEXIÓN DIRECTA (para evitar problemas con db_ops) ==========
    
    def _execute_query(self, query, params=(), commit=False):
        """Ejecuta consulta directa a la BD (backup si db_ops falla)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                resultados = cursor.fetchall()
                # ✅ CORRECCIÓN CRÍTICA: Convertir sqlite3.Row a diccionario
                return [dict(row) for row in resultados]
        except sqlite3.Error as e:
            print(f"❌ Error en consulta directa: {e}")
            return []
    
    # ========== FUNCIÓN NUEVA PARA ACTUALIZAR PRECIO DESDE TABLA ==========
    
    def actualizar_precio_producto(self, producto_id, nuevo_precio):
        """✅ ACTUALIZA EL PRECIO DE UN PRODUCTO DESDE LA TABLA DE CATÁLOGO"""
        try:
            print(f"🔄 CatalogoManager.actualizar_precio_producto: producto_id={producto_id}, nuevo_precio={nuevo_precio}")
            
            # Validar que el precio sea un número positivo
            try:
                precio_num = float(nuevo_precio)
                if precio_num < 0:
                    raise ValueError("El precio no puede ser negativo")
                if precio_num > 1000000:  # Límite razonable
                    raise ValueError("El precio es demasiado alto")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Precio inválido: {str(e)}")
            
            # Actualizar en la base de datos
            if self.db_ops and hasattr(self.db_ops, 'actualizar_producto'):
                try:
                    self.db_ops.actualizar_producto(producto_id, precio_venta=precio_num)
                    print(f"✅ Precio actualizado mediante DBOperations")
                    return True
                except Exception as e:
                    print(f"⚠️ Error con DBOperations.actualizar_producto: {e}, usando fallback")
            
            # FALLBACK: Actualización directa
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar que el producto existe
                cursor.execute('SELECT id FROM productos WHERE id = ?', (producto_id,))
                producto = cursor.fetchone()
                
                if not producto:
                    raise ValueError(f"Producto con ID {producto_id} no encontrado")
                
                # Actualizar el precio
                cursor.execute('''
                    UPDATE productos 
                    SET precio_venta = ?, ultima_actualizacion = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (precio_num, producto_id))
                
                conn.commit()
                
                print(f"✅ Precio actualizado exitosamente: ${precio_num:.2f} para producto ID {producto_id}")
                return True
                
        except Exception as e:
            print(f"❌ Error actualizando precio del producto: {e}")
            traceback.print_exc()
            raise
    
    # ========== FUNCIONES ESPECÍFICAS PARA UI (COMO SOLICITADO) ==========
    
    def obtener_ingredientes_activos(self):
        """✅ DEVUELVE LISTA DE INGREDIENTES ACTIVOS PARA COMBOBOX
        Formato: [(id, nombre, unidad), ...]
        """
        try:
            print("🔄 CatalogoManager.obtener_ingredientes_activos() - Cargando para combobox...")
            
            # Intentar primero con db_ops si está disponible
            if self.db_ops and hasattr(self.db_ops, 'get_ingredientes_activos'):
                ingredientes = self.db_ops.get_ingredientes_activos()
                if ingredientes and len(ingredientes) > 0:
                    print(f"✅ Obtenidos {len(ingredientes)} ingredientes desde db_ops")
                    
                    # ✅ CORRECCIÓN: Manejar correctamente sqlite3.Row
                    resultado = []
                    for ing in ingredientes:
                        if hasattr(ing, '__getitem__'):  # Es sqlite3.Row o dict
                            try:
                                id_ing = ing['id'] if 'id' in ing else ing[0]
                                nombre = ing['nombre'] if 'nombre' in ing else ing[1]
                                unidad = ing['unidad'] if 'unidad' in ing else (ing['abreviatura'] if 'abreviatura' in ing else 'unidad')
                                resultado.append((id_ing, nombre, unidad))
                            except (KeyError, IndexError):
                                continue
                        elif isinstance(ing, dict):
                            id_ing = ing.get('id', 0)
                            nombre = ing.get('nombre', '')
                            unidad = ing.get('unidad', ing.get('abreviatura', 'unidad'))
                            resultado.append((id_ing, nombre, unidad))
                        elif isinstance(ing, (list, tuple)) and len(ing) >= 3:
                            resultado.append((ing[0], ing[1], ing[2]))
                    
                    if resultado:
                        return resultado
            
            # ✅ CORRECCIÓN CRÍTICA: Usar nombre de columna CORRECTO (unidad_medida_id)
            print("⚠️ Usando consulta directa a BD para ingredientes...")
            resultados = self._execute_query('''
                SELECT i.id, i.nombre, um.abreviatura as unidad
                FROM ingredientes i
                LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE i.activo = 1
                ORDER BY i.nombre
            ''')
            
            if resultados:
                # ✅ CORRECCIÓN: Acceder correctamente a diccionario
                ingredientes_tuplas = [(row['id'], row['nombre'], row['unidad']) for row in resultados]
                print(f"✅ {len(ingredientes_tuplas)} ingredientes cargados desde BD directa")
                return ingredientes_tuplas
            
            print("⚠️ No se encontraron ingredientes activos")
            return []
            
        except Exception as e:
            print(f"❌ Error crítico en obtener_ingredientes_activos: {e}")
            traceback.print_exc()
            return []
    
    def obtener_productos_activos(self):
        """✅ DEVUELVE LISTA DE PRODUCTOS ACTIVOS PARA COMBOBOX
        Formato: [(id, nombre, precio_venta, unidad_venta), ...]
        """
        try:
            print("🔄 CatalogoManager.obtener_productos_activos() - Cargando para combobox...")
            
            # Intentar primero con db_ops si está disponible
            if self.db_ops and hasattr(self.db_ops, 'get_productos_activos'):
                productos = self.db_ops.get_productos_activos()
                if productos and len(productos) > 0:
                    print(f"✅ Obtenidos {len(productos)} productos desde db_ops")
                    
                    # ✅ CORRECCIÓN: Manejar correctamente sqlite3.Row
                    resultado = []
                    for prod in productos:
                        if hasattr(prod, '__getitem__'):  # Es sqlite3.Row o dict
                            try:
                                id_prod = prod['id'] if 'id' in prod else prod[0]
                                nombre = prod['nombre'] if 'nombre' in prod else prod[1]
                                precio = prod['precio_venta'] if 'precio_venta' in prod else prod[2]
                                unidad = prod['unidad_venta'] if 'unidad_venta' in prod else prod[3]
                                resultado.append((id_prod, nombre, precio, unidad))
                            except (KeyError, IndexError):
                                continue
                        elif isinstance(prod, dict):
                            id_prod = prod.get('id', 0)
                            nombre = prod.get('nombre', '')
                            precio = prod.get('precio_venta', 0.0)
                            unidad = prod.get('unidad_venta', 'unidad')
                            resultado.append((id_prod, nombre, precio, unidad))
                        elif isinstance(prod, (list, tuple)) and len(prod) >= 4:
                            resultado.append((prod[0], prod[1], prod[2], prod[3]))
                    
                    if resultado:
                        return resultado
            
            # ✅ CORRECCIÓN CRÍTICA: Usar nombre de columna CORRECTO (precio_venta)
            print("⚠️ Usando consulta directa a BD para productos...")
            resultados = self._execute_query('''
                SELECT id, nombre, precio_venta, unidad_venta
                FROM productos
                WHERE activo = 1
                ORDER BY nombre
            ''')
            
            if resultados:
                # ✅ CORRECCIÓN: Acceder correctamente a diccionario
                productos_tuplas = [(row['id'], row['nombre'], row['precio_venta'], row['unidad_venta']) 
                                   for row in resultados]
                print(f"✅ {len(productos_tuplas)} productos cargados desde BD directa")
                return productos_tuplas
            
            print("⚠️ No se encontraron productos activos")
            return []
            
        except Exception as e:
            print(f"❌ Error crítico en obtener_productos_activos: {e}")
            traceback.print_exc()
            return []
    
    # ========== FUNCIONES DE CARGA PARA MÓDULOS CONSUMIDORES ==========
    
    def cargar_ingredientes_para_compras(self):
        """✅ Función específica para módulo de compras"""
        return self.obtener_ingredientes_activos()
    
    def cargar_ingredientes_para_produccion(self):
        """✅ Función específica para módulo de producción"""
        return self.obtener_ingredientes_activos()
    
    def cargar_productos_para_ventas(self):
        """✅ Función específica para módulo de ventas"""
        return self.obtener_productos_activos()
    
    def cargar_productos_para_produccion(self):
        """✅ Función específica para módulo de producción"""
        return self.obtener_productos_activos()
    
    # ========== MANTENER FUNCIONES EXISTENTES (corregidas) ==========
    
    def obtener_ingredientes(self):
        """Obtiene todos los ingredientes activos (formato detallado)"""
        try:
            # Usar consulta directa para garantizar datos
            return self._execute_query('''
                SELECT i.*, um.nombre as unidad_nombre, um.abreviatura
                FROM ingredientes i
                LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE i.activo = 1
                ORDER BY i.nombre
            ''')
        except Exception as e:
            print(f"❌ Error obteniendo ingredientes: {e}")
            traceback.print_exc()
            return []
    
    def obtener_unidades_medida(self, tipo=None):
        """Obtiene las unidades de medida"""
        try:
            if self.db_ops:
                unidades = self.db_ops.get_unidades_medida(tipo)
                if unidades and len(unidades) > 0:
                    # ✅ CORRECCIÓN: Convertir sqlite3.Row a diccionario si es necesario
                    if isinstance(unidades[0], sqlite3.Row):
                        unidades = [dict(row) for row in unidades]
                    return unidades
            
            # FALLBACK: Consulta directa
            query = '''
                SELECT id, nombre, tipo, abreviatura
                FROM unidades_medida
                WHERE 1=1
            '''
            params = ()
            if tipo:
                query += ' AND tipo = ?'
                params = (tipo,)
            query += ' ORDER BY nombre'
            
            return self._execute_query(query, params)
        except Exception as e:
            print(f"❌ Error obteniendo unidades de medida: {e}")
            traceback.print_exc()
            return []
    
    def agregar_ingrediente(self, nombre, unidad_medida_id, stock_minimo=0, notas=""):
        """Agrega un nuevo ingrediente"""
        try:
            if self.db_ops:
                return self.db_ops.agregar_ingrediente(nombre, unidad_medida_id, stock_minimo, notas)
            
            # FALLBACK: Inserción directa
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO ingredientes (nombre, unidad_medida_id, stock_minimo, notas, activo)
                    VALUES (?, ?, ?, ?, 1)
                ''', (nombre, unidad_medida_id, stock_minimo, notas))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"❌ Error agregando ingrediente: {e}")
            traceback.print_exc()
            raise
    
    def actualizar_ingrediente(self, ingrediente_id, **kwargs):
        """Actualiza un ingrediente existente"""
        try:
            if self.db_ops:
                self.db_ops.actualizar_ingrediente(ingrediente_id, **kwargs)
                return
            
            # FALLBACK: Actualización directa
            if not kwargs:
                return
            
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(ingrediente_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE ingredientes 
                    SET {set_clause}
                    WHERE id = ?
                ''', values)
                conn.commit()
        except Exception as e:
            print(f"❌ Error actualizando ingrediente: {e}")
            traceback.print_exc()
            raise
    
    def eliminar_ingrediente(self, ingrediente_id):
        """Elimina (desactiva) un ingrediente"""
        try:
            if self.db_ops:
                self.db_ops.desactivar_ingrediente(ingrediente_id)
                return
            
            # FALLBACK: Actualización directa
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE ingredientes 
                    SET activo = 0 
                    WHERE id = ?
                ''', (ingrediente_id,))
                conn.commit()
        except Exception as e:
            print(f"❌ Error eliminando ingrediente: {e}")
            traceback.print_exc()
            raise
    
    def buscar_ingrediente(self, nombre):
        """Busca ingredientes por nombre"""
        try:
            return self._execute_query('''
                SELECT i.*, um.nombre as unidad_nombre, um.abreviatura
                FROM ingredientes i
                LEFT JOIN unidades_medida um ON i.unidad_medida_id = um.id
                WHERE i.nombre LIKE ? AND i.activo = 1
                ORDER BY i.nombre
            ''', (f'%{nombre}%',))
        except Exception as e:
            print(f"❌ Error buscando ingredientes: {e}")
            traceback.print_exc()
            return []
    
    # ========== PRODUCTOS ==========
    
    def obtener_productos(self):
        """Obtiene todos los productos activos (formato detallado)"""
        try:
            # Usar consulta directa
            return self._execute_query('''
                SELECT id, nombre, precio_venta, unidad_venta, descripcion
                FROM productos
                WHERE activo = 1
                ORDER BY nombre
            ''')
        except Exception as e:
            print(f"❌ Error obteniendo productos: {e}")
            traceback.print_exc()
            return []
    
    def agregar_producto(self, nombre, precio_venta, unidad_venta, descripcion=""):
        """Agrega un nuevo producto"""
        try:
            if self.db_ops:
                return self.db_ops.agregar_producto(nombre, precio_venta, unidad_venta, descripcion)
            
            # FALLBACK: Inserción directa
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO productos (nombre, precio_venta, unidad_venta, descripcion, activo)
                    VALUES (?, ?, ?, ?, 1)
                ''', (nombre, precio_venta, unidad_venta, descripcion))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"❌ Error agregando producto: {e}")
            traceback.print_exc()
            raise
    
    def actualizar_producto(self, producto_id, **kwargs):
        """Actualiza un producto existente"""
        try:
            if self.db_ops and hasattr(self.db_ops, 'actualizar_producto'):
                self.db_ops.actualizar_producto(producto_id, **kwargs)
                return
            
            # FALLBACK: Actualización directa
            if not kwargs:
                return
            
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(producto_id)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE productos 
                    SET {set_clause}
                    WHERE id = ?
                ''', values)
                conn.commit()
        except Exception as e:
            print(f"❌ Error actualizando producto: {e}")
            traceback.print_exc()
            raise
    
    def eliminar_producto(self, producto_id):
        """Elimina (desactiva) un producto"""
        try:
            # Verificar ventas recientes
            ventas = self._execute_query('''
                SELECT COUNT(*) as count FROM ventas 
                WHERE producto_id = ? AND fecha > date('now', '-30 days')
            ''', (producto_id,))
            
            if ventas and ventas[0]['count'] > 0:
                raise ValueError("No se puede eliminar. Tiene ventas recientes.")
            
            # Marcar como inactivo
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE productos 
                    SET activo = 0 
                    WHERE id = ?
                ''', (producto_id,))
                conn.commit()
        except Exception as e:
            print(f"❌ Error eliminando producto: {e}")
            traceback.print_exc()
            raise
    
    def buscar_producto(self, nombre):
        """Busca productos por nombre"""
        try:
            return self._execute_query('''
                SELECT * FROM productos 
                WHERE nombre LIKE ? AND activo = 1
                ORDER BY nombre
            ''', (f'%{nombre}%',))
        except Exception as e:
            print(f"❌ Error buscando productos: {e}")
            traceback.print_exc()
            return []
    
    # ========== UNIDADES DE MEDIDA ==========
    
    def agregar_unidad_medida(self, nombre, tipo, abreviatura):
        """Agrega una nueva unidad de medida"""
        try:
            nombre = validate_name(nombre, "nombre de la unidad")
            tipo = validate_name(tipo, "tipo de unidad")
            
            # Verificar que no exista
            existente = self._execute_query(
                'SELECT id FROM unidades_medida WHERE nombre = ?', 
                (nombre,)
            )
            if existente:
                raise ValueError(f"La unidad '{nombre}' ya existe")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO unidades_medida (nombre, tipo, abreviatura)
                    VALUES (?, ?, ?)
                ''', (nombre, tipo, abreviatura))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"❌ Error agregando unidad de medida: {e}")
            traceback.print_exc()
            raise
    
    def obtener_unidades_para_combobox(self, tipo=None):
        """✅ Obtiene unidades de medida para combobox: [(id, nombre), ...]"""
        try:
            query = 'SELECT id, nombre FROM unidades_medida WHERE 1=1'
            params = ()
            if tipo:
                query += ' AND tipo = ?'
                params = (tipo,)
            query += ' ORDER BY nombre'
            
            resultados = self._execute_query(query, params)
            return [(row['id'], row['nombre']) for row in resultados] if resultados else []
        except Exception as e:
            print(f"❌ Error obteniendo unidades para combobox: {e}")
            return []
    
    def verificar_estructura_bd(self):
        """Verifica la estructura de la base de datos"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar tablas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tablas = cursor.fetchall()
                print(f"📊 Tablas en BD: {[t[0] for t in tablas]}")
                
                # Verificar estructura de tabla ingredientes
                cursor.execute("PRAGMA table_info(ingredientes)")
                columnas = cursor.fetchall()
                print("📋 Columnas en 'ingredientes':")
                for col in columnas:
                    print(f"   {col[1]} ({col[2]})")
                    
                return True
        except Exception as e:
            print(f"❌ Error verificando estructura BD: {e}")
            return False
