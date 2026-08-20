---
phase: 8
slug: price-history-chart
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-08-20
---

# Phase 8 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| browser → Flask API | `GET /products/<product_id>/history` accepts an untrusted URL path segment from any CORS-allowed origin | product_id (untrusted string) |
| Flask API → MongoDB | `product_id` crosses into the `price_points` query filter | product_id (untrusted string) |
| npm registry → frontend build | `recharts` and its transitive dependencies enter the built bundle | third-party package code |
| API JSON → Recharts DOM | `ts` and `total_price` values from the database become axis tick and tooltip text inside the rendered SVG | price/date data (DB-sourced) |
| route parameter → request URL | `productId` from `useParams` is interpolated into the requested path | product_id (untrusted string) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-08-SC | Tampering | `npm install recharts@3.10.1` (frontend/package.json) | high | mitigate | Package-legitimacy gate required a human-verify checkpoint before install; `package-lock.json` pins the exact resolved version 3.10.1 with an SRI integrity hash; confirmed no `postinstall`/`preinstall` script exists in the installed package's own package.json — no install-time code execution surface | closed |
| T-08-01 | Information Disclosure | `price_service.get_price_history` → `/products/<id>/history` route | low | mitigate | Builds plain `{ts, total_price}` dicts and never hands a raw pymongo document to `jsonify()` — confirmed in `api/services/price_service.py`; the BSON `_id` and `item_price`/`listing_count` fields never reach the response | closed |
| T-08-02 | Tampering | `product_id` path segment → `db.price_points.find` filter | low | mitigate | `product_id` is bound as a plain value in an equality filter (`{"product_id": product_id}`), never interpolated into a query operator — confirmed in `api/services/price_service.py` | closed |
| T-08-03 | Denial of Service | unbounded `GET /products/<id>/history` response size | low | accept | Documented volume assumption (~6 points/day/product) with an explicit revisit trigger in the service docstring; a range/window parameter is deferred until real volume growth justifies it | closed |
| T-08-04 | Tampering | Recharts renders `ts`/`total_price` as tick and tooltip text | low | mitigate | Values pass through `Intl.DateTimeFormat`/numeric formatters into React text children (which escape by default); confirmed no `dangerouslySetInnerHTML` and no SVG string injection anywhere in `PriceHistoryChart.jsx` | closed |
| T-08-05 | Information Disclosure | unknown-id probing via `GET /products/<id>/history` | low | accept | Catalog is entirely public; returning `200 []` for an unknown id discloses strictly less than the existing product-detail route's 404 | closed |
| T-08-06 | Denial of Service | client-side render cost of an unbounded series | low | accept | Recharts renders SVG per point — an accepted tradeoff at current/expected v1.1 data volume; revisit trigger documented alongside T-08-03 | closed |
| T-08-07 | Tampering | Recharts SVG subtree treated as a test contract | low | mitigate | Tests assert only against the project-owned `data-testid` hook and CSS-module class, never against Recharts-internal element classes | closed |
| T-08-08 | Information Disclosure | chart section's error branch | low | mitigate | Renders a fixed literal string ("Couldn't load price history. Try refreshing the page.") and never interpolates the rejected `Error`'s message — confirmed in `ProductDetailPage.jsx`; no internal error detail can reach the page | closed |
| T-08-09 | Spoofing | `productId` from `useParams` interpolated into the request path | low | mitigate | `getPriceHistory` passes the value through `encodeURIComponent` before building the path — confirmed in `frontend/src/api/client.js:54` | closed |
| T-08-10 | Tampering | a stale in-flight response applied to the wrong product | low | mitigate | The history fetch uses an `AbortController` (upgraded from the plan's original `cancelled`-flag design per WR-02, `08-REVIEW.md`) — the superseded request is actually cancelled, not just its result discarded client-side; confirmed in `ProductDetailPage.jsx` | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-08-01 | T-08-03 | Unbounded history response size accepted at current ~6 pts/day/product volume; REQUIREMENTS.md records downsampling as explicitly out of scope for v1.1 with a documented revisit trigger | plan-time (08-01-PLAN.md) | 2026-08-20 |
| AR-08-02 | T-08-05 | `200 []` for an unknown product id discloses no more than the already-public catalog's existing 404 on the detail route | plan-time (08-02-PLAN.md) | 2026-08-20 |
| AR-08-03 | T-08-06 | Per-point SVG render cost accepted at current/expected v1.1 data volume, consistent with CLAUDE.md's Recharts-vs-Chart.js tradeoff table | plan-time (08-03-PLAN.md) | 2026-08-20 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-08-20 | 11 | 11 | 0 | orchestrator (L1 grep-depth: register authored at plan time across all 4 PLAN.md files, asvs_level 1 — mitigations verified directly against `price_service.py`, `PriceHistoryChart.jsx`, `ProductDetailPage.jsx`, `client.js`, `package-lock.json`; no OPEN threats found, so per the short-circuit rule the dedicated auditor subagent was not spawned) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-08-20
