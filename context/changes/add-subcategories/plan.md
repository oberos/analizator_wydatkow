# Add Subcategories Implementation Plan

## Overview

`Category` is currently a flat model (`name`, `color`, `user`) shared across the categories, transactions, and budgets apps. This plan adds a single level of category hierarchy (category → subcategory) so users can organize spending more granularly, while keeping top-level categories fully usable on their own (a transaction or budget allocation can target either level).

## Current State Analysis

- `Category` (`categories/models.py`) has no hierarchy; `unique_together = ("name", "user")`; color auto-assigned via `color_for_category_name` if not provided.
- Predefined categories are seeded twice: once via data migration (`categories/migrations/0002_seed_predefined_categories.py`, 5 names) and once via `post_save` signal (`categories/signals.py::create_predefined_categories`, 13 names incl. "Unknown") for newly registered users.
- `Transaction.category` (`transactions/models.py`) is `ForeignKey(Category, on_delete=SET_NULL, null=True, blank=True)` — generic, no hierarchy awareness needed.
- `MerchantCategoryMapping.category` (`transactions/models.py`) is `ForeignKey(Category, on_delete=CASCADE)` — also generic.
- Auto-categorization (`transactions/categorization.py::categorize_transaction`) and correction sync (`transactions/refinement.py::apply_category_correction` → `_sync_merchant_mapping`) both operate on whatever `Category` instance is passed — **no code change needed** for a merchant mapping or transaction to target a subcategory once one exists.
- `TransactionCategoryCorrectionForm` and `BudgetAllocationForm` (`transactions/forms.py`, `budgets/forms.py`) both build their category choices from `Category.objects.filter(user=user)` — a flat queryset. Subcategories will appear automatically; only the *presentation* (grouping/indentation) needs updating.
- `transactions/summary.py::get_user_category_summary` groups `Transaction` rows by `category__name` (or "Uncategorized") — flat, one row per category, no rollup.
- `budgets/summary.py::get_budget_comparison` joins `BudgetCategoryAllocation` rows with the flat summary above, keyed by `category_name` — also flat.
- `accounts/views.py::dashboard_view` calls `get_user_category_summary` directly and builds a pie-chart payload (`_build_dashboard_chart_payload`) by iterating rows — consumes the same flat shape used by `templates/dashboard.html`.
- `templates/categories/category_form.html` renders every visible form field generically (`{% for field in form.visible_fields %}`), special-casing only the `color` field as an `<input type="color">`; every other field (including a new `parent` field) renders as a bare `<input type="text">` unless the template is updated to special-case `<select>` fields.
- `templates/categories/category_list.html` renders a flat `<ul>` of all categories with no grouping.

## Desired End State

