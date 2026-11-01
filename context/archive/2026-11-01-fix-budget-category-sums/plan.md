# Fix budget category sums Implementation Plan

## Overview

The budget comparison is incorrectly treating actual spend and budgeted spend as different aggregation layers. Parent categories roll up child spending for the actual side, but the budgeted side can remain anchored to a single direct allocation, which makes the master category look over budget even when the combined child budget is still healthy. The fix should make the parent category compare against the aggregated budget for its whole category tree while keeping the existing row model and subcategory rows intact.

## Current State Analysis

- The core comparison logic lives in `budgets/summary.py`, specifically `get_budget_comparison()` and `_expense_totals_for_budget()`.
- Actual spend is deliberately aggregated up the category tree: `_expense_totals_for_budget()` walks parent links and adds descendant transaction totals to the parent row.
- Budgeted amounts are built from `budget.allocations.select_related("category").all()`, and each allocation is compared as a standalone row without first summing descendant allocations into the parent bucket.
- The existing test suite in `budgets/tests.py` covers parent-vs-subcategory independence and rollup behavior, but it does not explicitly protect the case where a parent category should be evaluated against the combined budget of its descendants as well as its own direct allocation.
- The bug is user-visible in the budget detail view because a parent row can report a negative difference when its subcategory spending is included in actuals but its budgeted amount is not, even though the category family is still within the intended plan.

## Desired End State

After the fix, the master category row should reflect the combined budget assigned to the category family, not just a single direct amount. Parent and child category rows should still be visible as separate rows where appropriate, but a parent category should no longer be “always negative” simply because spends are rolled up while its estimate remains a partial sum.

### Key Discoveries:

- `budgets/summary.py` aggregates actual spending by walking parent category links before calculating each row's `actual_amount`.
- `budgets/tests.py` already validates parent and subcategory row independence, which is a strong pattern to preserve during the fix.
- The issue is a comparison-layer bug, not a category hierarchy bug: the model and transaction data are structurally sound; the budget calculation is not combining the estimate side consistently.

## What We're NOT Doing

- We are not changing the category hierarchy model or category ownership rules.
- We are not redesigning the budget UI or data schema.
- We are not changing how transactions are assigned to categories; the issue is isolated to the budget comparison calculation.

## Implementation Approach

The fix should be implemented as a focused regression and calculation patch in the budget summary layer. We will first codify the failing scenario in a targeted test, then update the comparison logic so the parent row's `budgeted_amount` is derived from the full budgeted total for the category family while preserving the existing child-row behavior. The change should be narrow, testable, and compatible with the current row-ordering and UI semantics.

## Critical Implementation Details

- The important boundary is that `actual_amount` is already rolled up across descendants; the estimate side must be normalized to the same conceptual scope before comparing them.
- The fix should not collapse the parent and child rows into a single row; it must preserve the current ability to see direct parent and subcategory budget allocations independently.
- Any aggregation used for the parent estimate must avoid double counting when descendant allocations are already included in the parent row or when the same category is evaluated both directly and via its tree.
- The regression test should model a parent category with one or more child categories, where subcategory spending exists and the total child budget is non-zero but the parent direct budget is nil or smaller.

## Phase 1: Reproduce the bug in a focused regression test

### Overview

Capture the failing scenario in `budgets/tests.py` so the bug is locked down before logic is changed.

### Changes Required:

#### 1. Budget comparison regression

**File**: `budgets/tests.py`

**Intent**: Add a test where a parent category has child allocations and actual spend is rolled up, but the expected comparison reflects the combined budget assigned across the category family instead of only the direct parent allocation.

**Contract**: The new regression should validate the parent row's `budgeted_amount`, `actual_amount`, and `difference` in the same style as the existing subcategory comparison tests, without changing the contract of the public `get_budget_comparison()` API.

### Success Criteria:

- The failing case is encoded as an explicit regression test.
- The test demonstrates the current mismatch between rolled-up actual spend and partial parent budget estimation.
- The test stays aligned with the existing parent-vs-subcategory comparison conventions used elsewhere in the suite.

## Phase 2: Fix the parent estimate rollup in the summary logic

### Overview

