# Date-range summary reporting Implementation Plan

## Overview

Implement dashboard category-summary filtering by a user-selected date range, with a default last-30-days window, while preserving per-user data isolation and existing summary semantics.

## Current State Analysis

Dashboard summary currently aggregates all user transactions without date filtering. The dashboard view calls a single summary helper and renders a table in a server-rendered template. Date fields already exist on transactions, and integration tests already validate user isolation and summary correctness, but not date-boundary behavior.

## Desired End State

A logged-in user can view category totals for an explicit date range (start/end), defaulting to today minus 30 days through today (inclusive). Invalid ranges are rejected with visible validation errors, empty ranges show a range-specific empty state, and summary results remain user-scoped and netted exactly as today.

### Key Discoveries:

- Dashboard wiring is centralized in `accounts/views.py:21` with summary context from `transactions/summary.py:10`.
- Summary aggregation already applies user isolation in one place (`Transaction.objects.filter(user=user)` in `transactions/summary.py:13`).
- Dashboard rendering surface is isolated in `templates/dashboard.html:32` and can absorb range controls without route changes.
- Existing summary behavior tests in `accounts/tests.py:19` and `accounts/tests.py:66` provide a stable baseline to extend.

## What We're NOT Doing

- No transaction-list date filtering in this change.
- No budget-cycle presets or advanced period builders.
- No caching/materialized summary tables.
- No charting changes (pie chart remains a later slice).

## Implementation Approach

Keep the current server-rendered flow and extend it with a validated GET-based date-range form. Parse and validate range inputs in dashboard view, compute default inclusive range when missing, and pass the resolved range to summary aggregation. Extend the existing summary helper with optional date bounds on `Transaction.date`, then update dashboard template for controls, error display, and selected-range state. Finish with focused integration tests for boundary correctness, invalid-range handling, empty-state behavior, and user isolation.

## Phase 1: Date-range input and dashboard wiring

### Overview

Introduce validated date-range inputs and default-range behavior at the dashboard entry point.

### Changes Required:

#### 1. Date-range form contract

**File**: `transactions/forms.py`

**Intent**: Add a reusable date-range form used by dashboard GET filtering, with explicit validation for `start_date <= end_date`.

**Contract**: Introduce a form exposing `start_date` and `end_date` (`DateField`), with form-level validation that rejects inverted ranges.

#### 2. Dashboard query parsing and context wiring

**File**: `accounts/views.py`

**Intent**: Bind GET parameters into the date-range form, apply default last-30-days inclusive range when params are absent, and keep previous summary on invalid form input.

**Contract**: Dashboard context includes resolved range fields and the bound form; summary calls move from all-time signature to range-aware signature.

### Success Criteria:

#### Automated Verification:

- Django checks pass after form/view wiring: `$env:DEBUG="True" ; pdm run python manage.py check`
- Type checking passes for updated form and view contracts: `pdm run basedpyright`

#### Manual Verification:

- Opening dashboard without query params shows default last-30-days range prefilled
- Submitting `start_date > end_date` shows validation error without silently changing selected dates

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Range-aware summary aggregation

### Overview

Apply inclusive date filtering to the existing per-user summary helper while preserving current net-total and grouping semantics.

### Changes Required:

#### 1. Summary helper signature and filtering

**File**: `transactions/summary.py`

**Intent**: Extend the summary helper to accept optional date boundaries and filter the user-scoped queryset by `Transaction.date`.

**Contract**: `get_user_category_summary` accepts optional `start_date` and `end_date`; when provided, filtering is inclusive (`>= start_date`, `<= end_date`) on `date`.

#### 2. Call-site alignment

**File**: `accounts/views.py`

**Intent**: Pass resolved range bounds into summary helper so rendered totals reflect selected period.

**Contract**: Dashboard summary invocation always uses the resolved valid/default range for this slice.

### Success Criteria:

#### Automated Verification:

- Targeted summary tests pass after helper signature update: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests.DashboardSummaryTests transactions.tests.TransactionSummaryTests`
- Full app tests for reporting-related modules pass: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests transactions.tests`

#### Manual Verification:

- Setting a narrow date window visibly changes totals and transaction counts compared to default range
- Start/end boundary dates are included in totals (inclusive behavior)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Dashboard range UX and empty/error states

### Overview

Expose date-range controls and display clear feedback for selected range, invalid input, and no-data windows.

### Changes Required:

#### 1. Dashboard filter UI and state rendering

**File**: `templates/dashboard.html`

**Intent**: Add GET filter controls for `start_date` and `end_date`, preserve entered values, and make active range explicit near summary.

**Contract**: Template renders bound date-range form fields and submit action targeting dashboard route via GET query params.

#### 2. Empty-state and error-state messaging

**File**: `templates/dashboard.html`

