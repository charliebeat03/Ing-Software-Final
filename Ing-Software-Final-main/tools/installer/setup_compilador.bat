@echo off
chcp 65001 >nul
title COMPILACIÓN PYQT5 - GESTOR INVENTARIO
color 0A

echo ===================================================
echo    COMPILACIÓN PARA PYQT5 (Windows 10 LTSC)
echo ===================================================
echo.

echo [1] Verificando si se usa PyQt5.uic...
findstr /I "from PyQt5 import uic" modules\main_window.py >nul
if %errorlevel% equ 0 (
    echo   ✅ Se encontró importación de PyQt5.uic
    echo   📦 Verificando pyqt5-tools...
    pip show pyqt5-tools >nul 2>&1
    if %errorlevel% neq 0 (
        echo   📦 Instalando pyqt5-tools...
        pip install pyqt5-tools --quiet
    )
    echo   ✅ pyqt5-tools instalado/verificado
) else (
    echo   ⚠ No se encontró PyQt5.uic, verificando PyQt5...
    findstr /I "from PyQt5" modules\main_window.py >nul
    if %errorlevel% equ 0 (
        echo   ✅ Se encontró importación de PyQt5
    )
)

echo [2] Limpiando compilaciones anteriores...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist GestorInventario_Completo_v2.0 rmdir /s /q GestorInventario_Completo_v2.0
if exist GestorInventario.spec del GestorInventario.spec

echo [3] Ejecutando PyInstaller con PYQT5...
echo    ⏳ Esto tomará varios minutos...

pyinstaller ^
--name=GestorInventario ^
--onefile ^
--windowed ^
--clean ^
--noconfirm ^
--add-data="modules;modules" ^
--add-data="utils;utils" ^
--add-data="styles.qss;." ^
--add-data="database.py;." ^
--add-data="config.py;." ^
--hidden-import=PyQt5 ^
--hidden-import=PyQt5.QtCore ^
--hidden-import=PyQt5.QtGui ^
--hidden-import=PyQt5.QtWidgets ^
--hidden-import=PyQt5.QtPrintSupport ^
--hidden-import=PyQt5.QtSvg ^
--hidden-import=PyQt5.QtNetwork ^
--hidden-import=PyQt5.uic ^
--hidden-import=sqlite3 ^
--hidden-import=config ^
--hidden-import=database ^
--hidden-import=modules.main_window ^
--hidden-import=modules.catalogo ^
--hidden-import=modules.catalogo_ui ^
--hidden-import=modules.compras ^
--hidden-import=modules.compras_ui ^
--hidden-import=modules.excedentes ^
--hidden-import=modules.excedentes_ui ^
--hidden-import=modules.inventario ^
--hidden-import=modules.inventario_ui ^
--hidden-import=modules.pedidos_chef ^
--hidden-import=modules.pedidos_chef_ui ^
--hidden-import=modules.produccion ^
--hidden-import=modules.produccion_ui ^
--hidden-import=modules.ventas ^
--hidden-import=modules.ventas_ui ^
--hidden-import=modules.historial ^
--hidden-import=modules.historial_ui ^
--icon="icon.ico" ^
main_app.py

if errorlevel 1 (
    echo ❌ Error en la compilación
    echo.
    echo 🔧 Intenta compilar sin --onefile primero:
    echo    pyinstaller --windowed --add-data "modules;modules" main_app.py
    pause
    exit /b 1
)

echo ✅ Compilación exitosa

echo [4] Creando paquete de distribución PYQT5...
set "PAQUETE_DIR=GestorInventario_Completo_PyQt5"
if exist "%PAQUETE_DIR%" rmdir /s /q "%PAQUETE_DIR%"
mkdir "%PAQUETE_DIR%"

copy "dist\GestorInventario.exe" "%PAQUETE_DIR%\"
copy "styles.qss" "%PAQUETE_DIR%\" 2>nul
copy "database.py" "%PAQUETE_DIR%\" 2>nul
copy "config.py" "%PAQUETE_DIR%\" 2>nul

mkdir "%PAQUETE_DIR%\data" 2>nul

if exist "data\inventario.db" (
    copy "data\inventario.db" "%PAQUETE_DIR%\data\" 2>nul
)

(
echo GESTOR DE INVENTARIO - PYQT5 VERSION
echo =====================================
echo.
echo Esta versión usa PyQt5 para compatibilidad con Windows 10 LTSC.
echo.
echo Para usar la aplicación:
echo 1. Mantén todos los archivos en la misma carpeta
echo 2. Ejecuta "GestorInventario.exe"
echo 3. La aplicación creará automáticamente:
echo    - Carpeta "data" si no existe
echo    - Base de datos con todas las tablas
echo.
echo Si hay errores, verifica:
echo 1. Archivo app_log.txt (registro de la aplicación)
echo 2. Archivo error_*.txt (errores específicos)
echo.
echo Compatibilidad: Windows 10 LTSC, Windows 11, Windows 10
echo.
) > "%PAQUETE_DIR%\LEAME.txt"

echo.
echo ===================================================
echo ✅ ¡COMPILACIÓN PYQT5 COMPLETADA!
echo ===================================================
echo.
echo 📁 Carpeta final: %PAQUETE_DIR%
echo 📄 Ejecutable: GestorInventario.exe
echo 📝 Versión: PyQt5 (compatible con Windows 10 LTSC)
echo 🖥️  Compatible con: Windows 10 LTSC, Windows 11, Windows 10
echo.
echo 🚀 Para probar:
echo    Ejecuta "%PAQUETE_DIR%\GestorInventario.exe"
echo.
pause