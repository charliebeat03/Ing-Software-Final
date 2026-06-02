INSTRUCCIONES PARA EL CLIENTE - ELIMINADOR DE VENTAS

📁 ARCHIVOS NECESARIOS (deben estar en la misma carpeta):
1. eliminar_ventas.bat      (Este archivo que ejecutas)
2. eliminar_ultimas_ventas.py  (El programa principal)

🚀 CÓMO USAR:
1. Haz doble clic en "eliminar_ventas.bat"
2. El programa te preguntará cuántas ventas quieres eliminar
3. Ingresa el número (ej: 1, 2, 5, etc.)
4. El programa mostrará las últimas ventas para que confirmes
5. Se crea un BACKUP automático antes de eliminar
6. Confirma la eliminación escribiendo "SI"

🔒 SEGURIDAD:
- SOLO se eliminan ventas (tablas: ventas y ventas_detalle)
- NO se tocan productos, ingredientes, compras, etc.
- Se crea backup automático en: data/backup_ventas_FECHA.db
- Puedes restaurar manualmente el backup si es necesario

⚠️ ADVERTENCIAS:
- Esta operación NO se puede deshacer (excepto con el backup)
- Afecta los reportes de ventas y estadísticas
- No afecta el inventario de productos/ingredientes

📞 SOPORTE:
Si tienes problemas:
1. Verifica que Python esté instalado
2. Asegúrate de que la aplicación se haya ejecutado al menos una vez
3. Los archivos deben estar en la misma carpeta que la aplicación