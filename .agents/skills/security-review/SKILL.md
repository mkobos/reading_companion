---
name: security-review
description: Runs a STRIDE threat-model review on request, or before a security-relevant change (new tool, new trust boundary, new untrusted input source), and updates spec/threat_model.md. Cross-references spec/features/security.feature and spec/contracts/agent-contract.yaml's untrusted-content rules rather than rebuilding from scratch. Does not activate for routine code changes with no new trust boundary (see spec-sync) or for direct .feature editing (see gherkin-specification-writing).
---

# Security Review (STRIDE)

This skill runs a STRIDE threat-model review against this project's actual
architecture and keeps `spec/threat_model.md` in sync with it. It
cross-references the existing security spec (`spec/features/security.feature`,
`spec/contracts/agent-contract.yaml`'s `untrusted_content_wrapping` and tool
constraints) rather than rebuilding a generic STRIDE analysis from scratch —
those are the starting inventory this repo's Planning Gate already points
to.

## STRIDE categories for this project

| Category | This project's boundary |
|---|---|
| Spoofing | Workspace identity — reachable only via an unguessable workspace URL/ID, no login |
| Tampering | Prompt injection via document text, notes, discussion history, journal, or web-search results |
| Repudiation | Anything that logs or accepts input without an audit trail (e.g. feedback submission) |
| Information Disclosure | Cross-workspace data leakage, system-instruction disclosure, untrusted-delimiter markup leaking into responses |
| Denial of Service | Expensive endpoints (workspace creation, document upload, discussion turns, suggestions, journal generation) without rate limiting |
| Elevation of Privilege | Agent tools gaining write access, cross-workspace access, or reaching internal services beyond their contracted scope |

## Workflow

1. Read `spec/features/security.feature`,
   `spec/contracts/agent-contract.yaml`'s untrusted-content and tool-constraint
   sections, and the actual code at the relevant trust boundary (e.g.
   `discussion-agent/app/agent.py`, `untrusted.py`, `context_assembly.py`,
   `document_search.py`, `web_search.py`, `fast_api_app.py`) — don't reason
   from the spec alone when code exists to check against it.
2. For each STRIDE category, identify which existing scenario or contract
   clause already covers it. If none does, that's a gap.
3. Update `spec/threat_model.md`: one subsection per STRIDE category,
   listing covered threats (each with a pointer to the covering scenario or
   contract clause) and open gaps (described factually — what the gap is
   and why it matters — without including a ready-made exploit payload).
4. Never fix a flagged gap in the same change as the threat-model update.
   Findings get raised for a separate, normal Planning-Gate-approved
   change, and this step must never touch test or implementation files.
5. Don't invent threats the architecture doesn't actually have — if a
   category has no real boundary yet (e.g. there is no authentication
   layer), say so rather than fabricating a section for it.
