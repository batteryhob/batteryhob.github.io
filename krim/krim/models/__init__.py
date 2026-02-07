"""Model factory."""

from __future__ import annotations

from krim.models.base import Model
from krim.models.claude import ClaudeModel
from krim.models.openai import OpenAIModel

DEFAULT_MODELS = {
    "claude": "claude-sonnet-4-5-20250929",
    "openai": "gpt-4o",
}


def create_model(provider: str, model: str | None = None) -> Model:
    model_name = model or DEFAULT_MODELS.get(provider, "gpt-4o")
    if provider == "claude":
        return ClaudeModel(model_name)
    elif provider == "openai":
        return OpenAIModel(model_name)
    else:
        raise ValueError(f"unknown provider: {provider}")
