Feature: Notes
  Notes are user-authored text anchored to a passage. Saving a note involves
  no AI processing (user-spec §4.3). Anyone with the workspace URL can view
  and edit them (user-spec §3.5).

  Background:
    Given workspace "W" contains a parsed document

  Scenario: Adding a note to a passage
    Given the user has marked a passage
    When the user adds a note with text "Interesting argument here."
    Then the note is saved in workspace "W" with the text "Interesting argument here."
    And the saved note has a creation timestamp and a passage anchor
    And no AI call is made
    And a note indicator is displayed on the passage in the reading view

  Scenario: Viewing a note
    Given a note with text "Verify this citation." exists anchored to a passage in workspace "W"
    When the user views the note
    Then the note text "Verify this citation." is shown with the anchored passage text

  Scenario: Editing a note
    Given a note with text "Original note text." exists in workspace "W"
    When the user changes the note text to "Updated note text."
    Then the stored note text is updated to "Updated note text."
    And the note's updated timestamp is updated

  Scenario: Deleting a note
    Given a note exists in workspace "W"
    When the user deletes the note
    Then the note is removed from workspace "W"
    And the note's indicator is removed from the reading view

  Scenario: Notes are available as AI context
    Given a note with text "Crucial logic flaw." exists in workspace "W"
    When a discussion turn or journal generation is triggered
    Then the note text "Crucial logic flaw." is included in the context envelope as untrusted data

  Scenario: Empty note is rejected
    When the user attempts to save a note with empty text
    Then the note is not saved
    And the note input remains open for correction
