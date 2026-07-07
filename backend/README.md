# Backend

FastAPI service implementing the reading-companion backend from
[`spec/contracts/api.openapi.yaml`](../spec/contracts/api.openapi.yaml).

**Implemented so far**: workspace lifecycle (create/get/delete), document
upload/parsing, notes CRUD, agent-backed discussions (create, list, get,
follow-up turns), and the suggestions/journal plain-LLM endpoints. See
[`docs/repo_configuration_progress.md`](../docs/repo_configuration_progress.md)
for the phased plan.

Discussions are invoked against a **locally-running `discussion-agent`
process** (`DISCUSSION_AGENT_URL` in `.env.example`), over the same
`/api/reasoning_engine` / `/api/stream_reasoning_engine` routes Vertex AI
Agent Engine itself forwards calls to once deployed — `discussion-agent`
has not actually been deployed to Agent Engine yet, so both services must be
running locally for discussions to work end-to-end.

Suggestions and journal generation, by contrast, call Gemini **directly**
from `backend/` (`app/llm_client.py`) — no `discussion-agent` process
needed for those two endpoints, per
[`spec/contracts/agent-contract.yaml`](../spec/contracts/agent-contract.yaml)'s
`suggestions_call`/`journal_call` (plain LLM completions, not the agent).
They need Vertex AI or AI Studio credentials configured (see
`.env.example`); `app/llm_client.py`'s `LazyGenaiClient` defers actual
credential validation until the first real call, so the app still starts
without them.

## Layout

- `app/parsing.py` — Markdown (CommonMark, HTML disabled) and plain-text ->
  `Block` parsing, per
  [`spec/features/document-upload.feature`](../spec/features/document-upload.feature).
- `app/passages.py` — `Passage` anchor validation (unknown block ID,
  offset bounds, first-after-last, text-integrity self-check against the
  reconstructed range), shared by notes and future passage-anchored
  endpoints (discussions, suggestions).
- `app/store/` — `WorkspaceStore` Protocol; `FirestoreStore` (real) and
  `InMemoryWorkspaceStore` (test double).
- `app/blob/` — `BlobStore` Protocol; `GcsBlobStore` (real) and
  `InMemoryBlobStore` (test double).
- `app/rate_limit.py` — per-process sliding-window limiter (known
  single-instance limitation, see the Phase 1 plan's Security Boundaries
  section).
- `app/viewport.py` — resolves a viewport/anchor block-ID range to
  concatenated, marked-up block text, per
  [`spec/contracts/agent-contract.yaml`](../spec/contracts/agent-contract.yaml)'s
  `viewport_text` shared type.
- `app/discussion_agent_client.py` — HTTP client for `discussion-agent`'s
  reasoning_engine adapter surface (session creation + turn streaming);
  never wraps/escapes content itself, that stays `discussion-agent`'s job.
- `app/untrusted.py` — `wrap_untrusted`/`strip_untrusted_markup`, a
  byte-for-byte port of `discussion-agent/app/untrusted.py`'s
  prompt-injection defense, for backend's own direct LLM calls.
- `app/llm_client.py` — direct (non-agent) Gemini calls for suggestions and
  journal synthesis, wrapping `google.genai.Client`.
- `app/llm_prompts.py` — prompt assembly (untrusted-content wrapping,
  journal's 100k-char truncation) for the two calls above.
- `app/routers/` — the API routes.

## Commands

```bash
uv sync                                        # install dependencies
uv run pytest tests/unit tests/api tests/bdd   # hermetic (no external deps)
uv run uvicorn app.main:app --reload           # run locally
```

By default (no `GOOGLE_CLOUD_PROJECT`/`FIRESTORE_EMULATOR_HOST` or
`GCS_BUCKET_NAME` set), the app uses the in-memory store/blob fakes — useful
for a quick local run without any GCP setup. See `.env.example`.

### Firestore integration tests

`tests/integration/test_firestore_store.py` runs against the real Firestore
emulator (needs a JRE) and skips itself if one isn't reachable:

```bash
export PATH="/opt/homebrew/opt/openjdk/bin:$PATH"   # if `java -version` fails
gcloud emulators firestore start --host-port=localhost:8080 &
export FIRESTORE_EMULATOR_HOST=localhost:8080
uv run pytest tests/integration
```
