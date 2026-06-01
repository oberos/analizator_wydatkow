---
project: "Analizator Wydatkow"
version: 1
status: active
created: 2026-05-30
updated: 2026-05-30
prd_version: 1
main_goal: quality
top_blocker: none
---

# Roadmap: Analizator Wydatkow

> Derived from `context/foundation/prd.md` (v1) + auto-researched codebase baseline.
> Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Vision recap

The product removes monthly spreadsheet friction for a single user who imports CSV data from a Polish bank and needs useful spending categories quickly. The core promise is auto-categorization plus fast refinement so the user can trust category totals without manual Excel cleanup each month. This revision focuses on UX quality because core functionality is already running and the main gap is interface clarity and visual consistency.

## North star

**S-06: style-and-usability-refresh** — User can complete core budgeting flows in a clean, consistent interface with clear visual hierarchy and feedback.

> The north star means the smallest end-to-end slice that proves this iteration's hypothesis; here the hypothesis is that better UX quality reduces friction in daily use without changing core business logic.

## At a glance

| ID | Change ID | Outcome (user can …) | Prerequisites | PRD refs | Status |
|---|---|---|---|---|---|
| F-01 | auth-scaffold | (foundation) Login/registration and per-user data access control are in place | — | FR-001, FR-002 | done |
| S-01 | category-management | Create, edit, delete categories and use predefined starter categories | F-01 | FR-006, FR-007, FR-008 | done |
| S-02 | csv-import-autocategorize | Upload CSV and see transactions with auto-proposed categories | F-01, S-01 | FR-003, FR-004, US-01 | done |
| S-03 | category-refinement-summary | Refine categories and view category spending summary | S-02 | FR-005, FR-009, US-01 | ready |
| S-04 | transaction-filtering | Filter transactions by category and sort by any column | S-02 | FR-013, FR-014 | ready |
| S-05 | budget-cycles | Define paycheck-to-paycheck cycles and filter by cycle | S-02 | FR-010, FR-011 | ready |
| S-06 | style-and-usability-refresh | Use polished, consistent UI across dashboard/categories/transactions flows | S-02 | US-01, FR-004, FR-009, FR-013, FR-014 | ready |

## Streams

Navigation aid — groups items that share a Prerequisites chain. Canonical ordering still lives in the dependency graph below; this table is the proposed reading order across parallel tracks.

| Stream | Theme | Chain | Note |
|---|---|---|---|
| A | Delivered core flow | `F-01` → `S-01` → `S-02` | Completed chain that established the working MVP base. |
| B | Core product completion | `S-03` / `S-04` / `S-05` | Parallel-ready product capabilities after `S-02`. |
| C | UX quality pass | `S-06` | Prioritized by `main_goal: quality`; can run now on top of `S-02`. |

## Baseline

What's already in place in the codebase as of 2026-05-30 (auto-researched + user-confirmed).
Foundations below assume these are present and do NOT re-scaffold them.

- **Frontend:** present — Django templates are active (`templates/dashboard.html`, `templates/transactions/transaction_list.html`)
- **Backend / API:** present — Django class/function views and routing are wired (`analizator_wydatkow/urls.py`, `transactions/views.py`)
- **Data:** present — ORM models and migrations exist for categories/transactions (`transactions/models.py`, `transactions/migrations/`)
- **Auth:** present — login/register/session guards are in place (`accounts/views.py`, `accounts/urls.py`, Django auth includes)
- **Deploy / infra:** partial — `render.yaml` exists, but no CI workflow or container config
- **Observability:** absent — no explicit metrics/error tracking stack configured

## Foundations

### F-01: Auth scaffold

