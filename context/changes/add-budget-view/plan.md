# Budget Management Implementation Plan

## Overview

Add a budget management feature where users can create budgets with name, start/end dates, and per-category spending allocations. Display actual spending vs budgeted amounts with visual indicators (color-coded) showing whether spending is under, over, or close to budget.

## Current State Analysis

The codebase already has:
- **Date range filtering infrastructure**: `DashboardDateRangeForm`, `get_user_category_summary(start_date, end_date)` in `transactions/summary.py`
- **Transaction aggregation by category**: Existing logic in `transactions/summary.py:13-51` with proper user isolation
- **CRUD patterns**: Established in `categories/` app — `LoginRequiredMixin` + CBVs, shared `_form.html` templates, user assignment in `form_valid()`
- **UI components**: Bootstrap datepicker setup (`dashboard.html:133-138`), table rendering patterns, form validation display
- **User isolation**: All models use `ForeignKey(AUTH_USER_MODEL, on_delete=CASCADE)` with `get_queryset()` filtering

Missing:
- Budget models (Budget, BudgetCategoryAllocation)
- Budget CRUD views and templates
- Budget list view with summary cards showing total vs actual spending
- Comparison logic to calculate differences and visual indicators

### Key Discoveries:

- **Date overlap validation**: No existing pattern for date range overlap constraints in Django models — will need custom validator or DB-level check constraint
- **Aggregate pattern**: `transactions/summary.py:28-48` shows proper use of `Coalesce`, `Case/When`, `Sum`, `Abs` for category totals — reusable for budget comparison
- **Form patterns**: `transactions/forms.py:57-99` (`DashboardDateRangeForm`) is the template for budget date range validation
- **Template patterns**: `categories/category_list.html` shows card-based list with inline action buttons — adaptable for budget cards with summary data

## Desired End State

Users can:
1. Navigate to `/budgets/` and see a list of all their budgets (cards showing name, date range, total budgeted, actual spending, difference)
2. Create a new budget with name, start date, end date
3. Add/edit/delete category allocations within a budget (amount per category)
4. View a detailed budget breakdown table with columns: Category | Budgeted | Actual | Difference, with color-coded visual indicators:
   - Green badge: under budget
   - Red badge: over budget
   - Yellow badge: close to budget (within 10%)
5. Edit budget details (name, dates) and delete budgets
6. See empty-state messaging when no budgets exist or when a budget has no allocations

### Verification:
- Create a budget "July 2026" with start=2026-07-01, end=2026-07-31
- Add allocations: Groceries 1000 PLN, Transport 500 PLN
- Upload transactions within that range
- Budget list shows actual spending pulled from transaction summary
- Detail view shows per-category breakdown with correct differences and color badges
- Attempting to create overlapping budget (e.g., 2026-07-15 to 2026-08-15) is blocked with validation error

## What We're NOT Doing

- Budget templates or reusable budgets (each budget is a one-time period instance)
- Explicit budget total field (total is derived from sum of category allocations)
- Preventing category deletion when used in budgets (cascade delete removes allocations)
- Percentage columns in budget table (only absolute difference shown)
- Budget notifications or alerts for overspending
- Bulk budget operations (copy, clone, apply template)
- Historical budget comparison or trend analysis

## Implementation Approach

Create a new `budgets/` Django app following the established pattern:
1. Models: `Budget` (name, dates, user) + `BudgetCategoryAllocation` (budget, category, amount)
2. Use Django CBVs (CreateView, UpdateView, DeleteView, ListView, DetailView) with `LoginRequiredMixin`
3. Reuse date range form validation logic from `DashboardDateRangeForm`
4. Add custom model validation for date overlap constraint
5. Build comparison logic as a helper function that merges budget allocations with transaction summary for the same date range
6. Render budget list with summary cards (reuse `app-card` CSS class)
7. Render budget detail with table + color-coded badges

## Phase 1: Budget Models & Migrations

### Overview

Create the data model for budgets and per-category allocations. Establish user isolation, date range validation, and overlap constraint.

### Changes Required:

#### 1. Create budgets app structure

**File**: `budgets/` (new directory)

