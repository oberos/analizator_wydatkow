# Show transactions from budget — Plan Brief

> Full plan: `context/changes/show-transactions-from-budget/plan.md`

## What & Why

The budget detail view can already tell us which categories are over or under budget, but it stops short of helping the user inspect the actual transactions behind that number. This change adds a drill-down from each category row to the existing transaction list so the user sees only the transactions in that category during the budget's date window.

## Starting Point

The app already has a working budget comparison flow and a transaction list with category filtering, sorting, and pagination. The gap is that the budget detail page is purely informational, while the transaction list only understands manual filter state and does not yet accept a date range passed from another screen.

## Desired End State

A user can click a budget category and land on the transaction list pre-filtered to the correct category and budget period. The result set is still user-scoped, sortable, and paginated, and the user can clear the drill-down filter to return to the full list.

## Key Decisions Made

| Decision | Choice | Why |
| --- | --- | --- |
| Entry point | Redirect from budget detail category rows to the existing transactions page | Keeps the feature lightweight and reuses the filter UX already present in the app |
| Query contract | Extend the transaction list with optional `start_date` and `end_date` params | Allows the budget date window to drive the filtered results without inventing a new page |
| State handling | Preserve budget filters on transaction edits and clear them when the user resets the view | Keeps the drill-down flow consistent with the current behavior for category/sort/page filters |

## Scope

**In scope:** clicking from a budget category to a filtered transaction list, date-range-aware transaction filtering, preserving filter state through edit redirects, empty-state handling for no matches.

**Out of scope:** new budget models or migrations, export actions, dashboard redesign, cross-user or global filtering changes.

## Architecture / Approach

The feature reuses the existing transaction page as the drill-down destination and extends its URL query-state contract instead of creating a separate route. The budget detail view passes the category name plus the budget date window; the transaction list reads those values, applies the `date__range` query when present, and keeps the rest of the list behavior unchanged. This keeps the code path minimal and aligned with the current user-isolation and pagination architecture.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Budget drill-through and filter contract | Category rows open a filtered transaction list for that budget period | Missing date-range support in the list view |
| 2. Regression-proofing and UX polish | Filter state stays stable after edits, and empty states are clear | Breaking existing category/sort behavior while adding new params |

**Prerequisites:** Budget and transaction pages already exist; the feature depends on the current budget comparison and transaction list behavior being stable.
**Estimated effort:** ~1-2 focused implementation sessions across 2 phases

## Open Risks & Assumptions

- The transaction list is the single source of drill-down behavior and should remain the canonical place for filter logic.
- Budget periods are expected to align with transaction date values already used elsewhere in the app.
- The date-range filter should be optional so the standard transactions page still works unchanged when it is not triggered from a budget.

## Success Criteria (Summary)

- A user can click a budget category and land on the matching transaction subset.
- The filtered list respects both the category and budget date range.
- Existing sort, page, and category-change flows remain intact.
- No transaction data leaks across user accounts.
