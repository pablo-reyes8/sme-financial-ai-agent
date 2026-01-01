from __future__ import annotations

from enum import Enum
import re

from sme_agent.services.classification import normalize_text


class Intent(str, Enum):
    BREAK_EVEN = "break_even"
    CASHFLOW = "cashflow"
    MARGINS = "margins"
    LIQUIDITY = "liquidity"
    DEBT = "debt"
    GENERAL = "general"


_INTENT_PATTERNS = {
    Intent.BREAK_EVEN: [
        r"punto de equilibrio",
        r"break\s*even",
        r"umbral de rentabilidad",
        r"equilibrio financiero",
    ],
    Intent.CASHFLOW: [r"flujo de caja", r"caja neta", r"caja mensual"],
    Intent.MARGINS: [r"margen", r"rentabilidad", r"margen bruto", r"margen neto"],
    Intent.LIQUIDITY: [r"razon corriente", r"liquidez", r"activo corriente"],
    Intent.DEBT: [r"deuda", r"endeudamiento", r"ebitda", r"cobertura de intereses"],
}

_CALC_TRIGGER = re.compile(r"(calcula|calcular|cuanto|formula|numero|margen|punto de equilibrio)")


def detect_intent(text: str) -> Intent:
    normalized = normalize_text(text.lower())
    for intent, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, normalized):
                return intent
    return Intent.GENERAL


def should_use_calculator(text: str, intent: Intent) -> bool:
    normalized = normalize_text(text.lower())
    if intent == Intent.GENERAL:
        return False
    if _CALC_TRIGGER.search(normalized):
        return True
    if intent in {Intent.BREAK_EVEN, Intent.MARGINS, Intent.LIQUIDITY, Intent.DEBT}:
        return True
    if intent == Intent.CASHFLOW and re.search(r"\d", normalized):
        return True
    return False