**Intent**: Scaffold a new Django app to house budget-related models, views, forms, and templates.

**Contract**: Standard Django app structure with `__init__.py`, `apps.py`, `models.py`, `views.py`, `urls.py`, `admin.py`, `migrations/`, `tests.py`.

```bash
pdm run python manage.py startapp budgets
```

#### 2. Budget model

**File**: `budgets/models.py`

**Intent**: Define the Budget model representing a single budget period with name, start/end dates, and user ownership. Validate that start_date <= end_date and enforce no overlapping date ranges for the same user.

**Contract**: Model fields: `user` (ForeignKey), `name` (CharField max 200), `start_date` (DateField), `end_date` (DateField). Meta: ordering by `-start_date`, unique together constraint is not sufficient for overlaps — use custom `clean()` validation. Indexes on `(user, start_date)` for query performance.

#### 3. BudgetCategoryAllocation model

**File**: `budgets/models.py`

**Intent**: Define per-category budget allocations within a budget. Each allocation links a budget to a category with an amount (can be zero, no negatives).

**Contract**: Model fields: `budget` (ForeignKey to Budget, CASCADE), `category` (ForeignKey to Category, CASCADE), `amount` (DecimalField max_digits=12 decimal_places=2). Meta: unique together `(budget, category)` — one allocation per category per budget. Validation: amount >= 0, category must belong to same user as budget.user.

#### 4. Register budgets app

**File**: `analizator_wydatkow/settings.py`

**Intent**: Add 'budgets' to INSTALLED_APPS so Django recognizes the app and runs migrations.

**Contract**: Append `"budgets"` to the INSTALLED_APPS list (after `"transactions"`).

#### 5. Create initial migration

**File**: `budgets/migrations/0001_initial.py`

**Intent**: Generate and apply the migration to create Budget and BudgetCategoryAllocation tables in the database.

**Contract**: Run `pdm run python manage.py makemigrations budgets` then `pdm run python manage.py migrate`.

### Success Criteria:

#### Automated Verification:

- Migration applies cleanly: `pdm run python manage.py migrate`
- Models importable: `pdm run python manage.py shell -c "from budgets.models import Budget, BudgetCategoryAllocation; print('OK')"`
- Type checking passes: `pdm run basedpyright budgets/`
- Linting passes: `pdm run ruff check budgets/`

#### Manual Verification:

- Create a Budget instance via Django shell with valid dates — saves successfully
- Attempt to create overlapping budgets for same user — validation error raised
- Create BudgetCategoryAllocation with amount=0 — succeeds
- Create BudgetCategoryAllocation with amount=-100 — validation error raised
- Delete a category with allocations — allocations cascade delete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Budget Forms & Helper Logic

### Overview

Create Django forms for budget creation/editing and a helper function to merge budget allocations with actual transaction summaries for comparison display.

### Changes Required:

#### 1. Budget form

**File**: `budgets/forms.py`

**Intent**: Create a form for Budget model with name and date range fields. Validate start_date <= end_date and check for overlapping budgets within the same user's scope.

**Contract**: ModelForm for Budget, fields `['name', 'start_date', 'end_date']`. Widget for date fields uses `js-date-picker` class (matching `DashboardDateRangeForm` pattern). Custom `clean()` method checks date ordering and queries existing budgets to block overlaps.

#### 2. Budget allocation formset

**File**: `budgets/forms.py`

**Intent**: Create an inline formset for managing BudgetCategoryAllocation entries within a budget. Allow adding/editing/deleting multiple category allocations in one form submission.

**Contract**: Django `inlineformset_factory(Budget, BudgetCategoryAllocation, ...)` with fields `['category', 'amount']`. Filter category queryset by request.user in view's `get_form_kwargs()`. Set `extra=3` blank forms, `can_delete=True`.

#### 3. Budget comparison helper

**File**: `budgets/summary.py`

**Intent**: Merge budget allocations with actual transaction summary for the same date range. Return a list of dicts with keys: `category_name`, `category_color`, `budgeted_amount`, `actual_amount`, `difference`, `status` ('under'|'over'|'close').

