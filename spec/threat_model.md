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

- Covered: none. No `security.feature` scenario addresses audit/log
  integrity.
- **Open gap**: `discussion-agent/app/fast_api_app.py`'s `/feedback`
  endpoint logs an arbitrary client-supplied payload via
  `logging_client.logger` with no visible rate limiting or workspace
  scoping, and no corresponding `security.feature` scenario covers it.

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
- **Open gap**: `discussion-agent/app/agent.py`'s module-level `root_agent`
  is built with a fixed placeholder sample document (not `blocks=[]`), and
  `fast_api_app.py` reuses this same `root_agent` for its A2A route with no
  per-workspace document binding yet. If this scaffold's FastAPI app were
  deployed as-is, every request would be served against the placeholder
  document rather than a workspace-specific one — already flagged in
  `docs/repo_configuration_progress.md` as "do not deploy before this is
  addressed," now also tracked here.

## Denial of Service

**Boundary**: expensive endpoints (workspace creation, document upload,
discussion turns, suggestions, journal generation).

- Covered (spec-only, backend not yet built — see scope note above):
  *"Expensive endpoints are rate limited"* (Scenario Outline covering all
  five endpoint types) and *"Read-only endpoints remain available under
  write limits"* (`security.feature`).
- **Open gap**: `/feedback` (see Repudiation above) is also not in the
  rate-limited endpoint list, so it has no DoS coverage either, spec'd or
  implemented.

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
