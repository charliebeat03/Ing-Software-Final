from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


def find_inline_styles(base_dir: Path, exclude_dirs: List[str] | None = None, marker: str = "# allow-inline-style") -> List[Tuple[Path, int, str]]:
    """Search Python files for occurrences of `setStyleSheet(`.

    Returns a list of tuples (file_path, line_number, line_text) for each match
    unless the file contains the `marker` comment which allows inline styles.
    """
    exclude_dirs = set(exclude_dirs or ["venv", "archive", "build", "Output"])
    results: List[Tuple[Path, int, str]] = []
    for path in base_dir.rglob("*.py"):
        # skip common large or generated directories
        if any(part in exclude_dirs for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if marker in text:
            # file explicitly allows inline styles
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            if "setStyleSheet(" in line:
                results.append((path, i, line.strip()))
    return results


def format_findings(findings: List[Tuple[Path, int, str]]) -> str:
    parts: List[str] = []
    for p, ln, line in findings:
        parts.append(f"{p.relative_to(Path.cwd())}:{ln}: {line}")
    return "\n".join(parts)


def enforce_runtime_style_protection(marker: str = "# allow-inline-style") -> None:
    """Monkeypatch QWidget.setStyleSheet to ignore inline styles at runtime

    If a calling file contains the `marker` string it will be allowed; other
    calls are ignored and a console warning is emitted. This helps centralize
    styles while remaining opt-in for exceptional cases.
    """
    try:
        import inspect
        from PyQt5.QtWidgets import QWidget

        original = QWidget.setStyleSheet

        def _wrapper(self, style: str | None) -> None:
            # find the first non-library frame
            for frame_info in inspect.stack()[1:6]:
                filename = frame_info.filename
                try:
                    text = Path(filename).read_text(encoding="utf-8")
                except Exception:
                    continue
                if marker in text:
                    # allow this file to set inline styles
                    return original(self, style)
                # if the file is inside the project and not the PyQt internals,
                # block the inline style
                if Path(filename).exists() and not any(p in filename for p in ("site-packages", "PyQt5")):
                    # ignore change and warn
                    print(f"[style_guard] blocked inline style from {filename}")
                    return
            # fallback: call original
            return original(self, style)

        QWidget.setStyleSheet = _wrapper  # type: ignore
    except Exception:
        # If monkeypatching fails, fail silently — protection is advisory.
        pass
