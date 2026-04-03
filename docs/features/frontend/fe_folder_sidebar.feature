Feature: Folder Tree Sidebar
  As a team member
  I want to see and navigate folders in the sidebar as a tree
  So that I can find entries without scrolling through a flat list

  Background:
    Given I am authenticated
    And I have selected project "backend"
    And the project has the following folder structure:
      | id          | name       | parent     |
      | folder_adr  | ADR        | root       |
      | folder_pm   | Postmortem | root       |
      | folder_2024 | 2024       | folder_adr |
      | folder_q1   | Q1         | folder_2024|

  # ── RENDERING ─────────────────────────────────────────────────────────────

  Scenario: Root-level folders appear directly under the project name
    Then I see "ADR" and "Postmortem" listed under "backend" in the sidebar
    And I do not see a node labeled "" or "root"

  Scenario: Nested folders are hidden until parent is expanded
    Then I do not see "2024" in the sidebar
    And I do not see "Q1" in the sidebar

  Scenario: Expanding a folder reveals its children
    When I click the expand toggle on "ADR"
    Then I see "2024" indented under "ADR"
    And I do not see "Q1" in the sidebar

  Scenario: Expanding a nested folder reveals its children
    Given "ADR" is expanded
    When I click the expand toggle on "2024"
    Then I see "Q1" indented under "2024"

  Scenario: Collapsing a folder hides all its descendants
    Given "ADR" is expanded
    And "2024" is expanded
    When I click the expand toggle on "ADR"
    Then I do not see "2024" in the sidebar
    And I do not see "Q1" in the sidebar

  Scenario: Selected folder is visually highlighted
    When I click on folder "ADR"
    Then folder "ADR" appears highlighted in the sidebar
    And the main panel shows only entries that belong to "ADR"

  Scenario: Clicking a folder does not navigate to a new route
    When I click on folder "ADR"
    Then the URL does not change

  # ── ENTRIES IN TREE ───────────────────────────────────────────────────────

  Scenario: Entries inside a folder appear under it in the sidebar
    Given entry "ADR-001" belongs to folder "ADR"
    And "ADR" is expanded
    Then I see "ADR-001" listed under "ADR" in the sidebar

  Scenario: Clicking a project name shows root entries only
    Given entry "General update" belongs to root (no folder)
    When I click on the project name "backend"
    Then the main panel shows "General update"
    And the main panel does not show entries that belong to a folder
