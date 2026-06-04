---
project: "Analizator Wydatkow"
version: 1
status: active
created: 2026-06-01
updated: 2026-06-03
prd_version: 1
main_goal: quality
top_blocker: none
---

# Roadmap: Analizator Wydatkow

> Derived from `context/foundation/prd.md` (v1) + auto-researched codebase baseline.
> Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Vision recap

The product removes monthly spreadsheet friction for a single user who imports CSV data from a Polish bank and needs useful spending categories quickly. The core promise is high first-pass auto-categorization quality with quick correction so category totals are trustworthy for budgeting decisions. This update prioritizes improving predefined categories and merchant mappings to raise categorization accuracy immediately after upload.

## North star

**S-07: predefined-categories-mappings-refresh** — User can upload CSV and get more transactions categorized correctly on first pass through improved predefined categories and merchant mappings.

> The north star here means the smallest end-to-end slice whose successful delivery proves the core hypothesis of this roadmap update: better initial categorization quality is the fastest path to trustworthy budget reporting.

## At a glance

| ID | Change ID | Outcome (user can …) | Prerequisites | PRD refs | Status |
|---|---|---|---|---|---|
| F-01 | auth-scaffold | (foundation) Login/registration and per-user data access control are in place | — | FR-001, FR-002 | done |
| S-01 | category-management | Create, edit, delete categories and use predefined starter categories | F-01 | FR-006, FR-007, FR-008 | done |
| S-02 | csv-import-autocategorize | Upload CSV and see transactions with auto-proposed categories | F-01, S-01 | FR-003, FR-004, US-01 | done |
| S-07 | predefined-categories-mappings-refresh | Improve predefined category and merchant mapping coverage for better first-pass categorization | S-02 | US-01, FR-004, FR-006 | done |
| S-03 | category-refinement-summary | Refine categories and view category spending summary | S-02 | FR-005, FR-009, US-01 | done |
| S-04 | transaction-filtering | Filter transactions by category and sort by any column | S-02 | FR-013, FR-014 | ready |
| S-05 | budget-cycles | Define paycheck-to-paycheck cycles and filter by cycle | S-02 | FR-010, FR-011 | ready |
| S-06 | style-and-usability-refresh | Use polished, consistent UI across dashboard/categories/transactions flows | S-02 | US-01, FR-004, FR-009, FR-013, FR-014 | done |

## Streams

Navigation aid — groups items that share a Prerequisites chain. Canonical ordering still lives in the dependency graph below; this table is the proposed reading order across parallel tracks.

| Stream | Theme | Chain | Note |
|---|---|---|---|
| A | Delivered MVP base | `F-01` → `S-01` → `S-02` | Established flow that all remaining slices build on. |
| B | Categorization accuracy lift | `S-07` | Prioritized by `main_goal: quality`; fastest quality gain after `S-02`. |
| C | Core product completion | `S-03` / `S-04` / `S-05` | Parallel-ready capability expansion once import flow is stable. |
| D | UX consistency | `S-06` | Can run independently as a quality pass on top of existing flows. |

## Baseline

What's already in place in the codebase as of 2026-06-01 (auto-researched + user-confirmed).
Foundations below assume these are present and do NOT re-scaffold them.

- **Frontend:** partial — Django templates + Bootstrap + vanilla JS are in use, without a frontend build pipeline.
- **Backend / API:** partial — Django server-rendered routes/views are in place, without a REST API layer.
- **Data:** present — Django ORM models, migrations, and seeded predefined mappings/categories are in place.
- **Auth:** partial — session-based auth and route protection exist; token-based auth is not present.
- **Deploy / infra:** partial — Render deployment config exists; CI workflow and container config are absent.
- **Observability:** absent — no dedicated metrics/error tracking instrumentation is configured.

## Foundations

### F-01: Auth scaffold

- **Outcome:** (foundation) Authenticated sessions and strict per-user data isolation are established and enforced.
- **Change ID:** auth-scaffold
- **PRD refs:** FR-001, FR-002, Access Control section
- **Unlocks:** S-01, S-02, S-03, S-04, S-05, S-06, S-07
- **Prerequisites:** —
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Incorrect access-control assumptions would invalidate all downstream budgeting capabilities.
- **Status:** done

## Slices

### S-01: Category management

- **Outcome:** User can create, edit, and delete custom categories, starting from predefined defaults.
- **Change ID:** category-management
- **PRD refs:** FR-006, FR-007, FR-008
- **Prerequisites:** F-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Category correctness is foundational for reporting quality and user trust in categorization.
- **Status:** done

### S-02: CSV import with auto-categorization

