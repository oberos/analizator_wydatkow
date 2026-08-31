# Add Subcategories — Plan Brief

> Full plan: `context/changes/add-subcategories/plan.md`

## What & Why

Add one level of category hierarchy (category → subcategory) so users can organize spending more granularly than the current flat category list allows, while keeping every existing flat-category workflow (transaction assignment, auto-categorization, budget allocation, reporting) working unchanged for users who never create a subcategory.

## Starting Point

`Category` is a flat model (`name`, `color`, `user`, unique per user) used by three apps: `categories` (CRUD), `transactions` (assignment + merchant-based auto-categorization), and `budgets` (per-category allocations + comparison). Summaries (`transactions/summary.py`, `budgets/summary.py`, dashboard) group spending by a single flat `category_name`.

## Desired End State

Users can create a subcategory under any top-level category (one level deep only). Transactions and budget allocations can target either level. The dashboard and budget detail pages show each top-level category's rolled-up total (its own spending plus all its subcategories') with subcategory totals broken out underneath, and nothing is double-counted.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Nesting depth | One level only | Keeps model, validation, and UI simple; no real user need for deeper nesting surfaced | Plan |
| Transaction/allocation targeting | Either level (parent or subcategory) | Matches how the underlying `Category` FK already works everywhere with zero extra code | Plan |
| Summary/report shape | Rollup + expandable breakdown | Preserves the existing "total spend per top-level category" mental model while adding detail | Plan |
| Budget allocation targeting | Either level | Consistent with transaction targeting; no code change needed, only dropdown grouping | Plan |
| Merchant auto-categorization | Can target subcategories directly | Already works — mapping just stores whatever `Category` was corrected to | Plan |
| Parent deletion | Cascade to subcategories | Matches existing `SET_NULL`/`CASCADE` FK patterns already in the codebase; confirmation page warns first | Plan |
| Name uniqueness | Scoped to parent (siblings unique, cross-parent names can repeat) | Lets subcategories reuse common names (e.g. "Other") under different parents | Plan |
| Predefined categories | No default subcategories seeded | Keeps onboarding unchanged; users opt in by creating their own | Plan |
| Category form UI | Parent dropdown + indented list | Minimal UI change reusing the existing generic CRUD template structure | Plan |
| Subcategory color | Inherits parent's color by default, overridable | Visual grouping in charts/lists without forcing a color choice | Plan |
| Double-counting avoidance | Each allocation row compares against its own (rolled-up if parent) actual | Simplest rule that stays correct: parent vs. parent-rollup, child vs. child-only | Plan |
| Depth enforcement | Validated in `Category.clean()` | Centralizes the invariant at the model layer so all entry points (forms, admin, scripts) are protected | Plan |

## Scope

**In scope:**
- `Category.parent` self-FK, migration, validation (depth-1, scoped uniqueness, color inheritance, cascade delete)
- Category CRUD form/list/delete UI updates for hierarchy
- Category `<select>` grouping (optgroup) in transaction correction and budget allocation forms
- Rollup logic in `transactions/summary.py` and `budgets/summary.py`, threaded through dashboard and budget detail templates
- Cross-app test coverage for all of the above

**Out of scope:**
- Nesting deeper than one level
- Default/seeded subcategories for predefined categories
- CSV import/parsing changes
- Django admin registration for categories
- Bulk transaction re-parenting tools
- Predefined merchant-mapping seed changes

## Architecture / Approach

Add the `parent` FK and its model-layer validation first, since every other phase depends on it. The transaction-assignment and budget-allocation *targeting* paths need no backend changes at all — they already operate on arbitrary `Category` rows — so those phases are UI-only (dropdown grouping). The one genuinely new piece of logic is the summary rollup: a single aggregation query per app, combined in memory with the category tree (to avoid N+1 queries), producing a nested `{parent_row: {..., subcategories: [...]}}` shape that both the dashboard and budget comparison consume.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Data Model | `parent` FK, migration, depth/uniqueness/color validation | Getting the parent-scoped `unique_together` semantics right across dev SQLite and prod Postgres |
| 2. Category CRUD UI | Parent dropdown, nested list, cascade-delete warning | Generic form template only special-cases the color field today — needs a `<select>` branch |
| 3. Dropdown Grouping | Optgroup grouping in transaction/budget category selects | Must not regress existing flat-list behavior for users with no subcategories |
| 4. Reports & Summary Rollup | Rolled-up dashboard/budget totals with subcategory breakdown | Avoiding double-counted actuals when both parent and child have allocations |
| 5. Cross-App Test Coverage | Edge-case tests across categories/transactions/budgets | Ensuring rollup and validation edge cases are actually exercised, not just implemented |

**Prerequisites:** None beyond the current codebase state — no external dependencies or access needed.
**Estimated effort:** ~4-5 sessions across 5 phases (Phase 4 is the largest single piece of new logic).

## Open Risks & Assumptions

- Assumes SQLite (dev) and the Postgres target (Render, prod) both treat `NULL` as distinct for composite unique constraints on a single nullable column (`parent`) the same way — this is standard SQL behavior but should be confirmed by an automated test in Phase 1, not just assumed.
- Assumes no existing user data needs a subcategory backfill — this plan only adds structure going forward.

## Success Criteria (Summary)

- A user can create a subcategory, assign transactions to it (manually or via auto-categorization), and see its own transactions counted both in its own total and rolled into its parent's total.
- A user can allocate budget to a parent and/or its subcategories independently, and the budget detail page shows correct, non-double-counted figures for each.
- Deleting a parent category cleanly removes its subcategories after an explicit warning.
