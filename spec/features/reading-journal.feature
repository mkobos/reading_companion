Feature: Reading journal
  On request, a plain LLM call (not the agent, user-spec §7) synthesizes the
  user's notes and discussion history into a rolling reading journal that
  replaces the previous one and joins the shared context.

  Background:
    Given workspace "W" contains a parsed document

  Scenario: Generating the journal on request
    Given workspace "W" has several notes and discussion turns
    When the user requests a reading journal update
    Then the notes and discussion history are synthesized into a reading journal
    And the reading journal is saved in workspace "W"
    And the journal is displayed to the user

  Scenario: Journal synthesizes rather than transcribes
    Given workspace "W" has notes and discussion turns containing "Kant's definition of duty"
    When the user requests a reading journal update
    Then the reading journal contains a synthesis of the themes in "Kant's definition of duty"
    And the reading journal does not contain a verbatim transcription of the notes or discussion turns

  Scenario: Regeneration replaces the previous journal
    Given workspace "W" has a reading journal with content "Prior synthesis"
    And the user has since added new notes and discussion turns
    When the user requests a reading journal update
    Then the new reading journal is generated using the new notes, turns, and "Prior synthesis"
    And the new reading journal replaces the stored journal in workspace "W"

  Scenario: Journal becomes part of the shared context
    Given workspace "W" has a current journal
    When a subsequent discussion turn occurs
    Then the journal is included in the shared context provided to the agent

  Scenario: Reading journal update with nothing to synthesize
    Given workspace "W" has no notes and no discussion history
    When the user requests a reading journal update
    Then the application informs the user there is nothing to reflect on yet
    And no LLM call is made and no journal is saved

  Scenario: Generation failure leaves prior journal intact
    Given workspace "W" has a current journal
    And the journal generation service returns an error
    When the user requests a reading journal update
    Then a reading journal generation error is shown to the user with a retry option
    And the previously stored journal remains unchanged in workspace "W"
