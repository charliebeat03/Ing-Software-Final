@echo off
chcp 65001 >nul
echo ========================================
echo  INSTALADOR GESTOR DE INVENTARIO
echo ========================================
echo.
echo Archivo principal: main_app.py
echo Archivo de estilos: styles.qss
echo.

REM Verificar que existe main_app.py
if not exist "main_app.py" (
    echo ERROR: No se encuentra main_app.py
    echo    Asegurate de que el archivo principal este en esta carpeta
    pause
    exit /b 1
)

echo [1] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo Error creando entorno virtual
    echo    ¿Tienes Python instalado?
    pause
    exit /b 1
)

echo [2] Activando entorno virtual...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error activando entorno virtual
    pause
    exit /b 1
)

echo [3] Actualizando pip...
pip install --upgrade pip
if errorlevel 1 (
    echo Error actualizando pip
    pause
    exit /b 1
)

echo [4] Instalando dependencias...
echo PyQt6>=6.5.0 > requirements.txt
echo pyinstaller>=5.0.0 >> requirements.txt
echo pillow>=9.0.0 >> requirements.txt

pip install -r requirements.txt
if errorlevel 1 (
    echo Error instalando dependencias
    pause
    exit /b 1
)

echo [5] Verificando estructura de archivos...
if exist "styles.qss" (
    echo styles.qss encontrado
) else (
    echo Advertencia: No se encontro styles.qss
    echo    Creando archivo de estilos vacio...
    echo /* Estilos vacios - personaliza segun necesites */ > styles.qss
)

if exist "ui\" (
    echo Carpeta ui/ encontrada
) else (
    echo Carpeta ui/ no encontrada (puede ser normal)
)

if exist "data\" (
    echo Carpeta data/ encontrada
) else (
    echo Carpeta data/ no encontrada (puede ser normal)
)

echo.
echo [6] Compilando aplicacion...
python build_exe.py

echo.
echo ========================================
if exist "dist\GestorInventario.exe" (
    echo COMPILACION EXITOSA!
    echo Ejecutable: dist\GestorInventario.exe
    echo.
    echo Prueba el ejecutable con: dist\GestorInventario.exe
) else (
    echo COMPILACION FALLIDA
    echo.
    echo Posibles soluciones:
    echo   1. Verifica que main_app.py no tenga errores
    echo   2. Asegurate de tener todos los modulos necesarios
    echo   3. Prueba compilar manualmente con el comando:
    echo      pyinstaller --onefile --windowed main_app.py
)

pause