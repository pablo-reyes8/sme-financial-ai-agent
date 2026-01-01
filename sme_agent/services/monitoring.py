from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from langchain.callbacks.base import BaseCallbackHandler


@dataclass
class LLMUsage:
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    model: Optional[str] = None


def _extract_usage(llm_result) -> LLMUsage:
    usage = {}
    model = None

    if getattr(llm_result, "llm_output", None):
        output = llm_result.llm_output or {}
        usage = output.get("token_usage") or output.get("usage") or {}
        model = output.get("model") or output.get("model_name")

    if not usage and getattr(llm_result, "generations", None):
        generations = llm_result.generations
        if generations and generations[0]:
            info = generations[0][0].generation_info or {}
            usage = info.get("token_usage") or info.get("usage") or {}
            model = model or info.get("model")

    prompt_tokens = usage.get("prompt_tokens") or usage.get("input_tokens")
    completion_tokens = usage.get("completion_tokens") or usage.get("output_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens

    return LLMUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        model=model,
    )


class LLMMonitor(BaseCallbackHandler):
    def __init__(self) -> None:
        self.usage = LLMUsage()
        self.error: Optional[str] = None

    def on_llm_end(self, response, **kwargs: Any) -> None:
        self.usage = _extract_usage(response)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        self.error = str(error)
