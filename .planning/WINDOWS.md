---
schema_version: 1
open_count: 1
waived_count: 0
fixed_count: 0
total_count: 1
last_updated: 2026-08-20T11:17:09.047Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 08 | unrun-verify | frontend/src/pages/ProductDetailPage.jsx |  | Task 2's <human-check> (browser confirmation of the rendered Recharts line chart, axis ticks, gridlines, tooltip) not run in this worktree agent — deferred per workflow.human_verify_mode=end-of-phase; see 08-01-SUMMARY.md coverage item D2 | open |  | 2026-08-20T11:17:09.047Z |  |

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
  }
]
````
