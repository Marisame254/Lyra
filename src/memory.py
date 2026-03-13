"""Agent memory management via CompositeBackend / StoreBackend.

Memories live in ``/memories/AGENT.md`` routed through ``StoreBackend``,
stored with namespace ``("filesystem",)`` and key ``AGENT.md``.
"""

from __future__ import annotations

import logging

from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)

STORE_NAMESPACE: tuple[str, ...] = ("filesystem",)
AGENT_MEMORY_KEY: str = "/AGENT.md"


async def read_agent_memory(store: BaseStore) -> str | None:
    """Read the content of /memories/AGENT.md from the store.

    Returns the joined content lines, or None if not found.
    """
    try:
        item = await store.aget(STORE_NAMESPACE, AGENT_MEMORY_KEY)
        if not item or "content" not in item.value:
            return None
        return "\n".join(item.value["content"])
    except Exception:
        logger.debug("Failed to read agent memory", exc_info=True)
        return None


async def clear_agent_memory(store: BaseStore) -> bool:
    """Delete /memories/AGENT.md from the store."""
    try:
        await store.adelete(STORE_NAMESPACE, AGENT_MEMORY_KEY)
        return True
    except Exception:
        logger.debug("Failed to clear agent memory", exc_info=True)
        return False
