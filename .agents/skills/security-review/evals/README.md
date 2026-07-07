# Evals for `security-review`

`eval_cases.json` holds trigger/behavior eval cases per Evaluation-Driven
Development pattern: "a skill without a test is a hope, not a capability."
Each case has an `input`, `expected_behavior`, and a `rubric` of checkable
claims; `type` is `positive_trigger` (skill must activate) or
`negative_trigger` (skill must stay out of the way).

## Description check

The skill's frontmatter description (`.agents/skills/security-review/SKILL.md`)
is: *"Runs a STRIDE threat-model review on request, or before a
security-relevant change (new tool, new trust boundary, new untrusted input
source), and updates spec/threat_model.md. Cross-references
spec/features/security.feature and spec/contracts/agent-contract.yaml's
untrusted-content rules rather than rebuilding from scratch. Does not
activate for routine code changes with no new trust boundary (see
spec-sync) or for direct .feature editing (see
gherkin-specification-writing)."*

Checked against the four criteria:

- **Testable specificity** — names a concrete methodology (STRIDE), a
  concrete output artifact (`spec/threat_model.md`), and concrete trigger
  conditions (new tool, new trust boundary, new untrusted input source),
  so trigger/no-trigger is checkable per case.
- **Clarity** — "STRIDE" and "trust boundary" are domain terms already used
  elsewhere in this repo's spec (Planning Gate, agent-contract.yaml); no
  additional jargon introduced.
- **Execution fidelity** — matches what `SKILL.md`'s workflow actually does
  (read existing spec/code → map to STRIDE categories → update
  threat_model.md with covered-vs-gap subsections → never fix in the same
  step); the description doesn't promise auto-remediation.
- **Rephrasing stability** — "before a security-relevant change (new tool,
  new trust boundary...)" should still match paraphrases that never say
  "security" explicitly, like "I'm adding a tool that writes to Firestore"
  (case `positive-new-tool-new-trust-boundary` exercises this — the
  highest-risk failure mode for this skill is under-triggering on requests
  that don't use the word "security").

The identified overlap risk this description guards against by exclusion:
`spec-sync` (routine spec/code sync, no STRIDE analysis) and
`gherkin-specification-writing` (direct `.feature` authoring). Case
`negative-routine-refactor-no-new-boundary` confirms a plain refactor
doesn't pull in a full STRIDE pass.

## Target

90% trigger/behavior accuracy across the case set. This skill only ever
proposes edits to `spec/threat_model.md` under a human-approved plan (per
the Planning Gate), and explicitly never fixes flagged gaps in the same
step — so LLM-as-judge scoring against the rubrics above is a sufficient
bar, matching the tiering already applied to the other two project skills.

## Running

No harness wires these up yet (this repo has no eval runner — see
`docs/repo_configuration_improvements.md` §3.4 for the planned
`tests/eval/` layout). Until then, use these cases manually: paste the
`input` to the agent, check the response against `rubric`.
