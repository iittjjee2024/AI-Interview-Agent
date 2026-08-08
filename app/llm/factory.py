"""LLM provider factory."""

from app.core.config import get_settings
from app.llm.base import LLMProvider
from app.llm.providers.gemini_provider import GeminiProvider
from app.llm.providers.groq_provider import GroqProvider
from app.llm.providers.openai_provider import OpenAIProvider


def create_llm_provider(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider based on configuration."""
    settings = get_settings()

    provider_name = (provider or settings.llm_provider).lower()
    model_name = model or settings.llm_model
    key = api_key or settings.llm_api_key
    temperature = kwargs.get("temperature", settings.llm_temperature)
    max_tokens = kwargs.get("max_tokens", settings.llm_max_tokens)
    timeout = kwargs.get("timeout", settings.llm_timeout)

    if provider_name == "groq":
        return GroqProvider(
            model=model_name,
            api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    elif provider_name in ("openai", "openai-compatible"):
        return OpenAIProvider(
            model=model_name,
            api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            base_url=kwargs.get("base_url"),
        )
    elif provider_name == "openrouter":
        return OpenAIProvider(
            model=model_name,
            api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            base_url="https://openrouter.ai/api/v1/chat/completions",
        )
    elif provider_name == "gemini":
        return GeminiProvider(
            model=model_name,
            api_key=key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
    elif provider_name == "ollama":
        return OpenAIProvider(
            model=model_name,
            api_key="ollama",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            base_url="http://localhost:11434/v1/chat/completions",
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider_name}")
