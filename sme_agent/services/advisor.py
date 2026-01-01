from __future__ import annotations

from typing import Optional

from sme_agent.services.calculators import maybe_run_calculator
from sme_agent.services.intents import detect_intent, should_use_calculator


def maybe_handle_calculator(text: str) -> Optional[str]:
    intent = detect_intent(text)
    if not should_use_calculator(text, intent):
        return None
    result = maybe_run_calculator(text, intent)
    if result:
        return result.response
    return None
