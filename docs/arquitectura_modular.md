# Arquitectura Modular

## Objetivo
Dejar la aplicacion lista para trabajo en equipo sin que el arranque, la base de datos y la navegacion principal dependan de importaciones cruzadas fragiles.

## Entrada principal
- `main_app.py`: arranque de la aplicacion, aplica tema global, muestra login y crea la ventana principal.
- `config.py`: rutas, carpetas de trabajo y constantes de la app.
- `database.py`: singleton de SQLite, migraciones, respaldos diarios y tablas base.

## Nucleo compartido
- `app_core/auth.py`: autenticacion y dialogo de acceso.
- `app_core/context.py`: contexto compartido y contenedor de servicios.
- `app_core/module_registry.py`: registro central de modulos visibles, grupos y dificultad.
- `app_core/theme.py`: estilo visual general.
- `app_core/security.py`: hash y verificacion de contrasenas.

## Shell de interfaz
- `modules/main_window.py`: shell principal, sidebar, menu superior, estado, respaldo manual y carga diferida.
- `modules/dashboard_ui.py`: panel general con metricas, alertas y accesos rapidos.
- `modules/module_loader.py`: crea widgets por registro y les inyecta contexto.
- `modules/module_interface.py`: base ligera para modulos que necesiten ciclo de vida comun.

## Modulos funcionales
- `modules/catalogos.py` + `modules/catalogos_ui.py`
  Gestion de ingredientes, productos y unidades.
- `modules/compras.py` + `modules/compras_ui.py`
  Compras y costos de ingredientes.
- `modules/inventario.py` + `modules/inventario_ui.py`
  Stock real, alertas y resumen operativo.
- `modules/pedidos_chef.py` + `modules/pedidos_chef_ui.py`
  Salidas internas a cocina y detalle por ingrediente.
- `modules/produccion.py` + `modules/produccion_ui.py`
  Produccion de productos terminados.
- `modules/ventas.py` + `modules/ventas_ui.py`
  Ventas, detalle por movimiento y descuentos de inventario.
- `modules/excedentes.py` + `modules/excedentes_ui.py`
  Ajustes y cierre diario.
- `modules/historial.py` + `modules/historial_ui.py`
  Reportes diarios y mensuales.

## Regla de dependencia
Los modulos visuales reciben contexto desde `ModuleLoader` y deben reutilizar servicios compartidos desde `app_core/context.py`.
La navegacion y el registro de modulos se controlan desde `app_core/module_registry.py`.
La app ya no depende de `modules/__init__.py` para importar todo de golpe.

## Estructura de apoyo
- `utils/`: validaciones, fechas, operaciones de base y calculos auxiliares.
- `tools/maintenance/`: scripts de limpieza o migracion manual.
- `tools/diagnostics/`: pruebas y diagnosticos heredados.
- `tools/installer/`: recursos del empaquetado e instalador.
- `docs/legacy/`: documentos viejos que no deben mezclarse con la operacion diaria.

## Riesgos tecnicos actuales
- La mayor complejidad sigue estando en la coherencia de inventario entre compras, pedidos de cocina, produccion, ventas y cierre.
- Varias UIs siguen siendo largas; ahora cargan mejor, pero aun conviene dividir componentes internos en futuras iteraciones.
- Los scripts movidos a `tools/` deben asumirse como utilidades de soporte, no como parte del flujo principal de arranque.