- **Outcome:** (foundation) Authenticated user sessions and strict per-user data isolation are established and enforced.
- **Change ID:** auth-scaffold
- **PRD refs:** FR-001, FR-002, Access Control section
- **Unlocks:** S-01, S-02, S-03, S-04, S-05, S-06
- **Prerequisites:** —
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Low risk now; incorrect auth assumptions would invalidate all user-data features, so it remains the root prerequisite.
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
- **Risk:** Category correctness is foundational for later reporting and categorization trust.
- **Status:** done

### S-02: CSV import with auto-categorization

- **Outcome:** User can upload ING CSV data and immediately see categorized transactions with unknowns flagged.
- **Change ID:** csv-import-autocategorize
- **PRD refs:** FR-003, FR-004, US-01
- **Prerequisites:** F-01, S-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** This remains the product differentiator; regressions here directly harm core value.
- **Status:** done

### S-03: Category refinement and summary

- **Outcome:** User can correct transaction categories and view category-level spending totals.
- **Change ID:** category-refinement-summary
- **PRD refs:** FR-005, FR-009, US-01
- **Prerequisites:** S-02
- **Parallel with:** S-04, S-05, S-06
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Learning behavior and summary correctness must remain aligned with user edits.
- **Status:** ready

### S-04: Transaction filtering and sorting

- **Outcome:** User can filter and sort transaction lists to inspect spending details quickly.
- **Change ID:** transaction-filtering
- **PRD refs:** FR-013, FR-014
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-05, S-06
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Low technical risk; UX decisions on filter/sort controls can still affect usability.
- **Status:** ready

### S-05: Budget cycles

- **Outcome:** User can define non-calendar budget cycles and filter transactions by selected cycle.
- **Change ID:** budget-cycles
- **PRD refs:** FR-010, FR-011
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04, S-06
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Date-range correctness is critical for paycheck-based budgeting accuracy.
- **Status:** ready

### S-06: Style and usability refresh

- **Outcome:** User can navigate dashboard, categories, and transactions in a visually consistent, cleaner interface with clearer actions and feedback.
- **Change ID:** style-and-usability-refresh
- **PRD refs:** US-01, FR-004, FR-009, FR-013, FR-014
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04, S-05
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Scope creep risk is high in UI polish; keep scope to existing flows and avoid new business behavior.
- **Status:** ready

## Backlog Handoff

| Roadmap ID | Change ID | Suggested issue title | Ready for `/10x-plan` | Notes |
|---|---|---|---|---|
| F-01 | auth-scaffold | Auth scaffold with user isolation | no | Already implemented |
| S-01 | category-management | Category CRUD with predefined seed | no | Already implemented |
| S-02 | csv-import-autocategorize | CSV import and auto-categorization | no | Already implemented |
| S-03 | category-refinement-summary | Category refinement + summary table | yes | Run `/10x-plan category-refinement-summary` |
| S-04 | transaction-filtering | Category filter and sortable transactions | yes | Run `/10x-plan transaction-filtering` |
| S-05 | budget-cycles | Paycheck-cycle definition and filtering | yes | Run `/10x-plan budget-cycles` |
| S-06 | style-and-usability-refresh | UI polish for existing budgeting flows | yes | Run `/10x-plan style-and-usability-refresh` |

## Open Roadmap Questions

1. **No roadmap-wide open questions at this time.** — Owner: —. Block: —.

## Parked

- **FR-012: Bulk-edit category assignments** — Why parked: Nice-to-have in PRD; keep focus on must-have and current UX polish priority.
- **Direct bank API connection** — Why parked: Explicit PRD non-goal; CSV-only ingestion remains the MVP boundary.
- **Multi-bank support** — Why parked: Explicit PRD non-goal; ING-only scope preserved.
- **Shared/family accounts** — Why parked: Explicit PRD non-goal; single-user isolation remains required.

## Done

- **F-01: Auth scaffold** — Implemented 2026-05-30. Lesson: —.
- **S-01: Category management** — Implemented 2026-05-30. Lesson: —.
- **S-02: CSV import with auto-categorization** — Implemented 2026-05-30. Lesson: —.
