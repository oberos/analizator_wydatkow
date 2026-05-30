---
project: "Analizator Wydatkow"
version: 1
status: draft
created: 2026-05-29
updated: 2026-05-29
prd_version: 1
main_goal: speed
top_blocker: time
---

# Roadmap: Analizator Wydatkow

> Derived from `context/foundation/prd.md` (v1) + auto-researched codebase baseline.
> Edit-in-place; archive when superseded.
> Slices below are listed in dependency order. The "At a glance" table is the index.

## Vision recap

Bank categories don't match real spending categories. Every month the user exports a CSV from their Polish bank and spends an hour manually fixing categories in Excel before seeing actual spending breakdown. This app replaces that manual work with auto-categorization that learns from user corrections, targeting 80% accuracy so most transactions categorize themselves.

## North star

**S-02: csv-import-autocategorize** — User can upload a CSV and see transactions with auto-proposed categories.

> The north star is the smallest end-to-end slice whose successful delivery proves the core product hypothesis. Here, it's the moment when auto-categorization first runs on real bank data — the differentiator vs. Excel. Everything else only matters if this works.

## At a glance

| ID | Change ID | Outcome (user can …) | Prerequisites | PRD refs | Status |
|---|---|---|---|---|---|
| F-01 | auth-scaffold | (foundation) Login/registration views wired to Django auth | — | FR-001, FR-002 | ready |
| S-01 | category-management | Create, edit, delete custom categories; predefined categories seeded | F-01 | FR-006, FR-007, FR-008 | proposed |
| S-02 | csv-import-autocategorize | Upload CSV and see transactions with auto-proposed categories | F-01, S-01 | FR-003, FR-004, US-01 | proposed |
| S-03 | category-refinement-summary | Edit transaction category (system learns) and view spending summary | S-02 | FR-005, FR-009, US-01 | proposed |
| S-04 | transaction-filtering | Filter transactions by category and sort by any column | S-02 | FR-013, FR-014 | proposed |
| S-05 | budget-cycles | Define custom budget cycles and filter transactions by cycle | S-02 | FR-010, FR-011 | proposed |

## Streams

Navigation aid — groups items that share a Prerequisites chain. Canonical ordering still lives in the dependency graph below; this table is the proposed reading order across parallel tracks.

| Stream | Theme | Chain | Note |
|---|---|---|---|
| A | Core categorization flow | `F-01` → `S-01` → `S-02` → `S-03` | North star path — proves the 80% auto-categorization hypothesis. |
| B | Transaction analysis | `S-04` | Joins after `S-02`; parallel with `S-03`, `S-05`. |
| C | Budget cycle management | `S-05` | Joins after `S-02`; parallel with `S-03`, `S-04`. |

## Baseline

What's already in place in the codebase as of 2026-05-29 (auto-researched + user-confirmed).
Foundations below assume these are present and do NOT re-scaffold them.

- **Frontend:** absent — Django templates configured but no template files exist
- **Backend / API:** partial — Django 6.0.5 scaffold present (`manage.py`, `settings.py`), no app views beyond admin
- **Data:** partial — Django ORM configured with psycopg/PostgreSQL, no models defined
- **Auth:** partial — Django auth middleware in `settings.py`, no login/registration views
- **Deploy / infra:** partial — `render.yaml` present, no Dockerfile or CI/CD workflows
- **Observability:** absent — no logging, error tracking, or metrics

## Foundations

### F-01: Auth scaffold

- **Outcome:** (foundation) Django's built-in login/registration views wired with routes and minimal templates; authenticated sessions work end-to-end.
- **Change ID:** auth-scaffold
- **PRD refs:** FR-001, FR-002, Access Control section
- **Unlocks:** S-01, S-02, S-03, S-04, S-05 (all user-facing slices require authenticated user)
- **Prerequisites:** —
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Django auth is well-documented and battle-tested; low risk. Sequenced first because every slice depends on it.
- **Status:** ready

