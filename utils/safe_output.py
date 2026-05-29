from __future__ import annotations

import builtins
import sys


def _sanitize(value: object, encoding: str) -> str:
    return str(value).encode(encoding, errors="replace").decode(encoding)


def safe_print(*args, **kwargs) -> None:
    """Imprime mensajes sin fallar si la consola no soporta ciertos caracteres."""
    try:
        builtins.print(*args, **kwargs)
    except UnicodeEncodeError:
        file = kwargs.get("file") or sys.stdout
        encoding = getattr(file, "encoding", None) or "utf-8"
        sanitized_args = [_sanitize(arg, encoding) for arg in args]
        builtins.print(*sanitized_args, **kwargs)
