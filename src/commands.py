"""Chat command handlers for the interactive loop.

Each handler corresponds to a slash command available in the chat UI.
All handlers are async and return either a ChatLoopResult (to signal a
lifecycle change) or None (command was handled in-place).
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from src.constants import ChatCommand
from src.context_tracker import build_context_breakdown
from src.memory import clear_all_memories, list_memory_files, read_memory_file, read_memory_index
from src.providers import DEEPSEEK_MODELS, OPENAI_MODELS, list_ollama_models
from src.ui import (
    MCP_SUBCOMMANDS,
    console,
    show_context_breakdown,
    show_error,
    show_info,
    show_mcp_table,
    show_models_table,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result type — defined here to avoid circular imports with main.py
# ---------------------------------------------------------------------------


@dataclass
class ChatLoopResult:
    """Signals what the main loop should do after a command returns.

    Attributes:
        command: The action to take (NEW thread, EXIT, MODEL change, or MCP reload).
        thread_id: Target thread ID when resuming a conversation.
        model_name: New model name when command is MODEL.
        mcp_disabled: Updated set of disabled server names when command is MCP_RELOAD.
    """

    command: ChatCommand
    thread_id: str = ""
    model_name: str = ""
    mcp_disabled: frozenset[str] = field(default_factory=frozenset)


# ---------------------------------------------------------------------------
# /context
# ---------------------------------------------------------------------------


async def handle_context_command(
    agent,
    thread_id: str,
    user_id: str,
    all_tools: list,
    mcp_tool_count: int,
    max_context_tokens: int,
) -> None:
    """Display token usage breakdown for the current conversation."""
    from src.agent import get_system_prompt

    config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(config)
    checkpoint_messages = state.values.get("messages", []) if state.values else []

    content = read_memory_index()
    memories = content.splitlines() if content else []

    breakdown = build_context_breakdown(
        system_prompt=get_system_prompt(),
        memories=memories,
        messages=checkpoint_messages,
        tools=all_tools,
        mcp_tool_count=mcp_tool_count,
        max_tokens=max_context_tokens,
    )
    show_context_breakdown(breakdown)


# ---------------------------------------------------------------------------
# /memory
# ---------------------------------------------------------------------------


async def handle_memory_command(
    parts: list[str],
    user_id: str,
) -> None:
    """Handle the /memory command and its subcommands."""
    from rich.markdown import Markdown

    subcmd = parts[1].lower() if len(parts) > 1 else ""

    if subcmd in ("", "show"):
        content = read_memory_index()
        if not content:
            show_info("No hay memorias guardadas aún.")
        else:
            console.print()
            console.print(Markdown(content))
            console.print()

    elif subcmd == "list":
        files = list_memory_files()
        if not files:
            show_info("No hay archivos de memoria.")
        else:
            show_info(f"{len(files)} archivo(s) de memoria:")
            for f in files:
                console.print(f"  {f}")
            console.print()

    elif subcmd == "read":
        filename = parts[2].strip() if len(parts) > 2 else ""
        if not filename:
            show_error("Uso: /memory read <archivo>")
            return
        content = read_memory_file(filename)
        if not content:
            show_error(f"No se encontró el archivo '{filename}'.")
        else:
            console.print()
            console.print(Markdown(content))
            console.print()

    elif subcmd == "clear":
        try:
            confirm = await asyncio.get_running_loop().run_in_executor(
                None,
                lambda: input("Escribe 'si' para confirmar el borrado de memorias: "),
            )
        except (EOFError, KeyboardInterrupt):
            return
        if confirm.strip().lower() not in ("si", "sí", "yes"):
            show_info("Cancelado.")
            return
        ok = clear_all_memories()
        if ok:
            show_info("Todas las memorias han sido borradas.")
        else:
            show_error("No se pudieron borrar las memorias.")

    else:
        show_error(f"Subcomando desconocido: {subcmd}")
        show_info("Uso: /memory [show|list|read <archivo>|clear]")


# ---------------------------------------------------------------------------
# /mcp
# ---------------------------------------------------------------------------


async def handle_mcp_command(
    parts: list[str],
    mcp_config: dict,
    disabled_servers: frozenset[str],
) -> ChatLoopResult | None:
    """Handle the /mcp command and its subcommands.

    Returns a ChatLoopResult with MCP_RELOAD when a state change is needed,
    or None when the command only displays information.
    """
    from rich.panel import Panel
    from rich.text import Text

    subcmd = parts[1].lower() if len(parts) > 1 else "list"

    if subcmd == "list":
        show_mcp_table(mcp_config, disabled_servers)
        return None

    if subcmd == "help":
        content = Text()
        content.append("MCP subcommands:\n\n", style="bold")
        for cmd, desc in MCP_SUBCOMMANDS.items():
            content.append(f"  {cmd:<28}", style="bold cyan")
            content.append(f"{desc}\n", style="dim")
        console.print(Panel(content, title="MCP Help", border_style="bright_blue", padding=(1, 2)))
        console.print()
        return None

    if subcmd == "reload":
        return ChatLoopResult(command=ChatCommand.MCP_RELOAD, mcp_disabled=disabled_servers)

    if subcmd == "disable":
        name = parts[2] if len(parts) > 2 else ""
        if not name:
            show_error("Usage: /mcp disable <nombre>")
            return None
        if name not in mcp_config:
            show_error(f"Servidor '{name}' no encontrado en mcp_servers.json.")
            return None
        if name in disabled_servers:
            show_info(f"El servidor '{name}' ya está deshabilitado.")
            return None
        show_info(f"Deshabilitando servidor '{name}'...")
        return ChatLoopResult(
            command=ChatCommand.MCP_RELOAD,
            mcp_disabled=frozenset(disabled_servers | {name}),
        )

    if subcmd == "enable":
        name = parts[2] if len(parts) > 2 else ""
        if not name:
            show_error("Usage: /mcp enable <nombre>")
            return None
        if name not in mcp_config:
            show_error(f"Servidor '{name}' no encontrado en mcp_servers.json.")
            return None
        if name not in disabled_servers:
            show_info(f"El servidor '{name}' ya está activo.")
            return None
        show_info(f"Habilitando servidor '{name}'...")
        return ChatLoopResult(
            command=ChatCommand.MCP_RELOAD,
            mcp_disabled=frozenset(disabled_servers - {name}),
        )

    show_error(f"Subcomando desconocido: '{subcmd}'. Usa /mcp help para ver las opciones.")
    return None


# ---------------------------------------------------------------------------
# /model
# ---------------------------------------------------------------------------


async def handle_model_command(
    parts: list[str],
    current_model: str,
) -> ChatLoopResult | None:
    """Handle the /model command.

    Returns a ChatLoopResult with MODEL when switching models,
    or None when only listing available models.
    """
    new_model = parts[1].strip() if len(parts) > 1 else ""
    if new_model:
        return ChatLoopResult(command=ChatCommand.MODEL, model_name=new_model)

    # List available models
    models_by_provider: dict[str, list[str]] = {}
    try:
        models_by_provider["ollama"] = await list_ollama_models()
    except Exception as e:
        show_error(f"No se pudo obtener modelos de Ollama: {e}")
    models_by_provider["openai"] = list(OPENAI_MODELS)
    models_by_provider["deepseek"] = list(DEEPSEEK_MODELS)
    show_models_table(models_by_provider, current_model)
    return None