Update the budget summary calculation so the parent bucket evaluates the combined budget assigned to the parent and its descendants, while still leaving the child rows and display order intact.

### Changes Required:

#### 1. Budgeted total aggregation helper

**File**: `budgets/summary.py`

**Intent**: Add a small helper or inline aggregation step that computes the total allocated budget for each category and its descendant categories, then uses that value when creating the parent comparison row.

**Contract**: Maintain the public result shape of `get_budget_comparison()`—category name, color, budgeted amount, actual amount, difference, status, ordering—while correcting the parent-level estimate math. The implementation should remain deterministic and limited to this summary layer.

#### 2. Guard against double-counting and ordering issues

**File**: `budgets/summary.py`

**Intent**: Ensure that the parent-level estimate uses the family total without accidentally inflating totals when both parent and child rows are present in the comparison list.

**Contract**: Preserve the existing comparison ordering and keep separate rows for parent and child categories if the current UX expects them.

### Success Criteria:

- Parent category rows calculate an estimate that matches the combined direct + descendant budget allocation.
- Child category rows continue to calculate their own actual and budgeted totals independently.
- The comparison still sorts parent rows before their child rows and does not create duplicate or broken totals.

## Phase 3: Validate the user-facing budget result

### Overview

Confirm that the budget detail view reflects the corrected logic and that the negative parent budget symptom is gone without the broader budget model changing.

### Changes Required:

#### 1. Manual verification of budget detail output

**File**: `templates/budgets/budget_detail.html`

**Intent**: Check that the rendered budget table behaves as expected when a parent category has child allocations and the family total is within budget.

**Contract**: No template redesign is required unless a rendering bug is discovered; the main goal is to validate the data result rather than change the UI.

### Success Criteria:

- Parent rows no longer appear artificially negative when their descendant spend is included in actuals and the combined estimate is valid.
- Child rows continue to show their own allocations and costs correctly.
- The fix is limited to the budget summary math and does not disturb unrelated report views.

## Testing Strategy

### Unit Tests:

- Add a parent-level regression test covering the mixed direct-parent + child-category allocation scenario.
- Preserve the existing checks for subcategory scoping and parent/child independence in `budgets/tests.py`.
- Ensure the comparison uses the same category tree semantics as the transaction summary for actual spend.

### Integration Tests:

- Validate the budget comparison API via Django test cases rather than only template rendering.
- Check aggregate budget math with at least one parent plus two child categories.

### Manual Testing Steps:

1. Create a budget with a parent category and at least two subcategories.
2. Assign budget amounts to child categories and optionally the parent category.
3. Record spending across the parent and descendants.
4. Review the budget detail page and confirm the parent row reflects the same underlying rule as the shared actual summary.
5. Confirm there is no spurious “negative” parent category if the combined budget remains valid.

## Performance Considerations

This change is small and local to budget summary generation. The critical performance concern is avoiding repeated expensive aggregation work in the comparison loop. The implementation should keep the calculation within a single summary pass and not add database queries per row.

## Migration Notes

No migration is expected. This fix is limited to the comparison logic used for budget display and summary calculations.

## References

- Related logic: `budgets/summary.py`
- Existing regression coverage: `budgets/tests.py`
- Budget detail rendering: `templates/budgets/budget_detail.html`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Reproduce the bug in a focused regression test

#### Automated

- [x] 1.1 Add a regression test covering the parent-with-subcategory budget mismatch
- [x] 1.2 Confirm the test fails against the current logic and captures the real bug

#### Manual

- [x] 1.3 Review the new test scenario with the user to confirm the expected parent/child budget behavior

### Phase 2: Fix the parent estimate rollup in the summary logic

#### Automated

- [x] 2.1 Update the parent budget calculation to use aggregated family budget data
- [x] 2.2 Ensure child rows remain independent and do not double-count

#### Manual

- [x] 2.3 Spot-check the budget detail output after the logic change

### Phase 3: Validate the user-facing budget result

#### Automated

- [x] 3.1 Run the budget test subset and confirm the regression passes
- [x] 3.2 Run any relevant lint/type checks that cover the touched files

#### Manual

- [x] 3.3 Verify the end-user budget display matches the corrected behavior for a real category family
