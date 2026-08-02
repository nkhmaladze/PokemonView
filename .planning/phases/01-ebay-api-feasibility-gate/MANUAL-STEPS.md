# Manual Steps: eBay Developer Portal Setup & Marketplace Insights Growth Check

**Phase:** 01-ebay-api-feasibility-gate
**Owner:** You (the user) — every step below happens in eBay's web portal and cannot be automated or performed by Claude on your behalf.
**Purpose:** Create the eBay Developer Program account and keysets needed for all of Phase 1's code, and submit the Marketplace Insights Application Growth Check as this project's sold-price access go/no-go gate.

This guide is self-contained — you can work through it independently of any Claude session. Nothing here requires pasting secrets into chat.

---

## Step 1: Create an eBay Developer Program account

You do not yet have an eBay Developer Program account (D-01). This is a prerequisite for everything else in Phase 1 — it blocks the verification script's live run (Plan 01-03/01-04) until complete.

1. Go to [developer.ebay.com](https://developer.ebay.com) and sign up for the Developer Program (uses your existing eBay account, or create one).
2. Complete any required profile/verification steps eBay's portal presents.

**Done when:** You can log in to `developer.ebay.com/my/keys` and see an empty (or existing) keyset list.

---

## Step 2: Create Sandbox + Production keysets

1. From the Developer Portal, navigate to **Application Keys** (`developer.ebay.com/my/keys`).
2. Create a keyset — eBay generates both a **Sandbox** keyset and a **Production** keyset for the same application automatically.
3. Note the **Production** keyset's **Client ID (App ID)** and **Client Secret (Cert ID)** somewhere private (a password manager, not a text file in this repo).

**Why you need the Production keyset specifically, not just Sandbox:** The Browse API needs no special approval — any Production keyset can call it immediately. But eBay's Sandbox catalog data is sparse and synthetic (it won't return real Pokemon sealed-product listings), so this phase's live verification script (SC-1, SC-4) requires the **Production** keyset and a **Production** API call to succeed. Sandbox is fine only as an earlier smoke-test of the OAuth handshake shape, never as a substitute for the real proof-of-life call.

**Done when:** You have a Production Client ID and Client Secret recorded somewhere private.

---

## Step 3: Populate `.env`

The credential handoff rule for this project (D-02): **you create `.env` yourself and paste your real values into it directly — you never paste credentials into a Claude chat, and Claude's code only ever reads `.env` at runtime without seeing the raw values.**

1. In the project root, copy the example file:
   ```
   cp .env.example .env
   ```
2. Open `.env` in your own editor (not through a Claude conversation) and fill in:
   ```
   EBAY_CLIENT_ID=<your real Production Client ID>
   EBAY_CLIENT_SECRET=<your real Production Client Secret>
   EBAY_ENV=production
   ```
3. Save the file.

**Never do this:**
- Never paste your real Client ID or Client Secret into a chat message to Claude.
- Never `git add .env` or commit `.env` — it is already listed in `.gitignore` (added in Plan 01-01) specifically to prevent this.

**Done when:** `.env` exists locally with real values, `.env` does not appear in `git status`, and no real credential value has been shared in chat.

---

## Step 4: Submit the Marketplace Insights Application Growth Check

This is the single highest-risk unknown in the whole project (per `research/PITFALLS.md` Pitfall 1 and `research/STACK.md`): sold-price data access is **not automatic**. Submitting this request early, as a go/no-go gate, is the entire point of Phase 1.

1. Log in to the Developer Portal (you must already have a Production keyset from Step 2 — the Growth Check reviews an upgrade to an *existing* application, it does not create a new one).
2. Navigate to: `https://developer.ebay.com/my/support/tickets?tab=app-check`
3. Fill in every field marked with a red asterisk. **Read each field's live info-tooltip as you go** — the exact field list (use-case description, estimated call volume, business-entity details) was not directly confirmed during this project's research session, so do not assume a specific set of fields in advance; the portal itself is the source of truth.
4. When you reach the use-case / justification text field, use **"Save as Draft"** to pause, then open `GROWTH-CHECK-NARRATIVE.md` (in this same phase directory) and paste that text in, filling in the `[YOUR BUSINESS ENTITY NAME]` placeholder with your real entity name first.
5. Have your existing business entity's name and details on hand (D-05) — the application should be submitted under your existing registered business entity, not as a new registration and not as an individual/hobby applicant (community reports indicate "personal project" framing correlates with denial — see `GROWTH-CHECK-NARRATIVE.md` for why this matters).
6. Click **Submit**.

**No published SLA:** eBay does not publish a turnaround time for Growth Check review. Per D-06, submission itself — not approval — is what satisfies this phase's success criterion (SC-2). Do not wait on a response before continuing to other Phase 1 work or later phases.

**Done when:** The Growth Check ticket has been submitted (not just saved as a draft).

---

## Submission Tracking

Fill in this table once you submit the Growth Check in Step 4. This satisfies SC-2's requirement that status be tracked with a decision-by date.

**Status as of 2026-08-02: denied.** The always-on worker had accrued 15.3 continuous days and 94 successful/partial ingestion runs of real production usage (first healthy run 2026-07-18, most recent 2026-08-02) before submission. The Growth Check was submitted via the Developer Portal using the narrative in `GROWTH-CHECK-NARRATIVE.md` (including its "Usage to date" section). eBay has since responded: the request was **denied**. This resolves Phase 1's go/no-go gate on the "no" branch — the project proceeds per `FALLBACK-DECISION.md` **Option 1** (ship active-listing-only v1; sold-price work rolls to a later milestone).

| Field | Value |
|-------|-------|
| Submitted date | 2026-08-02 |
| Ticket / reference ID | 260802-000004 |
| Self-imposed decision-by date | 2026-08-16 (~14 days after submission) — moot/superseded, outcome arrived early |
| Outcome | **denied** |
| Outcome recorded date | 2026-08-02 |

This outcome is now final and recorded. `FALLBACK-DECISION.md` Option 1 is the active path. If eBay ever reverses or re-opens this decision, this table can be updated and Phase 8 pulled forward at that point.

---

## Summary Checklist

- [x] eBay Developer Program account created
- [x] Production keyset created (Client ID + Client Secret recorded privately)
- [x] `.env` created from `.env.example` and populated with real values (never shared in chat, never committed)
- [x] Marketplace Insights Application Growth Check submitted using the narrative in `GROWTH-CHECK-NARRATIVE.md`
- [x] Submission Tracking table above filled in with submitted date, ticket ID, and self-imposed decision-by date
