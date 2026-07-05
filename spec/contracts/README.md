# Contract File Formats and Conventions

The files in this directory mix industry standards with project-specific conventions. The rule of thumb: **standard where a standard exists (OpenAPI, JSON Schema), bespoke-but-consistent YAML where none does, with prose clearly separated from machine-readable shapes.**

## `api.openapi.yaml` — fully standard

An [OpenAPI 3.1](https://spec.openapis.org/oas/v3.1.0) document, the de-facto standard for describing HTTP APIs. This buys real tooling: it can be validated, rendered as interactive docs (Swagger UI / Redoc), used to generate client/server stubs, and diffed for breaking changes.

## `data-model.yaml` — custom envelope, standard core

The top-level layout (`schemas:`, `firestore_mapping:`, `blob_store_mapping:`) is a convention specific to this project. Everything under `schemas:`, however, is written as **JSON Schema** fragments (`type`, `properties`, `required`, `$ref`, `enum`, `pattern`, …) — which is why `api.openapi.yaml` can `$ref` directly into it: OpenAPI 3.1's schema dialect *is* JSON Schema.

The mapping sections sit outside `schemas:` deliberately, so the provider-specific part is separable from the neutral entity definitions. They are plain documentation, not machine-validatable.

## `agent-contract.yaml` — mostly custom

The overall structure (`untrusted_content_wrapping`, `discussion_context`, `suggestions_context`, `journal_context`, `discussion_agent`, `suggestions_call`, `journal_call`, `provider_binding`) is bespoke — there is no established standard for "agent contracts" yet.

Within it:

- Input/output shapes again use JSON Schema style.
- Tool definitions (`description`, `input`, `output`) intentionally mirror the shape of LLM function-calling / tool schemas (the same idea as Gemini/OpenAI function declarations or MCP tool definitions), so translating them into actual ADK `FunctionTool` signatures at implementation time is mechanical.
- Fields like `role:` and `behavior:` are prose for the implementer, not schema.

## Possible further standardization (not done, deliberately)

- Extract the entities into standalone JSON Schema files, validatable with any JSON Schema tool.

More ceremony than this project needs.
