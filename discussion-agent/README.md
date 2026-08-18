# discussion-agent

The tool-using discussion agent from the LLM-Powered Reading Companion
(see `../spec/contracts/agent-contract.yaml`'s `discussion_agent` section
and `../spec/features/discussion.feature` / `security.feature`). A Socratic
reading companion, anchored to the reader's shared context (viewport, marked
passage, notes, discussion history, journal), with two read-only tools:
`search_document` (keyword search over the workspace's document) and
`web_search` (external fact lookup via Google Search grounding). All
untrusted content — the incoming context and both tools' results — is
wrapped in delimited data sections before it reaches the model, per the
contract's prompt-injection defense.

Agent generated with `agents-cli` version `1.0.0`

## Project Structure

```
discussion-agent/
├── app/                        # Core agent code
│   ├── agent.py                # Agent construction (build_discussion_agent)
│   ├── context_assembly.py     # Wraps the incoming discussion_context envelope
│   ├── document_search.py      # search_document tool (ephemeral SQLite FTS5)
│   ├── web_search.py           # web_search tool (Google Search grounding sub-agent)
│   ├── untrusted.py            # Untrusted-content wrapping (wrap_untrusted)
│   ├── fast_api_app.py         # FastAPI Backend server
│   └── app_utils/              # App utilities and helpers
├── tests/                      # Unit, pytest-bdd, integration, and eval tests
├── GEMINI.md                   # AI-assisted development guide
└── pyproject.toml              # Project dependencies
```

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development - project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management in this project) - [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI - Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services - [Install](https://cloud.google.com/sdk/docs/install)


## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8080` | Run the agent service locally. |
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Agent Runtime                                                                |
| `agents-cli publish gemini-enterprise` | Register deployed agent to Gemini Enterprise                    |
| `make eval` | Generate eval traces and grade them (wraps `agents-cli eval generate`/`grade`); output under `artifacts/` |
| `make eval-gate` | `make eval`, then fail if the mean `custom_response_quality` score is below 4.0 (used by CI to block merges) |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

### LLM backend selection (development only)

By default the agent talks to Gemini via Vertex AI (`LLM_BACKEND=vertex`,
also the default when unset). Two local-dev-only alternatives are
available, selected via `LLM_BACKEND` in `discussion-agent/.env` (see
`.env.example`):

| `LLM_BACKEND` | What it does | Setup |
|---|---|---|
| `vertex` (default) | Real Gemini via Vertex AI | GCP credentials |
| `ollama` | A local [Ollama](https://ollama.com/) server | `ollama pull <tool-calling-capable model>`, `ollama serve`, `uv sync --extra local-llm`, then set `OLLAMA_MODEL` (and optionally `OLLAMA_API_BASE`) |
| `fake` | A canned, deterministic response (`app/fake_model.py`) — no model, network, or credentials at all | nothing to install |

Run `agents-cli playground` as usual afterwards; it picks up the setting automatically.

Notes:
- This is **local-dev-only**. Vertex AI Agent Engine (the deployed target)
  cannot reach a developer's localhost and has no use for canned
  responses; no deploy path sets `LLM_BACKEND`, and both alternatives
  refuse to construct if one is detected anyway — neither is ever a
  production alternative.
- The `web_search` tool relies on Gemini/Vertex search grounding and
  cannot run against `ollama` or `fake`; under either, it stays registered
  (same name/signature) but always reports itself unavailable.
- `make eval` / `make eval-gate` refuse to run under `ollama` or `fake` —
  eval scores from a different or canned model say nothing about the
  deployed agent. Never use either to make an `@eval` scenario pass.
- `backend/`'s own `LLM_BACKEND` (for its direct suggestions/journal
  calls) is a separate, independent setting — see `backend/.env.example`.
  Set both if you want a fully local, no-cloud dev setup end to end.

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
