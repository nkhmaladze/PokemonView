---
phase: 07-launch-hardening-v1-active-price
plan: 05
subsystem: infra
tags: [vercel, vite, cors, flask-cors, fly-io, deploy]

# Dependency graph
requires:
  - phase: 07-launch-hardening-v1-active-price (plan 04)
    provides: Live Fly.io-hosted Flask API at https://pokemonview.fly.dev with permissive placeholder CORS
provides:
  - Deployed public React SPA on Vercel at https://frontend-black-one-22.vercel.app
  - frontend/.env.production wiring the SPA's build-time API base URL to the live Fly API
  - Fixed api/client.js to actually read VITE_API_BASE_URL (previously hardcoded to '')
  - CORS_ORIGINS on the Fly API pinned to the real Vercel origin (closing the wildcard/placeholder window from plan 07-04)
affects: [phase-08, any-future-frontend-hosting-change, any-future-cors-origin-change]

# Tech tracking
tech-stack:
  added: [vercel (npm global CLI, human-approved via package-legitimacy gate)]
  patterns:
    - "Vite VITE_* env vars are inlined at build time via a per-environment .env.production file, never at runtime"
    - "CORS_ORIGINS is a Fly secret, updated via `fly secrets set` which triggers an automatic rolling restart (no `fly deploy` needed)"

key-files:
  created:
    - frontend/.env.production
  modified:
    - frontend/src/api/client.js
    - frontend/.gitignore

key-decisions:
  - "Approved vercel npm CLI install after human verification against npmjs.com/package/vercel (official Vercel org, 2.7M weekly downloads, SUS flag was a too-new false positive from continuous-release cadence)"
  - "Used https://frontend-black-one-22.vercel.app as the canonical public production origin — the two other Vercel-issued aliases for this deployment are behind Vercel's own SSO wall by default and are not the public-facing URL"
  - "CORS_ORIGINS set to the single explicit Vercel origin (not a wildcard), closing the temporary permissive-CORS window opened during plan 07-04's deploy verification"

patterns-established:
  - "Frontend env files only ever carry public VITE_* build-time values — never MONGODB_URI/eBay/Discord secrets — enforced by the acceptance-criteria grep in the plan and re-confirmed here"

requirements-completed: [SC-1]

coverage:
  - id: D1
    description: "vercel npm CLI install approved via blocking-human package-legitimacy checkpoint before use"
    requirement: "SC-1"
    verification:
      - kind: manual_procedural
        ref: "Human confirmed npmjs.com/package/vercel legitimacy and typed 'approved'"
        status: pass
    human_judgment: false
  - id: D2
    description: "frontend/.env.production created with VITE_API_BASE_URL=https://pokemonview.fly.dev, no secrets present"
    requirement: "SC-1"
    verification:
      - kind: other
        ref: "grep -c 'VITE_API_BASE_URL=https://' frontend/.env.production"
        status: pass
    human_judgment: false
  - id: D3
    description: "SPA deployed to Vercel production and reachable at https://frontend-black-one-22.vercel.app, API calls succeed with no CORS error, CORS_ORIGINS pinned to the real Vercel origin"
    requirement: "SC-1"
    verification:
      - kind: manual_procedural
        ref: "Human confirmed live in browser DevTools: GET https://pokemonview.fly.dev/products returns 200, no CORS console error"
        status: pass
    human_judgment: true
    rationale: "Live cross-origin browser verification (CORS behavior, actual rendered catalog data) requires human observation of DevTools Network tab — not scriptable from this agent's sandbox."

# Metrics
duration: N/A (multi-session, spans checkpoint-gated human actions)
completed: 2026-07-15
status: complete
---

# Phase 07 Plan 05: Deploy React SPA to Vercel + CORS Summary

**Vite SPA deployed to Vercel production at https://frontend-black-one-22.vercel.app, wired to the live Fly API via VITE_API_BASE_URL, with CORS_ORIGINS pinned to the real Vercel origin — completing SC-1 end-to-end.**

## Performance

- **Tasks:** 3/3 completed
- **Files modified:** 3 (`frontend/.env.production` created, `frontend/src/api/client.js` fixed, `frontend/.gitignore` updated)

