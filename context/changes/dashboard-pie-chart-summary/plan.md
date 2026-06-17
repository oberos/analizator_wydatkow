# Dashboard Pie Chart Summary Implementation Plan

## Overview

Add an optional dashboard pie chart generated from the current category summary data (including active date range), without changing existing summary semantics or weakening user-isolation guarantees.

## Current State Analysis

The dashboard already renders a range-aware category summary table and is the canonical reporting surface. Data is aggregated server-side in `get_user_category_summary(...)`, then passed by `dashboard_view` to `dashboard.html`. There is currently no chart rendering library or chart-specific data contract.

## Desired End State

Dashboard displays a read-only pie chart derived from the same summary rows as the table for the selected range. The chart remains optional and non-blocking: table behavior stays authoritative and fully usable even if chart rendering fails. Unknown and Uncategorized are included as slices; non-positive totals are excluded from pie visualization with an explicit explanatory note.

### Key Discoveries:

- Current summary source-of-truth is centralized in `transactions/summary.py:12` and consumed in `accounts/views.py:54`.
- Dashboard date-range UX and empty-state behavior already exist in `templates/dashboard.html:39` and `templates/dashboard.html:89`.
- Existing reporting tests already validate scope, net totals, and date boundaries in `accounts/tests.py:47` and `transactions/tests.py:676`.
- Template script injection pattern already uses per-page CDN scripts via `extra_js` in `templates/base.html:23` and `templates/dashboard.html:101`.
- No chart library is currently present in dependencies or templates (`requirements.txt:1`, `pyproject.toml:8`).

## What We're NOT Doing

- No changes to summary aggregation math or category semantics.
- No interactive chart behavior (click-to-filter, drill-down, hover-driven state sync).
- No frontend bundler introduction or npm pipeline setup.
- No new report pages or transaction-list behavior changes.
- No visual snapshot infrastructure or full E2E runner bootstrap in this slice.

## Implementation Approach

Implement a server-first chart data contract in the dashboard view, derived from already-computed `category_summary` rows. Render Chart.js pie in `dashboard.html` using a CDN script in `extra_js`, with deterministic ordering and color mapping keyed by category name. Keep the table as canonical reporting output. Add focused integration tests for chart payload parity and UI-state branches (empty range, non-positive exclusions, graceful chart-unavailable fallback messaging).

## Critical Implementation Details

### Performance constraints

Do not introduce a second aggregation query for charting. Chart payload must be built from already-fetched `category_summary` rows in memory, so S-06 does not change query count.

### State sequencing

The chart contract must be computed after date-range resolution and from the exact summary rows rendered in the table, ensuring table/chart drift cannot occur due to separate code paths.

## Phase 1: Dashboard chart data contract

### Overview

Introduce deterministic, view-level chart payload generation from existing summary rows while preserving current summary behavior as source of truth.

### Changes Required:

#### 1. Dashboard view chart payload wiring

**File**: `accounts/views.py`

**Intent**: Build a chart-specific context object from `category_summary` without changing summary computation ownership.

**Contract**: Add context keys for chart labels, chart values, excluded-non-positive categories, and a boolean indicating whether pie data is renderable.

#### 2. Shared transformation helper for chart-safe rows

**File**: `accounts/views.py` (or a nearby reporting helper module reused by dashboard view)

**Intent**: Keep chart filtering/order decisions explicit and testable.

**Contract**: Transform summary rows into deterministic pie payload: include Unknown/Uncategorized as-is, exclude `total_amount <= 0`, preserve stable ordering keyed by current summary order/category name.

### Success Criteria:

#### Automated Verification:

- Dashboard response includes chart context fields derived from current `category_summary`: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests.DashboardSummaryTests`
- Existing summary contract tests still pass unchanged: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests.TransactionSummaryTests`
- Type checking passes for updated dashboard context contract: `pdm run basedpyright`

#### Manual Verification:

- For a range with positive spending categories, chart data matches table categories/totals for all positive rows.
- Unknown and Uncategorized rows appear in chart payload when their totals are positive.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: Dashboard pie chart rendering and UX states

### Overview

Render the optional pie chart in dashboard template with deterministic colors/order, explicit non-positive note, and safe fallback behavior.

### Changes Required:

#### 1. Chart container and conditional rendering

**File**: `templates/dashboard.html`

**Intent**: Add a chart card area that appears only when renderable pie data exists.

**Contract**: Template conditionally renders chart canvas and legend/note block from new context fields; chart remains hidden on empty-range/no-positive-data states.

#### 2. Chart.js CDN wiring and initialization script

**File**: `templates/dashboard.html`

**Intent**: Initialize a read-only pie chart using existing per-page script pattern.

**Contract**: Add Chart.js CDN script in `extra_js` with `crossorigin` + `integrity` attributes and initialize chart from server-provided payload only.

#### 3. Graceful fallback and explanatory messaging

**File**: `templates/dashboard.html`

**Intent**: Preserve reporting reliability when chart cannot render.

**Contract**: If chart init fails, show non-blocking “Chart unavailable” hint while preserving summary table visibility; if non-positive categories are excluded, render explicit note that pie visualizes positive spending only.

