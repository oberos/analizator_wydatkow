---
project: "Analizator Wydatkow"
version: 1
status: draft
created: 2026-06-04
updated: 2026-06-16
prd_version: 2
main_goal: quality
top_blocker: none
---

# Roadmap: Analizator Wydatkow

> Derived from `context/foundation/prd-v2.md` (v2) + auto-researched codebase baseline.
> Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Vision recap

The product targets monthly budget workflow friction: a single user imports bank CSV files, then needs reliable category-based totals without spreadsheet cleanup. The differentiator remains automatic categorization that improves through user corrections, so reporting can be trusted for decisions. This roadmap prioritizes report correctness first, including date-range summary behavior and optional dashboard visualization.

## North star

**S-04: Date-range summary reporting** — User can get category totals for a chosen date range (default today-30d to today), proving that reporting outputs are decision-ready.

> The "north star" here means the smallest end-to-end slice that proves the core product hypothesis in practice: if this slice works reliably, the rest of the roadmap has value.

## At a glance

| ID | Change ID | Outcome (user can …) | Prerequisites | PRD refs | Status |
|---|---|---|---|---|---|
| F-01 | access-isolation-hardening | (foundation) access-isolation and auth entry constraints are explicitly hardened for downstream reporting flows | — | FR-001, FR-002, Access Control | ready |
| S-01 | category-management | create, edit, and delete custom categories | F-01 | FR-006, FR-007, FR-008 | done |
| S-02 | csv-import-autocategorization | upload CSV and see auto-proposed categories | F-01, S-01 | FR-003, FR-004, US-01 | done |
| S-03 | category-correction-loop | refine transaction categories and persist corrections | S-02 | FR-005, US-01 | done |
| S-04 | date-range-summary-reporting | view summary totals for selected start/end dates with default last-30-days window | S-02 | FR-009, FR-010, FR-011, US-01 | done |
| S-05 | transaction-list-filter-sort | filter transactions by category and sort by column | S-02 | FR-013, FR-014 | done |
| S-06 | dashboard-pie-chart-summary | view optional pie chart generated from current summary-table totals | S-04 | FR-015, US-01 | proposed |

## Streams

Navigation aid — groups items that share a Prerequisites chain. Canonical ordering still lives in the dependency graph below; this table is the proposed reading order across parallel tracks.

| Stream | Theme | Chain | Note |
|---|---|---|---|
| A | Core categorization path | `F-01` → `S-01` → `S-02` → `S-03` | Builds trusted categorized data before report expansion. |
| B | Reporting correctness | `S-04` → `S-06` | Joins Stream A at `S-02`; this is the quality-biased validation path. |
| C | Transaction inspection | `S-05` | Joins Stream A at `S-02`; expands analysis depth in parallel. |

## Baseline

What's already in place in the codebase as of 2026-06-04 (auto-researched + user-confirmed).
Foundations below assume these are present and do NOT re-scaffold them.

- **Frontend:** partial — server-rendered UI with reusable styling and JS exists, without a dedicated frontend build pipeline.
- **Backend / API:** present — application routing and request handlers are implemented.
- **Data:** partial — ORM models, schema migrations, and migration-based seed data exist.
- **Auth:** partial — session-based authentication and protected routes exist; token/role depth is limited.
- **Deploy / infra:** partial — deployment config exists; CI and container layers are not fully wired.
- **Observability:** absent — structured logging, metrics, and error-tracking foundations are missing.

## Foundations

### F-01: Access-isolation hardening

- **Outcome:** (foundation) access and isolation constraints are explicitly hardened so downstream reporting and categorization slices can assume user-safe boundaries.
- **Change ID:** access-isolation-hardening
- **PRD refs:** FR-001, FR-002, Access Control section, Guardrails
- **Unlocks:** S-01, S-02, S-03, S-04, S-05, S-06
- **Prerequisites:** —
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** If access boundaries drift, downstream reporting quality becomes untrustworthy despite correct business logic.
- **Status:** ready

## Slices

### S-01: Category management

- **Outcome:** user can create, edit, and delete custom categories.
- **Change ID:** category-management
- **PRD refs:** FR-006, FR-007, FR-008
- **Prerequisites:** F-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Poor category management undermines all later categorization and summary accuracy.
- **Status:** done

### S-02: CSV import with auto-categorization

