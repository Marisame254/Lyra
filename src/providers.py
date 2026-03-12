"""LLM provider factory and model catalogue.

Supported providers:
- ``ollama``   — local models via Ollama (default for bare model names)
- ``openai``   — OpenAI API (requires OPENAI_API_KEY)
- ``deepseek`` — DeepSeek API, OpenAI-compatible (requires DEEPSEEK_API_KEY)

Model strings use the ``provider/model`` format.  Bare names (no slash)
are treated as Ollama models for backward compatibility with MODEL_NAME.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Provider identifiers
# ---------------------------------------------------------------------------

PROVIDER_OLLAMA = "ollama"
PROVIDER_OPENAI = "openai"
PROVIDER_DEEPSEEK = "deepseek"

KNOWN_PROVIDERS: tuple[str, ...] = (PROVIDER_OLLAMA, PROVIDER_OPENAI, PROVIDER_DEEPSEEK)

# ---------------------------------------------------------------------------
# Curated model catalogues for cloud providers
# ---------------------------------------------------------------------------

OPENAI_MODELS: tuple[str, ...] = (
    "gpt-4o",
    "gpt-4o-mini",
    "o1",
    "o1-mini",
    "o3-mini",
)

DEEPSEEK_MODELS: tuple[str, ...] = (
    "deepseek-chat",
    "deepseek-reasoner",
)

# ---------------------------------------------------------------------------
# Known context windows (tokens) for cloud providers
# ---------------------------------------------------------------------------

OPENAI_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-4o-mini": 128_000,
    "o1": 200_000,
    "o1-mini": 128_000,
    "o3-mini": 200_000,
}

DEEPSEEK_CONTEXT_WINDOWS: dict[str, int] = {
    "deepseek-chat": 64_000,
    "deepseek-reasoner": 64_000,
}

# ---------------------------------------------------------------------------
# ModelSpec
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelSpec:
    """Parsed model identifier composed of a provider and a model name.

    Examples::

        ModelSpec.parse("qwen3:14b")              # → ollama/qwen3:14b
        ModelSpec.parse("ollama/llama3:8b")       # → ollama/llama3:8b
        ModelSpec.parse("openai/gpt-4o")          # → openai/gpt-4o
        ModelSpec.parse("deepseek/deepseek-chat") # → deepseek/deepseek-chat
    """

    provider: str
    name: str

    @classmethod
    def parse(cls, model_str: str) -> ModelSpec:
        """Parse a ``provider/name`` string.

        Bare model names (no ``/``) default to the Ollama provider so that
        existing ``MODEL_NAME`` env var values continue to work unchanged.

        Only the prefix before the *first* ``/`` is treated as a provider
        when it matches a known provider name.  This prevents Ollama model
        names that happen to contain slashes (e.g. ``hf.co/user/model:tag``)
        from being misidentified as a different provider.
        """
        if "/" in model_str:
            prefix, _, rest = model_str.partition("/")
            if prefix.lower() in KNOWN_PROVIDERS:
                return cls(provider=prefix.lower(), name=rest)
        return cls(provider=PROVIDER_OLLAMA, name=model_str)

    def __str__(self) -> str:
        return f"{self.provider}/{self.name}"


# ---------------------------------------------------------------------------
# LLM factory
# ---------------------------------------------------------------------------


def build_llm(spec: ModelSpec) -> BaseChatModel:
    """Instantiate the appropriate LangChain chat model for *spec*.

    All provider-specific imports are deferred so unused providers add no
    import overhead and missing optional packages only raise at call time.

    Raises:
        ValueError: Unknown provider or a required API key is not set.
    """
    if spec.provider == PROVIDER_OLLAMA:
        from langchain_ollama import ChatOllama

        return ChatOllama(model=spec.name)

    if spec.provider == PROVIDER_OPENAI:
        from langchain_openai import ChatOpenAI

        from src.config import OPENAI_API_KEY

        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set. Add it to your .env file.")
        return ChatOpenAI(model=spec.name, api_key=OPENAI_API_KEY)

    if spec.provider == PROVIDER_DEEPSEEK:
        from langchain_openai import ChatOpenAI

        from src.config import DEEPSEEK_API_KEY

        if not DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY is not set. Add it to your .env file.")
        return ChatOpenAI(
            model=spec.name,
            api_key=DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
        )

    raise ValueError(
        f"Unknown provider {spec.provider!r}. "
        f"Valid providers: {', '.join(KNOWN_PROVIDERS)}"
    )


# ---------------------------------------------------------------------------
# Model listing helpers
# ---------------------------------------------------------------------------


async def list_ollama_models() -> list[str]:
    """Return model names available in the local Ollama instance.

    Raises:
        Exception: If Ollama is not reachable.
    """
    from ollama import AsyncClient

    response = await AsyncClient().list()
    return [m.model for m in response.models]


# ---------------------------------------------------------------------------
# Context window detection
# ---------------------------------------------------------------------------

_context_window_cache: dict[str, int] = {}


async def _get_ollama_context_length(model_name: str) -> int | None:
    """Query Ollama for the model's context length."""
    from ollama import AsyncClient

    try:
        info = await AsyncClient().show(model_name)
        model_info = info.get("model_info", {})
        for key, value in model_info.items():
            if key.endswith("context_length") and isinstance(value, (int, float)):
                return int(value)
    except Exception:
        logger.debug("Failed to query Ollama context length for %s", model_name, exc_info=True)
    return None


async def get_model_context_window(spec: ModelSpec, fallback: int) -> int:
    """Detect the context window size for the given model.

    Uses the Ollama API for local models and hardcoded mappings for
    OpenAI/DeepSeek. Results are cached per model spec.

    Args:
        spec: Parsed model identifier.
        fallback: Value to return if detection fails.

    Returns:
        Context window size in tokens.
    """
    cache_key = str(spec)
    if cache_key in _context_window_cache:
        return _context_window_cache[cache_key]

    result: int | None = None

    if spec.provider == PROVIDER_OLLAMA:
        result = await _get_ollama_context_length(spec.name)
    elif spec.provider == PROVIDER_OPENAI:
        result = OPENAI_CONTEXT_WINDOWS.get(spec.name)
    elif spec.provider == PROVIDER_DEEPSEEK:
        result = DEEPSEEK_CONTEXT_WINDOWS.get(spec.name)

    detected = result if result is not None else fallback
    _context_window_cache[cache_key] = detected

    if result is not None:
        logger.info("Detected context window for %s: %d tokens", spec, detected)
    else:
        logger.info("Using fallback context window for %s: %d tokens", spec, detected)

    return detected
