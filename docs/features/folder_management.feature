Feature: Folder Management
  As a team member
  I want to organize entries into folders within a project
  So that I can navigate large knowledge bases without losing context

  Background:
    Given I am authenticated as "alice@example.com"
    And I am a member of project "backend" with id "proj_001"

  # ── CREATION ──────────────────────────────────────────────────────────────

  Scenario: Create a root folder
    When I send POST /projects/proj_001/folders with body:
      """
      { "name": "ADR", "parent_id": null }
      """
    Then the response status is 201
    And the response body contains:
      | field     | value |
      | name      | ADR   |
      | parent_id | null  |
    And the path ends with the new folder's id

  Scenario: Create a nested folder
    Given folder "ADR" exists with id "folder_adr" in project "proj_001"
    When I send POST /projects/proj_001/folders with body:
      """
      { "name": "2024", "parent_id": "folder_adr" }
      """
    Then the response status is 201
    And the response body contains:
      | field | value                   |
      | name  | 2024                    |
    And the path contains "/proj_001/folder_adr/"
    And the path ends with the new folder's id

  Scenario: Cannot create folder with duplicate name under same parent
    Given folder "ADR" exists under root of project "proj_001"
    When I send POST /projects/proj_001/folders with body:
      """
      { "name": "ADR", "parent_id": null }
      """
    Then the response status is 409
    And the response body contains error "A folder named 'ADR' already exists at this level"

  Scenario: Cannot create folder in a project I am not a member of
    Given I am not a member of project "proj_999"
    When I send POST /projects/proj_999/folders with body:
      """
      { "name": "Secret", "parent_id": null }
      """
    Then the response status is 403

  Scenario: Cannot create folder with empty name
    When I send POST /projects/proj_001/folders with body:
      """
      { "name": "", "parent_id": null }
      """
    Then the response status is 422

  # ── READ ──────────────────────────────────────────────────────────────────

  Scenario: Get full folder tree of a project
    Given the following folder structure exists in project "proj_001":
      | name       | parent     |
      | ADR        | root       |
      | Postmortem | root       |
      | 2024       | ADR        |
      | 2025       | ADR        |
      | Q1         | 2024       |
    When I send GET /projects/proj_001/folders
    Then the response status is 200
    And the response contains a tree with 2 root nodes
    And the node "ADR" has 2 children
    And the node "2024" has 1 child named "Q1"

  Scenario: Empty project returns empty folder tree
    When I send GET /projects/proj_001/folders
    Then the response status is 200
    And the response body is:
      """
      []
      """

  # ── RENAME ────────────────────────────────────────────────────────────────

  Scenario: Rename a folder
    Given folder "ADR" exists with id "folder_adr" in project "proj_001"
    When I send PUT /projects/proj_001/folders/folder_adr with body:
      """
      { "name": "Architecture Decision Records" }
      """
    Then the response status is 200
    And the response body contains:
      | field | value                         |
      | name  | Architecture Decision Records |
    And the folder path is unchanged

  Scenario: Cannot rename to a name already taken at the same level
    Given folder "ADR" exists under root of project "proj_001"
    And folder "Postmortem" exists with id "folder_postmortem" under root of project "proj_001"
    When I send PUT /projects/proj_001/folders/folder_postmortem with body:
      """
      { "name": "ADR" }
      """
    Then the response status is 409

  # ── MOVE ──────────────────────────────────────────────────────────────────

  Scenario: Move a folder to a new parent
    Given the following folder structure exists in project "proj_001":
      | id          | name       | parent     |
      | folder_adr  | ADR        | root       |
      | folder_pm   | Postmortem | root       |
      | folder_2024 | 2024       | folder_adr |
    When I send PUT /projects/proj_001/folders/folder_2024/move with body:
      """
      { "new_parent_id": "folder_pm" }
      """
    Then the response status is 200
    And folder "2024" has path "/proj_001/folder_pm/folder_2024"

  Scenario: Move a folder to project root
    Given the following folder structure exists in project "proj_001":
      | id          | name | parent     |
      | folder_adr  | ADR  | root       |
      | folder_2024 | 2024 | folder_adr |
    When I send PUT /projects/proj_001/folders/folder_2024/move with body:
      """
      { "new_parent_id": null }
      """
    Then the response status is 200
    And folder "2024" has path "/proj_001/folder_2024"

  Scenario: Moving a folder updates all descendant paths
    Given the following folder structure exists in project "proj_001":
      | id       | name | parent   |
      | folder_a | A    | root     |
      | folder_b | B    | folder_a |
      | folder_c | C    | folder_b |
    When I send PUT /projects/proj_001/folders/folder_b/move with body:
      """
      { "new_parent_id": null }
      """
    Then the response status is 200
    And folder "B" has path "/proj_001/folder_b"
    And folder "C" has path "/proj_001/folder_b/folder_c"

  Scenario: Cannot move a folder into one of its own descendants
    Given the following folder structure exists in project "proj_001":
      | id       | name | parent   |
      | folder_a | A    | root     |
      | folder_b | B    | folder_a |
      | folder_c | C    | folder_b |
    When I send PUT /projects/proj_001/folders/folder_a/move with body:
      """
      { "new_parent_id": "folder_c" }
      """
    Then the response status is 409
    And the response body contains error "Cannot move a folder into its own descendant"

  Scenario: Cannot move a folder to a parent in a different project
    Given folder "X" exists with id "folder_x" in project "proj_002"
    When I send PUT /projects/proj_001/folders/folder_adr/move with body:
      """
      { "new_parent_id": "folder_x" }
      """
    Then the response status is 409

  # ── DELETE ────────────────────────────────────────────────────────────────

  Scenario: Delete an empty folder
    Given folder "ADR" exists with id "folder_adr" and has no children and no entries
    When I send DELETE /projects/proj_001/folders/folder_adr
    Then the response status is 204
    And folder "folder_adr" no longer exists in the database

  Scenario: Cannot delete a folder that contains subfolders
    Given folder "ADR" with id "folder_adr" contains subfolder "2024"
    When I send DELETE /projects/proj_001/folders/folder_adr
    Then the response status is 409
    And the response body contains error "Cannot delete a folder that contains subfolders"

  Scenario: Cannot delete a folder that contains entries
    Given folder "ADR" with id "folder_adr" contains 3 entries
    When I send DELETE /projects/proj_001/folders/folder_adr
    Then the response status is 409
    And the response body contains error "Cannot delete a folder that contains entries"

  Scenario: Delete is blocked for non-members
    Given I am not a member of project "proj_001"
    When I send DELETE /projects/proj_001/folders/folder_adr
    Then the response status is 403