**Contract**: Function signature: `get_budget_comparison(budget: Budget) -> list[dict]`. Calls `get_user_category_summary(user, start_date, end_date)` for actuals, then merges with `budget.allocations.select_related('category')`. Status logic: if `abs(difference / budgeted) < 0.10` and budgeted > 0, status='close'; elif `difference < 0`, status='over'; else status='under'. Handle zero-budget and uncategorized cases.

### Success Criteria:

#### Automated Verification:

- Forms importable: `pdm run python manage.py shell -c "from budgets.forms import BudgetForm; print('OK')"`
- Helper function returns expected structure: unit test in `budgets/tests.py`
- Type checking passes: `pdm run basedpyright budgets/`
- Linting passes: `pdm run ruff check budgets/`
- Unit tests pass: `pdm run python manage.py test budgets.tests`

#### Manual Verification:

- Form validation catches overlapping dates with clear error message
- Form validation catches start_date > end_date
- Helper function correctly calculates difference and status for sample data
- Zero-budget categories marked as 'under' status
- Categories with no allocation but have transactions appear in comparison with status='over'

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Budget CRUD Views & URL Routing

### Overview

Implement Create, Update, Delete, List, and Detail views for budgets using Django CBVs. Wire up URL routing and register in main urlpatterns.

### Changes Required:

#### 1. Budget list view

**File**: `budgets/views.py`

**Intent**: Display all budgets for the logged-in user as summary cards showing name, date range, total budgeted (sum of allocations), actual spending (from transaction summary), and difference.

**Contract**: `LoginRequiredMixin + ListView`, model=Budget, `get_queryset()` filters by `request.user` ordered by `-start_date`. Add context: for each budget, call `get_budget_comparison()` and sum budgeted/actual/difference for card display. Template: `budgets/budget_list.html`.

#### 2. Budget detail view

**File**: `budgets/views.py`

**Intent**: Show detailed per-category breakdown table with columns: Category, Budgeted, Actual, Difference, and color-coded status badges.

**Contract**: `LoginRequiredMixin + DetailView`, model=Budget, `get_queryset()` filters by user. Add context: `comparison_data = get_budget_comparison(self.object)`. Template: `budgets/budget_detail.html`.

#### 3. Budget create view

**File**: `budgets/views.py`

**Intent**: Create a new budget with name and date range, then redirect to edit view to add category allocations.

**Contract**: `LoginRequiredMixin + CreateView`, model=Budget, form_class=BudgetForm. `form_valid()` assigns `form.instance.user = self.request.user`. Success URL redirects to budget detail or edit view. Template: `budgets/budget_form.html`.

#### 4. Budget update view

**File**: `budgets/views.py`

**Intent**: Edit budget name/dates and manage category allocations via inline formset.

**Contract**: `LoginRequiredMixin + UpdateView`, model=Budget, form_class=BudgetForm. Override `get_context_data()` to include allocation formset. Override `post()` to validate and save both budget form and formset. `get_queryset()` filters by user. Template: `budgets/budget_form.html` (shared with create).

#### 5. Budget delete view

**File**: `budgets/views.py`

**Intent**: Delete a budget and cascade-delete all its allocations.

**Contract**: `LoginRequiredMixin + DeleteView`, model=Budget. `get_queryset()` filters by user. Success URL redirects to budget list. Template: `budgets/budget_confirm_delete.html`.

#### 6. Budget URL patterns

**File**: `budgets/urls.py`

**Intent**: Define URL patterns for budget CRUD operations following Django conventions.

**Contract**: App name `budgets`, patterns: `''` → list, `'create/'` → create, `'<int:pk>/'` → detail, `'<int:pk>/edit/'` → update, `'<int:pk>/delete/'` → delete. URL names: `list`, `create`, `detail`, `edit`, `delete`.

#### 7. Register budget URLs in main urlpatterns

**File**: `analizator_wydatkow/urls.py`

**Intent**: Include budget URLs at `/budgets/` path.

**Contract**: Add `path("budgets/", include("budgets.urls"))` to urlpatterns (after transactions).

### Success Criteria:

#### Automated Verification:

