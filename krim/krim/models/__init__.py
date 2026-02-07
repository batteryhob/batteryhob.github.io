from krim.models.base import Model
from krim.models.claude import ClaudeModel
from krim.models.openai import OpenAIModel


def create_model(provider: str, model: str) -> Model:
    if provider == "claude":
        return ClaudeModel(model)
    elif provider == "openai":
        return OpenAIModel(model)
    else:
        raise ValueError(f"unknown provider: {provider}")
