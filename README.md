# Agent Hub

A simple multi-agent system managed with `uv`. Features a web interface built with FastAPI and agents that communicate using Redis pub/sub and generate responses via OpenRouter API (using `minimax` models by default).

## Features

- **Web Interface**: Simple chat UI to observe and interact with agents.
- **Multi-Agent System**:
  - **Alice**: An optimistic, enthusiastic AI.
  - **Bob**: A cynical, sarcastic AI.
  - **Coordinator**: Moderates the discussion and orchestrates stopping conditions.
- **Pub/Sub Communication**: Core infrastructure handled by Redis.
- **OpenRouter Support**: Uses OpenRouter models for agent intelligence.

## Prerequisites

1. Install `uv`: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
2. Install and run **Redis** locally (default port `6379`).
3. Get an API key from [OpenRouter](https://openrouter.ai/).

## Setup & Installation

The project uses `uv` for dependency management:
```bash
# Optional but recommended: set up your OPENROUTER_API_KEY
export OPENROUTER_API_KEY="your_openrouter_api_key_here"

# Sync/install dependencies via uv
uv sync
```

## Running the Application

To run the full system, you need at least two terminals.

### 1. Start the FastAPI Web Server
This serves the frontend UI and the REST API.
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*Access the web interface at: [http://localhost:8000](http://localhost:8000)*

### 2. Start the Agents
This boots up Alice, Bob, and the Coordinator so they can begin their interaction.
```bash
# Ensure API key is set in this terminal session!
export OPENROUTER_API_KEY="your_openrouter_api_key_here"

uv run python app/run_agents.py
```

#### Run with WildEdge Instrumentation (Optional)
If you want to monitor the agent instances with [WildEdge](https://github.com/wild-edge/wildedge-python), prefix the command with `wildedge run`:
```bash
export WILDEDGE_DSN="https://<secret>@ingest.wildedge.dev/<key>"
uv run wildedge run --integrations openai -- python app/run_agents.py
```

## Adding New Agents

1. Create a `[name].md` file in the `agents/` directory containing the agent's persona prompt.
2. Initialize it as a `RedisOpenRouterAgent` in `app/run_agents.py` and add its task to the asyncio gather list.
