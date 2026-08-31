# Show transactions from budget Implementation Plan

## Overview

Add a budget drill-down so a user can click a category in the budget detail view and immediately see only that category's transactions for the active budget period. The existing budget comparison logic already tells us which category totals matter; the missing piece is wiring that data to the transaction list and letting the list accept a budget-scoped date range without breaking the current category/sort behavior.

## Current State Analysis

The codebase already provides the building blocks for this feature:

- `budgets/views.py` builds `comparison_data` in `BudgetDetailView.get_context_data()` and renders each category row in `templates/budgets/budget_detail.html`.
- `budgets/summary.py` calculates each category's `actual_amount` for a budget date window via `get_user_category_summary(user, start_date, end_date)`.
- `transactions/views.py` already supports category filtering and sorting in `TransactionListView`, plus `sort_by`/`sort_order` and page state preservation.
- `templates/transactions/transaction_list.html` exposes a category dropdown and clear filters state, so the user can already narrow the list by category.
- All filters are scoped to the logged-in user and the app already protects data ownership.

What is missing:

- A click-through from the budget detail view into the transaction list.
- A way for the transaction list to accept a date range from an external source (the budget period), not just the default list view.
- State handling for a filtered list that is active because of budget context rather than the user manually choosing filters in the list page.

### Key Discoveries:

- `TransactionListView._get_filter_sort_state()` only normalizes `category`, `sort_by`, and `sort_order` today; it has no date-range contract to absorb a budget-derived range.
- `TransactionSetCategoryView` already preserves filter/sort/page state on redirect, which is a useful pattern to keep when budget drill-down becomes part of the request parameters.
- The budget detail table is a display layer over `get_budget_comparison()`, so the feature should reuse the category name and budget date window rather than re-deriving spending logic in the UI.

## Desired End State

Users can:

1. Open a budget detail page and see the per-category breakdown.
2. Click a category row (or category badge) to open the transactions page with that category pre-selected.
3. See only the transactions for that category within the budget's date range, not the full account history.
4. Keep the existing sort and pagination behavior while the budget filter is active.
5. Clear the budget-driven filter and return to the full transaction list without losing the standard transaction-list UX.

### Verification:

- With a budget from 2026-07-01 to 2026-07-31, clicking the Groceries row opens `/transactions/?category=Groceries&start_date=2026-07-01&end_date=2026-07-31`.
- The list shows only transactions from that category within that date range.
- Sorting and pagination still work when the filter is active.
- Clearing filters returns the full transaction list for the current user.

## What We're NOT Doing

- We are not changing the budget data model or category aggregation rules.
- We are not adding an export or CSV action for budget drill-downs.
- We are not modifying the historical dashboard or cross-user access rules.
- We are not introducing a separate page; the feature uses the existing transaction list as the drill-down target.

## Implementation Approach

Reuse the already-established transaction-list filter contract and extend it with optional `start_date` and `end_date` query params. The budget detail page becomes the entry point that passes the category name together with the budget's date window; the transactions page reads those parameters, applies them in `get_queryset()`, and keeps the rest of the list behavior unchanged. This is the lowest-risk approach because it preserves the current code paths, reduces duplication, and uses the same user-scoped data flow the app already relies on.

## Phase 1: Budget drill-through and filter contract

### Overview

Create the click-through from the budget detail table and extend the transaction list to understand budget-scoped date filters without breaking the existing category/sort workflow.

### Changes Required:

#### 1. Add drill-through links from budget rows

**File**: `templates/budgets/budget_detail.html`

**Intent**: Turn the category rows into navigation targets that send the user to `transactions:list` with the category name and the active budget date range already encoded in the URL.

**Contract**: Each row should navigate to a URL of the form `/transactions/?category=<category>&start_date=<budget.start_date>&end_date=<budget.end_date>`, while preserving the existing table layout and status badges. The row link should be the category label or a surrounding interactive element, not a separate page.

#### 2. Extend transaction-list query parsing to accept a budget window

**File**: `transactions/views.py`

**Intent**: Add optional `start_date` and `end_date` state to the transaction filter contract so the budget drill-down is treated as a valid, user-scoped list request.

**Contract**: Update the filter state logic to normalize optional `start_date` and `end_date` values, then apply them in `get_queryset()` using a `date__range` filter when present. Keep the `category` and sort state untouched. Add these params to the context so the template can display the active budget window or the standard list state.

#### 3. Render budget-driven filter state in the transaction list

**File**: `templates/transactions/transaction_list.html`

**Intent**: Make the budget-driven date range visible to the user and let standard filter controls keep working when this state is active.

**Contract**: Add a compact "Showing transactions for <date range>" signal and ensure `Clear Filters` removes both the category and date-range inputs. Preserve the existing sort controls, category dropdown, and page semantics.