- `Category` supports exactly one level of nesting via a nullable self-referential `parent` FK. A category with existing subcategories cannot itself be assigned a parent (depth capped at 1), enforced in `Category.clean()`.
- Name uniqueness is scoped to the parent: two subcategories under different parents (or a subcategory and a top-level category) may share a name; a subcategory name must be unique among its siblings, and top-level names remain unique among themselves.
- Deleting a parent category cascades to delete its subcategories (`on_delete=CASCADE` for `parent`), with the delete-confirmation page listing affected children before the user confirms.
- The category create/edit form gains an optional "Parent category" dropdown (top-level categories only, excluding categories that already have subcategories and, on edit, excluding the category itself and its own children). New subcategories pre-fill the parent's color but the user can override it.
- The category list page groups subcategories visually under their parent (indented), with top-level categories that have no parent shown at the top level.
- Category `<select>` widgets used elsewhere (transaction correction, budget allocation) group subcategories under their parent using `<optgroup>`.
- Spending summaries (`transactions/summary.py`, `budgets/summary.py`, `templates/dashboard.html`, `templates/budgets/budget_detail.html`) show one row per top-level category with a rolled-up total (its own directly-assigned transactions + all its subcategories' transactions) and an expandable/nested breakdown of subcategory totals underneath. Budget allocations can be made at either level; the comparison table shows the parent's own allocation vs. its own rolled-up actual, and separately each subcategory's allocation vs. its own actual — no amount is silently double-counted because each row compares its own allocation to its own (possibly rolled-up) actual.

### Key Discoveries:

- `transactions/refinement.py::apply_category_correction` and `transactions/categorization.py` require **zero changes** — they already operate on arbitrary `Category` instances, so subcategory assignment "just works" for transactions and merchant-mapping learning the moment the `parent` field exists.
- `budgets/forms.py::BudgetAllocationForm` and `budgets/views.py::BudgetUpdateView.get_context_data` already build allocation rows from `Category.objects.filter(user=user)` (flat) — allocating to a subcategory requires no model/view change, only presentation grouping.
- The only genuinely new backend logic is the summary/reporting rollup (Phase 4) — everything else is data model + presentation.

## What We're NOT Doing

- No nesting deeper than one level (subcategories cannot have their own subcategories).
- No default/seeded subcategories for the existing predefined categories — users create their own.
- No changes to CSV import/parsing or the ING CSV format.
- No admin-site (`categories/admin.py`) registration for categories or subcategories — out of scope, not currently used.
- No bulk "move all transactions from subcategory X to Y" tooling.
- No changes to the `MerchantCategoryMapping` predefined seed data (`transactions/mappings/`) — predefined mappings continue to target only top-level categories.

## Implementation Approach

Add the `parent` FK and its validation first (Phase 1), then the CRUD UI for managing hierarchy (Phase 2), then update the two existing category `<select>` widgets to visually group by parent (Phase 3), then rework the summary/reporting layer for rollup (Phase 4), and close with cross-app test coverage of the new edge cases (Phase 5). Phases 1–3 have no dependency on Phase 4, so the ordering keeps each phase's success criteria independently testable.

## Critical Implementation Details

### State sequencing

The rollup computation in Phase 4 must be done in Python after a single grouped DB query, not via a second correlated query per parent — `get_user_category_summary` should fetch all categories (with `parent_id`) and all per-category actual totals/counts in one annotated queryset each, then combine in memory: build a `{category_id: row}` map from the transaction aggregation, then walk categories to attach each subcategory's totals to its parent's row and compute the parent's rolled-up total as `own_total + sum(child totals)`. This avoids N+1 queries when a user has many subcategories.

## Phase 1: Data Model — Category Hierarchy

### Overview

Add the self-referential `parent` field to `Category`, migration, and validation rules (depth-1 cap, scoped uniqueness, color inheritance).

### Changes Required:

#### 1. Category model

**File**: `categories/models.py`

**Intent**: Add an optional `parent` FK so a `Category` can belong to another `Category` of the same user. Replace the global `unique_together` with parent-scoped uniqueness, cap nesting at one level, and default a new subcategory's color to its parent's color when not explicitly set.

**Contract**:
- New field: `parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="subcategories")`.
- `Meta.unique_together` becomes `("name", "user", "parent")` (Django treats `NULL` as distinct per-row in SQLite/Postgres, so this still prevents duplicate top-level names for a user because `parent` is `NULL` for all of them — verify this holds for the project's SQLite dev + Postgres/Render prod combination as part of Phase 1 automated verification, since unique-constraint NULL handling differs across databases only when a *composite* key contains multiple nullable columns, which is not the case here since only `parent` is nullable).
- `clean()` additions: raise `ValidationError` if `self.parent is not None and self.parent.parent is not None` (no grandchildren); raise `ValidationError` if `self.parent is not None and self.subcategories.exists()` (a category with children cannot become a child itself — relevant on edit); raise `ValidationError` if `self.parent_id == self.pk` (no self-parenting) — guard already implied by the depth check but keep an explicit check since `pk` may be falsy on create.
- `save()`: when `self.parent_id and not self.color` (i.e., no explicit color given), default `self.color` to `self.parent.color` instead of `color_for_category_name(self.name)`.
- Add a `is_subcategory` property (`self.parent_id is not None`) for template/view convenience.

#### 2. Migration

**File**: `categories/migrations/0004_category_parent.py` (new)

**Intent**: Add the `parent` column and update the unique constraint.

**Contract**: `AddField` for `parent` (self-FK, null/blank) plus `AlterUniqueTogether` from `("name", "user")` to `("name", "user", "parent")`. No data backfill needed — all existing rows get `parent=NULL`.

### Success Criteria:

#### Automated Verification:

- Migration applies cleanly: `pdm run python manage.py migrate`
- `makemigrations --check` reports no missing migrations: `pdm run python manage.py makemigrations --check --dry-run`
- Model unit tests pass: `pdm run python manage.py test categories.tests`
- Type checking passes: `pdm run basedpyright`
- Linting passes: `pdm run ruff check .`

#### Manual Verification:

- N/A for this phase (no UI yet) — covered by automated tests.

---

## Phase 2: Category CRUD UI

### Overview

Expose the parent/child relationship in the category create/edit form and list view, and update the delete-confirmation flow to warn about cascading subcategory deletion.

### Changes Required:

#### 1. Category views

**File**: `categories/views.py`

**Intent**: Add `parent` to the editable fields and constrain the parent dropdown's choices to valid targets (the user's own top-level categories, excluding the category being edited).

**Contract**: `CategoryCreateView.fields` and `CategoryUpdateView.fields` become `["name", "color", "parent"]`. Since these are generic `CreateView`/`UpdateView` using `fields=[...]` rather than an explicit form class, introduce a small `CategoryForm(forms.ModelForm)` in a new `categories/forms.py` so the `parent` field's queryset can be scoped per-user and per-edit-instance; wire both views to `form_class = CategoryForm` and pass `user=self.request.user` (and `instance` already provided by Django's `UpdateView`) via `get_form_kwargs`.

