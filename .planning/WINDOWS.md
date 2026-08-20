---
schema_version: 1
open_count: 2
waived_count: 0
fixed_count: 0
total_count: 2
last_updated: 2026-08-20T12:09:48.842Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 08 | unrun-verify | frontend/src/pages/ProductDetailPage.jsx |  | Task 2's <human-check> (browser confirmation of the rendered Recharts line chart, axis ticks, gridlines, tooltip) not run in this worktree agent — deferred per workflow.human_verify_mode=end-of-phase; see 08-01-SUMMARY.md coverage item D2 | open |  | 2026-08-20T11:17:09.047Z |  |
| 2 | 08 | unrun-verify | tests/conftest.py |  | pytest -q backend gate (phase verification) could not be confirmed green from Plan 08-04's worktree — 3 attempts all failed with pymongo.errors.OperationFailure/CollectionInvalid namespace-already-exists races from concurrent sibling worktree agents (08-02/08-03) sharing the same MongoDB Atlas pokemonview_test DB; not caused by 08-04's comment-only tokens.css change. Re-run sequentially post-merge for an authoritative signal. | open |  | 2026-08-20T12:09:48.842Z |  |

````json
[
  {
    "id": 1,
    "kind": "unrun-verify",
    "phase": "08",
    "file": "frontend/src/pages/ProductDetailPage.jsx",
    "line": null,
    "description": "Task 2's <human-check> (browser confirmation of the rendered Recharts line chart, axis ticks, gridlines, tooltip) not run in this worktree agent — deferred per workflow.human_verify_mode=end-of-phase; see 08-01-SUMMARY.md coverage item D2",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-20T11:17:09.047Z",
    "resolved_at": null
  },
  {
    "id": 2,
    "kind": "unrun-verify",
    "phase": "08",
    "file": "tests/conftest.py",
    "line": null,
    "description": "pytest -q backend gate (phase verification) could not be confirmed green from Plan 08-04's worktree — 3 attempts all failed with pymongo.errors.OperationFailure/CollectionInvalid namespace-already-exists races from concurrent sibling worktree agents (08-02/08-03) sharing the same MongoDB Atlas pokemonview_test DB; not caused by 08-04's comment-only tokens.css change. Re-run sequentially post-merge for an authoritative signal.",
    "status": "open",
    "reason": "",
    "recorded_at": "2026-08-20T12:09:48.842Z",
    "resolved_at": null
  }
]
````
