# Budget Management — Plan Brief

> Full plan: `context/changes/add-budget-view/plan.md`

## What & Why

Add budget management functionality where users can create budgets for specific time periods, allocate spending targets per category, and compare actual spending against budgeted amounts. This addresses the user need to track whether spending stays within planned limits for each category over a chosen date range.

## Starting Point

The codebase has complete transaction and category management with date-range filtering already working (`DashboardDateRangeForm`, `get_user_category_summary(start_date, end_date)`). Bootstrap datepicker UI and summary table rendering patterns are established. No budget models or views exist yet.

## Desired End State

Users navigate to `/budgets/` and see a list of their budgets as summary cards showing name, date range, total budgeted (sum of category allocations), actual spending, and difference. Clicking a budget reveals a detailed table with per-category breakdown: Category | Budgeted | Actual | Difference, with color-coded badges (green=under budget, red=over, yellow=close). Users can create, edit, and delete budgets, and manage per-category allocations via an inline formset.

## Key Decisions Made

| Decision                       | Choice                                     | Why (1 sentence)                                                                                      | Source |
| ------------------------------ | ------------------------------------------ | ----------------------------------------------------------------------------------------------------- | ------ |
| Budget reusability             | One-time period instances                  | Each budget = one date range; no template/recurring logic needed for MVP.                             | Plan   |
| Budget total                   | Derived from category allocations          | User enters per-category amounts; total auto-calculated as sum.                                       | Plan   |
| Category deletion              | Cascade delete allocations                 | Removing a category removes its budget allocations; simplifies data integrity without blocking users. | Plan   |
| Date range overlaps            | Block overlaps via validation              | One budget per date enforced in `clean()` to prevent conflicting targets for same period.             | Plan   |
| Budget navigation              | List with summary cards                    | Each card shows total vs actual at a glance without requiring drill-down.                             | Plan   |
| Comparison display             | Table + color-coded badges                 | Three columns (Budgeted, Actual, Difference) with green/red/yellow badges for visual status.          | Plan   |
| Zero budget allocations        | Allowed                                    | User can explicitly track categories they don't want to spend on by setting budget to zero.           | Plan   |
| Empty budget validation        | Allow budgets without allocations          | User can create budget container first, add category allocations later.                               | Plan   |

## Scope

**In scope:**
- New `budgets/` Django app with Budget and BudgetCategoryAllocation models
- CRUD views (list, create, detail, edit, delete) using Django CBVs + LoginRequiredMixin
- Budget list showing summary cards with total budgeted, actual, and difference
- Budget detail showing per-category comparison table with color-coded status badges
- Inline formset for managing category allocations within a budget
- Date range validation (start <= end) and overlap detection (no overlapping budgets for same user)
- Helper function `get_budget_comparison()` merging allocations with transaction summaries
- Templates reusing Bootstrap components, datepicker, and app-card styling
- Unit and integration tests covering model validation, comparison logic, and CRUD flows

**Out of scope:**
- Budget templates or reusable/recurring budgets
- Explicit budget total field (total is always derived)
- Preventing category deletion when used in budgets
- Percentage columns or variance calculations
- Budget notifications or alerts
- Bulk operations (copy, clone, apply template)
- Historical trend analysis or multi-budget comparison

## Architecture / Approach

New `budgets/` app follows the established pattern: Django CBVs with `LoginRequiredMixin`, models with user ForeignKey and queryset filtering in `get_queryset()`, shared `_form.html` templates for create/edit. Budget model has `name`, `start_date`, `end_date`, `user`. BudgetCategoryAllocation links Budget to Category with `amount` (DecimalField, >= 0). Comparison logic in `budgets/summary.py` calls existing `get_user_category_summary()` for actuals, merges with allocations, calculates difference and status ('under'|'over'|'close'). List view annotates each budget card with totals by summing allocations and querying transaction summary. Detail view passes `get_budget_comparison()` result to template for table rendering with color badges.

## Phases at a Glance

| Phase     | What it delivers                                   | Key risk                                                                                  |
| --------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 1. Models | Budget & BudgetCategoryAllocation with migrations  | Date overlap validation logic is complex and not fully enforceable at DB level (SQLite). |
| 2. Forms  | Budget form, allocation formset, comparison helper | Formset handling and overlap validation may have edge cases.                              |
| 3. Views  | CRUD views and URL routing                         | List view with per-budget summaries could be N+1 query issue if many budgets.            |
| 4. UI     | Templates with summary cards and comparison table  | Color-coded badges and date pickers need careful styling and JS initialization.          |
| 5. Tests  | Unit & integration tests for edge cases            | Overlap detection race conditions not fully testable without concurrent requests.        |

**Prerequisites:** Existing `transactions/summary.py`, `categories/models.py`, `DashboardDateRangeForm` pattern, Bootstrap UI components.

**Estimated effort:** ~3-4 sessions across 5 phases (model → forms → views → UI → tests).

## Open Risks & Assumptions

- **Date overlap validation** is performed in model `clean()`, not as a DB-level constraint. Race condition during concurrent budget creates is possible but unlikely in single-user MVP context.
- **List view performance**: Each budget card requires a transaction summary query. If a user has >10 budgets, consider prefetching allocations and batching summary queries.
- **Formset UX**: Dynamic add/remove of allocation rows may need JavaScript. Fallback: Django's default formset rendering with extra=3 blank forms.
- **Status threshold**: "Close to budget" is defined as within 10% (`abs(difference / budgeted) < 0.10`). This is arbitrary and may need tuning based on user feedback.

## Success Criteria (Summary)

- User can create a budget with name and date range, then add category allocations
- Budget list shows summary cards with total budgeted, actual spending, and difference for each budget
- Budget detail displays per-category breakdown table with correct differences and color-coded status badges (green/red/yellow)
- Attempting to create overlapping budgets is blocked with a clear validation error
- All tests pass (model validation, comparison logic, CRUD flows, edge cases)
