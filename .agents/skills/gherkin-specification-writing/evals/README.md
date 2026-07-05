# Evals for `gherkin-specification-writing`

`eval_cases.json` holds trigger/behavior eval cases per
Evaluation-Driven Development pattern: "a skill without a test is a hope,
not a capability." Each case has an `input`, `expected_behavior`, and a
`rubric` of checkable claims; `type` is `positive_trigger` (skill must
activate) or `negative_trigger` (skill must stay out of the way).

## Description check

The skill's frontmatter description (`.agents/skills/gherkin-specification-writing/SKILL.md`)
is: *"Helps write, review, and refactor Gherkin BDD specification files to
align with best practices, including declarative scenarios, structured
Scenario Outlines, and syntax verification."*

Checked against the four criteria:

- **Testable specificity** — names concrete actions (write/review/refactor)
  and a concrete artifact (Gherkin `.feature` files), so trigger/no-trigger
  is checkable per case rather than a vibe call.
- **Clarity** — no jargon beyond "Gherkin" and "Scenario Outlines," both of
  which are the domain terms an agent needs to match against a request.
- **Execution fidelity** — matches what `SKILL.md`'s workflow actually does
  (analytical review → implementation plan → refactor → syntax
  verification); the description doesn't promise anything the body skips.
- **Rephrasing stability** — "write/review/refactor ... Gherkin ...
  specification files" should still match paraphrases like "clean up this
  .feature file" or "spec out this behavior in Gherkin" (case
  `positive-review-existing-feature` exercises this).

The one identified gap: the description does not disambiguate "feature" as
in `.feature` file vs. "feature" as in software feature — case
`negative-unrelated-feature-flag` exists specifically to catch a
false-positive trigger on that word.

## Target

90% trigger/behavior accuracy across the case set, in line with the
read-only-workspace tiering in [notes.md's Day 3 discussion of skill
evaluation](../../../../docs/google_5-day_AI_agents_course/) (this skill
only edits spec files under human-approved plans, so LLM-as-judge scoring
against the rubrics above is a sufficient bar — no stricter deterministic
gate is warranted).

## Running

No harness wires these up yet (this repo has no eval runner — see
`docs/repo_configuration_improvements.md` §3.4 for the planned
`tests/eval/` layout). Until then, use these cases manually: paste the
`input` to the agent, check the response against `rubric`.
