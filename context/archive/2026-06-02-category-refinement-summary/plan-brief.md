# Category Refinement and Summary - Plan Brief

> Full plan: `context/changes/category-refinement-summary/plan.md`

## What & Why

This change delivers S-03: the user can correct transaction categories and see category spending totals. It closes the core journey from upload to trustworthy budget insight by ensuring manual corrections directly improve future auto-categorization and by exposing clear totals on the dashboard.

## Starting Point

Transactions and merchant mappings already exist from S-02, and CSV imports already auto-assign categories. However, category assignment is currently read-only on the Transactions page and dashboard has no spending summary.

## Desired End State

The user can adjust a transaction category in one action on the Transactions page, and that correction updates future matching behavior for the same merchant. The Dashboard shows per-category totals for the logged-in user, including explicit Unknown/unassigned handling. The full flow remains isolated per account, with no cross-user visibility or mutation.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| Edit location | Transactions page | Keeps correction action close to row context and matches existing table workflow. |
| Summary location | Dashboard page | Matches your explicit preference and keeps dashboard as the high-level spending view. |
| Learning behavior | Upsert mapping on concrete category; remove mapping when set to Unknown/empty | Prevents bad learning loops while preserving correction intent. |
| Summary computation | On-demand ORM aggregation | Avoids schema/caching complexity and keeps totals always consistent with edits. |
| Scope boundary | No bulk edit, no S-04/S-05 behavior | Protects S-03 from scope creep and keeps delivery focused. |
| Performance target | MVP scale (hundreds to low-thousands/user), no cache | Fits expected usage and avoids premature optimization. |

## Scope

**In scope:**
- Single-action category correction per transaction row.
- Mapping learning synchronization with correction behavior.
- Dashboard table with per-category spending totals.
- Focused tests for correction logic, summary correctness, and user isolation.

**Out of scope:**
- Bulk category editing.
- Filtering/sorting enhancements and budget-cycle filtering.
- Charting/advanced analytics.
- Materialized summary or cache invalidation architecture.

## Architecture / Approach

Use a server-rendered POST flow. A correction endpoint validates transaction/category ownership, applies the category update, and synchronizes merchant mapping using existing normalization logic. Dashboard summary is derived from user-scoped `Transaction` aggregation at request time. This keeps behavior consistent with existing Django CBV patterns and security conventions in the codebase.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Correction Backend | User-scoped correction endpoint + mapping sync rules | Incorrect validation could allow unauthorized updates. |
| 2. Transactions UX | Inline single-action category editing controls | Template/form wiring could regress existing upload/delete flows. |
| 3. Dashboard Summary | Category totals on dashboard from scoped aggregation | Misaligned Unknown/null handling could produce misleading totals. |
| 4. Regression Hardening | End-to-end confidence across import -> refine -> summary | Incomplete tests could miss learning regressions. |

**Prerequisites:** S-02 is implemented; categories and transaction models are already present.
**Estimated effort:** ~2-3 implementation sessions across 4 phases.

## Open Risks & Assumptions

- Assumes summary refresh on submit + reload is acceptable (no live in-page recompute requirement).
- Assumes mapping removal on Unknown/empty best reflects user intent for future imports.
- Assumes current MVP data volume does not require cached/materialized summary.

## Success Criteria (Summary)

- User can change any transaction category in one action on Transactions and see persisted result.
- Future imports reflect learned corrections for the same merchant, except when mapping is intentionally removed via Unknown/empty.
- Dashboard category totals are correct for the logged-in user and isolated from other accounts.
