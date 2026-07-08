# LLM-Powered Reading Companion

A capstone project for the ["5-Day AI Agents: Intensive Vibe Coding Course With Google"](https://www.kaggle.com/competitions/5-day-ai-agents-intensive-vibecoding-course-with-google) course: an LLM-powered discussion agent that helps a reader engage with an uploaded
document — marking passages, discussing them with a tool-using agent,
keeping notes, and synthesizing a reading journal.

## Specification-driven development

**The specification in [`spec/`](spec/) is the single source of truth for
this project.** The code (once it exists) is treated as disposable and
re-generatable from the spec; any change to behavior must be reflected back
into the spec in the same change.

- [`spec/user_specification.md`](spec/user_specification.md) — what the
  product does, from a user's perspective.
- [`spec/technical_specification.md`](spec/technical_specification.md) —
  provider-neutral architecture, with concrete technology bindings isolated
  in §8 so the same spec can re-target a different stack.
- [`spec/features/`](spec/features/) — behavior specified as Gherkin
  scenarios.
- [`spec/contracts/`](spec/contracts/) — machine-readable API, data-model,
  and agent contracts (OpenAPI, JSON Schema, YAML).

## Agent configuration

This repository's AI-coding-agent configuration is tool-agnostic by design.
The canonical rule file lives at [`.agents/AGENTS.md`](.agents/AGENTS.md),
and project-scoped skills live under [`.agents/skills/`](.agents/skills/).
Both **Claude Code and Gemini CLI-style coding agents are supported
out of the box**: `CLAUDE.md` and `GEMINI.md` are symlinks to
`.agents/AGENTS.md`, and `.claude/skills` is a symlink to `.agents/skills`.
This means a single rule file and skill set drives either tool without
duplication or drift — update `.agents/AGENTS.md` and both tools pick up the
change immediately.

Design/architecture work is routed to a more capable model than routine
implementation via an `architect` subagent (see the "Model Selection"
section of `.agents/AGENTS.md`): `.claude/agents/architect.md` (Claude Code)
and `.gemini/agents/architect.md` + `.gemini/settings.json` (Gemini CLI).
Subagent file formats differ per tool, so these two files are kept in sync
by hand rather than symlinked.

## Repository structure

- `spec/` — the specification (source of truth)
- `.agents/` — canonical agent rules and skills
- `docs/` — course reference material and working notes (not tracked in git)
- `discussion-agent/` — the ADK-based discussion agent (tools, prompt-
  injection defenses, and untrusted-content wrapping implemented; now wired
  to `backend/`'s discussions endpoints over its reasoning_engine adapter
  routes)
- `backend/` — the FastAPI service (Cloud Run deployable) implementing
  [`spec/contracts/api.openapi.yaml`](spec/contracts/api.openapi.yaml);
  workspace lifecycle, document upload/parsing, notes CRUD, agent-backed
  discussions, and the suggestions/journal plain-LLM endpoints implemented
  so far
- `frontend/` — the React SPA (Vite + TypeScript + Tailwind CSS). Phase 1
  implemented: workspace lifecycle (create/redirect/cookie/delete),
  document upload, and the reading view with viewport tracking. Discussions,
  notes, passage-marking/suggestions, and journal UI remain unimplemented.
  Runs as its own dev server locally (proxied to `backend/` in dev); the
  production `StaticFiles` mount that serves its built assets from `backend/`
  (tech-spec §8's single-deployable model) has not been added yet — see
  `backend/README.md`.

## Status

- `discussion-agent/`: agent logic (tools, untrusted-content wrapping, eval
  dataset) implemented and invoked from `backend/` for real (over HTTP
  against a locally-running discussion-agent process). **Not yet deployed
  to Vertex AI Agent Engine** — `deployment_metadata.json` still has no real
  agent-runtime ID; do not treat this as a live production agent.
- `backend/`: workspace lifecycle (create/get/delete), document
  upload/parsing, notes CRUD, agent-backed discussions (create, list, get,
  follow-up turns), and the suggestions/journal plain-LLM endpoints
  (`POST .../suggestions`, `GET`/`POST .../journal`) implemented. These two
  call Gemini directly (`app/llm_client.py`) rather than going through
  `discussion-agent` — see `spec/contracts/agent-contract.yaml`'s
  `suggestions_call`/`journal_call`. A stored journal, when one exists, is
  now included in a live discussion turn's shared context
  (`discussion_context.journal`). `app/telemetry.py` adds OpenTelemetry
  tracing (HTTP server + outbound `httpx` spans) and structured logging,
  env-gated and off by default — see `backend/README.md`'s "Observability"
  section. `discussion-agent/` already had equivalent coverage from its
  `agents-cli` scaffold (`app/app_utils/telemetry.py`).
- `frontend/`: Phase 1 implemented against the plan in
  `.claude/plans/frosty-drifting-comet.md` — workspace lifecycle (new-user
  auto-create, returning-user cookie redirect, recovery from a
  deleted-workspace cookie, explicit new-workspace/delete actions, direct
  shared-URL access, not-found handling), document upload (`.txt`/`.md`,
  immutable once present), and a reading view rendering server-parsed blocks
  with debounced viewport tracking. Verified live against a real local
  `backend/` (in-memory store), including a real 429 rate-limit case with no
  retry-storm. Discussions, notes, passage-marking/suggestions, and journal
  UI are explicitly deferred to later phases, as is the production
  `StaticFiles` mount that would let `backend/` serve the built SPA.

## Continuous Integration

`.github/workflows/ci.yml` runs on every PR and push to `main`: lint
(`ruff`/`ty`/`codespell` for `discussion-agent/`, `ruff` for `backend/`,
`oxlint` + a `dangerouslySetInnerHTML` check for `frontend/`), hermetic
pytest for both Python projects (`discussion-agent`'s two real-model tests
are excluded via `-m "not live_model"`), the frontend's Vitest suite and
production build (`tsc -b && vite build`), a Playwright e2e suite exercising
`frontend/` against a real local `backend/` process, the repo's pre-commit
hooks (end-of-file-fixer, trailing-whitespace, Semgrep), a
dependency-vulnerability audit (`pip-audit` against each Python project's
resolved `uv.lock`, via `uv export`/`--no-deps --disable-pip` so no audited
package is ever installed or imported), and an eval-suite gate (`make
eval-gate` in `discussion-agent/`, blocking merge if the mean
`custom_response_quality` score drops below 4.0).

The e2e job starts `backend/` with `RATE_LIMIT_MAX_REQUESTS=30` (up from the
production default of 10/60s) — the full Playwright suite runs serially from
one IP, and the default ceiling is low enough that unrelated tests'
cumulative workspace creations would spuriously trip the same 429 that
`tests/e2e/zzz-rate-limit.spec.ts` deliberately exercises (that test loops up
to 50 requests, so it still reliably hits a raised ceiling).

`.github/dependabot.yml` opens weekly PRs bumping `uv.lock` pins for both
projects and the workflow's own GitHub Action versions — these still have to
pass the full CI gate (including the audit above) like any other PR.

The eval job authenticates to Vertex AI via Workload Identity Federation (no
static API key) — a dedicated `github-ci-eval` service account
(`roles/aiplatform.user` only) is impersonated through a Workload Identity
Pool whose OIDC provider trusts GitHub Actions tokens from this exact repo
only. This matches the same Vertex path (`GOOGLE_GENAI_USE_ENTERPRISE=true`)
`discussion-agent/.env.example` documents as the local default — Google AI
Studio's free tier grants **zero quota for `gemini-2.5-pro`**, so a
`GEMINI_API_KEY` alone can't run real eval traces against this project's
model; Vertex (with billing) is required either way. See
`docs/repo_configuration_progress.md` for the full GCP resource inventory
(project, service account, pool/provider names).

Not yet covered by CI: AI-assisted PR review — queued as a separate future
phase (see `docs/repo_configuration_progress.md`). Sandboxed agent
execution (the coding-tool sandbox, not application code) was deliberately
skipped as low-value for this project — not a queued item.

## Deployment descriptors

`backend/Dockerfile` and `backend/deployment/terraform/` describe (but do not
provision) the Cloud Run deployment per
[`spec/technical_specification.md §8`](spec/technical_specification.md#8-implementation-mapping):
a Cloud Run service, a private GCS bucket for raw documents, a Firestore
(Native mode) database, and a backend service account scoped to only the
roles it needs (Firestore, Vertex AI, logging, and object access to just
that one bucket — no project-wide storage role). `discussion-agent/` already
had scaffold-generated Terraform/`Dockerfile` of its own for Agent Engine.

Authoring these is **not** the same as deploying them — no `terraform apply`
has run and no image has been built and pushed to a registry; the Cloud Run
service has no live `discussion-agent` target to call yet either
(`DISCUSSION_AGENT_URL` has no real value — Agent Engine deployment remains
a separate, explicitly-gated future step). Only offline checks
(`terraform validate`, a local `docker build`) have been run — see
`docs/repo_configuration_progress.md`.

## License

[MIT](LICENSE)
