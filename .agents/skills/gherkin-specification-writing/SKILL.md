---
name: gherkin-specification-writing
description: Helps write, review, and refactor Gherkin BDD specification files to align with best practices, including declarative scenarios, structured Scenario Outlines, and syntax verification.
---

# Gherkin Specification Writing

This skill assists in writing, reviewing, and refactoring Gherkin (.feature) specification files to ensure they are clean, executable-ready, and follow BDD best practices.

## Guidelines for Gherkin Features

When writing Gherkin files, always follow these core principles:

### 1. Declarative vs. Imperative Phrasing
* **Rule**: Describe *what* the system does from the user/business perspective, not *how* the UI or code executes it.
* **Bad**: `When the user clicks the "add note" button, inputs "Hello" in the textbox, and clicks "Save"`
* **Good**: `When the user adds a note with text "Hello"`
* **Bad**: `Then the client sends a POST request to /workspaces/W/notes with the payload...`
* **Good**: `Then the note is saved in workspace "W"`

### 2. Single Behavior Focus (No Chained Scenarios)
* **Rule**: Each scenario must test a single, distinct behavior. Avoid chaining multiple `When-Then` cycles in one scenario.
* **Bad**:
  ```gherkin
  When the user requests suggestions
  Then suggestions are shown
  When the user types a custom question
  Then the custom question is sent
  ```
* **Good**: Split into `Scenario: Selecting a suggested question` and `Scenario: Submitting a custom question`.

### 3. Proper Gherkin Grammar
* **Given**: Defines the state/precondition. Never start a scenario directly with `When` or `Then` without setting up the context (unless it is globally trivial).
* **When**: Represents the specific action/trigger.
* **Then**: Asserts the expected outcome.
* **Strict Constraint**: Never write assertion-only scenarios that have only `Then` / `And` steps (e.g. checking if ID is random). Use a `When` trigger (e.g., `When a workspace is created`).

### 4. Concrete Examples & Data Tables
* **Rule**: Use Gherkin `DocStrings` (`"""`) and `Data Tables` to specify inputs and outputs rather than abstract text.
* **Example**:
  ```gherkin
  When the user uploads a Markdown file with content:
    """markdown
    # Intro
    This is a paragraph.
    """
  Then the document is parsed into the following blocks:
    | block_id | type      | text       |
    | 000001   | heading   | Intro      |
    | 000002   | paragraph | This is... |
  ```

### 5. Efficient Endpoints Grouping via Scenario Outlines
* **Rule**: When testing the same flow (e.g. rate-limiting, error handling) across multiple endpoints/options, use `Scenario Outline` with `Examples` tables instead of duplicate scenarios.

---

## Workflow for Writing and Refactoring

1. **Analytical Review**: 
   * Audit existing Gherkin `.feature` documents.
   * Document specific issues (imperative steps, grammar errors, multi-transitions, missing preconditions, abstract assertions).

2. **Implementation Planning**:
   * Create an `implementation_plan.md` artifact outlining the specific file changes.
   * Await explicit user approval before applying changes to the codebase.

3. **Refactoring Execution**:
   * Apply changes cleanly using precise replacements.
   * Join split steps that cause syntax issues (e.g. lines wrapped without step keywords).

4. **Syntax Verification**:
   * Always run a syntax parser/dry-run check (such as `npx @cucumber/cucumber <path> --dry-run` or similar parser tools) to ensure Gherkin syntax is perfectly valid.
   * Update the task checklist and document the walkthrough.