**Intent**: Ensure a selected range with zero transactions shows a range-specific empty message, and invalid inputs surface form errors clearly.

**Contract**: Empty-state text distinguishes “no transactions in selected range” from generic no-data onboarding message.

### Success Criteria:

#### Automated Verification:

- Template and view integration tests for range UI rendering pass: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests`
- Linting passes after template/view updates: `pdm run ruff check .`

#### Manual Verification:

- Dashboard URL reflects selected range in query string and can be refreshed/bookmarked with same results
- Range with no matching transactions displays explicit range-empty message

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 4: Focused regression coverage for date-range behavior

### Overview

Add/extend integration tests to lock default behavior, validation behavior, boundary semantics, and user isolation under range filtering.

### Changes Required:

#### 1. Dashboard integration coverage

**File**: `accounts/tests.py`

**Intent**: Add tests for default 30-day range, invalid-range rejection, inclusive boundaries, and selected-range empty state.

**Contract**: New tests assert both context-level summary values and response content for key range behaviors.

#### 2. Summary behavior regression coverage

**File**: `transactions/tests.py`

**Intent**: Add range-aware summary tests at helper/service boundary to prevent future logic drift.

**Contract**: Tests verify date filtering does not break netting rules and remains user-scoped.

### Success Criteria:

#### Automated Verification:

- New dashboard date-range tests pass: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests.DashboardSummaryTests`
- New summary range tests pass: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests.TransactionSummaryTests`
- Full project test suite passes with debug local config: `$env:DEBUG="True" ; pdm run python manage.py test`

#### Manual Verification:

- End-to-end dashboard flow (default range -> custom valid range -> invalid range -> empty range) behaves consistently in browser
- Existing summary behavior (uncategorized bucket and user isolation) still appears correct after date-range additions

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Form validation for inverted ranges
- Summary helper date-bound filtering semantics (inclusive bounds)

### Integration Tests:

- Dashboard GET filtering with default window, custom window, invalid window, and empty-result window
- User isolation under date-filtered summary requests

### Manual Testing Steps:

1. Load dashboard with no params and verify default range + matching totals.
2. Submit a custom range and verify URL/query persistence and changed totals.
3. Submit invalid range and verify error visibility and unchanged summary behavior.
4. Submit no-data range and verify explicit range-empty state message.

## Performance Considerations

Use existing ORM aggregation with date predicates only; no caching/materialization in this slice. This aligns with current MVP scale and avoids invalidation complexity.

## Migration Notes

No schema changes or migrations expected for this change.

## References

- PRD reporting requirements: `context/foundation/prd-v2.md:83`
- Roadmap slice definition: `context/foundation/roadmap.md:115`
- Risk guidance for summary and boundary correctness: `context/foundation/test-plan.md:45`
- Existing dashboard summary flow: `accounts/views.py:21`
- Existing summary aggregation contract: `transactions/summary.py:10`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Date-range input and dashboard wiring

#### Automated

- [x] 1.1 Django checks pass after form/view wiring — ed8ca1c
- [x] 1.2 Type checking passes for updated form and view contracts — ed8ca1c

#### Manual

- [x] 1.3 Opening dashboard without query params shows default last-30-days range prefilled — ed8ca1c
- [x] 1.4 Submitting start_date > end_date shows validation error without silently changing selected dates — ed8ca1c

### Phase 2: Range-aware summary aggregation

#### Automated

- [x] 2.1 Targeted summary tests pass after helper signature update — a250288
- [x] 2.2 Full app tests for reporting-related modules pass — a250288

#### Manual

- [x] 2.3 Setting a narrow date window visibly changes totals and transaction counts compared to default range — a250288
- [x] 2.4 Start/end boundary dates are included in totals (inclusive behavior) — a250288

### Phase 3: Dashboard range UX and empty/error states

#### Automated

- [x] 3.1 Template and view integration tests for range UI rendering pass — 7ea39f7
- [x] 3.2 Linting passes after template/view updates — 7ea39f7

#### Manual

- [x] 3.3 Dashboard URL reflects selected range in query string and can be refreshed/bookmarked with same results — 7ea39f7
- [x] 3.4 Range with no matching transactions displays explicit range-empty message — 7ea39f7

### Phase 4: Focused regression coverage for date-range behavior

#### Automated

- [x] 4.1 New dashboard date-range tests pass — 0ed30e0
- [x] 4.2 New summary range tests pass — 0ed30e0
- [x] 4.3 Full project test suite passes with debug local config — 0ed30e0

#### Manual

- [x] 4.4 End-to-end dashboard flow (default range -> custom valid range -> invalid range -> empty range) behaves consistently in browser — 0ed30e0
- [x] 4.5 Existing summary behavior (uncategorized bucket and user isolation) still appears correct after date-range additions — 0ed30e0
