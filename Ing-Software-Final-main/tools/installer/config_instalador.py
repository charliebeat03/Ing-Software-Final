# config_installer.py - Configuración especial para instalador v2.0
import os
import sys
from pathlib import Path

class InstallerConfig:
    """Configuración para instalador - NO modifica tu config.py existente"""
    
    @staticmethod
    def get_appdata_path():
        """Obtiene ruta en AppData"""
        appdata = os.environ.get('APPDATA', '')
        if not appdata:
            appdata = str(Path.home())
        return Path(appdata) / "CodexiaSystems" / "Inventory"
    
    @staticmethod
    def get_modules_path():
        """Ruta de módulos en AppData"""
        return InstallerConfig.get_appdata_path() / "modules"
    
    @staticmethod
    def get_utils_path():
        """Ruta de utils en AppData"""
        return InstallerConfig.get_appdata_path() / "utils"
    
    @staticmethod
    def get_database_path():
        """Ruta de base de datos en AppData"""
        return InstallerConfig.get_appdata_path() / "inventory.db"
    
    @staticmethod
    def create_appdata_structure():
        """Crea toda la estructura en AppData"""
        paths = [
            InstallerConfig.get_appdata_path(),
            InstallerConfig.get_modules_path(),
            InstallerConfig.get_utils_path(),
            InstallerConfig.get_appdata_path() / "data",
            InstallerConfig.get_appdata_path() / "backups",
            InstallerConfig.get_appdata_path() / "logs"
        ]
        
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)
        
        return True

# Instancia global
config_installer = InstallerConfig()