#### 2. Category form (new file)

**File**: `categories/forms.py` (new)

**Intent**: Scope the `parent` field's queryset to the user's own top-level categories (excluding self on edit), and pre-fill `color` from the selected parent when creating a subcategory.

**Contract**: `CategoryForm.Meta.fields = ["name", "color", "parent"]`; `__init__(self, *args, user=None, **kwargs)` filters `self.fields["parent"].queryset = Category.objects.filter(user=user, parent__isnull=True)`, further excluding `self.instance.pk` when editing.

> **Adapted during implementation.** The original contract also applied `.exclude(subcategories__isnull=False)` to bar categories that already had children. That was wrong: it would cap every parent at exactly one subcategory, since a parent vanished from the dropdown as soon as it gained its first child. Depth-1 is already enforced without it — the `parent__isnull=True` filter means a subcategory can never be offered as a parent, and `Category.clean()` rejects assigning a parent to a category that already has children. Progress row 2.5 was reworded to match.

#### 3. Category form template

**File**: `templates/categories/category_form.html`

**Intent**: Render the new `parent` field as a `<select>` instead of falling into the generic text-input branch, and keep the existing color-input special case.

**Contract**: Extend the field-loop's conditional to special-case `field.html_name == 'parent'` (render `{{ field }}` — the bound `ModelChoiceField` widget already renders as a proper `<select class="form-select">` if the widget's `attrs` include that class — set `widgets = {"parent": forms.Select(attrs={"class": "form-select"})}` in `CategoryForm.Meta`) instead of building a raw `<input>`.

#### 4. Category list view + template

**File**: `categories/views.py`, `templates/categories/category_list.html`

**Intent**: Show subcategories nested under their parent instead of a flat alphabetical list.

