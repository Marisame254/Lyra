# Agent with MCP

Agente conversacional de terminal que integra herramientas del Model Context Protocol (MCP), busqueda web con Tavily y modelos LLM locales via Ollama. Incluye memoria persistente, checkpointing en PostgreSQL y una interfaz de terminal enriquecida.

## Caracteristicas

- **Conversaciones persistentes** - Hilos de conversacion guardados en PostgreSQL, reanudables en cualquier momento
- **Herramientas MCP** - Integracion con servidores MCP (filesystem, etc.) para dar capacidades al agente
- **Busqueda web** - Busqueda en tiempo real con Tavily
- **Memoria a largo plazo** - Extraccion automatica de hechos relevantes de las conversaciones
- **Gestion de contexto** - Resumen automatico al superar el limite de tokens, con visualizacion de uso
- **Interfaz rica** - UI de terminal con Rich, markdown renderizado y visualizacion de llamadas a herramientas en tiempo real

## Requisitos previos

- Python 3.13+
- PostgreSQL
- [Ollama](https://ollama.com/) corriendo localmente con un modelo descargado (por defecto: `qwen3:14b`)
- [Tavily API key](https://tavily.com)
- Node.js (para servidores MCP basados en stdio)

## Instalacion

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd agent_with_mcp

# Instalar dependencias con uv
uv sync

# O con pip
pip install -e .
```

## Configuracion

Crear un archivo `.env` en la raiz del proyecto:

```env
DATABASE_URL=postgresql://usuario:password@localhost:5432/agentes
TAVILY_API_KEY=tu-api-key

# Opcionales
MODEL_NAME=qwen3:14b
MAX_CONTEXT_TOKENS=9000
MCP_SERVERS_FILE=mcp_servers.json
```

### Servidores MCP

Configurar los servidores MCP en `mcp_servers.json`:

```json
{
  "servers": {
    "filesystem": {
      "transport": "stdio",
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "."]
    }
  }
}
```

## Uso

```bash
python main.py
```

### Comandos disponibles

| Comando | Descripcion |
|---------|-------------|
| `/new` | Iniciar un nuevo hilo de conversacion |
| `/threads` | Ver y reanudar conversaciones anteriores |
| `/context` | Mostrar desglose de uso de tokens |
| `/exit` | Salir de la aplicacion |

## Arquitectura

```
agent_with_mcp/
├── main.py                 # Punto de entrada y loop principal
├── src/
│   ├── agent.py            # Construccion del agente y streaming de eventos
│   ├── config.py           # Carga de configuracion y variables de entorno
│   ├── context_tracker.py  # Conteo de tokens y visualizacion de contexto
│   ├── memory.py           # Extraccion y recuperacion de memoria a largo plazo
│   └── ui.py               # Componentes de interfaz de terminal
├── mcp_servers.json        # Configuracion de servidores MCP
├── pyproject.toml          # Dependencias y metadata del proyecto
└── .env                    # Variables de entorno
```

### Stack tecnologico

| Componente | Tecnologia |
|------------|------------|
| Framework LLM | LangChain + LangGraph |
| Modelo local | Ollama |
| Busqueda web | Tavily |
| Herramientas externas | Model Context Protocol (MCP) |
| Persistencia | PostgreSQL (psycopg async) |
| Memoria | langmem |
| Interfaz | Rich + prompt-toolkit |

## Dependencias principales

```
langchain >= 1.2.10
langchain-ollama >= 1.0.1
langchain-mcp-adapters >= 0.1.0
langchain-tavily >= 0.2.17
langgraph >= 0.4.0
langgraph-checkpoint-postgres >= 3.0.4
langmem >= 0.0.20
rich >= 14.0.0
prompt-toolkit >= 3.0.50
psycopg[binary] >= 3.2.0
python-dotenv >= 1.1.0
```

## Licencia

MIT
