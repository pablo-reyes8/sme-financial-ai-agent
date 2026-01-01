from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional

from sme_agent.services.classification import normalize_text
from sme_agent.services.intents import Intent


NUMBER_PATTERN = r"\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?"
NUMBER_RE = re.compile(NUMBER_PATTERN)


@dataclass
class CalculatorResult:
    response: str


def parse_number(raw: str) -> Optional[float]:
    if not raw:
        return None
    raw = raw.replace(" ", "")
    if "," in raw and "." in raw:
        if raw.rfind(",") > raw.rfind("."):
            decimal_sep = ","
            thousand_sep = "."
        else:
            decimal_sep = "."
            thousand_sep = ","
        raw = raw.replace(thousand_sep, "")
        raw = raw.replace(decimal_sep, ".")
    else:
        if "," in raw:
            parts = raw.split(",")
            if len(parts[-1]) == 3 and len(parts[0]) <= 3:
                raw = "".join(parts)
            else:
                raw = raw.replace(",", ".")
        elif "." in raw:
            parts = raw.split(".")
            if len(parts[-1]) == 3 and len(parts[0]) <= 3:
                raw = "".join(parts)
        
    try:
        return float(raw)
    except ValueError:
        return None


def _find_value(text: str, patterns) -> Optional[float]:
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = parse_number(match.group("number"))
            if value is not None:
                return value
    return None


