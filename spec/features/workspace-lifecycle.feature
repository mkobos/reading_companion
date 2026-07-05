Feature: Workspace lifecycle
  A workspace bundles one document with its notes, discussions, and journal.
  Access is by capability URL only; a cookie remembers the
  last-used workspace. There is no login.

  Background:
    Given the application is running

  Scenario: New user gets an empty workspace automatically
    Given a visitor with no workspace cookie opens the app root
    When the app loads
    Then a new empty workspace is created with a high-entropy unguessable ID
    And the visitor is redirected to that workspace's URL
    And a cookie is set to remember the workspace ID
    And the workspace displays an empty state prompting for a document upload

  Scenario: Returning user is taken to their last workspace
    Given a visitor whose cookie references workspace "W"
    And workspace "W" still exists
    When the visitor opens the app root
    Then the visitor is redirected to workspace "W"
    And no new workspace is created

  Scenario: Returning user whose remembered workspace was deleted
    Given a visitor whose cookie references workspace "W"
    And workspace "W" no longer exists
    When the visitor opens the app root
    Then a transient "workspace not found" notice (toast) is shown
    And the visitor is redirected to a fresh empty workspace
    And the cookie is updated to remember the new workspace

  Scenario: Opening a shared workspace URL grants full access
    Given workspace "W" exists with a document, notes, and discussions
    And a visitor who has never seen workspace "W"
    When the visitor opens workspace "W"'s URL directly
    Then the full workspace is shown: document, notes, discussions, journal
    And the visitor has read and write permissions in workspace "W"
    And the visitor's cookie is updated to remember workspace "W"

  Scenario: Creating an additional workspace explicitly
    Given a visitor currently viewing workspace "W1"
    When the visitor requests a new workspace
    Then a new empty workspace "W2" is created and displayed
    And the cookie is updated to remember workspace "W2"
    And workspace "W1" remains intact and reachable via its URL

  Scenario: Deleting a workspace
    Given a visitor viewing workspace "W"
    When the visitor deletes the workspace
    Then workspace "W" and all its notes, discussions, and journal are removed
    And the workspace's uploaded raw file is removed from blob storage
    And subsequent requests to workspace "W"'s URL respond as not found
    And the visitor is redirected to a fresh empty workspace

  Scenario: Concurrent edits follow last-write-wins
    Given two visitors "A" and "B" have workspace "W" open via the same URL
    And both are editing the same note
    When "A" saves the note and then "B" saves the note
    Then the stored note content is "B"'s version
    And no error or merge conflict is surfaced to either visitor

  Scenario: Requesting a nonexistent or malformed workspace ID
    Opening a bad workspace URL must not create a workspace automatically;
    otherwise probing random URLs would mass-create workspaces.

    When a visitor opens a URL with a workspace ID that does not exist
    Then the app responds with not found, revealing nothing about other workspaces
    And an error page is shown with an explicit "create a new workspace" action
    And no workspace is created unless the visitor invokes that action
    And invoking the action creates a fresh empty workspace and updates the cookie
