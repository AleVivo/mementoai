Feature: Folder Deletion
  As a team member
  I want to delete empty folders from the sidebar
  So that I can keep the structure clean without orphaned nodes

  Background:
    Given I am authenticated
    And I have selected project "backend"

  # ── DELETE ────────────────────────────────────────────────────────────────

  Scenario: Delete an empty folder
    Given folder "OldFolder" exists with no subfolders and no entries
    When I right-click on "OldFolder" and select "Delete"
    Then a confirmation dialog appears with the message "Delete 'OldFolder'?"
    When I confirm the deletion
    Then "OldFolder" disappears from the sidebar

  Scenario: Pressing Escape on the confirmation dialog cancels deletion
    Given folder "OldFolder" exists with no subfolders and no entries
    When I right-click on "OldFolder" and select "Delete"
    And the confirmation dialog appears
    When I press Escape
    Then the dialog closes
    And "OldFolder" is still visible in the sidebar

  Scenario: Delete option is disabled for folders with subfolders
    Given folder "ADR" has subfolder "2024"
    When I right-click on "ADR"
    Then the "Delete" option in the context menu is disabled
    And a tooltip reads "Remove all subfolders before deleting"

  Scenario: Delete option is disabled for folders with entries
    Given folder "ADR" contains entry "ADR-001"
    When I right-click on "ADR"
    Then the "Delete" option in the context menu is disabled
    And a tooltip reads "Remove all entries before deleting"

  Scenario: Backend 409 shows an inline error (defensive — UI may be stale)
    Given folder "ADR" appears empty in the sidebar
    But the backend returns 409 when deleting "ADR"
    When I right-click on "ADR" and select "Delete"
    And I confirm the deletion
    Then the confirmation dialog shows the error "The folder is not empty. Refresh and try again."
    And "ADR" remains in the sidebar
