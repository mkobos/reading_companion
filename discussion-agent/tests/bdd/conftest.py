"""pytest-bdd harness for scenarios in ../../../spec/features/*.feature.

The .feature files are the repository's source of truth and are not copied
here — a scenario is wired with a named decorator:

    from pytest_bdd import scenario
    @scenario("../../../spec/features/<name>.feature", "<Scenario name>")
    def test_...(): pass

plus @given/@when/@then step definitions in the same file.

Routing rule (see ../../../spec/features/README.md and .agents/AGENTS.md,
"Test Strategy: pytest-bdd vs Eval"): a scenario tagged `@eval` never gets a
step definition here — it belongs in the eval harness (spec §3.4) instead.
Only untagged scenarios (deterministic: state, structure, or
tool-invocation-trace assertions) are pytest-bdd candidates.

Named `@scenario(...)` decorators (one per untagged scenario) are used
instead of a blanket `scenarios(path)` call specifically so that `@eval`
scenarios in the same feature file never need step definitions at all —
`scenarios(path)` would collect every scenario in the file and fail
collection for any `@eval` scenario missing a step.

Wired so far:
- test_discussion.py — "Agent receives the shared context", "Agent answers
  from context alone" (from discussion.feature).
- test_security.py — "All untrusted content is delimited uniformly", "Tools
  limit the blast radius of a successful injection", "Agent tools cannot
  cross workspace boundaries" (from security.feature).
"""
