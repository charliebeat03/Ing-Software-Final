#!/usr/bin/env python3
# reset_bd_completo.py - SCRIPT PARA REINICIAR COMPLETAMENTE LA BASE DE DATOS CON DATOS REALES

import sqlite3
import os
import traceback
from datetime import datetime

class ResetBaseDatos:
    def __init__(self, db_path='data/inventario.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
    def conectar(self):
        """Conecta a la base de datos"""
        try:
            # Asegurar que exista el directorio data
            os.makedirs('data', exist_ok=True)
            
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print("✅ Conectado a la base de datos")
            return True
        except Exception as e:
            print(f"❌ Error conectando a la BD: {e}")
            return False
    
    def desconectar(self):
        """Cierra la conexión a la base de datos"""
        if self.conn:
            self.conn.close()
            print("✅ Conexión cerrada")
    
    def desactivar_claves_foraneas(self):
        """Desactiva temporalmente las claves foráneas"""
        try:
            self.cursor.execute("PRAGMA foreign_keys = OFF")
            print("🔧 Claves foráneas desactivadas temporalmente")
        except Exception as e:
            print(f"❌ Error desactivando claves foráneas: {e}")
    
    def activar_claves_foraneas(self):
        """Reactiva las claves foráneas"""
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON")
            print("🔧 Claves foráneas reactivadas")
        except Exception as e:
            print(f"❌ Error reactivando claves foráneas: {e}")
    
    def eliminar_todos_los_datos(self):
        """Elimina todos los datos de todas las tablas (excepto estructura)"""
        print("\n" + "="*60)
        print("🗑️  ELIMINANDO TODOS LOS DATOS EXISTENTES")
        print("="*60)
        
        # Desactivar claves foráneas para poder eliminar en cualquier orden
        self.desactivar_claves_foraneas()
        
        # Lista de tablas en orden inverso de dependencias (basado en estructura real de database.py)
        tablas = [
            'ajustes_inventario',
            'excedentes',
            'ventas_detalle',
            'ventas',
            'produccion',
            'pedidos_chef_detalle',
            'pedidos_chef',
            'compras',
            'inventario_productos',
            'inventario_ingredientes',
            'productos',
            'ingredientes',
            'unidades_medida'
        ]
        
        total_eliminados = 0
        
        for tabla in tablas:
            try:
                self.cursor.execute(f"DELETE FROM {tabla}")
                eliminados = self.cursor.rowcount
                total_eliminados += eliminados
                print(f"✅ Tabla '{tabla}': {eliminados} registros eliminados")
            except sqlite3.OperationalError as e:
                # La tabla no existe, continuar
                if "no such table" in str(e):
                    print(f"⚠️  Tabla '{tabla}' no existe, continuando...")
                    continue
                else:
                    print(f"❌ Error eliminando tabla '{tabla}': {e}")
            except Exception as e:
                print(f"❌ Error eliminando tabla '{tabla}': {e}")
        
        self.conn.commit()
        
        # Reactivar claves foráneas
        self.activar_claves_foraneas()
        
        print(f"✅ Total eliminado: {total_eliminados} registros en todas las tablas")
        return total_eliminados
    
    def reiniciar_secuencias(self):
        """Reinicia las secuencias de autoincremento"""
        print("\n" + "="*60)
        print("🔄 REINICIANDO SECUENCIAS DE AUTOINCREMENTO")
        print("="*60)
        
        tablas_autoincrement = [
            'unidades_medida', 'ingredientes', 'productos', 
            'compras', 'ventas', 'produccion', 'pedidos_chef',
            'ventas_detalle', 'pedidos_chef_detalle', 'excedentes',
            'ajustes_inventario', 'inventario_ingredientes', 'inventario_productos'
        ]
        
        for tabla in tablas_autoincrement:
            try:
                # En SQLite, se reinicia la secuencia eliminando de sqlite_sequence
                self.cursor.execute("DELETE FROM sqlite_sequence WHERE name = ?", (tabla,))
                print(f"✅ Secuencia de '{tabla}' reiniciada")
            except Exception as e:
                # La tabla puede no existir o no tener autoincrement
                print(f"⚠️  No se pudo reiniciar secuencia de '{tabla}': {e}")
        
        self.conn.commit()
    
    def agregar_unidades_medida(self):
        """Agrega todas las unidades de medida necesarias"""
        print("\n" + "="*60)
        print("📏 AGREGANDO UNIDADES DE MEDIDA")
        print("="*60)
        
        # UNIDADES SEGÚN LA ESTRUCTURA REAL (database.py)
        unidades = [
            # Peso (de database.py)
            ('kilogramo', 'peso', 'kg'),
            ('gramo', 'peso', 'g'),
            ('libra', 'peso', 'lb'),
            ('onza', 'peso', 'oz'),
            
            # Volumen (de database.py)
            ('litro', 'volumen', 'L'),
            ('mililitro', 'volumen', 'ml'),
            
            # Unidad (de database.py)
            ('unidad', 'unidad', 'ud'),
            ('docena', 'unidad', 'dz'),
            ('paquete', 'unidad', 'pqt'),
            ('caja', 'unidad', 'caja'),
            ('ración', 'unidad', 'ración'),
            ('porción', 'unidad', 'porción'),
            
            # ✅ UNIDADES NUEVAS SOLICITADAS:
            ('Paquete', 'unidad', 'Pqte'),      # Para espagueti, caldo, salchichas
            ('Mano', 'unidad', 'mano'),         # Para Fongo
            ('Lata', 'unidad', 'lata'),         # Para crema de leche
        ]
        
        agregadas = 0
        for nombre, tipo, abreviatura in unidades:
            try:
                # Verificar si ya existe
                self.cursor.execute(
                    "SELECT id FROM unidades_medida WHERE nombre = ? OR abreviatura = ?",
                    (nombre, abreviatura)
                )
                existe = self.cursor.fetchone()
                
                if not existe:
                    self.cursor.execute(
                        "INSERT INTO unidades_medida (nombre, tipo, abreviatura, activo) VALUES (?, ?, ?, 1)",
                        (nombre, tipo, abreviatura)
                    )
                    agregadas += 1
                    print(f"✅ '{nombre}' ({abreviatura}) - {tipo}")
                else:
                    print(f"⚠️  '{nombre}' ya existe")
            except Exception as e:
                print(f"❌ Error agregando unidad '{nombre}': {e}")
        
        self.conn.commit()
        print(f"✅ {agregadas} unidades de medida agregadas")
        return agregadas
    
    def obtener_id_unidad(self, abreviatura):
        """Obtiene el ID de una unidad por su abreviatura"""
        try:
            self.cursor.execute(
                "SELECT id FROM unidades_medida WHERE abreviatura = ?",
                (abreviatura,)
            )
            resultado = self.cursor.fetchone()
            return resultado[0] if resultado else None
        except Exception as e:
            print(f"❌ Error obteniendo ID de unidad '{abreviatura}': {e}")
            return None
    
    def agregar_ingredientes(self):
        """Agrega todos los ingredientes con sus stocks mínimos (CORREGIDO CON VALORES REALES)"""
        print("\n" + "="*60)
        print("🥦 AGREGANDO INGREDIENTES CON STOCK MÍNIMO REAL")
        print("="*60)
        
        # Formato: (nombre, unidad_abreviatura, stock_minimo, notas)
        ingredientes = [
            # NOMBRE, UNIDAD, STOCK MÍNIMO (CORREGIDO), NOTAS
            # Ingredientes CON stock mínimo especificado:
            ('Queso', 'lb', 1.0, 'Queso para empanadas y hamburguesas'),
            ('Harina', 'lb', 10.0, 'Harina para masas'),
            ('Salchichas', 'pqt', 1.0, 'Salchichas para empanadas y pastas'),
            ('Aceite', 'L', 4.0, 'Aceite para freír'),
            ('Spaghetti', 'pqt', 5.0, 'Spaghetti para pastas'),
            ('Puré de tomate', 'L', 2.0, 'Puré de tomate para salsas'),
            ('Caldo de pollo', 'pqt', 5.0, 'Caldo en polvo o cubitos'),
            ('Ajo', 'ud', 10.0, 'Ajo fresco'),
            ('Cebolla', 'ud', 10.0, 'Cebolla blanca o morada'),
            ('Huevo', 'ud', 5.0, 'Huevos para preparaciones'),
            ('Guayaba', 'ud', 20.0, 'Guayaba para empanadas dulces'),
            ('Crema de leche', 'lata', 1.0, 'Crema de leche en lata'),
            ('Papas', 'lb', 1.0, 'Papas para tostones y salchipapas'),
            ('Termo pack', 'ud', 20.0, 'Envases para llevar'),
            ('Azúcar', 'lb', 1.0, 'Azúcar para preparaciones dulces'),
            ('Masa de Hamburguesa', 'lb', 0.5, 'Masa preparada para hamburguesas'),
            ('Panes de Hamburguesa', 'ud', 5.0, 'Pan para hamburguesas'),
            ('Fongo', 'mano', 1.0, 'Fongo (plátano verde) por manos'),
            
            # Ingredientes SIN stock mínimo especificado (se establecen en 0):
            ('Picadillo', 'lb', 0.0, 'Picadillo de carne para empanadas'),
            ('Levadura', 'lb', 0.0, 'Levadura para masas'),
            ('Vinagre', 'L', 0.0, 'Vinagre para aderezos'),
            ('Sal', 'lb', 0.0, 'Sal para sazonar'),
        ]
        
        agregados = 0
        ids_ingredientes = {}  # Para guardar IDs por nombre
        
        for nombre, unidad_abrev, stock_minimo, notas in ingredientes:
            try:
                # Obtener ID de la unidad
                unidad_id = self.obtener_id_unidad(unidad_abrev)
                if not unidad_id:
                    print(f"❌ Unidad '{unidad_abrev}' no encontrada para '{nombre}'")
                    continue
                
                # Insertar ingrediente (CORREGIDO: usar stock_minimo, no cantidad_minima)
                self.cursor.execute('''
                    INSERT INTO ingredientes 
                    (nombre, unidad_medida_id, stock_minimo, costo_promedio, activo, notas, fecha_creacion)
                    VALUES (?, ?, ?, 0.0, 1, ?, CURRENT_TIMESTAMP)
                ''', (nombre, unidad_id, float(stock_minimo), notas))
                
                ingrediente_id = self.cursor.lastrowid
                ids_ingredientes[nombre] = ingrediente_id
                agregados += 1
                
                # Inicializar inventario en 0 (CORREGIDO: usar inventario_ingredientes)
                self.cursor.execute('''
                    INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual, fecha_actualizacion)
                    VALUES (?, 0.0, datetime('now'))
                ''', (ingrediente_id,))
                
                # Mostrar con color según stock mínimo
                if stock_minimo > 0:
                    print(f"✅ {nombre}: {stock_minimo} {unidad_abrev} mínimo (ID: {ingrediente_id})")
                else:
                    print(f"⚠️  {nombre}: Sin stock mínimo definido (0 {unidad_abrev})")
                
            except Exception as e:
                print(f"❌ Error agregando ingrediente '{nombre}': {e}")
                traceback.print_exc()
        
        self.conn.commit()
        print(f"\n📊 RESUMEN INGREDIENTES:")
        print(f"   - {len([i for i in ingredientes if i[2] > 0])} ingredientes CON stock mínimo definido")
        print(f"   - {len([i for i in ingredientes if i[2] == 0])} ingredientes SIN stock mínimo (0)")
        print(f"✅ {agregados} ingredientes agregados e inventario inicializado en 0")
        return ids_ingredientes
    
    def agregar_productos(self):
        """Agrega todos los productos con sus precios (CORREGIDO CON PRECIOS REALES)"""
        print("\n" + "="*60)
        print("🍔 AGREGANDO PRODUCTOS CON PRECIOS REALES")
        print("="*60)
        
        # Formato: (nombre, precio_venta, unidad_venta, categoria, descripcion)
        productos = [
            # EMPANADAS
            ('Empanada Guayaba', 180.0, 'ud', 'Empanadas', 'Empanada de guayaba'),
            ('Empanada V.', 200.0, 'ud', 'Empanadas', 'Empanada de verdura'),
            ('Empanada P.', 240.0, 'ud', 'Empanadas', 'Empanada de pollo'),
            ('Empanada Salchichas', 280.0, 'ud', 'Empanadas', 'Empanada de salchichas'),
            ('Empanada Queso', 300.0, 'ud', 'Empanadas', 'Empanada de queso'),
            ('Empanada Dulce Leche', 400.0, 'ud', 'Empanadas', 'Empanada de dulce de leche'),
            
            # EMPANADAS MIXTAS
            ('Empanada V. + P.', 340.0, 'ud', 'Empanadas Mixtas', 'Empanada de verdura y pollo'),
            ('Empanada V. + Salchichas', 360.0, 'ud', 'Empanadas Mixtas', 'Empanada de verdura y salchichas'),
            ('Empanada Salchichas + Queso', 400.0, 'ud', 'Empanadas Mixtas', 'Empanada de salchichas y queso'),
            ('Empanada Guayaba + Queso', 400.0, 'ud', 'Empanadas Mixtas', 'Empanada de guayaba y queso'),
            ('Empanada a tu gusto', 750.0, 'ud', 'Empanadas Mixtas', 'Oferta de la casa - personalizada'),
            
            # HAMBURGUESAS
            ('Hamburguesa Simple', 400.0, 'ud', 'Hamburguesas', 'Hamburguesa básica'),
            ('Hamburguesa Queso', 600.0, 'ud', 'Hamburguesas', 'Hamburguesa con queso'),
            
            # PASTAS
            ('Pasta Napolitana', 550.0, 'ud', 'Pastas', 'Pasta con salsa napolitana'),
            ('Pasta Salchichas', 750.0, 'ud', 'Pastas', 'Pasta con salchichas'),
            
            # TOSTONES RELLENOS
            ('Tostones Rellenos P.', 800.0, 'ud', 'Tostones', 'Tostones rellenos de pollo'),
            ('Tostones Rellenos Salchichas', 1000.0, 'ud', 'Tostones', 'Tostones rellenos de salchichas'),
            
            # OTROS
            ('Croquetas de Pollo', 1200.0, 'pqt', 'Fritos', '20 unidades por paquete'),
            ('Salchipapas', 1500.0, 'ud', 'Platos Fuertes', 'Papas fritas con salchichas'),
        ]
        
        agregados = 0
        ids_productos = {}  # Para guardar IDs por nombre
        
        for nombre, precio_venta, unidad_venta, categoria, descripcion in productos:
            try:
                # Insertar producto (CORREGIDO: usar costo_estimado, no precio_costo)
                self.cursor.execute('''
                    INSERT INTO productos 
                    (nombre, precio_venta, unidad_venta, costo_estimado, activo, descripcion, fecha_creacion)
                    VALUES (?, ?, ?, ?, 1, ?, CURRENT_TIMESTAMP)
                ''', (nombre, float(precio_venta), unidad_venta, float(precio_venta) * 0.6, f"{categoria}: {descripcion}"))
                
                producto_id = self.cursor.lastrowid
                ids_productos[nombre] = producto_id
                agregados += 1
                
                # Inicializar inventario en 0 (CORREGIDO: usar inventario_productos)
                self.cursor.execute('''
                    INSERT INTO inventario_productos (producto_id, cantidad_disponible, fecha_actualizacion)
                    VALUES (?, 0, datetime('now'))
                ''', (producto_id,))
                
                print(f"✅ {nombre}: ${precio_venta:.0f} - {categoria}")
                
            except Exception as e:
                print(f"❌ Error agregando producto '{nombre}': {e}")
                traceback.print_exc()
        
        self.conn.commit()
        print(f"\n📊 RESUMEN PRODUCTOS:")
        print(f"   - 6 Empanas simples")
        print(f"   - 5 Empanadas mixtas")
        print(f"   - 2 Hamburguesas")
        print(f"   - 2 Pastas")
        print(f"   - 2 Tostones rellenos")
        print(f"   - 2 Otros productos")
        print(f"✅ {agregados} productos agregados con inventario inicializado en 0")
        return ids_productos
    
    def crear_tablas_si_no_existen(self):
        """Crea las tablas básicas si no existen (USANDO ESTRUCTURA REAL)"""
        print("\n" + "="*60)
        print("🏗️  VERIFICANDO ESTRUCTURA DE LA BASE DE DATOS")
        print("="*60)
        
        # Tabla unidades_medida (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS unidades_medida (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL,
                abreviatura TEXT,
                activo BOOLEAN DEFAULT 1
            )
        ''')
        
        # Tabla ingredientes (ESTRUCTURA REAL - CORREGIDA: stock_minimo en lugar de cantidad_minima)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ingredientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                unidad_medida_id INTEGER NOT NULL,
                stock_minimo REAL DEFAULT 0,
                costo_promedio REAL DEFAULT 0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT 1,
                notas TEXT,
                FOREIGN KEY (unidad_medida_id) REFERENCES unidades_medida(id)
            )
        ''')
        
        # Tabla inventario_ingredientes (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventario_ingredientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingrediente_id INTEGER UNIQUE NOT NULL,
                cantidad_actual REAL DEFAULT 0,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
            )
        ''')
        
        # Tabla productos (ESTRUCTURA REAL - CORREGIDA: costo_estimado en lugar de precio_costo)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                precio_venta REAL NOT NULL,
                unidad_venta TEXT NOT NULL,
                costo_estimado REAL DEFAULT 0,
                fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                activo BOOLEAN DEFAULT 1,
                descripcion TEXT,
                CHECK (precio_venta >= 0)
            )
        ''')
        
        # Tabla inventario_productos (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventario_productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER UNIQUE NOT NULL,
                cantidad_disponible INTEGER DEFAULT 0,
                fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        ''')
        
        # Tabla compras (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                ingrediente_id INTEGER NOT NULL,
                cantidad REAL NOT NULL,
                costo_unitario REAL NOT NULL,
                total REAL GENERATED ALWAYS AS (cantidad * costo_unitario) STORED,
                notas TEXT,
                FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id)
            )
        ''')
        
        # Tabla ventas (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad_total INTEGER NOT NULL DEFAULT 0,
                total_ventas REAL DEFAULT 0,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                UNIQUE(fecha, producto_id)
            )
        ''')
        
        # Tabla ventas_detalle (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventas_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venta_id INTEGER NOT NULL,
                hora TIME DEFAULT CURRENT_TIME,
                cantidad INTEGER NOT NULL,
                FOREIGN KEY (venta_id) REFERENCES ventas(id)
            )
        ''')
        
        # Tabla produccion (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS produccion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                costo_total REAL,
                notas TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            )
        ''')
        
        # Tabla pedidos_chef (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos_chef (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                ingrediente_id INTEGER NOT NULL,
                cantidad_total REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id),
                UNIQUE(fecha, ingrediente_id)
            )
        ''')
        
        # Tabla pedidos_chef_detalle (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos_chef_detalle (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER NOT NULL,
                hora TIME DEFAULT CURRENT_TIME,
                cantidad REAL NOT NULL,
                motivo TEXT,
                FOREIGN KEY (pedido_id) REFERENCES pedidos_chef(id)
            )
        ''')
        
        # Tabla excedentes (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS excedentes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATE NOT NULL,
                producto_id INTEGER NOT NULL,
                producido INTEGER NOT NULL,
                vendido INTEGER NOT NULL,
                excedente INTEGER GENERATED ALWAYS AS (producido - vendido) STORED,
                FOREIGN KEY (producto_id) REFERENCES productos(id),
                UNIQUE(fecha, producto_id)
            )
        ''')
        
        # Tabla ajustes_inventario (ESTRUCTURA REAL)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ajustes_inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                tipo TEXT NOT NULL,
                elemento_id INTEGER NOT NULL,
                cantidad_anterior REAL NOT NULL,
                cantidad_nueva REAL NOT NULL,
                motivo TEXT NOT NULL,
                notas TEXT
            )
        ''')
        
        self.conn.commit()
        print("✅ Estructura de tablas verificada/creada")
    
    def verificar_datos(self):
        """Verifica que los datos se hayan insertado correctamente (CORREGIDO)"""
        print("\n" + "="*60)
        print("🔍 VERIFICANDO DATOS INSERTADOS")
        print("="*60)
        
        # Contar unidades de medida
        self.cursor.execute("SELECT COUNT(*) FROM unidades_medida")
        total_unidades = self.cursor.fetchone()[0]
        print(f"📏 Unidades de medida: {total_unidades}")
        
        # Mostrar unidades
        self.cursor.execute("SELECT nombre, abreviatura, tipo FROM unidades_medida ORDER BY tipo, nombre")
        unidades = self.cursor.fetchall()
        for nombre, abrev, tipo in unidades:
            print(f"   - {nombre} ({abrev}) - {tipo}")
        
        # Contar ingredientes
        self.cursor.execute("SELECT COUNT(*) FROM ingredientes")
        total_ingredientes = self.cursor.fetchone()[0]
        print(f"\n🥦 Ingredientes: {total_ingredientes}")
        
        # Mostrar ingredientes con sus stocks mínimos (CORREGIDO: usar stock_minimo)
        print("\n📊 INGREDIENTES CON STOCK MÍNIMO:")
        self.cursor.execute('''
            SELECT i.nombre, um.abreviatura, i.stock_minimo 
            FROM ingredientes i 
            JOIN unidades_medida um ON i.unidad_medida_id = um.id 
            ORDER BY i.stock_minimo DESC, i.nombre
        ''')
        ingredientes = self.cursor.fetchall()
        
        print("\n📈 CON STOCK MÍNIMO DEFINIDO (>0):")
        for nombre, unidad, stock_min in ingredientes:
            if stock_min > 0:
                print(f"   ✅ {nombre}: {stock_min} {unidad}")
        
        print("\n⚠️  SIN STOCK MÍNIMO DEFINIDO (=0):")
        for nombre, unidad, stock_min in ingredientes:
            if stock_min == 0:
                print(f"   ⚠️  {nombre}: Sin mínimo (0 {unidad})")
        
        # Contar productos
        self.cursor.execute("SELECT COUNT(*) FROM productos")
        total_productos = self.cursor.fetchone()[0]
        print(f"\n🍔 Productos: {total_productos}")
        
        # Mostrar productos por categoría
        print("\n📦 PRODUCTOS POR CATEGORÍA:")
        self.cursor.execute('''
            SELECT 
                CASE 
                    WHEN nombre LIKE '%Empanada%' AND nombre NOT LIKE '%+%' THEN 'Empanadas'
                    WHEN nombre LIKE '%Empanada%' AND nombre LIKE '%+%' THEN 'Empanadas Mixtas'
                    WHEN nombre LIKE '%Hamburguesa%' THEN 'Hamburguesas'
                    WHEN nombre LIKE '%Pasta%' THEN 'Pastas'
                    WHEN nombre LIKE '%Tostones%' THEN 'Tostones'
                    ELSE 'Otros'
                END as categoria,
                COUNT(*) as cantidad,
                SUM(precio_venta) as valor_total
            FROM productos 
            GROUP BY categoria
            ORDER BY categoria
        ''')
        
        categorias = self.cursor.fetchall()
        for categoria, cantidad, valor_total in categorias:
            print(f"   - {categoria}: {cantidad} productos (Valor total: ${valor_total:.0f})")
        
        # Mostrar primeros 10 productos con su precio
        print("\n💰 TOP 10 PRODUCTOS POR PRECIO:")
        self.cursor.execute("SELECT nombre, precio_venta, unidad_venta FROM productos ORDER BY precio_venta DESC LIMIT 10")
        productos = self.cursor.fetchall()
        for nombre, precio, unidad in productos:
            print(f"   - {nombre}: ${precio:.0f} ({unidad})")
        
        # Verificar inventarios
        self.cursor.execute("SELECT COUNT(*) FROM inventario_ingredientes")
        inv_ingredientes = self.cursor.fetchone()[0]
        self.cursor.execute("SELECT COUNT(*) FROM inventario_productos")
        inv_productos = self.cursor.fetchone()[0]
        
        print(f"\n📊 INVENTARIOS INICIALIZADOS:")
        print(f"   - Ingredientes: {inv_ingredientes} registros (todos en 0)")
        print(f"   - Productos: {inv_productos} registros (todos en 0)")
        
        # Mostrar alertas potenciales (CORREGIDO: usar stock_minimo)
        print("\n⚠️  ALERTAS POTENCIALES (cuando se registren compras):")
        self.cursor.execute('''
            SELECT i.nombre, um.abreviatura, i.stock_minimo
            FROM ingredientes i 
            JOIN unidades_medida um ON i.unidad_medida_id = um.id 
            WHERE i.stock_minimo > 0
            ORDER BY i.stock_minimo DESC
        ''')
        alertas = self.cursor.fetchall()
        
        if alertas:
            for nombre, unidad, stock_min in alertas:
                print(f"   - {nombre}: Alerta cuando stock < {stock_min} {unidad}")
        else:
            print("   - No hay alertas configuradas (todos los stocks mínimos son 0)")
        
        return total_unidades, total_ingredientes, total_productos
    
    def crear_backup(self):
        """Crea un backup de la base de datos actual antes de hacer cambios"""
        import shutil
        import time
        
        if not os.path.exists(self.db_path):
            print("⚠️  No existe base de datos para hacer backup")
            return False
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = f"data/inventario_backup_{timestamp}.db"
        
        try:
            shutil.copy2(self.db_path, backup_path)
            print(f"💾 Backup creado: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False
    
    def ejecutar_reset_completo(self):
        """Ejecuta todo el proceso de reset"""
        print("="*60)
        print("🔄 REINICIO COMPLETO DE BASE DE DATOS")
        print("="*60)
        print(f"📁 Base de datos: {self.db_path}")
        print(f"🕐 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # 1. Crear backup
        print("\n1. CREANDO BACKUP...")
        self.crear_backup()
        
        # 2. Conectar
        print("\n2. CONECTANDO A LA BD...")
        if not self.conectar():
            return False
        
        try:
            # 3. Verificar/crear estructura
            print("\n3. VERIFICANDO ESTRUCTURA...")
            self.crear_tablas_si_no_existen()
            
            # 4. Eliminar todos los datos
            print("\n4. ELIMINANDO DATOS EXISTENTES...")
            self.eliminar_todos_los_datos()
            
            # 5. Reiniciar secuencias
            print("\n5. REINICIANDO SECUENCIAS...")
            self.reiniciar_secuencias()
            
            # 6. Agregar unidades de medida
            print("\n6. AGREGANDO UNIDADES DE MEDIDA...")
            self.agregar_unidades_medida()
            
            # 7. Agregar ingredientes
            print("\n7. AGREGANDO INGREDIENTES CON STOCK MÍNIMO...")
            ids_ingredientes = self.agregar_ingredientes()
            
            # 8. Agregar productos
            print("\n8. AGREGANDO PRODUCTOS...")
            ids_productos = self.agregar_productos()
            
            # 9. Verificar datos
            print("\n9. VERIFICANDO DATOS...")
            self.verificar_datos()
            
            print("\n" + "="*60)
            print("🎉 REINICIO COMPLETADO EXITOSAMENTE!")
            print("="*60)
            print("\n📋 RESUMEN COMPLETO:")
            print("   - Se eliminaron todos los datos anteriores")
            print("   - Se agregaron unidades de medida necesarias")
            print("   - Se agregaron 22 ingredientes (18 con stock mínimo, 4 sin mínimo)")
            print("   - Se agregaron 17 productos en 6 categorías diferentes")
            print("   - Todos los inventarios inicializados en 0")
            print("\n⚠️  IMPORTANTE PARA LAS ALERTAS:")
            print("   - 18 ingredientes tienen stock mínimo definido para alertas")
            print("   - 4 ingredientes NO tienen stock mínimo (se mantienen en 0)")
            print("   - Las alertas funcionarán automáticamente cuando el stock baje del mínimo")
            print("\n📝 SIGUIENTES PASOS:")
            print("   1. Registrar compras para tener stock inicial")
            print("   2. Probar las alertas en el módulo de Inventario")
            print("   3. Verificar que todos los módulos carguen correctamente")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR DURANTE EL PROCESO: {e}")
            traceback.print_exc()
            return False
        
        finally:
            # Siempre desconectar
            self.desconectar()

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("🔄 REINICIADOR DE BASE DE DATOS - SISTEMA DE CONTROL DE PRODUCCIÓN")
    print("="*60)
    print("\n⚠️  ADVERTENCIA: Este script eliminará TODOS los datos existentes")
    print("   y los reemplazará con los datos reales proporcionados.")
    print("\n📊 DATOS QUE SE INSERTARÁN:")
    print("   - 22 ingredientes con stocks mínimos REALES")
    print("   - 17 productos con precios REALES")
    print("   - Alertas configuradas para 18 ingredientes")
    print("\n¿Estás seguro de continuar?")
    
    respuesta = input("Escribe 'SI' para continuar, cualquier otra cosa para cancelar: ")
    
    if respuesta.upper() != 'SI':
        print("\n❌ Operación cancelada por el usuario")
        return
    
    # Crear instancia y ejecutar
    reset = ResetBaseDatos()
    exito = reset.ejecutar_reset_completo()
    
    if exito:
        print("\n✅ Proceso completado exitosamente!")
        print("\n🔧 Ahora puedes ejecutar el sistema y verificar:")
        print("   - Los ingredientes con sus stocks mínimos")
        print("   - Los productos con sus precios")
        print("   - Las alertas funcionando en el módulo de Inventario")
    else:
        print("\n❌ Ocurrió un error durante el proceso")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()