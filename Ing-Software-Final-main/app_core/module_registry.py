from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModuleSpec:
    module_id: str
    title: str
    module_file: str
    class_name: str
    group: str
    description: str
    difficulty: str
    default: bool = False


MODULE_SPECS: tuple[ModuleSpec, ...] = (
    ModuleSpec(
        module_id="dashboard",
        title="Panel General",
        module_file="dashboard_ui",
        class_name="DashboardWidget",
        group="Operacion",
        description="Resumen ejecutivo del dia, alertas y accesos rapidos.",
        difficulty="Media",
        default=True,
    ),
    ModuleSpec(
        module_id="inventario",
        title="Inventario",
        module_file="inventario_ui",
        class_name="InventarioWidget",
        group="Operacion",
        description="Estado actual de ingredientes, productos y alertas.",
        difficulty="Alta",
    ),
    ModuleSpec(
        module_id="compras",
        title="Compras",
        module_file="compras_ui",
        class_name="ComprasWidget",
        group="Operacion",
        description="Registro de compras y costos de ingredientes.",
        difficulty="Media",
    ),
    ModuleSpec(
        module_id="pedidos_chef",
        title="Pedidos de Cocina",
        module_file="pedidos_chef_ui",
        class_name="PedidosChefWidget",
        group="Operacion",
        description="Solicitudes internas del chef y consumo de inventario.",
        difficulty="Alta",
    ),
    ModuleSpec(
        module_id="produccion",
        title="Produccion",
        module_file="produccion_ui",
        class_name="ProduccionWidget",
        group="Operacion",
        description="Registro de lotes preparados para la venta.",
        difficulty="Alta",
    ),
    ModuleSpec(
        module_id="ventas",
        title="Ventas",
        module_file="ventas_ui",
        class_name="VentasWidget",
        group="Operacion",
        description="Ventas del dia y salidas de productos terminados.",
        difficulty="Alta",
    ),
    ModuleSpec(
        module_id="excedentes",
        title="Cierre Diario",
        module_file="excedentes_ui",
        class_name="CierreDiarioWidget",
        group="Control",
        description="Conciliacion del dia y devolucion de sobrantes.",
        difficulty="Alta",
    ),
    ModuleSpec(
        module_id="catalogos",
        title="Catalogos",
        module_file="catalogos_ui",
        class_name="CatalogosWidget",
        group="Control",
        description="Maestros de ingredientes, productos y unidades.",
        difficulty="Media",
    ),
    ModuleSpec(
        module_id="historial",
        title="Historial y Reportes",
        module_file="historial_ui",
        class_name="HistorialWidget",
        group="Analisis",
        description="Consulta historica y consolidado de ventas.",
        difficulty="Media",
    ),
)


def get_module_spec(module_id: str) -> ModuleSpec:
    for spec in MODULE_SPECS:
        if spec.module_id == module_id:
            return spec
    raise KeyError(f"Modulo no registrado: {module_id}")


def grouped_modules() -> dict[str, list[ModuleSpec]]:
    groups: dict[str, list[ModuleSpec]] = {}
    for spec in MODULE_SPECS:
        groups.setdefault(spec.group, []).append(spec)
    return groups


def default_module() -> ModuleSpec:
    for spec in MODULE_SPECS:
        if spec.default:
            return spec
    return MODULE_SPECS[0]
