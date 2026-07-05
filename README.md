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

## Repository structure

- `spec/` — the specification (source of truth)
- `.agents/` — canonical agent rules and skills
- `docs/` — course reference material and working notes (not tracked in git)
- `discussion-agent/` — the ADK-based discussion agent, scaffolded with
  `agents-cli` (prototype scope; no agent logic implemented yet)

## Status

Discussion agent scaffolded (`discussion-agent/`, via `agents-cli scaffold
create`) — no agent logic written yet. The FastAPI/Cloud Run service and the
React SPA are not yet scoped.

## License

[MIT](LICENSE)
