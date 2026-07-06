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
| `agents-cli install` | Install dependencies using uv                                                         |
| `agents-cli playground` | Launch local development environment                                                  |
| `agents-cli lint`    | Run code quality checks                                                               |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze, and more — see `agents-cli eval --help`) |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                                        |
| `agents-cli deploy`  | Deploy agent to Agent Runtime                                                                |
| `agents-cli publish gemini-enterprise` | Register deployed agent to Gemini Enterprise                    || [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | Launch A2A Protocol Inspector                                                        |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` - it auto-reloads on save.

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
