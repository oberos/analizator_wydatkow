# Remove income from budget — Plan Brief

> Full plan: `context/changes/remove-income-from-budget/plan.md`

## What & Why

Budget comparisons are currently using the net category summary, so positive income rows are being counted as if they were spending. That makes the budget variance look worse than the real outflow during the selected period. This change keeps the reporting summary as-is and makes budget cards and detail views measure only actual expenses against the budget.

## Starting Point

The budget list and detail pages already call `get_budget_comparison()` from `budgets/summary.py`, and that helper pulls its `actual_amount` directly from `get_user_category_summary()` in `transactions/summary.py`. The transaction summary intentionally includes signed net totals, which is useful for category reporting but incorrect for expense budgets.

## Desired End State

Budget rows show spending-only actuals for the selected period, and income is ignored when determining whether the budget is over or under. The user sees a true spend-versus-budget comparison while the broader category reports continue to reflect the net cash-flow behavior they were designed for.

## Key Decisions Made

| Decision | Choice | Why |
| --- | --- | --- |
| Budget scope | Measure expense-only actuals | Budgets represent outflows, not net cash flow |
| Reporting scope | Leave transaction category summaries unchanged | The net totals are intentionally used elsewhere and are not the bug |
| Fix location | Budget comparator, not templates | One helper feeds both the list and detail views |

## Scope

**In scope:**
- Correcting budget actual totals for categories containing both expenses and income
- Updating the shared budget comparison helper used by the budget list and detail pages
- Adding regression coverage for the mixed-income/expense scenario

**Out of scope:**
- Changing the general transaction summary semantics used for reports and dashboards
- Redesigning budget allocation schema or date-range logic
- Broad cleanup outside the budget comparison path

## Architecture / Approach

The fix is intentionally narrow: keep the transaction summary contract stable and filter budget actuals to expense amounts before the comparison is computed. That preserves the existing reporting model while making the budget layer reflect what the user actually spent during the budget period.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Add regression | Lock the expected behavior for mixed income/expense categories | The bug is accepted as normal if no test captures it |
| 2. Filter budget actuals | Budget calculations ignore income and reflect true spend | Accidentally changing the general reporting summary |

**Prerequisites:** None beyond the existing Django test setup and access to the budget UI.
**Estimated effort:** ~1-2 focused sessions across 2 phases.

## Open Risks & Assumptions

- The project intentionally treats income as part of net category summaries elsewhere, so the fix must stay budget-local.
- Refunds and reimbursements can also appear as positive amounts, and they should be treated the same as other incoming money in the budget context.

## Success Criteria (Summary)

- Budget cards and detail rows no longer inflate actual spend because of incoming money.
- Categories with both expenses and income are calculated against the expense side of the ledger only.
- Existing under/over budget tests still pass with the regression covered.
