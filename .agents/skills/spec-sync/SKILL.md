---
name: spec-sync
description: Checks that a code change under discussion-agent/app/ (or a future backend/ or frontend/) that alters agent behavior, tool signatures, or contract fields also updates the matching spec/features/*.feature, spec/contracts/*.yaml, README, or CHANGELOG in the same change. Does not activate for spec-only edits (see gherkin-specification-writing) or non-code discussion.
---

# Spec Sync

This skill checks that a code change kept `spec/` in sync, enforcing
`.agents/AGENTS.md`'s rule that the specification is the single source of
truth and must be updated every time the project changes. It is a judgment
check, not a file-diffing script: whether a spec update is *needed* depends
on what the change actually does, not just which paths it touches.

## What counts as a spec-relevant change

| Code change | Spec artifact to check |
|---|---|
| New or changed tool, tool signature, or tool-scoping behavior | `spec/contracts/agent-contract.yaml` |
| New or changed agent instruction/behavior (e.g. untrusted-content handling, refusal behavior) | `spec/contracts/agent-contract.yaml`, relevant `spec/features/*.feature` |
| New or changed API field, request/response shape | `spec/contracts/api.openapi.yaml`, `spec/contracts/data-model.yaml` |
| New or changed user-facing flow or scenario | `spec/features/*.feature` |
| Anything a new contributor or another agent would need to know to use the project | `README.md`, and `CHANGELOG.md` once it exists |

Changes that are **not** spec-relevant: pure refactors (renames, extraction
of a helper, reordering) with no behavior change; test-only changes;
comment/docstring-only changes; formatting/lint fixes.

## Workflow

1. **Read the actual diff**, not just the commit message or PR title — a
   message can claim "no behavior change" while the diff shows otherwise.
2. **Classify it** against the table above. If more than one row applies,
   check every matching spec artifact.
3. **If spec-relevant**: update the matching spec file(s) in the same
   change, or if you conclude no update is warranted, state why explicitly
   in your response (e.g. "pure rename, no behavior change — no spec
   update needed") rather than silently skipping it.
4. **Stay in scope**: this check only touches `spec/`, `README.md`, and
   `CHANGELOG.md`. Never use "keeping the spec in sync" as a reason to also
   edit test files in the same change — that would violate this repo's
   Test / Implementation Separation rule.
5. **Don't invent spec content** the code change doesn't support — if the
   change is ambiguous about intended behavior, ask before writing spec
   prose that guesses at it.
