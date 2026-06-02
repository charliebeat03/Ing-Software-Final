# migrate_simple.py - Migración básica de datos
import sqlite3
import os
import sys
from pathlib import Path

def migrate_simple():
    """Migración simple para el instalador"""
    print("Buscando datos de versión anterior...")
    
    # Ubicaciones posibles de datos viejos
    old_locations = [
        Path(os.environ.get('APPDATA', '')) / "GestorInventario" / "inventario.db",
        Path.home() / "Desktop" / "inventario.db",
        Path("C:/") / "inventario.db",
    ]
    
    # Ubicación nueva
    new_location = Path(os.environ.get('APPDATA', '')) / "CodexiaSystems" / "Inventory" / "data" / "inventory.db"
    
    # Buscar archivo viejo
    old_db = None
    for loc in old_locations:
        if loc.exists():
            old_db = loc
            print(f"Encontrado: {old_db}")
            break
    
    if old_db and not new_location.exists():
        try:
            # Copiar archivo
            import shutil
            new_location.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(old_db, new_location)
            print(f"✅ Datos migrados a: {new_location}")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    migrate_simple()
    input("Presione Enter para continuar...")