**Contract**: `CategoryListView.get_queryset` orders by `["parent__name", "name"]` (nulls-first ordering already achieved because `Meta.ordering = ["name"]` sorts `NULL` before values in SQLite; verify actual ordering behavior in the automated test rather than assuming). In the template, iterate top-level categories (`parent_id is None`) as the outer list items, and for each render its `subcategories.all` as an indented nested `<ul>` directly beneath.

#### 5. Delete confirmation

**File**: `templates/categories/category_confirm_delete.html`, `categories/views.py`

**Intent**: Warn the user when deleting a category that has subcategories, since they will be deleted too.

**Contract**: `CategoryDeleteView.get_context_data` (new method) adds `subcategory_count` to context; template shows an additional warning paragraph when `object.subcategories.exists()`, naming the count and listing subcategory names.

### Success Criteria:

#### Automated Verification:

- Category CRUD tests pass: `pdm run python manage.py test categories.tests`
- Linting passes: `pdm run ruff check .`
- Type checking passes: `pdm run basedpyright`

#### Manual Verification:

- Creating a category, then a subcategory under it, shows the subcategory nested under its parent in the list view
- The parent dropdown offers only top-level categories and never the category being edited; a parent that already has a subcategory is still offered, so it can take more
- Deleting a parent with subcategories shows a warning naming the affected subcategories before confirming
- New subcategory's color field pre-fills with the parent's color but can be changed

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 3.

---

## Phase 3: Category Dropdown Grouping (Transactions & Budgets)

### Overview

Update the two existing category `<select>` widgets outside the categories app (transaction correction, budget allocation) to visually group subcategories under their parent via `<optgroup>`, since both already include subcategories in their flat queryset with no further backend change needed.

### Changes Required:

#### 1. Transaction category correction dropdown

**File**: `transactions/views.py`, `templates/transactions/transaction_list.html`

**Intent**: Group the correction dropdown's options by parent category so subcategories appear visually nested.

**Contract**: `TransactionListView.get_context_data` replaces the flat `category_options` queryset with a grouped structure built by the shared `grouped_category_choices()` helper (single query, grouped in memory). The template renders native `<optgroup>` elements for parents that have children, keeping the parent itself selectable inside its own group.

> **Adapted during implementation.** The original contract targeted `TransactionCategoryCorrectionForm` in `transactions/forms.py`. That form is never rendered — it only validates the POST in `set_category` (`transactions/views.py`), while the UI hand-builds its `<select>` from `category_options` in `transaction_list.html`. Setting `.choices` on it would have been dead code with no visible effect, so the grouping moved to the view context plus the template. `transactions/forms.py` is intentionally left unchanged: its queryset already accepts subcategories, so validation is correct as-is.
>
> **Deferred.** The list's category filter uses `category__name`, which is ambiguous now that names are unique only per parent (two subcategories under different parents may share a name). Existing tests assert the name-based URL contract, so this is deferred to Phase 4 alongside the `budgets/summary.py` name-to-id keying work.

#### 2. Budget allocation form

**File**: `budgets/forms.py`

**Intent**: Apply the same grouping to `BudgetAllocationForm.fields["category"]`.

**Contract**: Same grouped-choices approach as above, applied after the existing `queryset = Category.objects.filter(user=user)` line (order by `["parent__name", "name"]` first).

### Success Criteria:

#### Automated Verification:

- Transactions tests pass: `pdm run python manage.py test transactions.tests`
- Budgets tests pass: `pdm run python manage.py test budgets.tests`
- Linting passes: `pdm run ruff check .`
- Type checking passes: `pdm run basedpyright`

#### Manual Verification:

- On the transaction list/correction UI, subcategories appear grouped under their parent category's optgroup in the dropdown
- On the budget edit page, the category allocation dropdown shows the same grouping
- Selecting a subcategory for a transaction correction still creates/updates a `MerchantCategoryMapping` pointing at that subcategory (no regression)

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 4.

---

## Phase 4: Reports & Summary Rollup

### Overview

