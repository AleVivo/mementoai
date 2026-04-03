Feature: Folder Creation and Rename
  As a team member
  I want to create and rename folders from the sidebar
  So that I can organise the knowledge base without leaving the app

  Background:
    Given I am authenticated
    And I have selected project "backend"

  # ── CREATE ────────────────────────────────────────────────────────────────

  Scenario: Create a root-level folder from the sidebar
    When I click the "New Folder" button in the sidebar
    Then an inline input field appears in the sidebar at the root level
    When I type "Infrastructure" and press Enter
    Then "Infrastructure" appears in the sidebar under "backend"
    And the inline input field disappears

  Scenario: Create a nested folder from the context menu
    Given folder "ADR" exists and is expanded
    When I right-click on "ADR" and select "New subfolder"
    Then an inline input field appears indented under "ADR"
    When I type "2025" and press Enter
    Then "2025" appears under "ADR" in the sidebar

  Scenario: Pressing Escape cancels folder creation
    When I click the "New Folder" button in the sidebar
    And an inline input field appears
    When I press Escape
    Then the inline input field disappears
    And no new folder is created

  Scenario: Cannot create a folder with an empty name
    When I click the "New Folder" button in the sidebar
    And I press Enter without typing anything
    Then the inline input shows an error "Name cannot be empty"
    And no API call is made

  Scenario: Duplicate name at the same level shows an inline error
    Given folder "ADR" already exists at root level
    When I click the "New Folder" button in the sidebar
    And I type "ADR" and press Enter
    Then the inline input shows an error "A folder named 'ADR' already exists at this level"
    And the input field remains open so I can correct the name

  # ── RENAME ────────────────────────────────────────────────────────────────

  Scenario: Rename a folder via context menu
    Given folder "ADR" exists in the sidebar
    When I right-click on "ADR" and select "Rename"
    Then the folder label becomes an editable input pre-filled with "ADR"
    When I clear the input, type "Architecture Decisions" and press Enter
    Then the sidebar shows "Architecture Decisions" where "ADR" was
    And the folder path in the database is unchanged

  Scenario: Pressing Escape cancels rename
    Given folder "ADR" exists in the sidebar
    When I right-click on "ADR" and select "Rename"
    And I clear the input and type "New Name"
    And I press Escape
    Then the folder label reverts to "ADR"
    And no API call is made