- **Outcome:** User can upload ING CSV data and immediately see categorized transactions with unknowns flagged.
- **Change ID:** csv-import-autocategorize
- **PRD refs:** FR-003, FR-004, US-01
- **Prerequisites:** F-01, S-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** This is the core product value; regressions here directly reduce user trust.
- **Status:** done

### S-07: Predefined categories and mappings refresh

- **Outcome:** User can rely on a stronger predefined category set and merchant mapping coverage so fewer imported transactions fall into "Unknown".
- **Change ID:** predefined-categories-mappings-refresh
- **PRD refs:** US-01, FR-004, FR-006
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04, S-05, S-06
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Over-broad mapping rules can improve hit-rate but silently misclassify merchants; precision guardrails are needed.
- **Status:** done

### S-03: Category refinement and summary

- **Outcome:** User can correct transaction categories and view category-level spending totals.
- **Change ID:** category-refinement-summary
- **PRD refs:** FR-005, FR-009, US-01
- **Prerequisites:** S-02
- **Parallel with:** S-04, S-05, S-06, S-07
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Learning behavior and summary totals must remain aligned with user corrections.
- **Status:** done

### S-04: Transaction filtering and sorting

- **Outcome:** User can filter and sort transaction lists to inspect spending details quickly.
- **Change ID:** transaction-filtering
- **PRD refs:** FR-013, FR-014
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-05, S-06, S-07
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Poor filter/sort UX can hide data and weaken trust even when logic is correct.
- **Status:** ready

### S-05: Budget cycles

- **Outcome:** User can define non-calendar budget cycles and filter transactions by selected cycle.
- **Change ID:** budget-cycles
- **PRD refs:** FR-010, FR-011
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04, S-06, S-07
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Date-range boundary bugs would distort paycheck-to-paycheck reporting.
- **Status:** ready

### S-06: Style and usability refresh

- **Outcome:** User can navigate dashboard, categories, and transactions in a visually consistent interface with clear actions and feedback.
- **Change ID:** style-and-usability-refresh
- **PRD refs:** US-01, FR-004, FR-009, FR-013, FR-014
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04, S-05, S-07
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Scope can drift from polish into behavior changes; this slice should stay UX-only.
- **Status:** ready

## Backlog Handoff

| Roadmap ID | Change ID | Suggested issue title | Ready for `/10x-plan` | Notes |
|---|---|---|---|---|
| F-01 | auth-scaffold | Auth scaffold with user isolation | no | Already implemented |
| S-01 | category-management | Category CRUD with predefined seed | no | Already implemented |
| S-02 | csv-import-autocategorize | CSV import and auto-categorization | no | Already implemented |
| S-07 | predefined-categories-mappings-refresh | Improve predefined categories and merchant mapping accuracy | no | Already implemented |
| S-03 | category-refinement-summary | Category refinement + summary table | no | Already implemented |
| S-04 | transaction-filtering | Category filter and sortable transactions | yes | Run `/10x-plan transaction-filtering` |
| S-05 | budget-cycles | Paycheck-cycle definition and filtering | yes | Run `/10x-plan budget-cycles` |
| S-06 | style-and-usability-refresh | UI polish for existing budgeting flows | no | Already implemented |

## Open Roadmap Questions

1. **No roadmap-wide open questions at this time.** — Owner: —. Block: —.

## Parked

- **FR-012: Bulk-edit category assignments** — Why parked: Nice-to-have in PRD; focus remains on must-have outcomes and categorization quality.
- **Direct bank API connection** — Why parked: Explicit PRD non-goal; CSV-only ingestion remains the MVP boundary.
- **Multi-bank support** — Why parked: Explicit PRD non-goal; ING-only scope is preserved.
- **Shared/family accounts** — Why parked: Explicit PRD non-goal; single-user account isolation is required.

## Done

- **F-01: Auth scaffold** — Implemented 2026-05-30. Lesson: —.
- **S-01: Category management** — Implemented 2026-05-30. Lesson: —.
- **S-02: CSV import with auto-categorization** — Implemented 2026-05-30. Lesson: —.
- **S-03: Category refinement and summary** — Implemented 2026-06-02. Lesson: context/foundation/lessons.md.
- **S-06: Style and usability refresh** — Implemented 2026-06-01. Lesson: context/foundation/lessons.md.
- **F-01: (foundation) Authenticated sessions and strict per-user data isolation are established and enforced.** — Archived 2026-06-03 → `context/archive/2026-05-30-auth-scaffold/`. Lesson: —.
- **S-01: User can create, edit, and delete custom categories, starting from predefined defaults.** — Archived 2026-06-03 → `context/archive/2026-05-30-category-management/`. Lesson: —.
- **S-02: User can upload ING CSV data and immediately see categorized transactions with unknowns flagged.** — Archived 2026-06-03 → `context/archive/2026-05-30-csv-import-autocategorize/`. Lesson: —.
