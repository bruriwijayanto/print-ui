"""Input validation helpers that guard against unsafe values reaching CUPS."""

from __future__ import annotations

import re

_PRINTER_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,127}$")


def is_valid_printer_name(name: str) -> bool:
    return bool(_PRINTER_NAME_RE.fullmatch(name or ""))
