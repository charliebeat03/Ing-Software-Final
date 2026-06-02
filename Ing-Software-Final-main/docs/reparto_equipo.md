# Reparto Sugerido del Equipo

## Modulos mas delicados
Estos son los que mas riesgo concentran y donde conviene poner a la gente fuerte:

1. `inventario`
   Es el eje de todo el flujo. Si aqui se rompe algo, compras, cocina, produccion, ventas y cierre se desalinean.
2. `ventas`
   Toca stock de productos, historial, totales del dia y cancelaciones.
3. `pedidos_chef`
   Mueve inventario de ingredientes y afecta el cierre diario.
4. `excedentes / cierre diario`
   Es el modulo de conciliacion. Un error aqui deja mal el inventario final del dia.

## Modulos de complejidad media
- `produccion`
- `catalogos`
- `compras`
- `historial`
- `dashboard / main_window`

## Asignacion recomendada

### Tu parte
- `inventario`
- `excedentes`
- supervision de `main_window` y `dashboard`

Motivo:
Son los puntos mas transversales y con mas impacto en reglas del negocio.

### Compañero mas fuerte
- `ventas`
- `pedidos_chef`
- `produccion`

Motivo:
Son modulos conectados entre si y con alto riesgo sobre cantidades y movimientos diarios.

### Compañero 2
- `catalogos`
- `compras`

Motivo:
Son modulos bastante claros, utiles para avanzar rapido y con menos riesgo estructural.

### Compañero 3
- `historial`
- apoyo visual en `dashboard` y revision de estilos

Motivo:
Es una entrada mas amable al proyecto y permite aportar valor en reportes, UI y pruebas de consistencia.

## Regla de trabajo para no pisarse
- Nadie debe editar `database.py` sin avisar al resto.
- Los cambios visuales de un modulo deben quedarse en su `*_ui.py`.
- Las reglas de negocio deben quedarse en el archivo del manager del modulo o en `utils/`.
- Si un modulo necesita datos de otro, debe pedirlos por servicios compartidos, no por importaciones en cadena nuevas.

## Orden recomendado de revision
1. Inventario
2. Ventas
3. Pedidos de cocina
4. Cierre diario
5. Produccion
6. Compras
7. Catalogos
8. Historial
