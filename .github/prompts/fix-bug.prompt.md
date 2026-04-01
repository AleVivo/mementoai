---
agent: agent
description: "Diagnose a bug with full awareness of MementoAI architecture"
tools: ["search/codebase", "vscode/askQuestions", ]
---

# Bug Diagnosis

Before proposing a fix, help me understand the bug fully. Ask me:

1. **Where does the bug appear?** (frontend UI / API response / AI pipeline / indexing / search / chat)
2. **What is the expected behavior?**
3. **What is the actual behavior?** (error message, wrong output, missing data)
4. **Is it reproducible?** Always / sometimes / after a specific action

Then, based on the area, check the most likely causes:

## If the bug is in the AI pipeline

Check in this order:
1. Is `langfuse_integration.is_active()` causing a path difference? (The observability code path has subtle differences from the non-active path)
2. Is the provider cache returning a stale provider? (Check if admin console changed config without the handler running)
3. Is the SSE stream closing before the `done` event? (Missing `finally` block in the generator)
4. Is `vector_status` still `pending` or `outdated`? (Entry was never indexed, so $vectorSearch finds nothing)

## If the bug is in authentication

Check in this order:
1. Is the access token expired? (30min TTL) — check if the silent refresh is firing correctly
2. Is the `require_admin` dependency used instead of `get_current_user` on a protected-but-not-admin endpoint? (returns 403 instead of 401)
3. Is `project_ids` correctly injected into agent tools via `InjectedState`? (project scoping is invisible to the LLM)

## If the bug is in save/index

**Critical distinction:** Save (`PUT /entries/:id`) and Index (`POST /entries/:id/index`) are completely separate. Confirm:
- Is `isDirty` being set correctly? (should be `true` on any content change, `false` after successful PUT)
- Is `vector_status` being set to `outdated` after a save? (backend responsibility)
- Is the `[Indicizza]` button correctly disabled while `isIndexing === true`?

## If the bug is in MongoDB

Check:
- Is the query filtering by `project_id` for multi-tenant data? Missing this filter would return entries from all projects.
- Is `ObjectId` conversion missing? (`str` IDs from the client must be cast to `ObjectId` before MongoDB queries)
- Is the `$vectorSearch` pre-filter matching the correct field name? (`project_id` must match the field name in the `chunks` collection metadata)

## Fix proposal

Only after the diagnosis, propose the minimal fix:
- Show the exact lines to change
- Explain why this fixes the root cause (not just the symptom)
- Note if the fix requires a corresponding change on the other side of the stack (e.g., a backend fix that also requires a frontend type update)
