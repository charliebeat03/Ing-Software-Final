from __future__ import annotations

from dataclasses import dataclass

from config import APP_DISPLAY_NAME, APP_NAME, APP_VERSION
from database import db


@dataclass
class ServiceContainer:
    _services: dict[str, object] | None = None

    def __post_init__(self) -> None:
        self._services = {}

    def get(self, name: str):
        if name not in self._services:
            self._services[name] = self._create(name)
        return self._services[name]

    def _create(self, name: str):
        if name == "database":
            return db
        if name == "catalogos":
            from modules.catalogos import CatalogoManager

            return CatalogoManager()
        if name == "compras":
            from modules.compras import ComprasManager

            return ComprasManager()
        if name == "inventario":
            from modules.inventario import InventarioManager

            return InventarioManager()
        if name == "pedidos_chef":
            from modules.pedidos_chef import PedidosChefManager

            return PedidosChefManager()
        if name == "produccion":
            from modules.produccion import ProduccionManager

            return ProduccionManager()
        if name == "ventas":
            from modules.ventas import VentasManager

            return VentasManager()
        if name == "excedentes":
            from modules.excedentes import CierreDiarioManager

            return CierreDiarioManager()
        if name == "historial":
            from modules.historial import HistorialManager

            return HistorialManager()
        raise KeyError(f"Servicio no registrado: {name}")


def build_app_context(current_user: dict | None = None) -> dict:
    services = ServiceContainer()
    return {
        "app_name": APP_NAME,
        "display_name": APP_DISPLAY_NAME,
        "version": APP_VERSION,
        "db": db,
        "services": services,
        "current_user": current_user or {},
    }
