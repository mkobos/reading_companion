Feature: Discussion with the tool-using agent
  Discussion turns are handled by the tool-using agent.
  Context assembly follows the context envelope
  contract; each turn is returned as a single complete
  response; completed turns are persisted to the workspace
  history.

  Background:
    Given workspace "W" contains a parsed document
    And the user is reading with a known viewport

  Scenario: Starting a discussion from a suggested question
    Given the user has marked a passage and suggestions are shown
    When the user picks one of the suggested questions
    Then a new discussion anchored to that passage is created in workspace "W" in a single request that carries the suggestion text as the first user message
    And the created discussion contains the completed first turn

  Scenario: Starting a discussion with a typed question
    Given the user has marked a passage
    When the user types their own question and sends it
    Then a new discussion anchored to that passage is created in a single request that carries the typed question as the first user message
    And the created discussion contains the completed first turn

  Scenario: Agent receives the shared context
    When the user sends a message in a discussion
    Then the agent is provided with a shared context containing:
      | context_element   | description                                          |
      | viewport_text     | text resolved from the user's visible viewport       |
      | marked_passage    | the anchored passage text, if a selection exists     |
      | active_discussion | the current discussion's prior turns in full (carried by the agent's per-discussion session) |
      | workspace_history | recent turns from other discussions in the workspace |
      | relevant_notes    | notes nearest to the anchor passage or viewport      |
      | reading_journal   | the current reading journal, if one exists           |

  @eval
  Scenario: Underspecified questions work because of shared context
    Given the user has marked the passage "the categorical imperative"
    When the user sends only "what does this mean?"
    Then the agent's response addresses the marked passage specifically
    And the user did not need to restate what they were looking at

  Scenario: Agent answers from context alone
    Given the agent can answer the user's message from the shared context alone
    When the user sends the message
    Then the agent responds without invoking any tool

  @eval
  Scenario: Agent searches the document for content outside the viewport
    Given the user asks about a part of the document outside the current viewport
    When the user sends the message
    Then the agent invokes document search scoped to workspace "W"
    And search results are incorporated into the answer with block references

  @eval
  Scenario: Agent invokes web search for external facts
    Given the user asks about an external fact not present in the document or context
    When the user sends the message
    Then the agent invokes web search
    And the answer distinguishes document content from external information

  Scenario: The client shows a pending state while the agent works
    When the user sends a message
    Then the client shows a pending indicator until the response arrives
    And the response is rendered once, as a complete message
    And any tool activity is visible from the turn's tool-call trace

  Scenario: Completed turns are persisted
    When a discussion turn completes
    Then the user message, the full agent response, and any tool-call trace are saved as one turn in the discussion within workspace "W"
    And the turn is available as context for all future turns

  @eval
  Scenario: Continuing an existing discussion
    Given a discussion with prior turns exists
    When the user sends a follow-up message in that discussion
    Then the full prior turns of that discussion are in the agent's context
    And the response is consistent with the earlier exchange

  Scenario: No discussion without a document
    Given a workspace with no document uploaded
    Then the UI offers no way to start a discussion
    And API attempts to create a discussion are rejected

  Scenario: Agent failure surfaces cleanly
    Given the agent runtime returns an error mid-turn
    When the failure occurs
    Then the user sees a clear error state with a retry option
    And no partial turn is persisted to the discussion history

  Scenario: Connection drops while waiting for a response
    Given the user has sent a message and the response is pending
    When the client's connection is lost before the response arrives
    Then the client shows a clear error state
    And the user's message is restored to the input box with a resend option
