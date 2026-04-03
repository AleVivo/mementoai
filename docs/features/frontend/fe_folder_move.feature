Feature: Moving Folders and Entries
  As a team member
  I want to move folders and entries via the sidebar context menu
  So that I can reorganise the knowledge base as the project evolves

  Background:
    Given I am authenticated
    And I have selected project "backend"
    And the project has the following folder structure:
      | id          | name       | parent     |
      | folder_adr  | ADR        | root       |
      | folder_pm   | Postmortem | root       |
      | folder_2024 | 2024       | folder_adr |

  # ── MOVE FOLDER ───────────────────────────────────────────────────────────

  Scenario: Move a folder to a different parent via context menu
    When I right-click on "2024" and select "Move to..."
    Then a folder picker dialog appears showing the project tree
    When I select "Postmortem" as the destination and confirm
    Then "2024" disappears from under "ADR" in the sidebar
    And "2024" appears under "Postmortem" in the sidebar

  Scenario: Move a folder to project root via context menu
    When I right-click on "2024" and select "Move to..."
    And I select "Project root" as the destination and confirm
    Then "2024" appears at the root level in the sidebar
    And "2024" is no longer listed under "ADR"

  Scenario: Cannot select a folder's own descendant as destination
    Given folder "2024" is a child of "ADR"
    When I right-click on "ADR" and select "Move to..."
    Then the folder picker shows "2024" as disabled and not selectable
    And the folder picker shows "ADR" itself as disabled and not selectable

  Scenario: Moving a folder updates the sidebar immediately without full reload
    When I move "2024" to "Postmortem"
    Then the sidebar reflects the new position without a full page refresh

  # ── MOVE ENTRY ────────────────────────────────────────────────────────────

  Scenario: Move an entry to a different folder via entry context menu
    Given entry "ADR-001" belongs to folder "ADR"
    When I right-click on "ADR-001" in the sidebar and select "Move to..."
    Then a folder picker dialog appears
    When I select "Postmortem" and confirm
    Then "ADR-001" disappears from under "ADR"
    And "ADR-001" appears under "Postmortem"

  Scenario: Move an entry to project root
    Given entry "ADR-001" belongs to folder "ADR"
    When I right-click on "ADR-001" and select "Move to..."
    And I select "Project root" and confirm
    Then "ADR-001" appears at the root level in the sidebar
    And it is no longer listed under "ADR"

  # ── FOLDER PICKER ─────────────────────────────────────────────────────────

  Scenario: Folder picker shows the full project tree
    When I open the folder picker
    Then I see "Project root" as the first option
    And I see "ADR", "Postmortem" as selectable options
    And I see "2024" indented under "ADR"

  Scenario: Closing the folder picker without confirming cancels the move
    When I right-click on "2024" and select "Move to..."
    And I click the close button on the folder picker without selecting
    Then no move API call is made
    And the sidebar is unchanged
