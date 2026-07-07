# Threat Model (STRIDE)

Maintained by the `security-review` skill
(`.agents/skills/security-review/SKILL.md`). Cross-references
`spec/features/security.feature` and `spec/contracts/agent-contract.yaml`'s
`untrusted_content_wrapping`/tool constraints as the existing inventory,
rather than restating STRIDE generically. Findings here are documented, not
fixed in the same change — any remediation goes through this repo's
Planning Gate as its own change.

**Scope note**: only `discussion-agent/` exists today (the ADK agent
itself, plus the `agents-cli`-scaffolded `app/fast_api_app.py` wrapper it
ships with). The "real" workspace/document/notes backend that
`spec/features/security.feature`'s workspace-isolation and rate-limiting
scenarios describe has not been built yet — those scenarios are
forward-looking spec for that future service, not yet implementable or
testable. `spec/features/document-upload.feature` (upload-safety,
Tampering-relevant) was not reviewed in this pass.

## Spoofing

**Boundary**: workspace identity — reachable only via an unguessable
workspace URL/ID, no login.

- Covered: *"Workspaces are unreachable without their URL"* and
  *"Workspace IDs are cryptographically secure"*
  (`spec/features/security.feature`) — ≥128 bits of randomness, CSPRNG-
  generated, no sequential/predictable IDs exposed.
- Not a gap, by design: there is no authentication layer. Anyone holding a
  workspace URL has full access to it — this is the app's stated security
  model (URL-as-secret), not an unaddressed threat.

## Tampering

**Boundary**: prompt injection via document text, notes, discussion
history, journal, or web-search results reaching the discussion agent.

- Covered: *"Instructions embedded in a document are not obeyed"*,
  *"Injection attempts in notes are inert"*, *"Injection attempts in web
  search results are inert"*, and *"All untrusted content is delimited
  uniformly"* (`spec/features/security.feature`), backed by
  `agent-contract.yaml`'s `untrusted_content_wrapping` rule/envelope/
  escaping and implemented in `discussion-agent/app/untrusted.py`
  (`wrap_untrusted`) and `context_assembly.py`.
- Not reviewed in this pass: document-upload-time tampering
  (`spec/features/document-upload.feature`).

## Repudiation

**Boundary**: anything that accepts or logs input without an audit trail.

- Covered: none beyond the item below. No other `security.feature` scenario
  addresses audit/log integrity.
- Previously an open gap, now fixed: `discussion-agent/app/fast_api_app.py`'s
  `/feedback` endpoint used to log an arbitrary client-supplied payload via
  `logging_client.logger` with no rate limiting. Now rate-limited per client
  IP via `discussion-agent/app/rate_limit.py`'s `SlidingWindowRateLimiter`
  (ported from `backend/app/rate_limit.py`, same per-process/multi-instance
  caveat applies), returning 429 with `Retry-After` once exceeded. Covered by
  `security.feature`'s new *"Feedback submission is rate limited"* scenario.
  There is still no workspace scoping — `/feedback` has no workspace concept
  to scope to (it's not a workspace-scoped endpoint) — so this is not a gap
  relative to the endpoint's actual design.

## Information Disclosure

**Boundary**: cross-workspace data leakage, system-instruction disclosure,
untrusted-delimiter markup leaking into responses.

- Covered: *"...the response does not disclose system instructions"*,
  *"no API response ever includes data belonging to 'W2'"*, *"no endpoint
  enumerates or lists workspace IDs"* (`security.feature`), and
  *"Untrusted delimiter markup never leaks into the visible response"* —
  enforced server-side by `_strip_leaked_untrusted_markup`
  (`discussion-agent/app/agent.py`) regardless of model compliance (already
  implemented and verified per `docs/repo_configuration_progress.md`).
- **Open gap, re-scoped after further investigation** (was previously
  described as an undeployed-scaffold risk; that undersold it):
  `discussion-agent/app/agent.py`'s module-level `root_agent`/`app` is built
  once at import time and reused by **two** real HTTP entry points —
  `attach_a2a_routes` (`app/app_utils/a2a.py`) *and*
  `attach_reasoning_engine_routes` (`app/app_utils/reasoning_engine_adapter.py`,
  serving `/api/reasoning_engine` and `/api/stream_reasoning_engine`). The
  second pair are the routes `backend/`'s `DiscussionAgentClient` actually
  calls in production (per `docs/repo_configuration_progress.md`'s Phase 3
  notes) — this is not a dead scaffold path. Document *text* delivered via
  the wire envelope's `context` field is unaffected (it already carries the
  real workspace's content, wrapped by `assemble_context`); only the
  `search_document` **tool**, whose blocks are bound once at agent
  construction, is affected — if the model calls it for content outside the
  supplied viewport, it searches whatever `root_agent` was built with,
  regardless of which real workspace is asking.
  - **Stopgap applied**: `root_agent` is now built with `blocks=[]` instead
    of a fixed sample document, so `search_document` returns nothing rather
    than another workspace's (or a fixed placeholder's) content. This
    closes the information-disclosure angle but is not full remediation.
  - **Known regression from the stopgap**: the eval harness's
    `document-search-outside-viewport` case (`tests/eval/datasets/basic-dataset.json`)
    relied on `root_agent`'s old placeholder blocks containing "veil of
    ignorance" text findable via `search_document` — that was always a gap
    in the eval setup (per `docs/repo_configuration_progress.md`: "no caller
    yet combines `assemble_context(context)` + `user_message`... outside of
    tests/eval authoring"), now exposed as a real score drop (5/5 → 1/5,
    confirmed via `make eval-generate && make eval-grade`; all other cases,
    including every injection case, unchanged at 5/5). Not fixed here — the
    eval case needs its own prompt/harness redesign once real per-workspace
    document wiring exists for the eval path to exercise.
  - **Deferred full fix** (not attempted here, its own future Planning-Gate
    change): thread real document blocks through the wire envelope
    (alongside `context`) so an agent can be constructed per session/
    per-workspace, rather than reused from one module-level instance shared
    by every caller.

## Denial of Service

**Boundary**: expensive endpoints (workspace creation, document upload,
discussion turns, suggestions, journal generation).

- Covered (spec-only, backend not yet built — see scope note above):
  *"Expensive endpoints are rate limited"* (Scenario Outline covering all
  five endpoint types) and *"Read-only endpoints remain available under
  write limits"* (`security.feature`).
- Previously an open gap, now fixed: `/feedback` (see Repudiation above) is
  now rate limited too, covered by the same new scenario.

## Elevation of Privilege

**Boundary**: agent tools gaining write access, cross-workspace access, or
reaching internal services beyond their contracted scope.

- Covered: *"Tools limit the blast radius of a successful injection"* and
  *"Agent tools cannot cross workspace boundaries"* (`security.feature`),
  backed by `agent-contract.yaml`'s `read_only`/`no_write_tools`/
  `no_cross_workspace_access` constraints. `document_search.py`'s
  `search_document` binds `blocks` via closure at construction time (not a
  model-controllable parameter), so cross-workspace access is impossible by
  construction, not just untested — see the existing test-review notes in
  `docs/repo_configuration_progress.md`.
- No current gap. This category should be re-checked (that's exactly what
  this skill's "before adding a new tool" trigger is for) whenever a new
  tool is proposed — e.g. the Firestore-write example in this skill's own
  eval cases would need this section revisited before merging.
