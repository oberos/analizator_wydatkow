# Remove income from budget Implementation Plan

## Overview

This change fixes a budgeting bug where positive income transactions are counted as if they were spending, making the budget variance appear larger than the actual outflow for the period. The fix keeps the broader category reporting logic intact and narrows the change to the budget comparison layer used by budget cards and the budget detail table.

## Current State Analysis

- `budgets/summary.py` builds `get_budget_comparison()` by pulling `actual_amount` from `get_user_category_summary()` and then comparing it directly with `budget.allocations`.
- `transactions/summary.py` intentionally uses signed totals where positive amounts reduce net spend, so income offsets expense within a category for reporting purposes.
- `budgets/views.py` sums these comparison rows for the list summary cards, so every budget card inherits the same income-inflated logic.
- Existing budget tests in `budgets/tests.py` validate under/over logic but do not cover the scenario where a category includes both expenses and incoming money.

## Desired End State

- Budget cards and the detailed budget view calculate actuals using expense-only transactions, ignoring income when comparing against the allocated spend.
- Categories with mixed income and expense entries show the true outflow used against the budget, not the net cash-flow total.
- The general category summary used elsewhere continues to show net totals, and targeted regression tests cover the income edge case.

### Key Discoveries:

- `transactions/summary.py` is intentionally netted by category, which is correct for payment analysis but not for expense budgets.
- `budgets/summary.py` is the single comparison source reused by both the list view and the detail view, so the fix belongs there rather than in templates.
- The bug is not in budget allocation or date-window logic; it is in the actual amount source used for budget comparison.

## What We're NOT Doing

- We are not changing the net category summary semantics used in transaction dashboards and reporting.
- We are not touching category assignment, auto-categorization, or the user budget model.
- We are not broadening the fix into a redesign of budget allocation logic or date filtering behavior.

## Implementation Approach

Use a budget-specific actuals calculation instead of the generic net category totals for budget comparisons. In practice, budget comparison should measure only outflows (`amount < 0`) for each category during the budget range and ignore income rows when computing the `actual_amount` and thus the `difference`. This isolates the change to the budget layer while preserving transaction summary semantics used in other screens.

## Critical Implementation Details

Budget calculations are about outflows, while the transaction summary is intentionally netted. Reusing the net totals in the budget layer makes income look like spend and skews under/over status. The correct correction is budget-local: keep the reporting helper untouched and filter budget actuals to expense amounts only.

## Phase 1: Add the regression for income in budget comparisons

### Overview

This phase pins the expected behavior before changing the helper so the fix is driven by a failing regression rather than a loose UI tweak.

### Changes Required:

#### 1. Budget regression tests

**File**: `budgets/tests.py`

**Intent**: Add a failing case where a budgeted category includes both an expense and a positive income transaction, and assert that the amount used for the budget comparison is still the expense side only.

**Contract**: The tests should cover a scenario such as budgeted `Groceries = 1000`, expense `-800`, income `+200`; the expected `actual_amount` stays `800`, `difference` stays `200`, and status remains `under`. Keep the test aligned with the existing `get_budget_comparison()` contract and structure used by the rest of the file.

### Success Criteria:

#### Automated Verification:

- Budget comparison handles mixed income and expense in one category without counting the income as spend
- Existing budget comparison tests still pass across the current scenarios

#### Manual Verification:

- The regression scenario is understandable from the test description and matches the real user issue
- No previous under/over assertions for simple expense-only budgets regress

---

## Phase 2: Filter budget actuals to spending-only values

### Overview

This phase changes only the actuals calculation used by the budget comparison helper and verifies the list/detail budget views pick up the corrected totals.

### Changes Required:

#### 1. Budget summary helper

**File**: `budgets/summary.py`

**Intent**: Compute `actual_amount` from expense-only transactions in the budget period instead of passing through the net category summary directly; keep the rest of the comparison and status logic unchanged.

**Contract**: `get_budget_comparison()` should still return the same structure and ordering, but `actual_amount` should reflect only negative transaction amounts for the category (or the equivalent expense-only sum after aggregation). The fix should leave zero-budget, uncategorized, and parent/child category behavior intact.

#### 2. Budget views and display surfaces

**File**: `budgets/views.py`

**Intent**: Ensure list-card totals inherit the corrected actuals from the budget comparison helper without any additional custom logic in the templates.

**Contract**: `total_actual` remains the sum of `comparison_data` entries, and because `get_budget_comparison()` is now filtering out income, the budget cards and detail table automatically reflect the same corrected spend totals.

### Success Criteria:

#### Automated Verification:

- `get_budget_comparison()` excludes positive amounts from the budget actual for categories containing income
- The list summary cards and detail table continue to show the same total structure used today
- Relevant budget test suite passes without unrelated regressions

#### Manual Verification:

- Budget cards no longer show a category as over budget because of incoming money in the same period
- Budget detail rows display the correct spend-versus-budget delta for categories that had both income and expenses

---

## Testing Strategy

### Unit Tests:

- Mixed income/expense in a budgeted category should count only the expense portion toward actuals
- Categories with a positive income-only entry should not become “over budget” due to the income amount
- Existing under/over/zero-budget comparisons should remain stable

### Integration Tests:

- Budget list cards and detail pages show the corrected totals for a user with mixed categories in the selected date range

### Manual Testing Steps:

1. Create a budget period with one category containing both a negative expense and a positive income transaction.
2. Open the budget detail page and confirm the category actual equals expense-only amount.
3. Check the budget list summary card and verify the same category no longer inflates the total budget variance.

## Performance Considerations

No material performance impact is expected because the change only filters expense rows within the existing budget comparison helper; it does not add a new query pattern or a broad data scan beyond the current summary pipeline.

## Migration Notes

No migration is required. This is a logic fix in the budget comparison helper and associated tests.

## References

- Related summary logic: `transactions/summary.py`
- Budget comparison source: `budgets/summary.py`
- Budget view integration: `budgets/views.py`
- Existing budget test coverage: `budgets/tests.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Add the regression for income in budget comparisons

#### Automated

- [x] 1.1 Add failing regression covering mixed income and expense in one budgeted category
- [x] 1.2 Confirm current budget comparison logic fails for positive income rows

#### Manual

- [ ] 1.3 Review the expected user-visible outcome for the budget detail view before implementing the fix

### Phase 2: Filter budget actuals to spending-only values

#### Automated

- [x] 2.1 Update `get_budget_comparison()` to ignore positive income amounts for budget actuals
- [x] 2.2 Verify the budget list/detail views reflect corrected totals and existing tests pass

#### Manual

- [ ] 2.3 Open the budget UI and confirm income no longer skews the variance
