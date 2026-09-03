# AfyaPlus Service Platform — Week 6 Capstone

A reproducible health-logistics platform combining a secured FastAPI service,
an MCP logistics server, and a budget-bounded LangChain agent.

## Architecture

```text
Client
  |
  | HTTP + JWT + X-Trace-ID
  v
FastAPI service (service/main.py)
  |-- /health              public
  |-- /token               login
  |-- /triage              clinician role
  `-- /agent/query         clinician or coordinator role
          |
          | MCP over stdio
          v
    MCP server (mcp_server/server.py)
      |-- check_stock tool
      |-- plan_delivery_route tool
      `-- clinics://directory resource
```

The agent defaults to `offline` mode. This mode still discovers and invokes the
real MCP tools over stdio but uses deterministic orchestration instead of a paid
LLM. `online` mode uses LangChain with an OpenAI-compatible endpoint.

## Quick start

Requirements: Python 3.12 and a POSIX shell.

```bash
cd wk6_capstone_project
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Replace `JWT_SECRET` in `.env` with a generated secret:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Start the API:

```bash
uvicorn service.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` or run, in another terminal:

```bash
scripts/curl_evidence.sh
scripts/agent_evidence.sh
python scripts/mcp_evidence.py
pytest -q
```

Demo credentials are intentionally local-only:

| Username | Password | Role |
|---|---|---|
| `clinician` | `clinical2026` | clinician |
| `coordinator` | `logistics2026` | coordinator |

Replace the demo identity store before any real deployment. Never place patient
identifiers or production inventory in this demonstration dataset.

## Container build and semantic release

The source version, image tag, OCI label, and Git tag are all `1.0.0` / `v1.0.0`.

```bash
docker build --build-arg APP_VERSION=1.0.0 -t afyaplus-service:1.0.0 .
docker run --rm --env-file .env -p 8000:8000 afyaplus-service:1.0.0
docker image inspect afyaplus-service:1.0.0 \
  --format 'bytes={{.Size}} version={{index .Config.Labels "org.opencontainers.image.version"}}'
```

Secrets are injected only at runtime through `--env-file`; `.env` is excluded
from both Git and the Docker build context. The container runs as an unprivileged
user with a health check. `docker compose up --build` provides the equivalent flow.

Record the measured image size in `docs/engineering-report.md`; image size depends
on Docker version, architecture, and package wheels and must not be guessed.

## Online agent (optional, paid)

Keep the default offline mode for grading without credits. To use OpenRouter:

```dotenv
AGENT_MODE=online
OPENROUTER_API_KEY=your-key
MODEL_BASE_URL=https://openrouter.ai/api/v1
MODEL_NAME=openai/gpt-4o-mini
```

The online agent has `recursion_limit=6`, a 20-second request timeout, one retry,
and temperature zero. Do not commit `.env`. A live run sends the prompt and tool
results to the configured provider and may incur charges.

## Full evidence bundle

With the API stopped and `.env` configured:

```bash
scripts/run_evidence.sh
```

This records HTTP responses, API/MCP logs, agent transcripts, and pytest results
under ignored `evidence/runtime/`. Follow `docs/screenshots/README.md` to capture
authentic screenshots for submission. Bearer tokens can appear in terminal output;
review and redact tokens before sharing evidence publicly.

## Fallback paths

- No Docker: use the Python virtual-environment quick start.
- No OpenAI/OpenRouter credits: retain `AGENT_MODE=offline`; MCP is still exercised.
- No MCP Inspector: run `python scripts/mcp_evidence.py` and `pytest tests/test_mcp_core.py`.
- No network: all offline tests and application paths use local data only after
  dependencies have been installed.
- Provider outage: `/agent/query` returns a controlled `503`; `/health`, `/token`,
  `/triage`, and the MCP server remain independently testable.

## Repository layout

```text
agent/          MCP-consuming LangChain integration and API router
mcp_server/     MCP transport, pure logistics operations, and clinic data
service/        configuration, JWT/RBAC, health, and triage API
tests/          pytest coverage for auth, validation, MCP, and agent behavior
scripts/        reproducible curl, MCP, and evidence runners
docs/           report, stakeholder memo, contribution and screenshot guidance
evidence/       evidence policy; generated runtime evidence is ignored
```

See [CONTRIBUTING.md](docs/CONTRIBUTING.md),
[engineering-report.md](docs/engineering-report.md), and
[memo.md](docs/memo.md).