### Success Criteria:

#### Automated Verification:

- Transaction list returns filtered results for category + date range: `pdm run python manage.py test transactions.tests`
- Category filter and page/sort state remain stable when the request includes a budget date range: `pdm run python manage.py test transactions.tests.TransactionListViewTests`
- User isolation remains intact for date-scoped queries: `pdm run python manage.py test transactions.tests`

#### Manual Verification:

- Click a category in a budget detail page and verify the transaction list opens in the targeted range.
- Confirm that unrelated categories are hidden while the budget filter is active.
- Confirm the transaction count and empty-state message reflect the filtered subset, not the full account history.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Regression-proofing and UX polish

### Overview

Ensure the new drill-through path is stable against existing filter behavior, back-button interactions, and the current transaction list UX.

### Changes Required:

#### 1. Preserve budget filter state on transaction updates

**File**: `transactions/views.py`

**Intent**: Keep the budget date range and category filter available when a user edits a transaction category from the filtered list.

**Contract**: Extend the redirect parameter preservation in `TransactionSetCategoryView` so it also keeps `start_date` and `end_date` when they were supplied via budget drill-down. This matches the existing logic for `category`, `sort_by`, `sort_order`, and `page`.

#### 2. Add regression tests for the drill-down flow

**File**: `transactions/tests.py`

**Intent**: Add focused tests for the new contract: valid date-range filtering, date-range + category combination, and filter state preservation across category edits.

**Contract**: The tests should assert that: (a) the queryset includes only transactions in the selected category within the budget dates; (b) a request with `category` + `start_date` + `end_date` returns the expected rows; and (c) a redirect from `set_category` preserves the budget date parameters.

#### 3. Validate empty and no-match states

**File**: `templates/transactions/transaction_list.html`

**Intent**: Ensure a budget drill-down with no matches shows a clear empty-state and does not create a confusing, blank list.

**Contract**: If the filtered queryset is empty, show a message such as “No transactions match this category in this budget period.” while still preserving the filter controls so the user can adjust the view.

### Success Criteria:

#### Automated Verification:

- New tests for budget drill-down and date-range filtering pass: `pdm run python manage.py test transactions.tests`
- Existing filter/sort tests remain green: `pdm run python manage.py test transactions.tests`

#### Manual Verification:

- The user can edit a transaction from the filtered budget view and stay in the same budget-scoped selection after save.
- Empty results are explicit and actionable.
- A budget click remains usable when there are no transactions in that category for the budget period.

## Testing Strategy

### Unit Tests:

- Add a test for the transaction list when `category` and `start_date`/`end_date` are combined.
- Add a test for preserving those query params when a category change is submitted.
- Confirm that category + date-range filters do not expose transactions from another user.

### Integration Tests:

- Use Django test client requests against the `/transactions/` route with real budget-date parameters and assert the filtered queryset.
- Smoke-test the full budget drill-down path from `BudgetDetailView` to `TransactionListView` in the browser.

### Manual Testing Steps:

1. Create a budget spanning a known date range and assign a category allocation.
2. Upload or create transactions in that category both inside and outside the budget window.
3. Click the category in the budget detail page and confirm only in-range transactions are shown.
4. Change the category of one of those transactions and confirm the redirect preserves the same budget-scoped filter.
5. Clear filters and confirm the list returns to the full account view.

## Performance Considerations

This feature adds a date-range constraint to the existing `category` filter but does not introduce any new data processing heavy enough to require special optimization. The transaction list already queries a filtered, user-scoped queryset and paginates at 50 items, so the additional range check is low-risk for the app's expected scale.

## Migration Notes

No database migration is required. This is a UI and query-logic change on top of the existing `transactions` and `budgets` models.

## References

- Budget detail view: `budgets/views.py:47-60`
- Budget comparison helper: `budgets/summary.py:11-86`
- Transaction list filtering: `transactions/views.py:21-92`
- Transaction list template: `templates/transactions/transaction_list.html`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Budget drill-through and filter contract

#### Automated

- [x] 1.1 Add drill-through links from budget detail rows to the filtered transaction list
- [x] 1.2 Extend transaction list query parsing for optional budget date-range filters
- [x] 1.3 Add regression tests for category + date-range filtering

#### Manual

- [x] 1.4 Verify category drill-through opens the matching filtered transaction view

### Phase 2: Regression-proofing and UX polish

#### Automated

- [x] 2.1 Preserve budget filter state when a transaction category is updated
- [x] 2.2 Add empty-state and no-match regression checks for the budget drill-down flow

#### Manual

- [x] 2.3 Confirm the filtered list remains usable after editing a transaction and after clearing filters