### Success Criteria:

#### Automated Verification:

- Dashboard template tests confirm chart block appears only for renderable pie payload and is absent for empty range/no-positive data.
- Template tests confirm explanatory note renders when non-positive categories are excluded.
- Linting passes after template/script additions: `pdm run ruff check .`

#### Manual Verification:

- Pie chart is visible for normal positive-spend range and matches table totals for included categories.
- Simulated chart-script failure leaves summary table functional and shows a non-blocking chart-unavailable hint.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Regression hardening for parity and edge cases

### Overview

Add focused integration coverage to lock chart/table parity, edge-case handling, and isolation behavior.

### Changes Required:

#### 1. Dashboard parity and state tests

**File**: `accounts/tests.py`

**Intent**: Prevent chart-specific regressions while following current context/assertion style.

**Contract**: Add tests for parity with summary rows, Unknown/Uncategorized inclusion, non-positive exclusion note, empty-range no-chart behavior, and chart fallback messaging path.

#### 2. Summary contract guardrails reused by chart assumptions

**File**: `transactions/tests.py`

**Intent**: Keep chart assumptions stable by preserving net-total and date-range semantics at source layer.

**Contract**: Extend/confirm summary tests covering negative/income-offset categories and inclusive range behavior that chart transformation depends on.

### Success Criteria:

#### Automated Verification:

- New dashboard chart behavior tests pass: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests.DashboardSummaryTests`
- Summary contract tests pass with chart-related assumptions intact: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests.TransactionSummaryTests`
- Full suite and type/lint gates pass: `$env:DEBUG="True" ; pdm run python manage.py test`, `pdm run basedpyright`, `pdm run ruff check .`

#### Manual Verification:

- End-to-end dashboard flow (default range, custom range, empty range) keeps table behavior correct while chart appears/disappears predictably.
- Chart and table stay numerically consistent for categories represented in pie.

**Implementation Note**: After completing this phase, all automated verification passes, and manual testing is successful, the feature is complete.

---

## Testing Strategy

### Unit Tests:

- Optional: isolated transformation checks for chart payload filtering/ordering if helper extraction warrants dedicated unit tests.

### Integration Tests:

- Dashboard context includes deterministic chart payload derived from summary.
- Unknown/Uncategorized inclusion and non-positive exclusion behavior.
- Empty-range and chart-unavailable fallback branches.
- Existing user-isolation and summary netting behavior remain intact.

### Manual Testing Steps:

1. Load dashboard with default range and verify chart/table coexist with matching positive-category totals.
2. Pick a range containing only zero/negative net categories and verify chart hidden with explanatory note.
3. Pick empty range and verify existing range-empty state remains and no chart is rendered.
4. Simulate chart script failure (disable CDN in browser devtools) and verify table remains functional with non-blocking fallback hint.

## Performance Considerations

- Reuse already-computed summary rows for chart payload generation; avoid duplicate aggregation queries.
- Keep chart rendering client-side and lightweight with one pie instance per page load.

## Migration Notes

- No database schema migration required.
- No model contract changes required.

## References

- PRD requirement: `context/foundation/prd.md` (FR-015, US-01)
- Roadmap slice: `context/foundation/roadmap.md:139`
- Existing summary source: `transactions/summary.py:12`
- Existing dashboard rendering: `accounts/views.py:32`, `templates/dashboard.html:32`
- Historical no-chart boundary in prior slice: `context/archive/2026-06-04-date-range-summary-reporting/plan.md:27`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Dashboard chart data contract

#### Automated

- [x] 1.1 Dashboard response includes chart context fields derived from current category summary — b327baa
- [x] 1.2 Existing summary contract tests still pass unchanged — b327baa
- [x] 1.3 Type checking passes for updated dashboard context contract — b327baa

#### Manual

- [x] 1.4 Chart data matches table categories/totals for positive rows in selected range — b327baa
- [x] 1.5 Unknown and Uncategorized rows appear in chart payload when totals are positive — b327baa

### Phase 2: Dashboard pie chart rendering and UX states

#### Automated

- [x] 2.1 Chart block renders only when pie payload is renderable and is absent for empty/no-positive states — 5f1ab1e
- [x] 2.2 Non-positive exclusion note renders when relevant — 5f1ab1e
- [x] 2.3 Linting passes after template and script additions — 5f1ab1e

#### Manual

- [x] 2.4 Pie chart is visible for normal positive-spend range and aligns with table totals — 5f1ab1e
- [x] 2.5 Chart script failure keeps summary table usable and shows non-blocking fallback hint — 5f1ab1e

### Phase 3: Regression hardening for parity and edge cases

#### Automated

- [x] 3.1 Dashboard chart behavior tests pass
- [x] 3.2 Summary contract tests pass with chart assumptions intact
- [x] 3.3 Full suite and quality gates pass

#### Manual

- [x] 3.4 Dashboard range flows keep chart visibility and table behavior consistent
- [x] 3.5 Chart and table stay numerically consistent for represented categories
