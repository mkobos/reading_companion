# Backend

FastAPI service implementing the reading-companion backend from
[`spec/contracts/api.openapi.yaml`](../spec/contracts/api.openapi.yaml).

**Implemented so far**: workspace lifecycle (create/get/delete), document
upload/parsing, and notes CRUD. Agent-backed discussions, suggestions, and
journal are not implemented yet — see
[`docs/repo_configuration_progress.md`](../docs/repo_configuration_progress.md)
for the phased plan.

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
