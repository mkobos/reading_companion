# Feature file conventions

## `@eval` tag: pytest-bdd vs. eval routing

Every scenario in this directory maps to exactly one test mechanism, marked
by a Gherkin tag rather than by file location — several scenarios mix a
deterministic assertion with an LLM-judgment assertion in the same
`Scenario`, so tagging (not file-splitting) is what lets both concerns live
in one coherent narrative.

- **`@eval`** — the scenario's outcome requires judging LLM output content,
  relevance, or quality. A hardcoded or mocked model response could not
  legitimately satisfy it. These scenarios are evaluated via the eval
  harness (LLM-as-judge), never via a pytest-bdd step definition.
- **Untagged** — the scenario reduces to a deterministic check: state,
  persistence, structure, configuration, or a tool-invocation trace (which
  tool was called, with what scope — not what the model said). These are
  pytest-bdd candidates.

**Rule for mixed scenarios**: if *any* step in a scenario requires judging
LLM output, tag the whole scenario `@eval` — do not split it just to keep
the deterministic half in pytest-bdd. The deterministic part is exercised as
a byproduct of the eval run; if it's independently valuable to check in
isolation (e.g. under a different fixture), write a separate untagged
scenario for that narrower assertion instead of partially tagging one.

**Two common false positives to watch for** (from `security.feature`): "the
untrusted content is delimited uniformly" and "tools are read-only /
scoped server-side" both sound behavior-like but actually check how the
prompt or tool registration is *constructed* in code — inspectable without
invoking a model. These stay untagged.

Files with no `@eval` tags at all (`document-upload.feature`,
`notes.feature`, `reading-view.feature`, `workspace-lifecycle.feature`)
contain no LLM-judgment scenarios — every scenario in them is deterministic.

See `.agents/AGENTS.md` ("Test Strategy: pytest-bdd vs Eval") for how this
routes into actual test code, and `docs/repo_configuration_progress.md` §3.3
for status.
