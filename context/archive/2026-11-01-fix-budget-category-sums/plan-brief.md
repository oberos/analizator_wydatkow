# Fix budget category sums — Plan Brief

> Full plan: `context/changes/fix-budget-category-sums/plan.md`

## What & Why

The budget summary currently rolls up actual spending across a parent category and its child categories, but the parent row can still compare against only its direct budget allocation. That mismatch makes a master category look negative even when the family-level budget is not actually overrun. The fix is to align the estimate side with the same aggregation scope used for actual spends.

## Starting Point

The comparison logic in `budgets/summary.py` already creates rolled-up actual totals by walking parent links, while budget allocations are read as standalone per-category rows. The current test coverage in `budgets/tests.py` validates independence between parent and child rows but does not cover the combined-budget scenario that triggers the bug.

## Desired End State

A parent category row should reflect the total budget assigned across the category family, while still preserving separate child rows for subcategory transparency. The budget detail view should no longer show a master category as artificially negative just because actual spend is rolled up and the direct parent estimate is incomplete.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Scope | Fix the summary-layer budget math only | The issue is in comparison logic, not in the category model or transaction data | Plan |
| Regression style | Add a focused Django test for parent + child allocation mismatch | This makes the bug explicit and prevents reintroduction | Plan |
| User-visible behavior | Keep parent and child rows separate, but unify parent estimate calculation | It preserves the current budget UI while correcting the underlying mismatch | Plan |

## Scope

**In scope:**
- Correct the parent budget comparison calculation in `budgets/summary.py`
- Add a targeted regression in `budgets/tests.py`
- Validate the rendered budget detail behavior

**Out of scope:**
- Category hierarchy redesign or migration
- Transaction assignment logic changes
- UI redesign beyond validating the existing rendered table

## Architecture / Approach

The fix stays in the budget summary layer. We will keep the current row structure and display order, but normalize the parent row's budgeted total to the same category-tree scope as the actual totals. This narrows the risk to one calculation path while preserving the existing user-facing segmentation between master and subcategories.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Regression | Lock down the failing parent + child budget case | Missing the real mismatch pattern |
| 2. Summary fix | Correct parent estimate aggregation without disturbing child rows | Double counting or broken ordering |
| 3. Validation | Confirm the page reflects the corrected behavior | Subtle UI/data drift |

**Prerequisites:** existing Django test suite and budget detail view
**Estimated effort:** ~1-2 focused implementation passes with targeted regression coverage

## Open Risks & Assumptions

- The intended behavior is to aggregate the parent estimate across the category family, not to eliminate parent row visibility.
- The fix should remain intentionally narrow to avoid changing broader budgeting semantics.

## Success Criteria (Summary)

- Parent category rows reflect the combined category-family budget, not only the direct parent allocation.
- Child category rows remain independently understandable and correctly scoped.
- The budget detail page no longer shows a master category as artificially negative when the family-level budget is valid.