## Slices

### S-01: Category management

- **Outcome:** User can create, edit, and delete custom categories; a starter set of predefined categories (Groceries, Transport, Entertainment, Bills, Health) ships with the app.
- **Change ID:** category-management
- **PRD refs:** FR-006, FR-007, FR-008
- **Prerequisites:** F-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Straightforward CRUD. Sequenced before S-02 because transactions need categories to be categorized into.
- **Status:** proposed

### S-02: CSV import with auto-categorization

- **Outcome:** User can upload a CSV file (ING Poland format) and see transactions with auto-proposed categories based on merchant-to-category mappings learned from previous corrections.
- **Change ID:** csv-import-autocategorize
- **PRD refs:** FR-003, FR-004, US-01
- **Prerequisites:** F-01, S-01
- **Parallel with:** —
- **Blockers:** —
- **Unknowns:** —
- **Risk:** CSV parsing for ING format needs specification research; auto-categorization logic is the core differentiator. This is the riskiest slice — sequenced early per "speed" goal to surface integration issues fast.
- **Status:** proposed

### S-03: Category refinement and spending summary

- **Outcome:** User can edit a transaction's category with a single action (system remembers merchant→category mapping for future auto-categorization); user can view a summary table with spending totals per category.
- **Change ID:** category-refinement-summary
- **PRD refs:** FR-005, FR-009, US-01
- **Prerequisites:** S-02
- **Parallel with:** S-04, S-05
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Learning mechanism (merchant→category storage) must be correct for 80% accuracy target. Summary is straightforward aggregation.
- **Status:** proposed

### S-04: Transaction filtering and sorting

- **Outcome:** User can filter transactions by category and sort the transaction list by any column (date, amount, merchant, category).
- **Change ID:** transaction-filtering
- **PRD refs:** FR-013, FR-014
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-05
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Standard list manipulation; low risk. Sequenced after core flow because filtering enhances but doesn't define the product.
- **Status:** proposed

### S-05: Budget cycles

- **Outcome:** User can define a budget cycle (custom date range, e.g., paycheck to paycheck) and filter transactions by that cycle.
- **Change ID:** budget-cycles
- **PRD refs:** FR-010, FR-011
- **Prerequisites:** S-02
- **Parallel with:** S-03, S-04
- **Blockers:** —
- **Unknowns:** —
- **Risk:** Date range logic is straightforward. Sequenced last because it's an analysis enhancement, not core categorization.
- **Status:** proposed

## Backlog Handoff

| Roadmap ID | Change ID | Suggested issue title | Ready for `/10x-plan` | Notes |
|---|---|---|---|---|
| F-01 | auth-scaffold | Wire Django login/registration views | yes | Run `/10x-plan auth-scaffold` |
| S-01 | category-management | Implement category CRUD with predefined seed | no | Blocked by F-01 |
| S-02 | csv-import-autocategorize | CSV upload with ING parser and auto-categorization | no | Blocked by S-01 |
| S-03 | category-refinement-summary | Transaction category editing with learning + summary view | no | Blocked by S-02 |
| S-04 | transaction-filtering | Filter by category and sort transactions | no | Blocked by S-02 |
| S-05 | budget-cycles | Custom budget cycle definition and filtering | no | Blocked by S-02 |

## Open Roadmap Questions

*No open questions — PRD is complete and all dependencies are internal.*

## Parked

- **FR-012: Bulk-edit category assignments** — Why parked: PRD marks as nice-to-have; 3-week timeline prioritizes must-haves only.
- **Observability (logging, error tracking)** — Why parked: Not in PRD NFRs for MVP; can add post-launch if needed.
- **CI/CD workflows** — Why parked: `render.yaml` enables manual deploy; auto-deploy can be added post-MVP.

## Done

(Empty on first generation. `/10x-archive` appends entries here when changes are archived.)
