# Evals for `spec-sync`

`eval_cases.json` holds trigger/behavior eval cases per Evaluation-Driven
Development pattern: "a skill without a test is a hope, not a capability."
Each case has an `input`, `expected_behavior`, and a `rubric` of checkable
claims; `type` is `positive_trigger` (skill must activate) or
`negative_trigger` (skill must stay out of the way).

## Description check

The skill's frontmatter description (`.agents/skills/spec-sync/SKILL.md`)
is: *"Checks that a code change under discussion-agent/app/ (or a future
backend/ or frontend/) that alters agent behavior, tool signatures, or
contract fields also updates the matching spec/features/*.feature,
spec/contracts/*.yaml, README, or CHANGELOG in the same change. Does not
activate for spec-only edits (see gherkin-specification-writing) or
non-code discussion."*

Checked against the four criteria:

- **Testable specificity** — names concrete code locations
  (`discussion-agent/app/`), concrete change categories (agent behavior,
  tool signatures, contract fields), and concrete spec artifacts
  (`.feature`, `.yaml`, README, CHANGELOG), so trigger/no-trigger is
  checkable per case.
- **Clarity** — no jargon beyond terms already established elsewhere in
  this repo's rule files (`agent-contract.yaml`, `.feature`).
- **Execution fidelity** — matches what `SKILL.md`'s workflow actually does
  (read diff → classify against the table → update or explicitly justify
  skipping → stay out of test files); the description doesn't promise a
  deterministic script, since the body is explicit that this is a judgment
  check.
- **Rephrasing stability** — "code change ... alters agent behavior, tool
  signatures, or contract fields" should still match paraphrases like "I
  changed how the tool works, does the contract need updating?" (case
  `positive-new-tool-param-no-spec-update`).

The identified gap this skill's description guards against by exclusion:
overlap with `gherkin-specification-writing`, which owns direct `.feature`
authoring/refactoring. Case `negative-direct-feature-file-edit-request`
exists specifically to confirm the two skills don't both fire on the same
request.

The second positive case (`positive-pure-rename-no-spec-update-needed`)
guards against the opposite failure mode: the skill reflexively flagging
every code diff regardless of whether it's actually spec-relevant, which
would make it noise rather than signal.

## Target

90% trigger/behavior accuracy across the case set. This skill only ever
proposes edits to `spec/`, `README.md`, or `CHANGELOG.md` under a
human-approved plan (per the Planning Gate) — it never touches test or
implementation code — so LLM-as-judge scoring against the rubrics above is
a sufficient bar, matching the tiering already applied to
`gherkin-specification-writing`.

## Running

No harness wires these up yet (this repo has no eval runner — see
`docs/repo_configuration_improvements.md` §3.4 for the planned
`tests/eval/` layout). Until then, use these cases manually: paste the
`input` to the agent, check the response against `rubric`.