## Accomplishments
- Human approved the `vercel` npm global CLI against the package-legitimacy gate (SUS `too-new` false positive; official Vercel org, 2.7M weekly downloads).
- Created `frontend/.env.production` with `VITE_API_BASE_URL=https://pokemonview.fly.dev` (the real Fly host recorded in plan 07-04), containing only a public build-time value — no secrets.
- Found and fixed a real bug in `frontend/src/api/client.js`: `BASE` was hardcoded to `''` and never read `VITE_API_BASE_URL` at all, which would have made the deployed SPA call its own Vercel origin (a 404, no such route) instead of the Fly API — silently breaking the entire production deploy despite `.env.production` being correctly configured.
- Deployed the SPA to Vercel production (`vercel --prod` from `frontend/`), auto-detected as a Vite project, inlining `VITE_API_BASE_URL` at build time. Public production URL: `https://frontend-black-one-22.vercel.app` (two other Vercel-issued aliases exist but sit behind Vercel's own SSO wall by default and are not used as the canonical public URL).
- Updated `frontend/.gitignore` for the `.vercel/` local project-link metadata directory that `vercel --prod` auto-creates (project id / org id, not a secret).
- Ran `fly secrets set CORS_ORIGINS="https://frontend-black-one-22.vercel.app" --app pokemonview`, which triggered Fly's automatic rolling restart (no `fly deploy` needed) and pinned the API's CORS policy to the real Vercel origin, closing the permissive placeholder-CORS window from plan 07-04.
- Verified the CORS mechanism directly via curl origin tests: requests from the Vercel origin are allowed, requests from an arbitrary other origin are blocked.
- Human confirmed live in a real browser: the SPA loads at its Vercel URL, DevTools Network tab shows `GET https://pokemonview.fly.dev/products` returning HTTP 200 with no CORS console error, and the catalog renders live data from the deployed API.

## Task Commits

Each task was committed atomically:

1. **Task 1: Package-legitimacy gate — vercel (npm global CLI)** — checkpoint approved by human, no code commit (approval-only gate).
2. **Task 2: Create frontend/.env.production with the live Fly API URL** — `9efe0ce` (feat) — includes the Rule 1/2 auto-fix to `api/client.js` described below.
3. **Task 3: Deploy SPA to Vercel + point CORS_ORIGINS at the Vercel origin + verify no CORS error** — `331691e` (chore, `.gitignore` update); the Vercel deploy itself and the `fly secrets set` CORS update are external-service actions with no local commit artifact beyond the `.gitignore` change.

_Note: No plan-metadata docs commit for this SUMMARY exists yet — created in this closing pass._

## Files Created/Modified
- `frontend/.env.production` - `VITE_API_BASE_URL=https://pokemonview.fly.dev` (public build-time value, no secrets)
- `frontend/src/api/client.js` - `BASE` now reads `import.meta.env.VITE_API_BASE_URL` (falls back to `''` for dev/test) instead of being hardcoded to `''`
- `frontend/.gitignore` - ignores `.vercel/` local project-link metadata (auto-created by `vercel --prod`)

## Decisions Made
- Approved `vercel` npm CLI after human verification against npmjs.com/package/vercel — SUS flag confirmed as a `too-new` false positive from Vercel's continuous-release cadence, not a typosquat/unknown publisher.
- Selected `https://frontend-black-one-22.vercel.app` as the canonical public production URL; the other Vercel-issued aliases are behind Vercel's default SSO wall and intentionally not used as the public-facing origin.
- Set `CORS_ORIGINS` to the single explicit Vercel origin (not a wildcard), matching Phase 5 CR-02's comma-split convention in `api/config.py` and closing the temporary permissive-CORS state from plan 07-04.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `api/client.js`'s `BASE` never read `VITE_API_BASE_URL`**
- **Found during:** Task 2 (Create frontend/.env.production with the live Fly API URL)
- **Issue:** `BASE` was hardcoded to `''` with a comment claiming it was "relative — Vite dev proxy (or same-origin prod) handles routing." In production the SPA is served from a static host (Vercel) with no same-origin API — this would have made every fetch call target the SPA's own origin (`https://frontend-black-one-22.vercel.app/products`), a 404, completely breaking the production deploy despite `frontend/.env.production` being correctly set. This directly threatened Pitfall 4 (VITE_* inlining) and SC-1.
- **Fix:** Changed `BASE` to `import.meta.env.VITE_API_BASE_URL || ''`, so dev/test still falls back to the empty string (Vite proxy handles `/products` locally) while production build inlines the real Fly API origin.
- **Files modified:** `frontend/src/api/client.js`
- **Verification:** Confirmed via the completed Vercel deploy + browser DevTools check — `GET https://pokemonview.fly.dev/products` returns 200 with the correct absolute origin, catalog renders live data.
- **Committed in:** `9efe0ce` (part of Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix, Rule 1)
**Impact on plan:** This fix was essential — without it, the entire SC-1 end-to-end deploy would have silently failed (SPA calling a nonexistent same-origin route). No scope creep; purely a correctness fix required to make the plan's stated outcome achievable.

## Issues Encountered
None beyond the deviation documented above.

## User Setup Required
None - all external service configuration (Vercel auth, `fly secrets set`) was performed as part of the plan's human-action checkpoints and is already live in production.

## Next Phase Readiness
- SC-1 is fully satisfied end-to-end: the public SPA at `https://frontend-black-one-22.vercel.app` successfully reads live data from the public Fly API at `https://pokemonview.fly.dev` with no CORS errors.
- CORS_ORIGINS is pinned to the real Vercel origin (not a wildcard), closing the last open security item from plan 07-04.
- This is the final plan in Phase 7 (launch hardening) — Phase 7 is now complete pending orchestrator-level STATE.md/ROADMAP.md updates.

---
*Phase: 07-launch-hardening-v1-active-price*
*Completed: 2026-07-15*