- URL resolution works: `pdm run python manage.py shell -c "from django.urls import reverse; print(reverse('budgets:list'))"`
- Views importable: `pdm run python manage.py shell -c "from budgets.views import BudgetListView; print('OK')"`
- Type checking passes: `pdm run basedpyright budgets/`
- Linting passes: `pdm run ruff check budgets/`
- Integration tests pass: `pdm run python manage.py test budgets.tests`

#### Manual Verification:

- Navigate to `/budgets/` → see empty state message
- Click "Create Budget" → form renders with date pickers
- Submit valid budget → redirects to detail/edit view
- Edit budget → formset shows existing allocations, can add/delete rows
- Delete budget → confirmation page, then budget removed from list
- List view cards show correct totals and differences
- Detail view table shows per-category breakdown with color badges

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 4: Budget Templates & UI

### Overview

Create templates for budget list (summary cards), budget detail (comparison table with color badges), budget form (create/edit with formset), and delete confirmation. Reuse existing Bootstrap and datepicker setup.

### Changes Required:

#### 1. Budget list template

**File**: `templates/budgets/budget_list.html`

**Intent**: Display budget summary cards in a responsive grid. Each card shows budget name, date range, total budgeted, actual spending, difference, and action buttons (View, Edit, Delete).

**Contract**: Extends `base.html`. Uses `.app-card` class. Empty state: "No budgets yet. Create your first budget to track spending." Loop over `budgets` context var, each with computed `total_budgeted`, `total_actual`, `total_difference`. Link to `budgets:create`, `budgets:detail`, `budgets:edit`, `budgets:delete`.

#### 2. Budget detail template

**File**: `templates/budgets/budget_detail.html`

**Intent**: Show budget header (name, date range) and comparison table with Category | Budgeted | Actual | Difference columns. Each row has a color-coded badge indicating status.

**Contract**: Extends `base.html`. Table uses `.table .table-hover` classes. Badge colors: `.badge .bg-success` (under), `.badge .bg-danger` (over), `.badge .bg-warning` (close). Display "No allocations yet" if `comparison_data` is empty. Action buttons: Back to List, Edit Budget.

#### 3. Budget form template (shared create/edit)

**File**: `templates/budgets/budget_form.html`

**Intent**: Render budget form (name, start_date, end_date) with date pickers. On edit mode, also render allocation formset below with Add/Remove buttons.