Rework the category spending summary so top-level categories show a rolled-up total (their own transactions plus all subcategories' transactions), with each subcategory's own total available as a nested breakdown, and thread this new shape through budget comparison and the dashboard.

### Changes Required:

#### 1. Transaction category summary

**File**: `transactions/summary.py`

**Intent**: Restructure `get_user_category_summary` to return one row per top-level category (plus an "Uncategorized" row), each carrying its own rolled-up `total_amount`/`transaction_count` and a `subcategories` list of same-shaped rows for its children.

**Contract**: Query stays a single grouped-by-`category` aggregation (group by actual `category_id`/`category__parent_id`, not just name, since uniqueness is no longer global-by-name). Build an in-memory map of `category_id -> {name, color, total_amount, transaction_count}` from the aggregation, then a second pass walks the user's `Category` queryset (`select_related("parent")`) to assemble parent rows with `subcategories` lists and rolled-up totals per the Critical Implementation Details note above. Keep the returned row shape backward-compatible for top-level rows (`category_name`, `category_color`, `total_amount`, `transaction_count` keys preserved) and add a new `subcategories` key (list, possibly empty) to each row so existing consumers that ignore the new key keep working.

#### 2. Budget comparison

**File**: `budgets/summary.py`

**Intent**: Match `BudgetCategoryAllocation` rows (which may target a parent or a subcategory) against the new nested summary shape, producing one comparison row per allocation (parent or subcategory) compared against that same category's own (possibly rolled-up, if parent) actual total — plus unallocated categories/subcategories with spending.

**Contract**: Flatten the nested summary from `get_user_category_summary` into a lookup keyed by `category_id` (using each row's own total for that level — parent rows already carry the rolled-up total, subcategory rows carry their own) before joining with allocations, replacing the current `category_name`-keyed lookup (which breaks now that names aren't globally unique). Comparison rows keep their existing keys; sort order becomes parent-then-children (top-level categories in name order, each immediately followed by its own subcategories in name order) instead of a flat alphabetical sort.

#### 3. Dashboard view

**File**: `accounts/views.py`

**Intent**: Keep the pie-chart payload builder (`_build_dashboard_chart_payload`) working against top-level rolled-up totals only (one slice per top-level category, matching current chart granularity) since it already iterates `category_summary` rows without expecting a `subcategories` key.

**Contract**: No change required if `get_user_category_summary`'s top-level rows keep the same keys the payload builder reads (`category_name`, `category_color`, `total_amount`) — verify with the existing dashboard tests. If the payload builder needs the raw list without the nested key, that's already satisfied since it only reads the keys it always read.

#### 4. Dashboard & budget detail templates

**File**: `templates/dashboard.html`, `templates/budgets/budget_detail.html`

**Intent**: Render each top-level category's rolled-up row followed by its (initially collapsed or simply indented) subcategory breakdown rows.

**Contract**: Add a nested `{% for sub in row.subcategories %}` loop rendering an indented row (or a Bootstrap collapse) directly beneath each top-level row in both the dashboard summary table and the budget comparison table.

### Success Criteria:

#### Automated Verification:

- Transactions summary tests pass: `pdm run python manage.py test transactions.tests`
- Budgets summary tests pass: `pdm run python manage.py test budgets.tests`
- Accounts/dashboard tests pass: `pdm run python manage.py test accounts.tests`
- Linting passes: `pdm run ruff check .`
- Type checking passes: `pdm run basedpyright`

#### Manual Verification:

- Dashboard shows one pie slice / table row per top-level category with subcategory spending included in the total
- Dashboard table shows subcategory rows nested/indented beneath their parent with their own totals
- A budget with an allocation on a parent category and a separate allocation on one of its subcategories shows two independent comparison rows, and the parent row's actual figure includes all its subcategories' spending (not just its own direct transactions)
- No transaction amount is visibly double-counted in the sum of displayed totals when both a parent and a child have allocations

**Implementation Note**: Pause here for manual confirmation before proceeding to Phase 5.

---

## Phase 5: Cross-App Test Coverage & Polish

### Overview

Fill in test coverage for the new hierarchy-specific edge cases across all three affected apps.

### Changes Required:

#### 1. Category model/view tests

**File**: `categories/tests.py`

**Intent**: Cover depth-1 enforcement, parent-scoped uniqueness, cascade delete, and color inheritance.

**Contract**: New test cases: creating a subcategory of a subcategory raises `ValidationError`; assigning a parent to a category that already has subcategories raises `ValidationError`; two subcategories with the same name under different parents both save successfully; a subcategory and a top-level category may share a name; deleting a parent category cascades to delete its subcategories; a subcategory created without an explicit color inherits its parent's color; an explicit color on a new subcategory is preserved (not overwritten by inheritance).

#### 2. Transaction categorization/ownership tests

**File**: `transactions/tests.py`

**Intent**: Confirm auto-categorization, correction, and merchant-mapping sync work unchanged when the target category is a subcategory.

**Contract**: New test cases: `apply_category_correction` to a subcategory creates a `MerchantCategoryMapping` pointing at that subcategory; a subsequent import matching that merchant auto-assigns the subcategory; cross-user ownership checks still reject a subcategory owned by another user.

#### 3. Budget allocation/comparison tests

**File**: `budgets/tests.py`

**Intent**: Confirm allocations at either level compare correctly and don't double-count.

**Contract**: New test cases: an allocation on a subcategory produces a comparison row scoped to that subcategory's own transactions; an allocation on a parent with its own directly-assigned transactions plus subcategory transactions produces a rolled-up actual; a budget with both a parent allocation and a subcategory allocation produces two independent rows.

#### 4. Transaction list category filter (added during implementation)

**File**: `transactions/views.py`, `templates/transactions/transaction_list.html`, `transactions/tests.py`

**Intent**: Resolve the `?category=<name>` ambiguity deferred from Phase 3.

**Contract**: `TransactionListView` filters on `category_id` instead of `category__name`. A non-empty but unresolvable value (non-numeric, or an id not owned by the requesting user) yields an empty queryset rather than silently dropping the filter, so a stale link can never widen the visible set. `get_context_data` keeps `selected_category` as the raw query-string value for URL round-tripping and adds `selected_category_id` / `selected_category_name` for rendering. The now-unused flat `category_options` context entry is removed; the filter dropdown renders `<optgroup>` elements from the existing `category_groups`. Selecting a parent matches only its directly-assigned transactions — filtering stays an exact-category operation and deliberately does not adopt the dashboard's rollup semantics.

> **Adapted during implementation.** This section was not in the approved plan. The `?category=<name>` filter was deferred from Phase 3 "to Phase 4", but Phase 4's scope turned out to be summary rollup only, so the item was carried into Phase 5. With names now unique only per parent, two subcategories named `Other` under different parents both matched `?category=Other`. The user chose the id-based fix over keeping names. Five existing tests in `PaginationAndFilterSortTests` were updated from name-based to id-based query parameters.

### Success Criteria:

#### Automated Verification:

- Full test suite passes: `pdm run python manage.py test`
- Linting passes: `pdm run ruff check .`
- Formatting is clean: `pdm run ruff format --check .`
- Type checking passes: `pdm run basedpyright`

#### Manual Verification:

- Spot-check the full user flow end-to-end: create a parent category, create a subcategory under it, correct a transaction to the subcategory, verify the merchant mapping learns it, create a budget with allocations at both levels, confirm the dashboard and budget detail page show correct rolled-up and per-subcategory figures.

---

## Testing Strategy

### Unit Tests:

- Model validation: depth-1 cap, parent-scoped uniqueness, cascade delete, color inheritance (`categories/tests.py`)
- Form scoping: parent dropdown excludes invalid targets (`categories/tests.py`)
- Auto-categorization and correction targeting subcategories (`transactions/tests.py`)
- Budget comparison rollup and no-double-count invariant (`budgets/tests.py`)

### Integration Tests:

- End-to-end: create subcategory → correct transaction → verify merchant mapping → verify dashboard/budget rollup reflects the change

### Manual Testing Steps:

1. Create a top-level category and a subcategory under it via the UI.
2. Attempt to nest a subcategory under another subcategory — confirm it's rejected.
3. Correct a transaction to the subcategory and re-import a CSV with the same merchant — confirm auto-categorization to the subcategory.
4. Create a budget, allocate to both the parent and the subcategory, and confirm the budget detail page shows two rows with correct, non-double-counted actual figures.
5. Delete the parent category and confirm the subcategory is also removed, with the confirmation page having warned about it beforehand.

## Performance Considerations

The rollup computation in Phase 4 must avoid N+1 queries (see Critical Implementation Details) — one aggregation query plus one category-with-parent query per summary call, regardless of subcategory count.

## Migration Notes

The Phase 1 migration is purely additive (nullable FK + constraint change) — no data backfill is required, and existing categories remain valid top-level categories after migration.

## References

- Related change folder: `context/changes/add-subcategories/`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Data Model — Category Hierarchy

#### Automated

- [x] 1.1 Migration applies cleanly — a292f62
- [x] 1.2 makemigrations --check reports no missing migrations — a292f62
- [x] 1.3 Model unit tests pass — a292f62
- [x] 1.4 Type checking passes — a292f62
- [x] 1.5 Linting passes — a292f62

### Phase 2: Category CRUD UI

#### Automated

- [x] 2.1 Category CRUD tests pass — 34e82a9
- [x] 2.2 Linting passes — 34e82a9
- [x] 2.3 Type checking passes — 34e82a9

#### Manual

- [x] 2.4 Creating a subcategory shows it nested under its parent in the list view — 34e82a9
- [x] 2.5 Parent dropdown offers only top-level categories, excludes the category itself, and still offers parents that already have subcategories — 34e82a9
- [x] 2.6 Deleting a parent with subcategories warns about cascading deletion — 34e82a9
- [x] 2.7 New subcategory's color pre-fills from parent but can be changed — 34e82a9

### Phase 3: Category Dropdown Grouping (Transactions & Budgets)

#### Automated

- [x] 3.1 Transactions tests pass — 61c5e84
- [x] 3.2 Budgets tests pass — 61c5e84
- [x] 3.3 Linting passes — 61c5e84
- [x] 3.4 Type checking passes — 61c5e84

#### Manual

- [x] 3.5 Transaction correction dropdown groups subcategories under parent — 61c5e84
- [x] 3.6 Budget allocation dropdown groups subcategories under parent — 61c5e84
- [x] 3.7 Selecting a subcategory for a transaction correction still syncs the merchant mapping — 61c5e84

### Phase 4: Reports & Summary Rollup

#### Automated

- [x] 4.1 Transactions summary tests pass — 1dd2e10
- [x] 4.2 Budgets summary tests pass — 1dd2e10
- [x] 4.3 Accounts/dashboard tests pass — 1dd2e10
- [x] 4.4 Linting passes — 1dd2e10
- [x] 4.5 Type checking passes — 1dd2e10

#### Manual

- [x] 4.6 Dashboard pie/table shows rolled-up totals per top-level category — 1dd2e10
- [x] 4.7 Dashboard table shows subcategory rows nested beneath their parent — 1dd2e10
- [x] 4.8 Budget detail shows independent parent + subcategory allocation rows with correct rollup — 1dd2e10
- [x] 4.9 No amount is double-counted across displayed totals — 1dd2e10

### Phase 5: Cross-App Test Coverage & Polish

#### Automated

- [x] 5.1 Full test suite passes
- [x] 5.2 Linting passes
- [x] 5.3 Formatting is clean
- [x] 5.4 Type checking passes

#### Manual

- [x] 5.5 End-to-end spot check of the full user flow
