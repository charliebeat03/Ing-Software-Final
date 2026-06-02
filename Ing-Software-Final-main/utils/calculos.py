# utils/calculos.py - Cálculos automáticos
from datetime import date
from database import db

def calcular_excedentes_dia(fecha=None):
    """Calcula los excedentes del día (Producción - Ventas)"""
    if fecha is None:
        fecha = date.today().isoformat()
    
    # Obtener producción del día
    produccion = db.execute_query('''
        SELECT producto_id, SUM(cantidad) as total
        FROM produccion 
        WHERE fecha = ?
        GROUP BY producto_id
    ''', (fecha,))
    
    # Obtener ventas del día
    ventas = db.execute_query('''
        SELECT producto_id, cantidad_total as total
        FROM ventas 
        WHERE fecha = ?
    ''', (fecha,))
    
    # Convertir a diccionarios para fácil acceso
    prod_dict = {row['producto_id']: row['total'] for row in produccion}
    ventas_dict = {row['producto_id']: row['total'] for row in ventas}
    
    excedentes = []
    
    # Calcular excedentes para cada producto producido
    for producto_id, producido in prod_dict.items():
        vendido = ventas_dict.get(producto_id, 0)
        excedente = producido - vendido
        
        if excedente > 0:
            # Guardar o actualizar excedente
            db.execute_query('''
                INSERT OR REPLACE INTO excedentes 
                (fecha, producto_id, producido, vendido)
                VALUES (?, ?, ?, ?)
            ''', (fecha, producto_id, producido, vendido))
            
            # Actualizar inventario de productos (sumar excedente)
            actualizar_inventario_producto(producto_id, excedente, 'sumar')
            
            excedentes.append({
                'producto_id': producto_id,
                'producido': producido,
                'vendido': vendido,
                'excedente': excedente
            })
    
    return excedentes

def actualizar_inventario_ingrediente(ingrediente_id, cantidad, operacion='sumar'):
    """Actualiza el inventario de un ingrediente"""
    inventario = db.get_one('inventario_ingredientes', 'ingrediente_id = ?', (ingrediente_id,))
    
    if not inventario:
        # Crear registro si no existe
        db.execute_insert('''
            INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual)
            VALUES (?, ?)
        ''', (ingrediente_id, cantidad))
        return cantidad
    
    cantidad_actual = inventario['cantidad_actual']
    
    if operacion == 'sumar':
        nueva_cantidad = cantidad_actual + cantidad
    elif operacion == 'restar':
        nueva_cantidad = cantidad_actual - cantidad
        if nueva_cantidad < 0:
            raise ValueError(f"Stock insuficiente. Disponible: {cantidad_actual}")
    else:
        nueva_cantidad = cantidad
    
    # Actualizar inventario
    db.execute_query('''
        UPDATE inventario_ingredientes 
        SET cantidad_actual = ?, fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE ingrediente_id = ?
    ''', (nueva_cantidad, ingrediente_id))
    
    return nueva_cantidad

def actualizar_inventario_producto(producto_id, cantidad, operacion='sumar'):
    """Actualiza el inventario de un producto"""
    inventario = db.get_one('inventario_productos', 'producto_id = ?', (producto_id,))
    
    if not inventario:
        # Crear registro si no existe
        db.execute_insert('''
            INSERT INTO inventario_productos (producto_id, cantidad_disponible)
            VALUES (?, ?)
        ''', (producto_id, cantidad))
        return cantidad
    
    cantidad_actual = inventario['cantidad_disponible']
    
    if operacion == 'sumar':
        nueva_cantidad = cantidad_actual + cantidad
    elif operacion == 'restar':
        nueva_cantidad = cantidad_actual - cantidad
        if nueva_cantidad < 0:
            raise ValueError(f"Stock insuficiente. Disponible: {cantidad_actual}")
    else:
        nueva_cantidad = cantidad
    
    # Actualizar inventario
    db.execute_query('''
        UPDATE inventario_productos 
        SET cantidad_disponible = ?, fecha_actualizacion = CURRENT_TIMESTAMP
        WHERE producto_id = ?
    ''', (nueva_cantidad, producto_id))
    
    return nueva_cantidad

def calcular_costo_promedio_ingrediente(ingrediente_id):
    """Calcula el costo promedio de un ingrediente basado en las compras"""
    compras = db.execute_query('''
        SELECT SUM(cantidad) as total_cantidad, 
               SUM(cantidad * costo_unitario) as total_costo
        FROM compras 
        WHERE ingrediente_id = ?
    ''', (ingrediente_id,))
    
    if compras and compras[0]['total_cantidad'] and compras[0]['total_cantidad'] > 0:
        costo_promedio = compras[0]['total_costo'] / compras[0]['total_cantidad']
        
        # Actualizar en la tabla de ingredientes
        db.execute_query('''
            UPDATE ingredientes 
            SET costo_promedio = ?
            WHERE id = ?
        ''', (costo_promedio, ingrediente_id))
        
        return costo_promedio
    
    return 0

def obtener_total_ventas_dia(fecha=None):
    """Obtiene el total de ventas del día"""
    if fecha is None:
        fecha = date.today().isoformat()
    
    result = db.execute_query('''
        SELECT SUM(total_ventas) as total
        FROM ventas 
        WHERE fecha = ?
    ''', (fecha,))
    
    return result[0]['total'] if result and result[0]['total'] else 0

def obtener_pedidos_chef_dia(fecha=None):
    """Obtiene los pedidos del chef acumulados del día"""
    if fecha is None:
        fecha = date.today().isoformat()
    
    return db.execute_query('''
        SELECT i.nombre, pc.cantidad_total, um.abreviatura
        FROM pedidos_chef pc
        JOIN ingredientes i ON pc.ingrediente_id = i.id
        JOIN unidades_medida um ON i.unidad_medida_id = um.id
        WHERE pc.fecha = ?
    ''', (fecha,))