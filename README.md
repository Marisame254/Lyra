# Lyra

Agente conversacional de terminal que integra herramientas del Model Context Protocol (MCP), busqueda web con Tavily y multiples proveedores de LLM (Ollama, OpenAI, DeepSeek). Incluye memoria persistente, checkpointing en PostgreSQL y una interfaz de terminal enriquecida.

## Caracteristicas

- **Conversaciones persistentes** — Hilos guardados en PostgreSQL, reanudables en cualquier momento
- **Multi-proveedor** — Soporte para Ollama (local), OpenAI y DeepSeek; cambio de modelo en caliente con `/model`
- **Herramientas MCP** — Integracion con servidores MCP via stdio o HTTP; habilitar/deshabilitar sin reiniciar
- **Busqueda web** — Busqueda en tiempo real con Tavily (opcional)
- **Memoria a largo plazo** — Extraccion automatica de hechos relevantes de las conversaciones
- **Gestion de contexto** — Resumen automatico al superar el limite de tokens, con visualizacion de uso
- **Aprobacion de herramientas** — Flujo HITL para aprobar o rechazar llamadas a herramientas sensibles
- **Interfaz rica** — Terminal con Rich, markdown renderizado y streaming en tiempo real

## Requisitos previos

- Python 3.13+
- PostgreSQL corriendo localmente
- [uv](https://docs.astral.sh/uv/) como gestor de paquetes
- Node.js (para servidores MCP basados en stdio, ej. `@modelcontextprotocol/server-filesystem`)
- Al menos uno de los siguientes:
  - [Ollama](https://ollama.com/) corriendo localmente con un modelo descargado
  - API key de OpenAI o DeepSeek

## Instalacion

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd Lyra

# Instalar dependencias
uv sync

# O con pip (instala el comando `lyra`)
pip install -e .
```

## Configuracion

Crear un archivo `.env` en la raiz del proyecto (ver `.env.example`):

```env
# Requerido
DATABASE_URL=postgresql://usuario:password@localhost:5432/agentes

# Opcionales — busqueda web y modelos en la nube
TAVILY_API_KEY=tu-api-key
OPENAI_API_KEY=tu-api-key
DEEPSEEK_API_KEY=tu-api-key

# Modelo por defecto (formato: provider/modelo o solo nombre para Ollama)
MODEL_NAME=qwen3:14b

# Limite de contexto en tokens
MAX_CONTEXT_TOKENS=9000

# Archivo de configuracion MCP
MCP_SERVERS_FILE=mcp_servers.json

# Nivel de logging (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=WARNING
```

> **Nota:** No uses la palabra `export` en el `.env`. Escribe solo `VARIABLE=valor`.

### Servidores MCP

Configurar los servidores en `mcp_servers.json`. Soporta transporte `stdio` y `http`:

```json
{
  "filesystem": {
    "transport": "stdio",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
  },
  "mi-servidor": {
    "transport": "http",
    "url": "http://127.0.0.1:8000/mcp",
    "headers": {
      "Authorization": "Bearer mi-token"
    }
  }
}
```

## Uso

```bash
# Con el comando instalado
lyra

# O directamente
python main.py
```

### Seleccion de modelo

El formato de modelo es `provider/nombre`. Los nombres sin `/` se tratan como modelos de Ollama.

```
qwen3:14b              → Ollama (local)
ollama/llama3:8b       → Ollama (local)
openai/gpt-4o          → OpenAI
deepseek/deepseek-chat → DeepSeek
```

### Comandos disponibles

| Comando | Descripcion |
|---------|-------------|
| `/new` | Iniciar un nuevo hilo de conversacion |
| `/threads` | Ver y reanudar conversaciones anteriores |
| `/context` | Mostrar desglose de uso de tokens |
| `/model [nombre]` | Cambiar modelo en caliente (sin args: lista modelos disponibles) |
| `/memory` | Listar memorias guardadas |
| `/memory search <query>` | Buscar en la memoria |
| `/memory add <texto>` | Agregar una memoria manualmente |
| `/memory delete <n>` | Eliminar memoria por numero |
| `/memory clear` | Borrar todas las memorias |
| `/mcp` | Listar servidores MCP y su estado |
| `/mcp enable <nombre>` | Habilitar un servidor MCP |
| `/mcp disable <nombre>` | Deshabilitar un servidor MCP |
| `/mcp reload` | Recargar configuracion MCP |
| `/help` | Mostrar ayuda |
| `/exit` | Salir de la aplicacion |

## Arquitectura

```
Lyra/
├── main.py                 # Punto de entrada, loop de chat y manejo de comandos
├── src/
│   ├── agent.py            # Construccion del agente LangGraph y streaming de eventos
│   ├── config.py           # Carga de configuracion y variables de entorno
│   ├── constants.py        # Constantes y enums centralizados
│   ├── context_tracker.py  # Conteo de tokens y visualizacion de contexto
│   ├── memory.py           # Extraccion y recuperacion de memoria a largo plazo
│   ├── providers.py        # Factory de LLMs (Ollama, OpenAI, DeepSeek)
│   ├── tools.py            # Herramienta ask_user para interaccion HITL
│   └── ui.py               # Componentes de interfaz de terminal (Rich)
├── mcp_servers.json        # Configuracion de servidores MCP
├── pyproject.toml          # Dependencias y metadata del proyecto
└── .env                    # Variables de entorno (no incluido en git)
```

### Stack tecnologico

| Componente | Tecnologia |
|------------|------------|
| Orquestacion | LangChain + LangGraph |
| Modelos locales | Ollama |
| Modelos en la nube | OpenAI, DeepSeek |
| Busqueda web | Tavily |
| Herramientas externas | Model Context Protocol (MCP) |
| Persistencia | PostgreSQL via psycopg async |
| Memoria | langmem |
| Interfaz | Rich + prompt-toolkit |

## Licencia

MIT
