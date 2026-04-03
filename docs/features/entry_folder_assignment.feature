Feature: Entry to Folder Assignment
  As a team member
  I want to place entries in folders
  So that the knowledge base reflects the project structure

  Background:
    Given I am authenticated as "alice@example.com"
    And I am a member of project "proj_001"
    And folder "ADR" exists with id "folder_adr" in project "proj_001"

  # ── CREATE ────────────────────────────────────────────────────────────────

  Scenario: Create an entry inside a folder
    When I send POST /entries with body:
      """
      {
        "title": "Use MongoDB",
        "content": "<p>We decided...</p>",
        "entry_type": "adr",
        "project_id": "proj_001",
        "folder_id": "folder_adr"
      }
      """
    Then the response status is 201
    And the response body contains:
      | field     | value      |
      | folder_id | folder_adr |

  Scenario: Create an entry at project root (no folder)
    When I send POST /entries with body:
      """
      {
        "title": "General update",
        "content": "<p>...</p>",
        "entry_type": "update",
        "project_id": "proj_001"
      }
      """
    Then the response status is 201
    And the response body contains:
      | field     | value |
      | folder_id | null  |

  Scenario: Cannot assign an entry to a folder from a different project
    Given folder "X" exists with id "folder_x" in project "proj_002"
    When I send POST /entries with body:
      """
      {
        "title": "Misplaced",
        "content": "<p>...</p>",
        "entry_type": "adr",
        "project_id": "proj_001",
        "folder_id": "folder_x"
      }
      """
    Then the response status is 409
    And the response body contains error "Folder does not belong to the specified project"

  # ── MOVE ──────────────────────────────────────────────────────────────────

  Scenario: Move an entry to a different folder
    Given entry "entry_001" is currently in folder "folder_adr"
    And folder "Postmortem" exists with id "folder_pm" in project "proj_001"
    When I send PUT /entries/entry_001 with body:
      """
      { "folder_id": "folder_pm" }
      """
    Then the response status is 200
    And the response body contains:
      | field     | value     |
      | folder_id | folder_pm |

  Scenario: Move an entry to project root
    Given entry "entry_001" is currently in folder "folder_adr"
    When I send PUT /entries/entry_001 with body:
      """
      { "folder_id": null }
      """
    Then the response status is 200
    And the response body contains:
      | field     | value |
      | folder_id | null  |

  # ── LIST ──────────────────────────────────────────────────────────────────

  Scenario: List entries in a specific folder (direct children only)
    Given the following entries exist:
      | id    | title   | folder_id  |
      | e_001 | ADR-001 | folder_adr |
      | e_002 | ADR-002 | folder_adr |
      | e_003 | PM-001  | folder_pm  |
    When I send GET /entries?project_id=proj_001&folder_id=folder_adr
    Then the response status is 200
    And the response contains exactly 2 entries
    And all entries have folder_id "folder_adr"

  Scenario: List entries recursively from a folder and all its subfolders
    Given the following structure exists:
      | folder      | parent      | entries      |
      | folder_adr  | root        | e_001, e_002 |
      | folder_2024 | folder_adr  | e_003        |
      | folder_q1   | folder_2024 | e_004        |
    When I send GET /entries?project_id=proj_001&folder_id=folder_adr&recursive=true
    Then the response status is 200
    And the response contains exactly 4 entries

  # ── SEARCH ────────────────────────────────────────────────────────────────

  Scenario: Semantic search is scoped to a folder and its descendants when folder_id is provided
    When I send POST /search with body:
      """
      {
        "query": "database decision",
        "project_id": "proj_001",
        "folder_id": "folder_adr",
        "top_k": 5
      }
      """
    Then the response status is 200
    And all results belong to folder "folder_adr" or its descendants
