# AI Agent Guidelines

This is the instruction manual for AI coding assistants working on this repository. It is written once and read by any tool-agnostic agent — see [README.md](../README.md) for how this file is linked into tool-specific locations.

## Stack

Chosen in [spec/technical_specification.md §8](../spec/technical_specification.md#8-implementation-mapping) — that section is the single place where concrete technology names and versions live; check it (and its pinned versions, once code exists) before writing code, since your training data may be stale:

- Python + FastAPI backend on Cloud Run
- Google Agent Development Kit (ADK) `LlmAgent`, deployed to Vertex AI Agent Engine
- Gemini via Vertex AI
- Firestore (Native mode) + Google Cloud Storage
- React SPA frontend

## General Rules

- **The specification is the single source of truth for the project**. The specification resides in `spec/`. The idea is that in principle you can re-generate the source code from the specification if needed. Make sure you update the specification — including `README.md` and, once it exists, `CHANGELOG.md` — every time you introduce any change in the project so it keeps being up-to-date.

## Coding-Agent Discipline

- **Think before coding.** State assumptions explicitly, surface tradeoffs, and halt to ask the user at genuine ambiguity instead of guessing silently.
- **Write only the minimum code needed.** No speculative features, no unrequested abstractions, no designing for hypothetical future requirements.
- **Make surgical edits.** Change only the lines needed to accomplish the task, match existing style, leave adjacent code untouched. However, if you see an opportunity to refactor the code to improve future maintenance, let the user know and ask them for the permission to do that.
- **Goal-driven execution.** Break tasks into a plan with explicit success criteria; write a failing test first, then loop until it strictly passes.
- **Rule accretion.** Whenever you do something you should not have, add a rule here (or to a relevant skill) so it does not recur. Review changes to this file in PRs like code.

## Planning Gate

Before generating implementation code for any non-trivial change, present a plan for human approval. Every plan must include a dedicated **"Security Boundaries & Assertions"** section listing exploit-relevant edge cases for the change (the spec's [security.feature](../spec/features/security.feature) and [agent-contract.yaml](../spec/contracts/agent-contract.yaml) untrusted-content wrapping are the starting inventory of these).

## Test / Implementation Separation

Never modify tests and implementation code in the same change. Tests are the objective baseline: an agent must not delete, weaken, or mock a test merely to turn it green. For bug fixes, write a failing reproduction test first, and leave it in the codebase after the fix.

## Code Style & Rules

- Keep files small and focused on a single responsibility.
- Use TDD for new functionalities.

## Skills Catalog

Use these when the situation matches — see each `SKILL.md` for exact trigger conditions:

| Skill | Use when |
|---|---|
| [gherkin-specification-writing](skills/gherkin-specification-writing/SKILL.md) | Writing, reviewing, or refactoring any `spec/features/*.feature` file |

## Project Structure

- `spec/` — user specification and technical specification (source of truth)
- `README.md` — project orientation for humans and agents
