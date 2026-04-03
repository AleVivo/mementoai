Feature: Project Lifecycle
  As a team member
  I want projects to manage their own folder and entry structure automatically
  So that I never end up with orphaned data or missing root folders

  Background:
    Given I am authenticated as "alice@example.com"

  # ── ROOT FOLDER (R1) ──────────────────────────────────────────────────────

  Scenario: Creating a project automatically creates a root folder
    When I send POST /projects with body:
      """
      { "name": "my-new-project" }
      """
    Then the response status is 201
    And a folder exists in the database with:
      | field      | value              |
      | project_id | <new_project_id>   |
      | parent_id  | null               |
      | name       | ""                 |
    And the root folder path equals "/<new_project_id>"

  Scenario: The root folder is not visible in the folder tree endpoint
    Given project "proj_001" exists with its root folder
    When I send GET /projects/proj_001/folders
    Then the response status is 200
    And the response does not contain a folder with name ""

  # ── CASCADE DELETE (R8) ───────────────────────────────────────────────────

  Scenario: Deleting a project removes all its folders
    Given project "proj_001" has the following folder structure:
      | id          | name       | parent     |
      | folder_adr  | ADR        | root       |
      | folder_pm   | Postmortem | root       |
      | folder_2024 | 2024       | folder_adr |
    When I send DELETE /projects/proj_001
    Then the response status is 204
    And no folders exist in the database with project_id "proj_001"

  Scenario: Deleting a project removes all its entries
    Given project "proj_001" has 5 entries across different folders
    When I send DELETE /projects/proj_001
    Then the response status is 204
    And no entries exist in the database with project_id "proj_001"

  Scenario: Deleting a project removes all indexed chunks
    Given project "proj_001" has 3 indexed entries
    When I send DELETE /projects/proj_001
    Then the response status is 204
    And no chunks exist in the database with project_id "proj_001"

  Scenario: Deleted project entries are no longer returned by search
    Given project "proj_001" has 2 indexed entries about "database decisions"
    And I send DELETE /projects/proj_001
    When I send POST /search with body:
      """
      {
        "query": "database decisions",
        "project_id": "proj_001",
        "top_k": 5
      }
      """
    Then the response status is 200
    And the response contains exactly 0 entries

  # ── DELETE AUTHORIZATION ──────────────────────────────────────────────────

  Scenario: Only the project owner can delete a project
    Given "bob@example.com" is a member (not owner) of project "proj_001"
    And I am authenticated as "bob@example.com"
    When I send DELETE /projects/proj_001
    Then the response status is 403
    And the response body contains error "Only the project owner can delete a project"

  Scenario: Deleting a non-existent project returns 404
    When I send DELETE /projects/proj_nonexistent
    Then the response status is 404

  Scenario: Cannot delete a project I am not a member of
    Given I am not a member of project "proj_999"
    When I send DELETE /projects/proj_999
    Then the response status is 403
