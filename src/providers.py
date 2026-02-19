"""LLM provider factory and model catalogue.

Supported providers:
- ``ollama``   — local models via Ollama (default for bare model names)
- ``openai``   — OpenAI API (requires OPENAI_API_KEY)
- ``deepseek`` — DeepSeek API, OpenAI-compatible (requires DEEPSEEK_API_KEY)

Model strings use the ``provider/model`` format.  Bare names (no slash)
are treated as Ollama models for backward compatibility with MODEL_NAME.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel

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
