"""Agent memory management — filesystem-based, Claude Code style.

Multi-file memory system stored at ``~/.lyra/memory/``:
- ``MEMORY.md`` is the concise index (auto-loaded each turn).
- Individual topic files (``user_role.md``, ``feedback_style.md``, …) hold content.
"""

from __future__ import annotations

import logging
from pathlib import Path

from src.constants import MEMORY_DIR_NAME, MEMORY_INDEX_FILENAME, MEMORY_SUBDIR

logger = logging.getLogger(__name__)


def get_memory_dir() -> Path:
    """Return the memory directory path, creating it if needed."""
    memory_dir = Path.home() / MEMORY_DIR_NAME / MEMORY_SUBDIR
    memory_dir.mkdir(parents=True, exist_ok=True)
    return memory_dir


def get_memory_index_path() -> Path:
    """Return the absolute path to MEMORY.md."""
    return get_memory_dir() / MEMORY_INDEX_FILENAME


def read_memory_index() -> str | None:
    """Read the content of MEMORY.md from the filesystem."""
    try:
        path = get_memory_index_path()
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8").strip()
        return content or None
    except Exception:
        logger.debug("Failed to read memory index", exc_info=True)
        return None


def read_memory_file(filename: str) -> str | None:
    """Read a specific topic file from the memory directory."""
    try:
        path = get_memory_dir() / filename
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8").strip()
        return content or None
    except Exception:
        logger.debug("Failed to read memory file %s", filename, exc_info=True)
        return None


def list_memory_files() -> list[str]:
    """List all memory topic files (excluding MEMORY.md)."""
    try:
        memory_dir = get_memory_dir()
        return sorted(
            f.name
            for f in memory_dir.glob("*.md")
            if f.name != MEMORY_INDEX_FILENAME
        )
    except Exception:
        logger.debug("Failed to list memory files", exc_info=True)
        return []


def clear_all_memories() -> bool:
    """Delete MEMORY.md and all topic files from the memory directory."""
    try:
        memory_dir = get_memory_dir()
        for f in memory_dir.glob("*.md"):
            f.unlink()
        return True
    except Exception:
        logger.debug("Failed to clear memories", exc_info=True)
        return False
