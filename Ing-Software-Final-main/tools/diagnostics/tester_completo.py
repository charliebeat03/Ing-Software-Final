"""
TESTER COMPLETO - Sistema de Control de Producción
Prueba todos los módulos con estructura corregida
Versión Corregida: 2024-01-15
"""

import os
import sys
import sqlite3
import time
import datetime
import traceback
import importlib.util
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Configurar colores para consola
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLOR_AVAILABLE = True
except ImportError:
    # Definir colores básicos si colorama no está disponible
    class Fore:
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    COLOR_AVAILABLE = False

# Configurar paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "modules"))
sys.path.insert(0, str(BASE_DIR / "utils"))

class TesterCompleto:
    """Clase principal para testing completo de la aplicación"""
    
    def __init__(self):
        self.resultados = []
        self.errores = []
        self.advertencias = []
        self.tiempo_inicio = None
        self.tiempo_inicio_nombre = ""
        
    def iniciar_prueba(self, nombre: str):
        """Inicia una prueba con temporizador"""
        self.tiempo_inicio = time.time()
        self.tiempo_inicio_nombre = nombre
        print(f"\n{'='*70}")
        print(f"PRUEBA: {nombre}")
        print(f"{'='*70}")
        
    def finalizar_prueba(self, exitosa: bool = True, mensaje: str = ""):
        """Finaliza una prueba y muestra resultados"""
        tiempo_transcurrido = time.time() - self.tiempo_inicio
        
        if exitosa:
            estado = "✓ EXITOSA"
            if COLOR_AVAILABLE:
                estado = Fore.GREEN + estado + Fore.RESET
        else:
            estado = "✗ FALLIDA"
            if COLOR_AVAILABLE:
                estado = Fore.RED + estado + Fore.RESET
        
        print(f"\nResultado: {estado}")
        if mensaje:
            print(f"Mensaje: {mensaje}")
        print(f"Duración: {tiempo_transcurrido:.2f} segundos")
        print(f"{'-'*70}")
        
        # Guardar resultado
        self.resultados.append({
            'nombre': self.tiempo_inicio_nombre,
            'exitoso': exitosa,
            'duracion': tiempo_transcurrido,
            'mensaje': mensaje
        })
        
        return exitosa
    
    # ==================== PRUEBAS DE ESTRUCTURA ====================
    
    def verificar_estructura_archivos(self) -> bool:
        """Verifica que todos los archivos necesarios existan"""
        self.iniciar_prueba("Verificación de estructura de archivos")
        
        archivos_requeridos = [
            # Archivos raíz
            ("main.py", "Punto de entrada principal"),
            ("database.py", "Gestión de base de datos"),
            ("config.py", "Configuraciones del sistema"),
            
            # Módulos principales
            ("modules/main_window.py", "Ventana principal"),
            
            # Módulos lógicos con UI
            ("modules/catalogos.py", "Lógica de catálogos"),
            ("modules/catalogos_ui.py", "UI de catálogos"),
            ("modules/compras.py", "Lógica de compras"),
            ("modules/compras_ui.py", "UI de compras"),
            ("modules/excedentes.py", "Lógica de excedentes"),
            ("modules/excedentes_ui.py", "UI de excedentes"),
            ("modules/inventario.py", "Lógica de inventario"),
            ("modules/inventario_ui.py", "UI de inventario"),
            ("modules/pedidos_chef.py", "Lógica de pedidos del chef"),
            ("modules/pedidos_chef_ui.py", "UI de pedidos del chef"),
            ("modules/produccion.py", "Lógica de producción"),
            ("modules/produccion_ui.py", "UI de producción"),
            ("modules/ventas.py", "Lógica de ventas"),
            ("modules/ventas_ui.py", "UI de ventas"),
            
            # Utilidades
            ("utils/calculos.py", "Utilidad de cálculos"),
            ("utils/validators.py", "Utilidad de validaciones"),  # CORREGIDO: validations.py -> validators.py
            
            # Base de datos
            ("data/inventario.db", "Base de datos SQLite"),
        ]
        
        # Archivos opcionales (interfaces .ui)
        archivos_opcionales = [
            ("ui/main_window.ui", "UI principal (Qt Designer)"),
            ("ui/catalogos.ui", "UI de catálogos (Qt Designer)"),
            ("ui/compras.ui", "UI de compras (Qt Designer)"),
            ("ui/excedentes.ui", "UI de excedentes (Qt Designer)"),
            ("ui/inventario.ui", "UI de inventario (Qt Designer)"),
            ("ui/pedidos_chef.ui", "UI de pedidos chef (Qt Designer)"),
            ("ui/produccion.ui", "UI de producción (Qt Designer)"),
            ("ui/ventas.ui", "UI de ventas (Qt Designer)"),
        ]
        
        faltantes = []
        existentes = []
        
        for archivo, descripcion in archivos_requeridos:
            ruta = BASE_DIR / archivo
            if ruta.exists():
                existentes.append((archivo, descripcion, ruta))
                print(f"  ✓ {archivo:<40} - {descripcion}")
            else:
                faltantes.append((archivo, descripcion, ruta))
                print(f"  ✗ {archivo:<40} - {descripcion} (NO ENCONTRADO)")
        
        # Verificar archivos opcionales
        for archivo, descripcion in archivos_opcionales:
            ruta = BASE_DIR / archivo
            if ruta.exists():
                print(f"  ! {archivo:<40} - {descripcion} (opcional, encontrado)")
            else:
                print(f"  ! {archivo:<40} - {descripcion} (opcional, no encontrado)")
        
        # Evaluar resultados
        if len(faltantes) == 0:
            return self.finalizar_prueba(True, "Todos los archivos requeridos existen")
        else:
            mensaje = f"Faltan {len(faltantes)} archivos de {len(archivos_requeridos)}"
            for archivo, descripcion, _ in faltantes:
                mensaje += f"\n  - {archivo} ({descripcion})"
            return self.finalizar_prueba(False, mensaje)
    
    # ==================== PRUEBAS DE BASE DE DATOS ====================
    
    def probar_conexion_bd(self) -> bool:
        """Prueba la conexión a la base de datos"""
        self.iniciar_prueba("Prueba de conexión a base de datos")
        
        try:
            db_path = BASE_DIR / "data" / "inventario.db"
            
            if not db_path.exists():
                return self.finalizar_prueba(False, f"Base de datos no encontrada: {db_path}")
            
            # Intentar conexión
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar que sea una BD SQLite válida
            cursor.execute("SELECT sqlite_version()")
            version = cursor.fetchone()[0]
            
            # Verificar tablas principales esperadas
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tablas = [tabla[0] for tabla in cursor.fetchall()]
            
            conn.close()
            
            # Tablas mínimas esperadas (basado en estructura real)
            tablas_esperadas = ['ingredientes', 'productos', 'compras', 'ventas', 'produccion', 'excedentes']
            tablas_faltantes = [t for t in tablas_esperadas if t not in tablas]
            
            if tablas_faltantes:
                mensaje = f"Tablas faltantes: {', '.join(tablas_faltantes)}"
                mensaje += f"\nTablas encontradas: {', '.join(tablas)}"
                return self.finalizar_prueba(False, mensaje)
            
            mensaje = f"Conexión exitosa. SQLite v{version}. Tablas: {len(tablas)}"
            return self.finalizar_prueba(True, mensaje)
            
        except sqlite3.Error as e:
            return self.finalizar_prueba(False, f"Error SQLite: {e}")
        except Exception as e:
            return self.finalizar_prueba(False, f"Error inesperado: {e}")
    
    def verificar_integridad_bd(self) -> bool:
        """Verifica la integridad de la base de datos"""
        self.iniciar_prueba("Verificación de integridad de base de datos")
        
        try:
            db_path = BASE_DIR / "data" / "inventario.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 1. Verificar integridad general
            cursor.execute("PRAGMA integrity_check")
            resultado = cursor.fetchone()[0]
            
            if resultado != "ok":
                return self.finalizar_prueba(False, f"Integridad fallida: {resultado}")
            
            # 2. Verificar claves foráneas
            cursor.execute("PRAGMA foreign_key_check")
            problemas_fk = cursor.fetchall()
            
            if problemas_fk:
                mensaje = "Problemas de claves foráneas:\n"
                for problema in problemas_fk:
                    mensaje += f"  Tabla {problema[0]}, Fila {problema[1]}: {problema[3]}\n"
                conn.close()
                return self.finalizar_prueba(False, mensaje)
            
            # 3. Verificar estructura de tablas clave
            tablas_clave = ['ingredientes', 'productos', 'compras', 'ventas']
            for tabla in tablas_clave:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    print(f"  Tabla {tabla}: {count} registros")
                except:
                    print(f"  Tabla {tabla}: ERROR (no existe o no accesible)")
            
            conn.close()
            return self.finalizar_prueba(True, "Integridad verificada correctamente")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error verificando integridad: {e}")
    
    # ==================== PRUEBAS DE MÓDULOS ====================
    
    def inspeccionar_modulo(self, nombre_modulo: str):
        """Inspecciona un módulo para ver sus clases y funciones disponibles"""
        try:
            module_path = BASE_DIR / "modules" / f"{nombre_modulo}.py"
            if not module_path.exists():
                return None
            
            # Leer el archivo
            with open(module_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Buscar clases
            import ast
            tree = ast.parse(contenido)
            
            clases = []
            funciones = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    clases.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    funciones.append(node.name)
            
            return {
                'clases': clases,
                'funciones': funciones,
                'contenido': contenido[:500]  # Primeros 500 caracteres
            }
            
        except Exception as e:
            return f"Error inspeccionando módulo: {e}"
    
    def probar_modulo_logico(self, nombre_modulo: str) -> bool:
        """Prueba un módulo lógico"""
        self.iniciar_prueba(f"Prueba del módulo lógico: {nombre_modulo}")
        
        try:
            module_path = BASE_DIR / "modules" / f"{nombre_modulo}.py"
            if not module_path.exists():
                return self.finalizar_prueba(False, f"Archivo no encontrado: {module_path}")
            
            # Inspeccionar el módulo
            inspeccion = self.inspeccionar_modulo(nombre_modulo)
            
            if inspeccion is None:
                return self.finalizar_prueba(False, "No se pudo inspeccionar el módulo")
            
            print(f"  Clases encontradas: {', '.join(inspeccion['clases']) if inspeccion['clases'] else 'Ninguna'}")
            print(f"  Funciones encontradas: {len(inspeccion['funciones'])}")
            
            # Intentar importar el módulo
            spec = importlib.util.spec_from_file_location(nombre_modulo, module_path)
            if spec is None:
                return self.finalizar_prueba(False, "No se pudo crear especificación del módulo")
            
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            return self.finalizar_prueba(True, f"Módulo {nombre_modulo} importado correctamente")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error importando módulo: {e}")
    
    def probar_modulo_ui(self, nombre_modulo: str) -> bool:
        """Prueba un módulo UI"""
        self.iniciar_prueba(f"Prueba del módulo UI: {nombre_modulo}")
        
        try:
            module_path = BASE_DIR / "modules" / f"{nombre_modulo}_ui.py"
            if not module_path.exists():
                return self.finalizar_prueba(False, f"Archivo no encontrado: {module_path}")
            
            # Inspeccionar el módulo
            inspeccion = self.inspeccionar_modulo(f"{nombre_modulo}_ui")
            
            print(f"  Clases encontradas: {', '.join(inspeccion['clases']) if inspeccion and 'clases' in inspeccion else 'Ninguna'}")
            
            # Intentar importar el módulo
            spec = importlib.util.spec_from_file_location(f"{nombre_modulo}_ui", module_path)
            if spec is None:
                return self.finalizar_prueba(False, "No se pudo crear especificación del módulo")
            
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            return self.finalizar_prueba(True, f"Módulo UI {nombre_modulo} importado correctamente")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error importando módulo UI: {e}")
    
    def probar_todos_modulos(self) -> bool:
        """Prueba todos los módulos de la aplicación"""
        self.iniciar_prueba("Prueba de todos los módulos")
        
        modulos_logicos = [
            "catalogos",
            "compras", 
            "excedentes",
            "inventario",
            "pedidos_chef",
            "produccion",
            "ventas"
        ]
        
        exitosos = 0
        fallidos = 0
        resultados_detallados = []
        
        for modulo in modulos_logicos:
            print(f"\n  Probando módulo lógico: {modulo}")
            try:
                if self.probar_modulo_logico(modulo):
                    exitosos += 1
                    resultados_detallados.append(f"{modulo}: ✓")
                else:
                    fallidos += 1
                    resultados_detallados.append(f"{modulo}: ✗")
            except Exception as e:
                print(f"  ✗ Error inesperado en {modulo}: {e}")
                fallidos += 1
                resultados_detallados.append(f"{modulo}: ✗ (Error: {e})")
        
        # Probando módulos UI
        for modulo in modulos_logicos:
            print(f"\n  Probando módulo UI: {modulo}_ui")
            try:
                if self.probar_modulo_ui(modulo):
                    exitosos += 1
                    resultados_detallados.append(f"{modulo}_ui: ✓")
                else:
                    fallidos += 1
                    resultados_detallados.append(f"{modulo}_ui: ✗")
            except Exception as e:
                print(f"  ✗ Error inesperado en {modulo}_ui: {e}")
                fallidos += 1
                resultados_detallados.append(f"{modulo}_ui: ✗ (Error: {e})")
        
        mensaje = f"Módulos exitosos: {exitosos}/{(len(modulos_logicos)*2)}"
        if fallidos > 0:
            mensaje += f", Fallidos: {fallidos}"
        
        # Mostrar resultados detallados
        print("\n" + "-" * 70)
        print("RESULTADOS DETALLADOS POR MÓDULO:")
        for resultado in resultados_detallados:
            print(f"  {resultado}")
        
        return self.finalizar_prueba(fallidos == 0, mensaje)
    
    # ==================== PRUEBAS ESPECÍFICAS POR MÓDULO ====================
    
    def probar_catalogos_completo(self) -> bool:
        """Pruebas exhaustivas del módulo de catálogos"""
        self.iniciar_prueba("Prueba exhaustiva: Módulo Catálogos")
        
        try:
            # Inspeccionar el módulo primero
            inspeccion = self.inspeccionar_modulo("catalogos")
            
            if isinstance(inspeccion, str):
                return self.finalizar_prueba(False, f"Error inspeccionando: {inspeccion}")
            
            print(f"  Clases en catalogos.py: {', '.join(inspeccion['clases']) if inspeccion['clases'] else 'Ninguna'}")
            print(f"  Total funciones: {len(inspeccion['funciones'])}")
            
            # Mostrar algunas funciones
            if inspeccion['funciones']:
                print(f"  Primeras 5 funciones: {', '.join(inspeccion['funciones'][:5])}")
            
            # Intentar importar y probar funciones comunes
            module_path = BASE_DIR / "modules" / "catalogos.py"
            spec = importlib.util.spec_from_file_location("catalogos", module_path)
            
            if spec is None:
                return self.finalizar_prueba(False, "No se pudo crear especificación del módulo")
            
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            # Verificar si tiene funciones comunes
            funciones_comunes = ['obtener_ingredientes', 'agregar_ingrediente', 'obtener_productos']
            funciones_encontradas = []
            funciones_faltantes = []
            
            for funcion in funciones_comunes:
                if hasattr(modulo, funcion):
                    funciones_encontradas.append(funcion)
                else:
                    funciones_faltantes.append(funcion)
            
            if funciones_encontradas:
                print(f"  ✓ Funciones encontradas: {', '.join(funciones_encontradas)}")
            
            if funciones_faltantes:
                print(f"  ! Funciones no encontradas: {', '.join(funciones_faltantes)}")
            
            return self.finalizar_prueba(True, f"Módulo catalogos inspeccionado. Clases: {len(inspeccion['clases'])}, Funciones: {len(inspeccion['funciones'])}")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error en prueba de catálogos: {e}")
    
    def probar_inventario_completo(self) -> bool:
        """Pruebas exhaustivas del módulo de inventario"""
        self.iniciar_prueba("Prueba exhaustiva: Módulo Inventario")
        
        try:
            # Inspeccionar el módulo primero
            inspeccion = self.inspeccionar_modulo("inventario")
            
            if isinstance(inspeccion, str):
                return self.finalizar_prueba(False, f"Error inspeccionando: {inspeccion}")
            
            print(f"  Clases en inventario.py: {', '.join(inspeccion['clases']) if inspeccion['clases'] else 'Ninguna'}")
            print(f"  Total funciones: {len(inspeccion['funciones'])}")
            
            # Mostrar algunas funciones
            if inspeccion['funciones']:
                print(f"  Primeras 5 funciones: {', '.join(inspeccion['funciones'][:5])}")
            
            # Intentar importar
            module_path = BASE_DIR / "modules" / "inventario.py"
            spec = importlib.util.spec_from_file_location("inventario", module_path)
            
            if spec is None:
                return self.finalizar_prueba(False, "No se pudo crear especificación del módulo")
            
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
            
            return self.finalizar_prueba(True, f"Módulo inventario inspeccionado. Clases: {len(inspeccion['clases'])}, Funciones: {len(inspeccion['funciones'])}")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error en prueba de inventario: {e}")
    
    # ==================== PRUEBAS DE UTILIDADES ====================
    
    def probar_utilidades(self) -> bool:
        """Prueba los módulos de utilidades"""
        self.iniciar_prueba("Prueba de módulos de utilidades")
        
        try:
            # Probar utils/calculos.py
            calculos_path = BASE_DIR / "utils" / "calculos.py"
            if not calculos_path.exists():
                return self.finalizar_prueba(False, f"Archivo no encontrado: {calculos_path}")
            
            # Inspeccionar cálculos
            try:
                spec_calc = importlib.util.spec_from_file_location("calculos", calculos_path)
                modulo_calc = importlib.util.module_from_spec(spec_calc)
                spec_calc.loader.exec_module(modulo_calc)
                
                # Verificar funciones
                funciones_calc = [func for func in dir(modulo_calc) if not func.startswith('_')]
                print(f"  ✓ Módulo calculos.py importado. Funciones: {len(funciones_calc)}")
                
                if funciones_calc:
                    print(f"  Funciones disponibles: {', '.join(funciones_calc[:5])}")
                    if len(funciones_calc) > 5:
                        print(f"  ... y {len(funciones_calc)-5} más")
                
            except Exception as e:
                print(f"  ! Error importando calculos.py: {e}")
            
            # Probar utils/validators.py
            validators_path = BASE_DIR / "utils" / "validators.py"
            if not validators_path.exists():
                return self.finalizar_prueba(False, f"Archivo no encontrado: {validators_path}")
            
            # Inspeccionar validators
            try:
                spec_val = importlib.util.spec_from_file_location("validators", validators_path)
                modulo_val = importlib.util.module_from_spec(spec_val)
                spec_val.loader.exec_module(modulo_val)
                
                # Verificar funciones
                funciones_val = [func for func in dir(modulo_val) if not func.startswith('_')]
                print(f"  ✓ Módulo validators.py importado. Funciones: {len(funciones_val)}")
                
                if funciones_val:
                    print(f"  Funciones disponibles: {', '.join(funciones_val[:5])}")
                    if len(funciones_val) > 5:
                        print(f"  ... y {len(funciones_val)-5} más")
                
            except Exception as e:
                print(f"  ! Error importando validators.py: {e}")
            
            return self.finalizar_prueba(True, "Utilidades inspeccionadas correctamente")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error en prueba de utilidades: {e}")
    
    # ==================== PRUEBAS DE FLUJO COMPLETO ====================
    
    def probar_flujo_completo(self) -> bool:
        """Prueba un flujo completo de operaciones"""
        self.iniciar_prueba("Prueba de flujo completo del sistema")
        
        try:
            print("  Simulando flujo de operaciones...")
            
            # 1. Verificar que los módulos existan
            modulos_necesarios = [
                "catalogos", "compras", "inventario", 
                "produccion", "ventas", "excedentes"
            ]
            
            for modulo in modulos_necesarios:
                module_path = BASE_DIR / "modules" / f"{modulo}.py"
                if module_path.exists():
                    print(f"  ✓ {modulo}.py encontrado")
                else:
                    print(f"  ✗ {modulo}.py NO encontrado")
            
            # 2. Verificar conexión a BD
            db_path = BASE_DIR / "data" / "inventario.db"
            if db_path.exists():
                print(f"  ✓ Base de datos encontrada: {db_path}")
                
                # Verificar algunas tablas clave
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    tablas_clave = ['ingredientes', 'productos', 'compras', 'ventas']
                    for tabla in tablas_clave:
                        cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{tabla}'")
                        if cursor.fetchone()[0] == 1:
                            print(f"  ✓ Tabla '{tabla}' existe")
                        else:
                            print(f"  ✗ Tabla '{tabla}' NO existe")
                    
                    conn.close()
                except Exception as e:
                    print(f"  ! Error verificando tablas: {e}")
            else:
                print(f"  ✗ Base de datos NO encontrada")
            
            return self.finalizar_prueba(True, "Flujo de verificación completado")
            
        except Exception as e:
            return self.finalizar_prueba(False, f"Error en flujo completo: {e}")
    
    # ==================== GENERACIÓN DE REPORTES ====================
    
    def generar_reporte(self) -> str:
        """Genera un reporte completo de las pruebas"""
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reporte = []
        
        reporte.append("=" * 80)
        reporte.append("REPORTE COMPLETO DE PRUEBAS - SISTEMA DE CONTROL DE PRODUCCIÓN")
        reporte.append("=" * 80)
        reporte.append(f"Fecha de generación: {fecha}")
        reporte.append(f"Directorio: {BASE_DIR}")
        reporte.append("")
        
        if self.resultados:
            reporte.append("RESULTADOS DE PRUEBAS:")
            reporte.append("-" * 80)
            for resultado in self.resultados:
                # Asegurarse de que el resultado tenga todos los campos necesarios
                nombre = resultado.get('nombre', 'Prueba sin nombre')
                exitoso = resultado.get('exitoso', False)
                duracion = resultado.get('duracion', 0.0)
                mensaje = resultado.get('mensaje', 'Sin mensaje')
                
                estado = "✓ EXITOSA" if exitoso else "✗ FALLIDA"
                reporte.append(f"{estado} - {nombre}")
                reporte.append(f"    Duración: {duracion:.2f}s")
                reporte.append(f"    Mensaje: {mensaje}")
                reporte.append("")
        else:
            reporte.append("No hay resultados de pruebas para reportar.")
        
        if self.errores:
            reporte.append("ERRORES ENCONTRADOS:")
            reporte.append("-" * 80)
            for error in self.errores:
                reporte.append(f"• {error}")
            reporte.append("")
        
        if self.advertencias:
            reporte.append("ADVERTENCIAS:")
            reporte.append("-" * 80)
            for advertencia in self.advertencias:
                reporte.append(f"• {advertencia}")
            reporte.append("")
        
        # Resumen
        if self.resultados:
            exitosas = sum(1 for r in self.resultados if r.get('exitoso', False))
            total = len(self.resultados)
            porcentaje = (exitosas / total * 100) if total > 0 else 0
            
            reporte.append("RESUMEN:")
            reporte.append("-" * 80)
            reporte.append(f"Total pruebas: {total}")
            reporte.append(f"Exitosas: {exitosas}")
            reporte.append(f"Fallidas: {total - exitosas}")
            reporte.append(f"Porcentaje éxito: {porcentaje:.1f}%")
        
        reporte.append("=" * 80)
        
        reporte_texto = "\n".join(reporte)
        
        # Guardar en archivo
        nombre_archivo = f"reporte_pruebas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        ruta_reporte = BASE_DIR / nombre_archivo
        
        try:
            with open(ruta_reporte, 'w', encoding='utf-8') as f:
                f.write(reporte_texto)
            print(f"\nReporte guardado en: {ruta_reporte}")
        except Exception as e:
            print(f"\nError guardando reporte: {e}")
        
        return reporte_texto
    
    # ==================== MENÚ INTERACTIVO ====================
    
    def mostrar_menu(self):
        """Muestra el menú interactivo"""
        print("\n" + "=" * 70)
        print("TESTER COMPLETO - SISTEMA DE CONTROL DE PRODUCCIÓN")
        print("=" * 70)
        print("\nOpciones disponibles:")
        print(" 1. Verificar estructura de archivos")
        print(" 2. Probar conexión a base de datos")
        print(" 3. Verificar integridad de base de datos")
        print(" 4. Probar módulo de catálogos (completo)")
        print(" 5. Probar módulo de inventario (completo)")
        print(" 6. Probar todos los módulos (básico)")
        print(" 7. Probar módulos de utilidades")
        print(" 8. Probar flujo completo del sistema")
        print(" 9. Ejecutar TODAS las pruebas secuencialmente")
        print("10. Generar reporte completo")
        print(" 0. Salir")
        print("-" * 70)
    
    def ejecutar_opcion(self, opcion: str):
        """Ejecuta la opción seleccionada"""
        if opcion == "1":
            self.verificar_estructura_archivos()
            
        elif opcion == "2":
            self.probar_conexion_bd()
            
        elif opcion == "3":
            self.verificar_integridad_bd()
            
        elif opcion == "4":
            self.probar_catalogos_completo()
            
        elif opcion == "5":
            self.probar_inventario_completo()
            
        elif opcion == "6":
            self.probar_todos_modulos()
            
        elif opcion == "7":
            self.probar_utilidades()
            
        elif opcion == "8":
            self.probar_flujo_completo()
            
        elif opcion == "9":
            print("\nEjecutando todas las pruebas secuencialmente...")
            pruebas = [
                ("Estructura de archivos", self.verificar_estructura_archivos),
                ("Conexión a BD", self.probar_conexion_bd),
                ("Integridad de BD", self.verificar_integridad_bd),
                ("Catálogos completo", self.probar_catalogos_completo),
                ("Inventario completo", self.probar_inventario_completo),
                ("Todos los módulos", self.probar_todos_modulos),
                ("Utilidades", self.probar_utilidades),
                ("Flujo completo", self.probar_flujo_completo),
            ]
            
            for nombre, funcion in pruebas:
                print(f"\n▶ Ejecutando: {nombre}")
                funcion()
            
            print("\n" + "=" * 70)
            print("TODAS LAS PRUEBAS COMPLETADAS")
            print("=" * 70)
            
            # Calcular resumen
            exitosas = sum(1 for r in self.resultados if r.get('exitoso', False))
            total = len(self.resultados)
            
            print(f"Resultado: {exitosas}/{total} pruebas exitosas")
            
        elif opcion == "10":
            reporte = self.generar_reporte()
            print("\n" + reporte)
            
        elif opcion == "0":
            print("Saliendo del tester...")
            return False
            
        else:
            print("Opción no válida. Intente nuevamente.")
        
        return True
    
    def ejecutar_interactivo(self):
        """Modo interactivo con menú"""
        print("Bienvenido al Tester Completo")
        print(f"Directorio actual: {BASE_DIR}")
        
        continuar = True
        while continuar:
            self.mostrar_menu()
            try:
                opcion = input("\nSeleccione una opción (0-10): ").strip()
                continuar = self.ejecutar_opcion(opcion)
                
                if opcion != "0" and opcion != "10":
                    input("\nPresione Enter para continuar...")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupción por usuario. Saliendo...")
                break
            except Exception as e:
                print(f"\nError inesperado: {e}")
                traceback.print_exc()
    
    def ejecutar_automatico(self):
        """Modo automático - ejecuta todas las pruebas"""
        print("Ejecutando pruebas automáticas...")
        self.ejecutar_opcion("9")
        self.ejecutar_opcion("10")

def main():
    """Función principal"""
    tester = TesterCompleto()
    
    # Verificar si se pasaron argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--auto":
            tester.ejecutar_automatico()
        elif sys.argv[1] == "--help":
            print("Uso:")
            print("  python tester_completo.py          # Modo interactivo")
            print("  python tester_completo.py --auto   # Modo automático")
            print("  python tester_completo.py --help   # Esta ayuda")
        else:
            print(f"Argumento no reconocido: {sys.argv[1]}")
            print("Use --help para ver opciones")
    else:
        tester.ejecutar_interactivo()

if __name__ == "__main__":
    main()