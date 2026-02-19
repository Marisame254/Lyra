# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Terminal-based conversational AI agent (Python 3.13+) that integrates MCP tools, Tavily web search, and local LLM inference via Ollama. Uses LangChain + LangGraph for agentic orchestration, PostgreSQL for persistence, and Rich for terminal UI. Documentation and user-facing strings are in Spanish.

## Commands

```bash
# Install dependencies (uv is the primary package manager)
uv sync

# Run the application
python main.py

# Alternative: after pip install -e .
agent-with-mcp
```

There are no test, lint, or build commands configured.

## Architecture

**Entry point:** `main.py:main()` — validates config, connects PostgreSQL, initializes MCP client, builds the LangGraph agent, then runs the interactive chat loop.

**Core flow:**
1. `src/config.py` loads env vars (DATABASE_URL, TAVILY_API_KEY, MODEL_NAME, etc.) from `.env`
2. `src/agent.py:build_agent()` constructs the LangGraph agent with ChatOllama, MCP tools, Tavily search, SummarizationMiddleware, and PostgreSQL checkpointer/store
3. `src/agent.py:stream_agent_turn()` is an async generator yielding `AgentEvent` dataclass instances (TOOL_START, TOOL_END, TOKEN, RESPONSE) consumed by the chat loop for real-time UI rendering
4. `src/memory.py` handles long-term memory extraction (via langmem) after each turn — best-effort, failures are silently logged
5. `src/context_tracker.py` provides token counting (tiktoken with char-based fallback)
6. `src/ui.py` wraps Rich + prompt-toolkit for all terminal output

**Persistence:** PostgreSQL backs both conversation checkpointing (`AsyncPostgresSaver`) and memory storage (`AsyncPostgresStore`). Memory uses the `("memories",)` namespace.

**Key patterns:**
- Fully async throughout (asyncio, async context managers for DB resources)
- Event streaming architecture — agent yields events, UI layer consumes them
- On Windows, `SelectorEventLoop` is required for psycopg compatibility (handled in `__main__` block)
- MCP server config is loaded from `mcp_servers.json`; failures are non-fatal
- Constants and thresholds live in `src/constants.py`

## Configuration

Required env vars: `DATABASE_URL`, `TAVILY_API_KEY`
Optional: `MODEL_NAME` (default: qwen3:14b), `MAX_CONTEXT_TOKENS` (default: 9000), `MCP_SERVERS_FILE`, `LOG_LEVEL`

## Dependencies

Uses `uv` with `pyproject.toml`. Key deps: langchain, langchain-ollama, langchain-mcp-adapters, langchain-tavily, langgraph, langgraph-checkpoint-postgres, langmem, rich, prompt-toolkit, psycopg, tiktoken.
