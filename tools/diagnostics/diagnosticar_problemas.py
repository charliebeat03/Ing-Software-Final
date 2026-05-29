# diagnosticar_problemas.py
import os
import sys
import subprocess

def verificar_pyinstaller():
    """Verificar si PyInstaller está instalado y funciona"""
    print("\n🔍 Verificando PyInstaller...")
    try:
        import PyInstaller
        print(f"✅ PyInstaller versión: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller no está instalado")
        print("   Instálalo con: pip install pyinstaller")
        return False

def verificar_pyqt6():
    """Verificar si PyQt6 está instalado"""
    print("\n🔍 Verificando PyQt6...")
    try:
        import PyQt6
        print("✅ PyQt6 está instalado")
        
        # Verificar módulos específicos
        módulos = ['QtCore', 'QtGui', 'QtWidgets', 'QtPrintSupport']
        for módulo in módulos:
            try:
                __import__(f'PyQt6.{módulo}')
                print(f"  ✅ PyQt6.{módulo}")
            except:
                print(f"  ❌ PyQt6.{módulo} (FALTA)")
        
        return True
    except ImportError:
        print("❌ PyQt6 no está instalado")
        print("   Instálalo con: pip install PyQt6")
        return False

def verificar_estructura():
    """Verificar estructura del proyecto"""
    print("\n📁 Verificando estructura del proyecto...")
    
    requeridos = {
        'main_app.py': 'Archivo principal',
        'config.py': 'Configuración',
        'database.py': 'Base de datos',
        'styles.qss': 'Estilos',
        'modules/': 'Módulos de la aplicación',
        'data/': 'Datos y base de datos',
    }
    
    todo_ok = True
    for item, desc in requeridos.items():
        if os.path.exists(item):
            if os.path.isdir(item):
                print(f"✅ {item} (carpeta) - {desc}")
                # Mostrar contenido si es modules
                if item == 'modules/':
                    archivos = os.listdir('modules')
                    print(f"   Contiene {len(archivos)} archivos:")
                    for archivo in archivos[:10]:  # Mostrar primeros 10
                        print(f"     - {archivo}")
                    if len(archivos) > 10:
                        print(f"     ... y {len(archivos)-10} más")
            else:
                print(f"✅ {item} - {desc}")
        else:
            print(f"❌ {item} - {desc} (NO ENCONTRADO)")
            todo_ok = False
    
    return todo_ok

def verificar_imports():
    """Verificar que todos los módulos se pueden importar"""
    print("\n🔄 Verificando imports...")
    
    # Agregar rutas al sys.path
    sys.path.insert(0, '.')
    sys.path.insert(0, 'modules')
    sys.path.insert(0, 'utils')
    
    módulos_a_verificar = [
        'main_app',
        'config',
        'database',
        'modules.main_window',
    ]
    
    # Verificar módulos de la carpeta modules
    if os.path.exists('modules'):
        for archivo in os.listdir('modules'):
            if archivo.endswith('.py') and archivo != '__init__.py':
                módulo = f'modules.{archivo[:-3]}'
                módulos_a_verificar.append(módulo)
    
    errores = []
    for módulo in módulos_a_verificar:
        try:
            __import__(módulo)
            print(f"✅ {módulo}")
        except ImportError as e:
            print(f"❌ {módulo}: {e}")
            errores.append((módulo, str(e)))
        except Exception as e:
            print(f"⚠️  {módulo}: Error inesperado - {e}")
            errores.append((módulo, str(e)))
    
    return len(errores) == 0

def ejecutar_pyinstaller_simple():
    """Ejecutar PyInstaller con configuración mínima para verificar"""
    print("\n⚙️  Probando PyInstaller con configuración mínima...")
    
    # Comando simple
    comando = 'pyinstaller --onefile --windowed --clean main_app.py'
    
    print(f"Ejecutando: {comando}")
    print("(Esto puede tomar un momento)")
    
    resultado = subprocess.run(
        comando,
        shell=True,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    
    if resultado.returncode == 0:
        print("✅ PyInstaller funcionó correctamente")
        if os.path.exists('dist/main_app.exe'):
            print("✅ Ejecutable creado: dist/main_app.exe")
    else:
        print("❌ PyInstaller falló")
        print(f"Salida de error:\n{resultado.stderr}")
    
    return resultado.returncode == 0

def main():
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE PROBLEMAS DE COMPILACIÓN")
    print("=" * 80)
    
    # Verificar todo
    verificar_pyinstaller()
    verificar_pyqt6()
    
    if not verificar_estructura():
        print("\n❌ Problemas con la estructura del proyecto")
        return 1
    
    if not verificar_imports():
        print("\n❌ Problemas con los imports")
        return 1
    
    # Preguntar si probar PyInstaller
    respuesta = input("\n¿Quieres probar PyInstaller con configuración mínima? (s/n): ")
    if respuesta.lower() == 's':
        ejecutar_pyinstaller_simple()
    
    print("\n" + "=" * 80)
    print("📋 RESUMEN DEL DIAGNÓSTICO")
    print("=" * 80)
    print("\n🎯 RECOMENDACIONES:")
    print("1. Si hay errores de importación, corrígelos primero")
    print("2. Asegúrate de que todos los módulos tengan __init__.py")
    print("3. Verifica que no haya errores de sintaxis en los archivos .py")
    print("4. Prueba ejecutar la aplicación normal: python main_app.py")
    print("\n💡 Si python main_app.py funciona, el problema es de PyInstaller")
    
    input("\nPresiona Enter para terminar...")
    return 0

if __name__ == "__main__":
    sys.exit(main())