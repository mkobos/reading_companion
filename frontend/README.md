# Frontend

React SPA (Vite + TypeScript + Tailwind CSS) implementing the client side of
[`spec/contracts/api.openapi.yaml`](../spec/contracts/api.openapi.yaml).
Phases 1-3 — see `docs/repo_configuration_progress.md` for what shipped.

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

**Phase 3 implemented**: the right column is now a `Discussions | Notes |
Journal` tab switch in `DocumentWorkspace.tsx` (no new routes — tab state is
local, same precedent as Phase 2's discussion selection). Notes CRUD
(`src/note/`) anchored to a passage, with an inline indicator on the
anchored block in the reading view. Passage-marking
(`src/document/passageFromSelection.ts`, a pure selection→`Passage`
converter that mirrors `backend/app/passages.py`'s code-point-offset and
multi-block `"\n"`-join reconstruction exactly, so a selection the client
accepts is always accepted by the backend) drives a suggestions popover
(`src/document/SuggestionsPopover.tsx`): 3-5 questions from
`POST .../suggestions`, falling back to a free-form question input on a 503.
Reading journal (`src/journal/`): a generate/regenerate button; `GET` 404 is
treated as an empty/CTA state, never an error; content renders via
`react-markdown` with no `rehype-raw`/`allowDangerousHtml` and links
stripped to plain text — this is the app's first Markdown-rendering
surface. Marking a passage and dismissing without acting persists nothing
(no note, no discussion, no mark record).

**Not yet implemented**: the production `StaticFiles` mount in
`backend/app/main.py` that would let `backend/` serve this app's built
assets (tech-spec §8's single-deployable model) — this service currently
only runs via its own dev server.

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
  `useViewportTracker` itself; its optional `onPassageMarked` prop (Phase 3)
  reports a selection-derived `Passage` the same way.
  `passageFromSelection.ts` is a pure, DOM-selection→`Passage` converter
  (no React) — the load-bearing piece that must stay in lockstep with
  `backend/app/passages.py`'s validation/reconstruction rules.
  `SuggestionsPopover` renders the ephemeral suggested-questions UI for a
  marked passage.
- `src/discussion/` — the discussions UI: `MessageComposer` (submit/pending/
  error+Resend states; input clears only on success), `mapComposerError`
  (429/502/network-drop -> display text, never a raw exception message),
  `PendingIndicator`, `TurnItem`/`TurnList` (agent responses always render
  as plain, whitespace-preserved text — never `dangerouslySetInnerHTML`),
  `ToolCallTrace` (plain-text tool-use summaries), `DiscussionList`/
  `DiscussionListView` (start a discussion), `DiscussionThread` (continue
  one), and `DiscussionPanel` (switches between the two; local component
  state, no route/URL param).
- `src/note/` — notes CRUD: `NotesTab`/`NoteItem`/`NoteComposer` (keeps input
  open and the message visible on failure, same pattern as
  `MessageComposer`), `mapNoteError`, and `NoteIndicator` (rendered inline in
  `ReadingView` on a note's anchored block).
- `src/journal/` — `JournalTab` (generate/regenerate, 404→CTA, 409→"nothing
  to reflect on yet", 503 keeps the previously-shown journal visible),
  `JournalMarkdown` (the `react-markdown` wrapper — no `rehype-raw`, no
  `allowDangerousHtml`, links rendered as plain text), `mapJournalError`.
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

Document/note/suggestion/error text is always rendered as plain React text
content — never `dangerouslySetInnerHTML`, never re-parsed as Markdown/HTML
— since `backend/` has already flattened and neutralized the source
document into typed blocks. The one exception is the reading journal
(`src/journal/JournalMarkdown.tsx`), which is genuinely Markdown and is the
app's first Markdown-rendering surface: it uses `react-markdown` with
**no** `rehype-raw`/`allowDangerousHtml` (so raw HTML in the source never
becomes live DOM) and renders links as inert plain text (no `<a>` tag, no
href/scheme to worry about). A passage anchor the client submits is never
trusted server-side — `backend/app/passages.py` re-derives and compares the
text itself, and its rejection messages are static strings that never echo
document content back. See `.claude/plans/frosty-drifting-comet.md` §6 (Phase 1)
and `.claude/plans/glimmering-orbiting-narwhal.md` §5 (Phase 3) for the full
Security Boundaries & Assertions lists from each phase's Planning Gate.
