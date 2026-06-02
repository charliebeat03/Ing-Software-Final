# main.py - Limpiador de base de datos para pruebas
import os
import sys
from database import db
import traceback

def limpiar_base_datos():
    """Limpia todos los datos de la base de datos excepto las unidades de medida"""
    print("🧹 LIMPIANDO BASE DE DATOS PARA PRUEBAS")
    print("="*60)
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Lista de tablas a limpiar (en orden inverso por dependencias de claves foráneas)
        tablas_a_limpiar = [
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
            'recetas',
            'productos',
            'ingredientes',
            # NO limpiar: 'unidades_medida', 'categorias_productos'
        ]
        
        # Desactivar temporalmente las restricciones de claves foráneas
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Limpiar cada tabla
        for tabla in tablas_a_limpiar:
            try:
                cursor.execute(f"DELETE FROM {tabla}")
                print(f"   ✓ Limpiada: {tabla}")
                
                # Reiniciar contador de autoincremento (si la tabla tiene)
                cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{tabla}'")
                
            except Exception as e:
                print(f"   ⚠️  Tabla {tabla}: {e}")
        
        # Reactivar restricciones de claves foráneas
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Verificar que unidades_medida sigue intacta
        cursor.execute("SELECT COUNT(*) as total FROM unidades_medida")
        unidades_count = cursor.fetchone()['total']
        print(f"\n   📏 Unidades de medida intactas: {unidades_count} registros")
        
        # Verificar estructura
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tablas = cursor.fetchall()
        print(f"   📊 Tablas existentes: {len(tablas)}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ BASE DE DATOS LIMPIADA EXITOSAMENTE")
        print("   Se han conservado las unidades de medida y la estructura de tablas.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR LIMPIANDO BASE DE DATOS: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        print("\n   Traceback:")
        traceback.print_exc()
        return False

def verificar_base_datos_vacia():
    """Verifica que la base de datos esté vacía"""
    print("\n🔍 VERIFICANDO BASE DE DATOS VACÍA")
    print("="*60)
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Verificar tablas clave
        tablas_a_verificar = [
            ('ingredientes', 'Ingredientes'),
            ('productos', 'Productos'),
            ('compras', 'Compras'),
            ('pedidos_chef', 'Pedidos del Chef'),
            ('produccion', 'Producción'),
            ('ventas', 'Ventas'),
            ('excedentes', 'Excedentes'),
        ]
        
        todas_vacias = True
        
        for tabla, nombre in tablas_a_verificar:
            cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
            count = cursor.fetchone()['total']
            estado = "✅ VACÍA" if count == 0 else f"❌ TIENE {count} REGISTROS"
            print(f"   {estado} - {nombre}")
            
            if count > 0:
                todas_vacias = False
        
        # Verificar unidades de medida (deberían estar)
        cursor.execute("SELECT COUNT(*) as total FROM unidades_medida")
        unidades_count = cursor.fetchone()['total']
        print(f"   📏 Unidades de medida: {unidades_count} registros (deben permanecer)")
        
        conn.close()
        
        return todas_vacias
        
    except Exception as e:
        print(f"❌ Error verificando: {e}")
        return False

def insertar_datos_prueba_minimos():
    """Inserta datos mínimos para probar que funciona"""
    print("\n🧪 INSERTANDO DATOS DE PRUEBA MÍNIMOS")
    print("="*60)
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Obtener ID de kilogramo
        cursor.execute("SELECT id FROM unidades_medida WHERE nombre='kilogramo' LIMIT 1")
        kg_row = cursor.fetchone()
        
        if not kg_row:
            print("❌ No se encontró la unidad 'kilogramo'")
            return False
        
        kg_id = kg_row['id']
        
        # Insertar 1 ingrediente de prueba
        cursor.execute('''
            INSERT INTO ingredientes (nombre, unidad_medida_id, stock_minimo, notas)
            VALUES (?, ?, ?, ?)
        ''', ('Harina de Prueba', kg_id, 5.0, 'Ingrediente de prueba'))
        
        ingrediente_id = cursor.lastrowid
        
        # Crear registro en inventario
        cursor.execute('''
            INSERT INTO inventario_ingredientes (ingrediente_id, cantidad_actual)
            VALUES (?, 0)
        ''', (ingrediente_id,))
        
        # Insertar 1 producto de prueba
        cursor.execute('''
            INSERT INTO productos (nombre, precio_venta, unidad_venta, descripcion)
            VALUES (?, ?, ?, ?)
        ''', ('Producto de Prueba', 10.0, 'unidad', 'Producto de prueba'))
        
        producto_id = cursor.lastrowid
        
        # Crear registro en inventario
        cursor.execute('''
            INSERT INTO inventario_productos (producto_id, cantidad_disponible)
            VALUES (?, 0)
        ''', (producto_id,))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Datos mínimos insertados:")
        print(f"   - Ingrediente: Harina de Prueba (ID: {ingrediente_id})")
        print(f"   - Producto: Producto de Prueba (ID: {producto_id})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error insertando datos de prueba: {e}")
        return False

def mostrar_estado_final():
    """Muestra el estado final de la base de datos"""
    print("\n📊 ESTADO FINAL DE LA BASE DE DATOS")
    print("="*60)
    
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Contar registros por tabla
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tablas = cursor.fetchall()
        
        print("Tabla                 | Registros")
        print("-" * 40)
        
        for tabla_row in tablas:
            tabla = tabla_row['name']
            cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
            count = cursor.fetchone()['total']
            print(f"{tabla:20} | {count:8}")
        
        conn.close()
        
        print("\n🎯 La base de datos está lista para desarrollar la interfaz gráfica.")
        
    except Exception as e:
        print(f"❌ Error mostrando estado: {e}")

def main():
    """Función principal"""
    print("🔄 LIMPIADOR DE BASE DE DATOS - Control de Producción y Ventas")
    print("="*60)
    print("Este programa limpiará todos los datos de prueba pero mantendrá:")
    print("1. La estructura de tablas")
    print("2. Las unidades de medida")
    print("3. Las categorías de productos")
    print("="*60)
    
    # Preguntar confirmación
    respuesta = input("\n⚠️  ¿Estás seguro de limpiar TODOS los datos? (s/N): ").strip().lower()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("\n❌ Operación cancelada por el usuario.")
        return
    
    print("\n" + "="*60)
    print("INICIANDO LIMPIEZA...")
    print("="*60)
    
    # Paso 1: Limpiar base de datos
    if not limpiar_base_datos():
        print("\n❌ No se pudo limpiar la base de datos. Deteniendo.")
        return
    
    # Paso 2: Verificar que esté vacía
    if not verificar_base_datos_vacia():
        print("\n⚠️  Algunas tablas no están vacías. Continuando de todos modos.")
    
    # Paso 3: Insertar datos mínimos de prueba (opcional)
    respuesta2 = input("\n¿Deseas insertar datos mínimos de prueba? (s/N): ").strip().lower()
    
    if respuesta2 in ['s', 'si', 'sí', 'y', 'yes']:
        insertar_datos_prueba_minimos()
    
    # Paso 4: Mostrar estado final
    mostrar_estado_final()
    
    print("\n" + "="*60)
    print("✅ PROCESO COMPLETADO")
    print("="*60)
    print("\nAhora puedes:")
    print("1. Desarrollar la interfaz gráfica con Qt Designer")
    print("2. Probar la aplicación desde cero")
    print("3. Los archivos .ui deben colocarse en la carpeta 'ui/'")
    
    # Pausa en Windows
    if os.name == 'nt':
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Operación interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n💥 ERROR INESPERADO: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        print("\n   Traceback completo:")
        traceback.print_exc()
        
        if os.name == 'nt':
            input("\nPresiona Enter para salir...")