- **Outcome:** user can upload CSV and immediately see transactions with auto-proposed categories.
- **Change ID:** csv-import-autocategorization
- **PRD refs:** FR-003, FR-004, US-01
- **Prerequisites:** F-01, S-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Ingestion/categorization regressions collapse trust in every downstream reporting capability.
- **Status:** done

### S-03: Category correction loop

- **Outcome:** user can correct category assignments and keep categorization outcomes aligned with intent.
- **Change ID:** category-correction-loop
- **PRD refs:** FR-005, US-01
- **Prerequisites:** S-02
- **Parallel with:** S-04, S-05
- **Blockers:** —
- **Unknowns:** —
- **Risk:** If corrections do not reliably feed the categorization loop, quality stalls below target.
- **Status:** done

### S-04: Date-range summary reporting

- **Outcome:** user can view category summary totals for a chosen start/end date range, defaulting to last 30 days.
- **Change ID:** date-range-summary-reporting
- **PRD refs:** FR-009, FR-010, FR-011, US-01
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-05
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Date-boundary handling errors can silently distort financial totals and erode trust.
- **Status:** done

### S-05: Transaction list filtering and sorting

- **Outcome:** user can filter transactions by category and sort by any key column for detailed inspection.
- **Change ID:** transaction-list-filter-sort
- **PRD refs:** FR-013, FR-014
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Weak inspection UX makes it harder to validate whether summary totals are correct.
- **Status:** done

### S-06: Dashboard pie-chart visualization

- **Outcome:** user can optionally view a pie chart generated from the same summary-table totals for the selected date range.
- **Change ID:** dashboard-pie-chart-summary
- **PRD refs:** FR-015, US-01
- **Prerequisites:** S-04
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** If chart values diverge from summary totals, confidence drops even when table values are correct.
- **Status:** proposed

## Backlog Handoff

| Roadmap ID | Change ID | Suggested issue title | Ready for `/10x-plan` | Notes |
|---|---|---|---|---|
| F-01 | access-isolation-hardening | Harden access isolation assumptions for reporting path | yes | Run `/10x-plan access-isolation-hardening` |
| S-01 | category-management | Category CRUD and management flow | no | Already implemented |
| S-02 | csv-import-autocategorization | CSV import plus first-pass auto-categorization | no | Already implemented |
| S-03 | category-correction-loop | Category correction persistence loop | no | Already implemented |
| S-04 | date-range-summary-reporting | Summary table by selected date range with default last-30-days | no | Depends on S-02 |
| S-05 | transaction-list-filter-sort | Transaction filtering and sorting for drilldown | no | Depends on S-02 |
| S-06 | dashboard-pie-chart-summary | Optional dashboard pie chart from summary totals | no | Depends on S-04 |

## Open Roadmap Questions

1. **What is the expected request volume (`target_scale.qps`) for this MVP?** — Owner: user. Block: roadmap-wide.
2. **What is the expected data-volume ballpark (`target_scale.data_volume`) for this MVP?** — Owner: user. Block: roadmap-wide.

## Parked

- **FR-012: Bulk-edit category assignments** — Why parked: marked nice-to-have in PRD; must-have reporting and categorization quality come first.
- **Direct bank API connection** — Why parked: explicit PRD non-goal; CSV-only ingestion stays in scope boundary.
- **Multi-bank support** — Why parked: explicit PRD non-goal; ING-only scope remains the MVP limit.
- **No mobile app** — Why parked: explicit PRD non-goal; native mobile surface is deferred.
- **Shared/family accounts** — Why parked: explicit PRD non-goal; single-user isolation model is preserved.

## Done

- **S-01: user can create, edit, and delete custom categories.** — Implemented 2026-06-04. Lesson: —.
- **S-02: user can upload CSV and see auto-proposed categories.** — Implemented 2026-06-04. Lesson: —.
- **S-03: user can refine transaction categories and persist corrections.** — Implemented 2026-06-04. Lesson: —.
- **S-04: user can view category summary totals for a chosen start/end date range, defaulting to last 30 days.** — Archived 2026-06-16 → `context/archive/2026-06-04-date-range-summary-reporting/`. Lesson: —.
- **S-05: user can filter transactions by category and sort by any key column for detailed inspection.** — Archived 2026-06-16 → `context/archive/2026-06-04-transaction-list-filter-sort/`. Lesson: —.
