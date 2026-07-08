# Frontend

React SPA (Vite + TypeScript + Tailwind CSS) implementing the client side of
[`spec/contracts/api.openapi.yaml`](../spec/contracts/api.openapi.yaml).
Phase 1 only — see `.claude/plans/frosty-drifting-comet.md` (session-local,
not committed) for the approved scope and `docs/repo_configuration_progress.md`
for what shipped.

## Status

**Phase 1 implemented**: workspace lifecycle (new-user auto-create,
returning-user cookie redirect, recovery from a deleted-workspace cookie,
explicit new-workspace/delete actions, direct shared-URL access, not-found
handling), document upload (`.txt`/`.md`, immutable once present), and a
reading view rendering server-parsed blocks (never re-parsed client-side)
with debounced viewport tracking.

**Not yet implemented** (deferred to later phases): discussions, notes,
passage-marking/suggestions, reading journal UI, and the production
`StaticFiles` mount in `backend/app/main.py` that would let `backend/` serve
this app's built assets (tech-spec §8's single-deployable model) — this
service currently only runs via its own dev server.

## Layout

- `src/api/` — `types.ts` is generated from `api.openapi.yaml`
  (`npm run generate:types`); `client.ts` is a hand-written thin fetch
  wrapper (`ApiError` with status/message/`Retry-After`, no auto-retry);
  `workspaces.ts`/`documents.ts` are per-resource endpoint functions;
  `queries.ts` holds the TanStack Query hooks.
- `src/workspace/` — root-redirect/cookie logic, the workspace-scoped page
  shell, and the not-found page.
- `src/document/` — upload panel, reading view, block rendering, viewport
  tracking.
- `src/ui/`, `src/lib/` — small shared UI/utility helpers.
- `tests/unit/` — Vitest + React Testing Library (+ MSW for API mocking).
- `tests/e2e/` — Playwright specs, named after the `spec/features/*.feature`
  scenarios they satisfy (deterministic/untagged scenarios only — see
  `.agents/AGENTS.md`'s "Test Strategy: pytest-bdd vs Eval"; no `@eval`
  scenario is exercised here).

## Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start the Vite dev server on `:5173`, proxying `/api` to `http://localhost:8000` |
| `npm run build` | Type-check (`tsc -b`) and produce a production build in `dist/` |
| `npm run lint` | `oxlint` + a script asserting zero `dangerouslySetInnerHTML` usage in `src/` |
| `npm test` | Run the Vitest unit/component suite |
| `npm run test:e2e` | Run the Playwright suite (needs a local `backend/` running on `:8000`) |
| `npm run generate:types` | Regenerate `src/api/types.ts` from `spec/contracts/api.openapi.yaml` |

## Local development

Start `backend/` first (in-memory store/blob, no GCP credentials needed):

```bash
cd backend && uv run uvicorn app.main:app --reload --port 8000
```

Then, in `frontend/`:

```bash
npm install
npm run dev
```

Open `http://localhost:5173`. All API calls are same-origin `/api/*` paths,
proxied by Vite to the backend — no CORS configuration is needed for this
setup. See `.env.example` for the (non-secret) `VITE_API_BASE_URL` override
if pointing at a different backend origin directly (in which case the
backend's `ALLOW_ORIGINS` env var must be set instead).

## Security notes

Document/note/error text is always rendered as plain React text content —
never `dangerouslySetInnerHTML`, never re-parsed as Markdown/HTML — since
`backend/` has already flattened and neutralized the source document into
typed blocks. See `.claude/plans/frosty-drifting-comet.md` §6 for the full
Security Boundaries & Assertions list from this phase's Planning Gate.
