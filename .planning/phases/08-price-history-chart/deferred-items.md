# Deferred Items — Phase 08 (price-history-chart)

Out-of-scope discoveries logged per the executor's scope-boundary rule
("Only auto-fix issues DIRECTLY caused by the current task's changes").
Not fixed here.

## Plan 08-01

- **`npm audit` findings pre-existing before `recharts` install** — after
  installing `recharts@3.10.1`, `npm audit` reported 4 vulnerabilities
  (1 moderate, 3 high): `nanoid` (via `vite`'s `postcss` dependency),
  `postcss` itself, `undici` (via `jsdom`), and `react-router` (a direct
  dependency already pinned at `7.18.1` before this plan, vulnerable
  range `7.12.0 - 7.18.1`, fix available at `7.18.2`). Confirmed via
  `npm ls nanoid postcss undici` that none of these are transitive
  dependencies of `recharts` — `npm ls recharts` shows `recharts@3.10.1`
  with no further tree. All four predate this plan's changes and are
  unrelated to the file this task modified. Not fixed here — flagging
  for a future maintenance pass (e.g. `npm audit fix` for the
  `react-router` bump to `7.18.2`, which the plan's `<files>` list does
  not include).
