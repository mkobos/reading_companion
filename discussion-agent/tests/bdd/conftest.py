"""pytest-bdd harness for scenarios in ../../../spec/features/*.feature.

The .feature files are the repository's source of truth and are not copied
here — wire a scenario with:

    from pytest_bdd import scenarios
    scenarios("../../../spec/features/<name>.feature")

plus @given/@when/@then step definitions in this directory.

Routing rule (see ../../../spec/features/README.md and .agents/AGENTS.md,
"Test Strategy: pytest-bdd vs Eval"): a scenario tagged `@eval` never gets a
step definition here — it belongs in the eval harness (spec §3.4) instead.
Only untagged scenarios (deterministic: state, structure, or
tool-invocation-trace assertions) are pytest-bdd candidates. pytest-bdd
converts Gherkin tags to pytest marks, so if a `.feature` file is ever loaded
wholesale, `@eval` scenarios can still be excluded with `-m "not eval"`.

No scenarios are wired yet: discussion.feature and security.feature (the
only feature files relevant to this component) do have untagged/deterministic
scenarios now, but no deterministic agent logic exists yet to bind a step to
(app/agent.py is still the scaffold placeholder).
"""
