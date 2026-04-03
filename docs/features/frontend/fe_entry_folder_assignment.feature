Feature: Entry Creation with Folder Assignment
  As a team member
  I want to create entries already placed in a specific folder
  So that I don't have to move them manually after creation

  Background:
    Given I am authenticated
    And I have selected project "backend"
    And the project has folders "ADR" and "Postmortem" at root level

  # ── NEW ENTRY DIALOG ──────────────────────────────────────────────────────

  Scenario: New entry dialog pre-selects the currently active folder
    Given I have clicked on folder "ADR" in the sidebar
    When I open the New Entry dialog (Cmd+N or "+ New" button)
    Then the "Folder" field in the dialog shows "ADR" pre-selected

  Scenario: New entry dialog defaults to root when no folder is selected
    Given I have clicked on the project name "backend" (not a folder)
    When I open the New Entry dialog
    Then the "Folder" field shows "Project root" pre-selected

  Scenario: I can change the folder before creating the entry
    Given the New Entry dialog is open with "ADR" pre-selected
    When I click the "Folder" field and select "Postmortem"
    Then the "Folder" field shows "Postmortem"
    When I fill in the title and confirm
    Then the new entry appears under "Postmortem" in the sidebar

  Scenario: I can assign the entry to project root from the dialog
    Given the New Entry dialog is open with "ADR" pre-selected
    When I click the "Folder" field and select "Project root"
    Then the "Folder" field shows "Project root"
    When I fill in the title and confirm
    Then the new entry appears at root level in the sidebar

  Scenario: Created entry appears in the sidebar immediately
    When I create an entry titled "New ADR" with folder "ADR"
    Then "New ADR" appears under "ADR" in the sidebar without a page refresh
    And the editor opens with the new entry active
