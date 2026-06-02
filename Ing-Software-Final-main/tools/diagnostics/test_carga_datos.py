"""
TESTER ESPECÍFICO - DIAGNÓSTICO DE CARGA DE DATOS
Propósito: Identificar por qué falla la carga de ingredientes/productos en módulos específicos
Fecha: 2024-01-15
"""

import os
import sys
import sqlite3
import traceback
import inspect
from pathlib import Path
from typing import List, Dict, Any

# Configurar paths
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "modules"))
sys.path.insert(0, str(BASE_DIR / "utils"))

class DiagnosticadorCarga:
    """Diagnóstico específico de problemas de carga en módulos"""
    
    def __init__(self):
        self.resultados = []
        self.problemas_detallados = []
        self.db_path = BASE_DIR / "data" / "inventario.db"
    
    def log(self, mensaje: str, tipo: str = "INFO"):
        """Registra un mensaje"""
        prefijos = {
            "INFO": "[INFO]",
            "ERROR": "[ERROR]",
            "WARN": "[ADVERTENCIA]",
            "SUCCESS": "[ÉXITO]"
        }
        print(f"{prefijos.get(tipo, '[INFO]')} {mensaje}")
    
    # ==================== DIAGNÓSTICO DE BASE DE DATOS ====================
    
    def verificar_tablas_datos(self):
        """Verifica tablas y datos específicos"""
        self.log("Verificando estructura de tablas y datos...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 1. Verificar tablas críticas
            tablas_criticas = [
                'ingredientes',
                'productos', 
                'inventario_ingredientes',
                'inventario_productos',
                'unidades_medida'
            ]
            
            for tabla in tablas_criticas:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tabla}'")
                existe = cursor.fetchone()
                if existe:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
                    count = cursor.fetchone()[0]
                    self.log(f"Tabla '{tabla}': {count} registros", "SUCCESS" if count > 0 else "WARN")
                else:
                    self.log(f"Tabla '{tabla}': NO EXISTE", "ERROR")
            
            # 2. Verificar estructura de tabla ingredientes
            self.log("\nAnalizando estructura de tabla 'ingredientes':")
            cursor.execute("PRAGMA table_info(ingredientes)")
            columnas = cursor.fetchall()
            for col in columnas:
                self.log(f"  Columna {col[1]}: Tipo {col[2]}, Nullable: {col[3]==0}")
            
            # 3. Verificar datos de ingredientes
            self.log("\nPrimeros 5 ingredientes:")
            cursor.execute("SELECT id, nombre, unidad_medida, cantidad_minima FROM ingredientes LIMIT 5")
            ingredientes = cursor.fetchall()
            for ing in ingredientes:
                self.log(f"  ID: {ing[0]}, Nombre: {ing[1]}, Unidad: {ing[2]}, Mín: {ing[3]}")
            
            # 4. Verificar unidades de medida
            self.log("\nUnidades de medida disponibles:")
            cursor.execute("SELECT id, nombre, abreviatura FROM unidades_medida")
            unidades = cursor.fetchall()
            for unidad in unidades:
                self.log(f"  ID: {unidad[0]}, Nombre: {unidad[1]}, Abrev: {unidad[2]}")
            
            conn.close()
            
        except Exception as e:
            self.log(f"Error verificando base de datos: {e}", "ERROR")
    
    # ==================== DIAGNÓSTICO DE MÓDULOS ====================
    
    def analizar_modulo(self, nombre_modulo: str):
        """Analiza un módulo específico para encontrar funciones de carga"""
        self.log(f"\n{'='*60}")
        self.log(f"ANALIZANDO MÓDULO: {nombre_modulo}")
        self.log(f"{'='*60}")
        
        try:
            module_path = BASE_DIR / "modules" / f"{nombre_modulo}.py"
            
            if not module_path.exists():
                self.log(f"Archivo no encontrado: {module_path}", "ERROR")
                return
            
            # Leer el archivo completo
            with open(module_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            self.log(f"Tamaño del archivo: {len(contenido)} caracteres")
            
            # Buscar funciones relacionadas con carga
            funciones_carga = []
            lineas = contenido.split('\n')
            
            for i, linea in enumerate(lineas):
                linea_lower = linea.lower()
                if any(keyword in linea_lower for keyword in ['cargar', 'obtener', 'get_', 'load_', 'ingrediente', 'producto']):
                    if 'def ' in linea_lower:
                        funciones_carga.append((i+1, linea.strip()))
            
            if funciones_carga:
                self.log("Funciones de carga encontradas:", "INFO")
                for num_linea, funcion in funciones_carga:
                    self.log(f"  Línea {num_linea}: {funcion}")
            else:
                self.log("No se encontraron funciones de carga obvias", "WARN")
            
            # Buscar consultas SQL
            self.log("\nBuscando consultas SQL...")
            consultas_sql = []
            for i, linea in enumerate(lineas):
                if any(sql_keyword in linea.upper() for sql_keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                    # Encontrar consulta completa (puede ser multi-línea)
                    consulta = linea.strip()
                    j = i + 1
                    while j < len(lineas) and not lineas[j].strip().startswith('def ') and lineas[j].strip() != '':
                        consulta += ' ' + lineas[j].strip()
                        j += 1
                    consultas_sql.append((i+1, consulta))
            
            if consultas_sql:
                self.log("Consultas SQL encontradas:", "INFO")
                for num_linea, consulta in consultas_sql[:10]:  # Mostrar solo las primeras 10
                    self.log(f"  Línea {num_linea}: {consulta[:100]}...")
            
            # Buscar posibles errores comunes
            self.log("\nBuscando posibles problemas...")
            problemas = []
            
            for i, linea in enumerate(lineas):
                # 1. Conexiones no cerradas
                if 'sqlite3.connect' in linea and 'close()' not in '\n'.join(lineas[i:i+10]):
                    problemas.append(f"Línea {i+1}: Posible conexión no cerrada")
                
                # 2. Consultas sin manejo de errores
                if 'cursor.execute' in linea and 'try:' not in '\n'.join(lineas[max(0,i-5):i]):
                    problemas.append(f"Línea {i+1}: Consulta sin manejo de errores")
                
                # 3. Referencias a tablas/columnas que podrían no existir
                if any(tabla in linea for tabla in ['ingrediente', 'producto']):
                    problemas.append(f"Línea {i+1}: Referencia a tabla/columna")
            
            if problemas:
                self.log("Problemas potenciales encontrados:", "WARN")
                for problema in problemas[:10]:
                    self.log(f"  {problema}")
            
            # Intentar importar el módulo
            self.log("\nIntentando importar módulo...")
            try:
                spec = __import__(f'modules.{nombre_modulo}', fromlist=['*'])
                
                # Listar todas las funciones/clases
                elementos = [attr for attr in dir(spec) if not attr.startswith('_')]
                self.log(f"Elementos públicos: {len(elementos)}")
                
                # Mostrar funciones relacionadas con carga
                funciones_carga_import = [f for f in elementos if any(keyword in f.lower() 
                                                                     for keyword in ['cargar', 'obtener', 'get', 'load', 'ingrediente', 'producto'])]
                if funciones_carga_import:
                    self.log("Funciones de carga (importadas):", "INFO")
                    for func in funciones_carga_import:
                        self.log(f"  {func}")
                
            except ImportError as e:
                self.log(f"Error importando módulo: {e}", "ERROR")
            
        except Exception as e:
            self.log(f"Error analizando módulo: {e}", "ERROR")
            traceback.print_exc()
    
    def probar_carga_ingredientes(self):
        """Prueba específica de carga de ingredientes"""
        self.log(f"\n{'='*60}")
        self.log("PRUEBA ESPECÍFICA: CARGA DE INGREDIENTES")
        self.log(f"{'='*60}")
        
        # Probar desde diferentes módulos
        modulos_a_probar = ['compras', 'ventas', 'produccion', 'pedidos_chef', 'catalogos']
        
        for modulo in modulos_a_probar:
            self.log(f"\nProbando carga desde módulo: {modulo}")
            
            try:
                # Intentar importar el módulo
                module = __import__(f'modules.{modulo}', fromlist=['*'])
                
                # Buscar funciones que carguen ingredientes
                funciones = [attr for attr in dir(module) 
                           if not attr.startswith('_') and 
                           any(keyword in attr.lower() 
                               for keyword in ['ingrediente', 'ingredients', 'get_ing', 'load_ing'])]
                
                for funcion_nombre in funciones:
                    self.log(f"  Función encontrada: {funcion_nombre}")
                    
                    try:
                        funcion = getattr(module, funcion_nombre)
                        
                        # Verificar si es llamable
                        if callable(funcion):
                            # Intentar ejecutar (algunas pueden necesitar parámetros)
                            try:
                                resultado = funcion()
                                self.log(f"    Resultado: {type(resultado)}", "SUCCESS")
                                
                                # Si es una lista/tupla, mostrar cantidad
                                if isinstance(resultado, (list, tuple)):
                                    self.log(f"    Elementos: {len(resultado)}")
                                    if resultado:
                                        self.log(f"    Primer elemento: {resultado[0]}")
                                
                            except TypeError as e:
                                # Puede necesitar parámetros
                                self.log(f"    Necesita parámetros: {e}", "WARN")
                                # Intentar ver la firma
                                try:
                                    signature = inspect.signature(funcion)
                                    self.log(f"    Firma: {signature}")
                                except:
                                    pass
                            
                            except Exception as e:
                                self.log(f"    Error ejecutando: {e}", "ERROR")
                    
                    except Exception as e:
                        self.log(f"    Error accediendo a función: {e}", "ERROR")
                
            except ImportError as e:
                self.log(f"  No se pudo importar módulo: {e}", "ERROR")
    
    def probar_consultas_directas(self):
        """Prueba consultas SQL directamente"""
        self.log(f"\n{'='*60}")
        self.log("PRUEBA DIRECTA DE CONSULTAS SQL")
        self.log(f"{'='*60}")
        
        consultas_comunes = [
            ("SELECT * FROM ingredientes", "Todos los ingredientes"),
            ("SELECT id, nombre, unidad_medida FROM ingredientes WHERE activo = 1", "Ingredientes activos"),
            ("SELECT * FROM productos", "Todos los productos"),
            ("SELECT id, nombre, precio FROM productos WHERE activo = 1", "Productos activos"),
            ("SELECT i.*, u.nombre as unidad_nombre FROM ingredientes i LEFT JOIN unidades_medida u ON i.unidad_medida = u.id", "Ingredientes con unidad"),
            ("SELECT p.*, COUNT(pi.ingrediente_id) as num_ingredientes FROM productos p LEFT JOIN producto_ingredientes pi ON p.id = pi.producto_id GROUP BY p.id", "Productos con conteo ingredientes")
        ]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for consulta_sql, descripcion in consultas_comunes:
                self.log(f"\nConsulta: {descripcion}")
                self.log(f"SQL: {consulta_sql[:80]}...")
                
                try:
                    cursor.execute(consulta_sql)
                    resultados = cursor.fetchall()
                    
                    if resultados:
                        self.log(f"  Resultados: {len(resultados)} filas", "SUCCESS")
                        
                        # Mostrar columnas
                        descripcion_columnas = [desc[0] for desc in cursor.description]
                        self.log(f"  Columnas: {', '.join(descripcion_columnas)}")
                        
                        # Mostrar primeros 3 resultados
                        for i, fila in enumerate(resultados[:3]):
                            self.log(f"  Fila {i+1}: {fila}")
                        
                        if len(resultados) > 3:
                            self.log(f"  ... y {len(resultados)-3} filas más")
                    else:
                        self.log("  Resultados: 0 filas", "WARN")
                        
                except sqlite3.Error as e:
                    self.log(f"  Error SQL: {e}", "ERROR")
                    
                    # Verificar si la tabla/columna existe
                    if "no such table" in str(e):
                        self.log("  ❌ La tabla no existe", "ERROR")
                    elif "no such column" in str(e):
                        self.log("  ❌ La columna no existe", "ERROR")
            
            conn.close()
            
        except Exception as e:
            self.log(f"Error general en consultas: {e}", "ERROR")
    
    def analizar_errores_comunes(self):
        """Analiza errores comunes en la aplicación"""
        self.log(f"\n{'='*60}")
        self.log("ANÁLISIS DE ERRORES COMUNES")
        self.log(f"{'='*60}")
        
        problemas_comunes = [
            {
                "descripcion": "Conexiones a BD no cerradas",
                "sintomas": ["Memory leak", "Lentitud progresiva", "Error 'database is locked'"],
                "solucion": "Usar context managers (with statement) o asegurar conn.close()"
            },
            {
                "descripcion": "Consultas sin manejo de errores",
                "sintomas": ["La aplicación crashea", "Errores no informativos", "Datos inconsistentes"],
                "solucion": "Usar try-except alrededor de todas las consultas SQL"
            },
            {
                "descripcion": "Joins incorrectos o tablas inexistentes",
                "sintomas": ["'no such table'", "'no such column'", "Datos faltantes"],
                "solucion": "Verificar nombres de tablas y columnas en consultas"
            },
            {
                "descripcion": "Falta de índices en tablas grandes",
                "sintomas": ["Consultas lentas", "Interfaz se congela", "Alta CPU"],
                "solucion": "Agregar índices a columnas usadas en WHERE y JOIN"
            },
            {
                "descripcion": "Problemas de concurrencia",
                "sintomas": ["Errores aleatorios", "Datos sobrescritos", "Transacciones fallidas"],
                "solucion": "Usar transacciones SQLite y manejo adecuado de locks"
            }
        ]
        
        for problema in problemas_comunes:
            self.log(f"\nProblema: {problema['descripcion']}")
            self.log(f"Síntomas: {', '.join(problema['sintomas'])}")
            self.log(f"Solución: {problema['solucion']}")
    
    def generar_reporte_diagnostico(self):
        """Genera un reporte completo de diagnóstico"""
        self.log(f"\n{'='*60}")
        self.log("REPORTE DE DIAGNÓSTICO COMPLETO")
        self.log(f"{'='*60}")
        
        # Ejecutar todas las pruebas
        self.verificar_tablas_datos()
        self.analizar_modulo('compras')
        self.analizar_modulo('ventas')
        self.analizar_modulo('produccion')
        self.analizar_modulo('pedidos_chef')
        self.analizar_modulo('catalogos')
        self.probar_carga_ingredientes()
        self.probar_consultas_directas()
        self.analizar_errores_comunes()
        
        # Recomendaciones
        self.log(f"\n{'='*60}")
        self.log("RECOMENDACIONES PRIORIZADAS")
        self.log(f"{'='*60}")
        
        recomendaciones = [
            "1. VERIFICAR que las tablas 'ingredientes' y 'productos' existan y tengan datos",
            "2. REVISAR las consultas SQL en cada módulo problemático",
            "3. AÑADIR manejo de errores (try-except) en todas las consultas a BD",
            "4. USAR logging para registrar errores en lugar de solo mostrar en consola",
            "5. IMPLEMENTAR funciones de 'carga segura' que verifiquen datos antes de usar",
            "6. CREAR una función centralizada para cargar ingredientes/productos",
            "7. VALIDAR que las conexiones a BD se cierren correctamente",
            "8. PROBAR cada módulo individualmente con datos de prueba"
        ]
        
        for rec in recomendaciones:
            self.log(rec)
    
    def ejecutar_diagnostico_completo(self):
        """Ejecuta el diagnóstico completo"""
        print("\n" + "="*80)
        print("DIAGNÓSTICO DE PROBLEMAS DE CARGA - SISTEMA DE CONTROL DE PRODUCCIÓN")
        print("="*80)
        
        self.generar_reporte_diagnostico()
        
        print("\n" + "="*80)
        print("DIAGNÓSTICO COMPLETADO")
        print("="*80)
        print("\nPara continuar con las correcciones, usa el siguiente prompt:")

def main():
    """Función principal"""
    diagnosticador = DiagnosticadorCarga()
    diagnosticador.ejecutar_diagnostico_completo()

if __name__ == "__main__":
    main()