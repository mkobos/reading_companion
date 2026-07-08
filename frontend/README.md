# Frontend

React SPA (Vite + TypeScript + Tailwind CSS) implementing the client side of
[`spec/contracts/api.openapi.yaml`](../spec/contracts/api.openapi.yaml).
Phases 1-2 — see `docs/repo_configuration_progress.md` for what shipped.

## Status

**Phase 1 implemented**: workspace lifecycle (new-user auto-create,
returning-user cookie redirect, recovery from a deleted-workspace cookie,
explicit new-workspace/delete actions, direct shared-URL access, not-found
handling), document upload (`.txt`/`.md`, immutable once present), and a
reading view rendering server-parsed blocks (never re-parsed client-side)
with debounced viewport tracking.

**Phase 2 implemented**: a discussions panel alongside the reading view
(`src/discussion/`) — start a no-anchor "ask about this document" discussion
or continue an existing one, synchronous request/response per turn (5-30s,
no streaming), pending/error/Resend states, and a plain-text tool-call
trace. The reading view's tracked viewport is threaded into every
create-discussion/post-turn call via `ReadingView`'s new optional
`onViewportChange` prop.

**Not yet implemented** (deferred to later phases): notes,
passage-marking/suggestions, reading journal UI, and the production
`StaticFiles` mount in `backend/app/main.py` that would let `backend/` serve
this app's built assets (tech-spec §8's single-deployable model) — this
service currently only runs via its own dev server.

## Layout

- `src/api/` — `types.ts` is generated from `api.openapi.yaml`
  (`npm run generate:types`); `client.ts` is a hand-written thin fetch
  wrapper (`ApiError` with status/message/`Retry-After`, no auto-retry);
  `workspaces.ts`/`documents.ts`/`discussions.ts` are per-resource endpoint
  functions; `queries.ts` holds the TanStack Query hooks.
- `src/workspace/` — root-redirect/cookie logic, the workspace-scoped page
  shell, the not-found page, and `DocumentWorkspace.tsx` (the two-column
  reading-view + discussion-panel shell shown once a document exists).
- `src/document/` — upload panel, reading view, block rendering, viewport
  tracking. `ReadingView`'s optional `onViewportChange` prop (Phase 2)
  reports the tracked viewport to a parent without lifting
  `useViewportTracker` itself.
- `src/discussion/` — the discussions UI: `MessageComposer` (submit/pending/
  error+Resend states; input clears only on success), `mapComposerError`
  (429/502/network-drop -> display text, never a raw exception message),
  `PendingIndicator`, `TurnItem`/`TurnList` (agent responses always render
  as plain, whitespace-preserved text — never `dangerouslySetInnerHTML`),
  `ToolCallTrace` (plain-text tool-use summaries), `DiscussionList`/
  `DiscussionListView` (start a discussion), `DiscussionThread` (continue
  one), and `DiscussionPanel` (switches between the two; local component
  state, no route/URL param).
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
