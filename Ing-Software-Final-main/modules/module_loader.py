from __future__ import annotations

import importlib
import inspect

from PyQt5.QtWidgets import QLabel


class ModuleLoader:
    def __init__(self, context: dict | None = None):
        self.context = context or {}
        self.widgets: dict[str, object] = {}

    def _build_widget(self, module, class_name: str):
        if hasattr(module, "create_widget") and callable(module.create_widget):
            return module.create_widget(self.context)

        widget_cls = getattr(module, class_name, None)
        if widget_cls is None:
            raise AttributeError(f"No existe la clase {class_name} en {module.__name__}")

        signature = inspect.signature(widget_cls.__init__)
        parameters = [param for name, param in signature.parameters.items() if name != "self"]
        accepts_context = any(param.name in {"context", "app_context"} for param in parameters)

        if accepts_context:
            return widget_cls(context=self.context)
        return widget_cls()

    def _apply_context(self, widget) -> None:
        if hasattr(widget, "setup") and callable(widget.setup):
            widget.setup(self.context)
        elif hasattr(widget, "set_context") and callable(widget.set_context):
            widget.set_context(self.context)
        else:
            setattr(widget, "context", self.context)

    def load(self, spec) -> object:
        if spec.module_id in self.widgets:
            return self.widgets[spec.module_id]

        try:
            module = importlib.import_module(f"modules.{spec.module_file}")
            widget = self._build_widget(module, spec.class_name)
            self._apply_context(widget)
        except Exception as exc:
            widget = QLabel(f"No fue posible cargar el modulo {spec.title}.\n\n{exc}")
        self.widgets[spec.module_id] = widget
        return widget
