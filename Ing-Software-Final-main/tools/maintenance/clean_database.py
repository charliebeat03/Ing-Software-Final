# clean_database.py - Limpia base de datos para instalador v2.0
import sqlite3
import os
from pathlib import Path
from datetime import datetime
import sys

class DatabaseCleaner:
    """Limpia la base de datos para la versión 2.0"""
    
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self.backup_path = self.db_path.parent / "backups" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
    def create_backup(self):
        """Crea backup de la base de datos actual"""
        try:
            if self.db_path.exists():
                self.backup_path.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                shutil.copy2(self.db_path, self.backup_path)
                print(f"✅ Backup creado: {self.backup_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False
    
    def clean_database(self):
        """Limpia todos los datos excepto productos e ingredientes"""
        if not self.db_path.exists():
            print("❌ Base de datos no encontrada")
            return False
        
        try:
            # Crear backup primero
            self.create_backup()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            print("🔄 Limpiando base de datos...")
            
            # 1. Lista de tablas a limpiar completamente
            tables_to_truncate = [
                'compras',
                'ventas',
                'ventas_detalle',
                'pedidos_chef',
                'pedidos_chef_detalle',
                'produccion',
                'excedentes',
                'ajustes_inventario',
                'inventario_ingredientes',
                'inventario_productos'
            ]
            
            for table in tables_to_truncate:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"  - {table}: Limpio ✓")
                except sqlite3.OperationalError:
                    print(f"  - {table}: No existe o error")
            
            # 2. Resetear secuencias autoincrementales
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                          tables_to_truncate)
            
            # 3. Mantener solo datos esenciales en productos
            cursor.execute("""
                UPDATE productos SET 
                    precio_venta = CASE WHEN precio_venta < 0 THEN 0 ELSE precio_venta END,
                    costo_estimado = 0,
                    activo = 1
            """)
            
            # 4. Mantener solo datos esenciales en ingredientes
            cursor.execute("""
                UPDATE ingredientes SET 
                    costo_promedio = 0,
                    activo = 1
            """)
            
            # 5. Insertar datos de prueba si no hay productos
            cursor.execute("SELECT COUNT(*) FROM productos")
            if cursor.fetchone()[0] == 0:
                self.insert_sample_data(cursor)
            
            # 6. Optimizar base de datos
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            print("✅ Base de datos limpiada exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error limpiando base de datos: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def insert_sample_data(self, cursor):
        """Inserta datos de muestra para pruebas"""
        print("📝 Insertando datos de muestra...")
        
        # Insertar unidades de medida de muestra
        unidades = [
            ('kilogramo', 'peso', 'kg'),
            ('litro', 'volumen', 'L'),
            ('unidad', 'unidad', 'ud'),
            ('porción', 'unidad', 'porción')
        ]
        
        cursor.executemany(
            "INSERT OR IGNORE INTO unidades_medida (nombre, tipo, abreviatura) VALUES (?, ?, ?)",
            unidades
        )
        
        # Insertar ingredientes de muestra
        cursor.execute("SELECT id FROM unidades_medida WHERE nombre='kilogramo'")
        unidad_id = cursor.fetchone()[0]
        
        ingredientes = [
            ('Harina', unidad_id, 10, 0.5, 'Harina de trigo'),
            ('Azúcar', unidad_id, 5, 0.8, 'Azúcar refinada'),
            ('Huevos', unidad_id, 50, 0.1, 'Huevos unidad'),
            ('Leche', unidad_id, 5, 1.2, 'Leche entera')
        ]
        
        cursor.executemany(
            "INSERT INTO ingredientes (nombre, unidad_medida_id, stock_minimo, costo_promedio, notas) VALUES (?, ?, ?, ?, ?)",
            ingredientes
        )
        
        # Insertar productos de muestra
        productos = [
            ('Pan Francés', 2.5, 'porción', 1.2, 'Pan francés recién horneado'),
            ('Pastel de Chocolate', 4.0, 'porción', 2.0, 'Pastel de chocolate'),
            ('Café', 1.5, 'taza', 0.5, 'Café espresso')
        ]
        
        cursor.executemany(
            "INSERT INTO productos (nombre, precio_venta, unidad_venta, costo_estimado, descripcion) VALUES (?, ?, ?, ?, ?)",
            productos
        )
        
        print("  - Datos de muestra insertados ✓")
    
    def verify_clean_database(self):
        """Verifica que la base de datos esté limpia"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Verificar tablas vacías
            tables_to_check = ['compras', 'ventas', 'pedidos_chef', 'produccion']
            
            for table in tables_to_check:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"❌ Tabla {table} no está vacía: {count} registros")
                    conn.close()
                    return False
            
            # Verificar que productos e ingredientes existen
            cursor.execute("SELECT COUNT(*) FROM productos")
            productos_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ingredientes")
            ingredientes_count = cursor.fetchone()[0]
            
            conn.close()
            
            if productos_count > 0 and ingredientes_count > 0:
                print(f"✅ Verificación exitosa: {productos_count} productos, {ingredientes_count} ingredientes")
                return True
            else:
                print("❌ No hay productos o ingredientes")
                return False
                
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            return False

def main():
    """Función principal"""
    print("=" * 60)
    print("LIMPIADOR DE BASE DE DATOS - Codexia Systems v2.0")
    print("=" * 60)
    
    # Determinar ruta de la base de datos
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        # Buscar base de datos en ubicaciones comunes
        possible_paths = [
            "data/inventario.db",
            "inventario.db",
            "database.sqlite",
            "appdata/CodexiaSystems/Inventory/inventory.db"
        ]
        
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
        
        if not db_path:
            print("❌ No se encontró la base de datos")
            return 1
    
    print(f"📂 Base de datos: {db_path}")
    
    cleaner = DatabaseCleaner(db_path)
    
    # Limpiar base de datos
    if cleaner.clean_database():
        # Verificar limpieza
        if cleaner.verify_clean_database():
            print("\n" + "=" * 60)
            print("✅ BASE DE DATOS LISTA PARA INSTALADOR v2.0")
            print("=" * 60)
            print("\nLa base de datos ha sido limpiada y está lista para:")
            print("1. Incluir en el instalador")
            print("2. Pruebas del sistema")
            print("3. Migración a v2.0")
            return 0
        else:
            print("❌ La verificación falló")
            return 1
    else:
        print("❌ Falló la limpieza de la base de datos")
        return 1

if __name__ == "__main__":
    sys.exit(main())