**Contract**: Extends `base.html`. Detect mode via `{% if object %}`. Form follows `category_form.html` pattern: csrf_token, hidden fields, visible fields with labels/errors. Date inputs use `js-date-picker` class. Formset management script (optional JavaScript for dynamic add/remove rows, or rely on Django's formset template rendering).

#### 4. Budget delete confirmation template

**File**: `templates/budgets/budget_confirm_delete.html`

**Intent**: Confirm deletion with budget name and warning about cascade-deleting allocations.

**Contract**: Extends `base.html`. Form with POST method, csrf_token, submit button "Confirm Delete", and cancel link. Display budget name and date range for clarity.

#### 5. Add Budgets link to dashboard navigation

**File**: `templates/dashboard.html`

**Intent**: Add a "Budgets" card or navigation link to the dashboard so users can access budget management.

**Contract**: Insert a new `.app-card` in the grid (matching Transactions and Categories cards pattern) with heading "Budgets", description "Track spending against planned budgets for each period.", and link to `{% url 'budgets:list' %}`.

#### 6. Initialize date pickers on budget forms

**File**: `templates/budgets/budget_form.html` (extra_js block)

**Intent**: Activate Bootstrap datepicker on budget date fields using existing setup from `dashboard.html`.

**Contract**: Copy the jQuery datepicker initialization script from `dashboard.html:133-138` into `{% block extra_js %}` of `budget_form.html`. Ensure jQuery and datepicker libs are loaded via `{% block extra_head %}` with CDN links (or reference existing base includes).

### Success Criteria:

#### Automated Verification:

- Templates render without syntax errors: `pdm run python manage.py check --deploy`
- Linting passes: `pdm run ruff check budgets/`
- Type checking passes: `pdm run basedpyright budgets/`

#### Manual Verification:

- Budget list page renders empty state when no budgets exist
- Budget list shows cards with correct summary data when budgets exist
- Create budget form shows date pickers in Polish locale (dd/mm/yyyy)
- Edit budget form pre-fills name and dates, shows allocation formset
- Formset allows adding new allocation rows (if JS enabled)
- Detail view table shows correct color badges: green for under budget, red for over, yellow for close
- Delete confirmation page displays budget name and date range
- Dashboard includes "Budgets" navigation card

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 5: Testing & Edge Case Handling

### Overview

Write unit and integration tests covering budget creation, overlap validation, comparison logic, and edge cases (zero budgets, empty allocations, uncategorized transactions).

### Changes Required:

#### 1. Budget model tests

**File**: `budgets/tests.py`

**Intent**: Test budget creation, date validation, overlap detection, and cascade deletion of allocations when category is deleted.

**Contract**: Test cases:
- `test_budget_creation_valid` — create budget with valid dates
- `test_budget_start_after_end_invalid` — start_date > end_date raises ValidationError
- `test_budget_overlap_blocked` — creating overlapping budget for same user raises ValidationError
- `test_category_delete_cascades_allocation` — deleting category removes its allocations

#### 2. Budget allocation tests

**File**: `budgets/tests.py`

**Intent**: Test allocation creation, zero-amount handling, negative-amount rejection, and duplicate prevention.

**Contract**: Test cases:
- `test_allocation_zero_amount_allowed` — amount=0 is valid
- `test_allocation_negative_amount_invalid` — amount<0 raises ValidationError
- `test_allocation_duplicate_category_blocked` — same category twice in one budget raises IntegrityError
- `test_allocation_cross_user_category_blocked` — assigning another user's category raises ValidationError

#### 3. Budget comparison tests

**File**: `budgets/tests.py`

**Intent**: Test `get_budget_comparison()` logic with various scenarios: under budget, over budget, close to budget, zero budget, no allocations, uncategorized transactions.

**Contract**: Test cases:
- `test_comparison_under_budget` — budgeted=1000, actual=800 → difference=200, status='under'
- `test_comparison_over_budget` — budgeted=500, actual=600 → difference=-100, status='over'
- `test_comparison_close_to_budget` — budgeted=1000, actual=950 → status='close'
- `test_comparison_zero_budget` — budgeted=0, actual=100 → status='over'
- `test_comparison_no_allocation_but_spending` — category not in budget but has transactions → appears in comparison as 'over'
- `test_comparison_allocation_no_spending` — budgeted=500, actual=0 → difference=500, status='under'

#### 4. Budget view integration tests

**File**: `budgets/tests.py`

**Intent**: Test CRUD views with authenticated user: list, create, detail, edit, delete. Verify queryset filtering (user can only see own budgets) and success redirects.

**Contract**: Test cases:
- `test_budget_list_requires_login` — unauthenticated request redirects to login
- `test_budget_list_shows_only_user_budgets` — user A sees only their budgets, not user B's
- `test_budget_create_assigns_current_user` — new budget has `user=request.user`
- `test_budget_detail_shows_comparison_data` — context includes `comparison_data`
- `test_budget_update_saves_form_and_formset` — both budget and allocations updated
- `test_budget_delete_removes_budget_and_allocations` — cascade delete verified

### Success Criteria:

#### Automated Verification:

- All tests pass: `pdm run python manage.py test budgets.tests`
- Test coverage acceptable: coverage report shows >80% for budgets/ app (optional: `coverage run --source='budgets' manage.py test budgets.tests && coverage report`)
- Type checking passes: `pdm run basedpyright budgets/`
- Linting passes: `pdm run ruff check budgets/`

#### Manual Verification:

- Run each test case individually to verify expected behavior
- Check test output for any flaky tests or timing issues
- Verify test fixtures (users, categories, transactions) are properly isolated

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Budget model: date validation, overlap detection, cascade behavior
- BudgetCategoryAllocation model: amount validation, uniqueness, user isolation
- `get_budget_comparison()`: status calculation, edge cases (zero, empty, uncategorized)
- Forms: overlap validation, date ordering, formset handling

### Integration Tests:

- Budget CRUD views: authentication, queryset filtering, success redirects
- End-to-end flow: create budget → add allocations → view detail → see correct comparison
- Edge case scenarios: empty budgets, overlapping attempts, category deletion during active budget

### Manual Testing Steps:

1. **Create budget flow**:
   - Navigate to `/budgets/`, click "Create Budget"
   - Enter name "August 2026", start_date=2026-08-01, end_date=2026-08-31
   - Submit → redirected to detail or edit view
   - Add allocations: Groceries 1200, Transport 600
   - Save → see allocations listed

2. **Overlap validation**:
   - Try creating another budget "Mid-August" with start_date=2026-08-15, end_date=2026-09-15
   - Expect validation error "Budget dates overlap with existing budget"

3. **Comparison display**:
   - Upload transactions within August 2026 (Groceries: 1000, Transport: 700)
   - View budget detail → table shows:
     - Groceries: Budgeted 1200 | Actual 1000 | Difference 200 | Green badge
     - Transport: Budgeted 600 | Actual 700 | Difference -100 | Red badge
   - List view card shows: Total Budgeted 1800 | Total Actual 1700 | Difference 100

4. **Edge cases**:
   - Create budget with zero allocation for a category → status='under'
   - Create budget without allocations → detail view shows "No allocations yet"
   - Delete a category with allocations → allocations removed, budget totals recalculated

## Performance Considerations

- Budget list view performs one comparison query per budget (N+1 concern if many budgets). Optimize by prefetching allocations and batching transaction summary queries if user has >10 budgets.
- Date overlap validation queries existing budgets on every save. Index on `(user, start_date)` mitigates this.
- Comparison logic joins budget allocations with transaction summary (both already filtered by user and date range). Expected to be fast for typical dataset (<50 categories, <500 transactions per month).

## Migration Notes

- No existing data to migrate (new feature).
- Budget model includes date overlap validation in `clean()` — cannot be enforced at DB level with standard constraints (requires complex exclusion constraint in PostgreSQL, not portable to SQLite). Current approach: validate in model, accept risk of race condition during concurrent creates (low probability for single-user MVP).

## References

- Related PRD: `context/foundation/prd.md` — FR requirements mention budget cycles as future enhancement
- Similar implementation pattern: `categories/` app — CRUD views, LoginRequiredMixin, user filtering
- Date range forms: `transactions/forms.py:57-99` (`DashboardDateRangeForm`)
- Summary aggregation: `transactions/summary.py:13-51` (`get_user_category_summary()`)
- Template patterns: `templates/dashboard.html` (date pickers, summary table), `templates/categories/category_list.html` (card-based list)

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Budget Models & Migrations

#### Automated

- [x] 1.1 Migration applies cleanly
- [x] 1.2 Models importable
- [x] 1.3 Type checking passes
- [x] 1.4 Linting passes

#### Manual

- [x] 1.5 Budget creation and overlap validation verified

### Phase 2: Budget Forms & Helper Logic

#### Automated

- [ ] 2.1 Forms importable
- [ ] 2.2 Helper function unit tests pass
- [ ] 2.3 Type checking passes
- [ ] 2.4 Linting passes
- [ ] 2.5 Unit tests pass

#### Manual

- [ ] 2.6 Form validation and helper function behavior verified

### Phase 3: Budget CRUD Views & URL Routing

#### Automated

- [ ] 3.1 URL resolution works
- [ ] 3.2 Views importable
- [ ] 3.3 Type checking passes
- [ ] 3.4 Linting passes
- [ ] 3.5 Integration tests pass

#### Manual

- [ ] 3.6 CRUD operations work end-to-end

### Phase 4: Budget Templates & UI

#### Automated

- [ ] 4.1 Templates render without errors
- [ ] 4.2 Linting passes
- [ ] 4.3 Type checking passes

#### Manual

- [ ] 4.4 UI renders correctly with date pickers and color badges

### Phase 5: Testing & Edge Case Handling

#### Automated

- [ ] 5.1 All tests pass
- [ ] 5.2 Type checking passes
- [ ] 5.3 Linting passes

#### Manual

- [ ] 5.4 Edge cases verified manually
