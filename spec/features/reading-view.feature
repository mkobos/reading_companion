Feature: Reading view and viewport reporting
  The user reads the parsed document in-app. The client tracks which blocks
  are visible and includes that range in AI-invoking requests;
  it never sends full document text back to the server.

  Background:
    Given workspace "W" contains a parsed document of many blocks

  Scenario: Rendering the document
    When the user opens workspace "W"
    Then the document content is displayed in its original block order
    And each document block has a stable, addressable block ID

  Scenario: Scrolling updates the tracked viewport
    Given the user is viewing blocks "000010" through "000018"
    When the user scrolls to make blocks "000040" through "000047" visible
    Then the user's active viewport is updated to blocks "000040" through "000047"

  Scenario: Viewport range accompanies discussion requests
    Given the user's active viewport is blocks "000040" through "000047"
    When the user marks a passage and sends a discussion message
    Then the discussion request is sent with only the active viewport block range IDs
    And the backend resolves the viewport text from those block IDs

  Scenario: Anchored items are visible in the margin
    Given workspace "W" has notes and discussions anchored to passages
    When the user views a document region containing these passages
    Then the reading view displays indicators for the anchored notes or discussions
    And selecting an indicator displays the corresponding note or discussion
