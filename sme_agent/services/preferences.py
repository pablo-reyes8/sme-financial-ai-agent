from __future__ import annotations

import re
from typing import Optional, Tuple

from sme_agent.services.classification import normalize_text


_SAVE_PATTERN = re.compile(
    r"^(guardar|recordar)\s*[:\-]?\s*(?P<key>[^:=]+?)\s*[:=]\s*(?P<value>.+)$"
)
_SHOW_PATTERN = re.compile(r"^(mis datos|mis preferencias|ver datos|ver preferencias)$")


def parse_save_command(text: str) -> Optional[Tuple[str, str]]:
    normalized = normalize_text(text.lower().strip())
    if not _SAVE_PATTERN.match(normalized):
        return None

    original = text.strip()
    lowered = normalize_text(original.lower())
    rest = original
    if lowered.startswith("guardar"):
        rest = original[len("guardar") :].strip()
    elif lowered.startswith("recordar"):
        rest = original[len("recordar") :].strip()
    if rest.startswith(":") or rest.startswith("-"):
        rest = rest[1:].strip()

    key = ""
    value = ""
    if ":" in rest:
        key, value = rest.split(":", 1)
    elif "=" in rest:
        key, value = rest.split("=", 1)

    key = normalize_text(key.strip().lower())
    value = value.strip()
    if not key or not value:
        return None
    return key, value


def is_show_preferences(text: str) -> bool:
    normalized = normalize_text(text.lower().strip())
    return bool(_SHOW_PATTERN.match(normalized))


def format_preferences(items) -> str:
    if not items:
        return (
            "No tengo datos guardados. Puedes decir por ejemplo: "
            "guardar: sector=alimentos o guardar: ciudad=Bogota."
        )
    lines = ["Estos son los datos guardados:", ""]
    for item in items:
        lines.append(f"- {item.key}: {item.value}")
    lines.append("")
    lines.append("Si quieres actualizar alguno, escribe: guardar: clave=valor")
    return "\n".join(lines)


def build_preference_context(items) -> str:
    if not items:
        return ""
    parts = [f"{item.key}={item.value}" for item in items]
    return "Datos del usuario: " + ", ".join(parts)
