# Historial y Producción: Correcciones aplicadas

## Objetivo

Corregir y estabilizar los módulos de historial y producción en la aplicación, sin modificar estilos globales ni la hoja de estilo principal.

## Archivos modificados

- `modules/produccion.py`
- `modules/historial_ui.py`

## Problemas detectados

1. `modules/produccion.py` intentaba usar `VentasManager.registrar_venta` con una firma incorrecta, asumiendo que retornaba un `venta_id` cuando en realidad el método retorna el total de la venta.
2. `modules/historial_ui.py` no tenía una conexión explícita para actualizar la UI cuando el manager emite `datos_actualizados`.

## Correcciones aplicadas

- En `modules/produccion.py` se ajustó la llamada a `VentasManager.registrar_venta(producto_id, cantidad)` para usar la firma existente.
- Se agregó manejo de errores seguro para evitar fallas si la venta automática no se puede registrar.
- En `modules/historial_ui.py` se conectó `HistorialManager.datos_actualizados` a `HistorialWidget.actualizar_ui()` cuando el manager disponible lo expone.
- Se implementó `actualizar_ui()` para refrescar la vista diaria o mensual según el estado actual.

## Resultados esperados

- El módulo de producción ya no depende de un valor erróneo de retorno de `registrar_venta`.
- El historial se refrescará correctamente cuando el manager indique que hay datos actualizados.
- No se tocó `styles.qss` ni se modificaron estilos globales.

## Cómo verificar

1. Abrir la aplicación.
2. Ir al módulo de Producción y registrar una producción.
3. Verificar que la producción se guarde y que el inventario se actualice.
4. Ir al módulo de Historial y confirmar que la vista diaria y mensual se actualizan correctamente.

## Nota de git

Se creará una nueva rama para este conjunto de cambios y se empujará al repositorio remoto proporcionado.