def extract_amounts(text: str) -> Dict[str, float]:
    normalized = normalize_text(text.lower())
    values = {
        "ventas": _find_value(
            normalized,
            [
                r"ventas?[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"ingresos?[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "costos_fijos": _find_value(
            normalized,
            [
                r"costos? fijos?[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"gastos? fijos?[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "costo_variable_unit": _find_value(
            normalized,
            [
                r"costo variable[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"costo unitario[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "precio_unit": _find_value(
            normalized,
            [
                r"precio[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"ticket promedio[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "egresos": _find_value(
            normalized,
            [
                r"egresos?[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"gastos?[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "costo_ventas": _find_value(
            normalized,
            [
                r"costo de ventas[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"costo ventas[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "utilidad_neta": _find_value(
            normalized,
            [
                r"utilidad neta[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"ganancia neta[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "activo_corriente": _find_value(
            normalized,
            [
                r"activo corriente[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"activos corrientes[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "pasivo_corriente": _find_value(
            normalized,
            [
                r"pasivo corriente[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"pasivos corrientes[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "deuda_total": _find_value(
            normalized,
            [
                r"deuda total[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"pasivo total[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "ebitda": _find_value(
            normalized,
            [r"ebitda[^\d]*(?P<number>" + NUMBER_PATTERN + r")"],
        ),
        "intereses": _find_value(
            normalized,
            [
                r"intereses[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
                r"gastos? financieros[^\d]*(?P<number>" + NUMBER_PATTERN + r")",
            ],
        ),
        "utilidad_operativa": _find_value(
            normalized,
            [r"utilidad operativa[^\d]*(?P<number>" + NUMBER_PATTERN + r")"],
        ),
    }
    return {key: value for key, value in values.items() if value is not None}


def extract_percent(text: str, keyword: str) -> Optional[float]:
    normalized = normalize_text(text.lower())
    match = re.search(rf"{keyword}[^\d]*(?P<number>\d+(?:[.,]\d+)?)\s*%", normalized)
    if match:
        value = parse_number(match.group("number"))
        if value is not None:
            return value / 100
    return None


def format_currency(value: float) -> str:
    return "$" + f"{value:,.0f}"


def format_ratio(value: float) -> str:
    return f"{value:.2f}"


def format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def build_break_even(text: str) -> Optional[CalculatorResult]:
    values = extract_amounts(text)
    fixed_costs = values.get("costos_fijos")
    price = values.get("precio_unit")
    variable_cost = values.get("costo_variable_unit")
    margin_percent = extract_percent(text, "margen de contribucion")

    missing = []
    if fixed_costs is None:
        missing.append("costos fijos mensuales")

    if price is None and margin_percent is None:
        missing.append("precio promedio por unidad o margen de contribucion (%)")
    if variable_cost is None and margin_percent is None and price is not None:
        missing.append("costo variable unitario")

    if missing:
        steps = "\n".join([f"- Necesito {item}." for item in missing])
        response = (
            "Puedo calcular el punto de equilibrio, pero necesito algunos datos.\n\n"
            f"{steps}\n\n"
            "- Separar costos fijos y variables mejora la precision.\n\n"
            "Cuando tengas los datos, compartelos y hago el calculo."
        )
        return CalculatorResult(response=response)

    if margin_percent is not None:
        if margin_percent <= 0:
            return CalculatorResult(
                response=(
                    "El margen de contribucion debe ser mayor a 0%. "
                    "Revisa los datos y vuelve a intentarlo."
                )
            )
        sales_break_even = fixed_costs / margin_percent
        response = (
            "Con los datos suministrados, el punto de equilibrio estimado es:\n\n"
            f"- Costos fijos: {format_currency(fixed_costs)}\n"
            f"- Margen de contribucion: {format_percent(margin_percent)}\n"
            f"- Ventas de equilibrio: {format_currency(sales_break_even)}\n\n"
            "- Si el margen baja, el punto de equilibrio sube.\n\n"
            "Si quieres, puedo convertir esto a unidades o ajustar con datos mas precisos."
        )
        return CalculatorResult(response=response)

    contribution = price - variable_cost
    if contribution <= 0:
        return CalculatorResult(
            response=(
                "El margen unitario es menor o igual a cero. "
                "Necesitas un precio mayor o un costo variable menor para equilibrio."
            )
        )

    units = fixed_costs / contribution
    sales_break_even = units * price
    response = (
        "Con los datos suministrados, el punto de equilibrio estimado es:\n\n"
        f"- Costos fijos: {format_currency(fixed_costs)}\n"
        f"- Precio unitario: {format_currency(price)}\n"
        f"- Costo variable unitario: {format_currency(variable_cost)}\n"
        f"- Unidades de equilibrio: {units:,.1f}\n"
        f"- Ventas de equilibrio: {format_currency(sales_break_even)}\n\n"
        "- Si los costos variables cambian, el equilibrio tambien cambia.\n\n"
        "Si quieres, revisamos escenarios y sensibilidad con mas datos."
    )
    return CalculatorResult(response=response)


def build_cashflow(text: str) -> Optional[CalculatorResult]:
    values = extract_amounts(text)
    ingresos = values.get("ventas")
    egresos = values.get("egresos")

    if ingresos is None or egresos is None:
        return None

    net = ingresos - egresos
    response = (
        "Con los datos suministrados, el flujo de caja neto estimado es:\n\n"
        f"- Ingresos: {format_currency(ingresos)}\n"
        f"- Egresos: {format_currency(egresos)}\n"
        f"- Neto: {format_currency(net)}\n\n"
        "- Este calculo no incluye impuestos ni pagos extraordinarios.\n\n"
        "Si quieres, puedo desagregar por semanas o categorias."
    )
    return CalculatorResult(response=response)


def build_margins(text: str) -> Optional[CalculatorResult]:
    values = extract_amounts(text)
    ventas = values.get("ventas")
    costo_ventas = values.get("costo_ventas")
    utilidad_neta = values.get("utilidad_neta")

    if ventas is None:
        return None

    lines = []
    if costo_ventas is not None:
        margen_bruto = (ventas - costo_ventas) / ventas if ventas else 0
        lines.append(f"- Margen bruto: {format_percent(margen_bruto)}")
    if utilidad_neta is not None:
        margen_neto = utilidad_neta / ventas if ventas else 0
        lines.append(f"- Margen neto: {format_percent(margen_neto)}")

    if not lines:
        return None

    response = (
        "Con los datos suministrados, estos son los margenes estimados:\n\n"
        f"- Ventas: {format_currency(ventas)}\n"
        + "\n".join(lines)
        + "\n\n"
        "- Revisa costos indirectos para explicar variaciones del margen.\n\n"
        "Si quieres, calculo margenes por producto o canal."
    )
    return CalculatorResult(response=response)


def build_liquidity(text: str) -> Optional[CalculatorResult]:
    values = extract_amounts(text)
    activos = values.get("activo_corriente")
    pasivos = values.get("pasivo_corriente")

    if activos is None or pasivos is None:
        return None

    ratio = activos / pasivos if pasivos else 0
    response = (
        "Con los datos suministrados, la razon corriente estimada es:\n\n"
        f"- Activo corriente: {format_currency(activos)}\n"
        f"- Pasivo corriente: {format_currency(pasivos)}\n"
        f"- Razon corriente: {format_ratio(ratio)}\n\n"
        "- Un valor bajo puede presionar la caja de corto plazo.\n\n"
        "Si quieres, revisamos liquidez proyectada y capital de trabajo."
    )
    return CalculatorResult(response=response)


def build_debt(text: str) -> Optional[CalculatorResult]:
    values = extract_amounts(text)
    deuda = values.get("deuda_total")
    ebitda = values.get("ebitda") or values.get("utilidad_operativa")
    intereses = values.get("intereses")

    lines = []
    if deuda is not None and ebitda not in (None, 0):
        ratio = deuda / ebitda
        lines.append(f"- Deuda/EBITDA: {format_ratio(ratio)}")

    if intereses not in (None, 0) and ebitda not in (None, 0):
        cobertura = ebitda / intereses
        lines.append(f"- Cobertura de intereses: {format_ratio(cobertura)}")

    if not lines:
        return None

    response = (
        "Con los datos suministrados, estos son los indicadores de deuda:\n\n"
        + "\n".join(lines)
        + "\n\n"
        "- Ajusta los calculos con datos mensuales comparables.\n\n"
        "Si quieres, analizamos escenarios de pago y sensibilidad." 
    )
    return CalculatorResult(response=response)


def maybe_run_calculator(text: str, intent: Intent) -> Optional[CalculatorResult]:
    if intent == Intent.BREAK_EVEN:
        return build_break_even(text)
    if intent == Intent.CASHFLOW:
        return build_cashflow(text)
    if intent == Intent.MARGINS:
        return build_margins(text)
    if intent == Intent.LIQUIDITY:
        return build_liquidity(text)
    if intent == Intent.DEBT:
        return build_debt(text)
    return None
