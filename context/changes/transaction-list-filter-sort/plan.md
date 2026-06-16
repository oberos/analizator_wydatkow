# Transaction List Filtering & Sorting Implementation Plan

## Overview

Add filtering by category and sorting by Date/Amount to the transaction list. Users can filter to a single category (or "All"), sort ascending/descending on Date or Amount, and navigate paginated results. Filter and sort state persists in URL query parameters (e.g., `?category=Food&sort_by=date&sort_order=desc&page=2`), enabling shareable links and browser back/forward behavior.

## Current State Analysis

**Existing transaction list** (`transactions/transaction_list.html` + `TransactionListView`):
- Template displays Date, Merchant, Description, Amount, Category columns in a Bootstrap table
- Backend enforces `.filter(user=self.request.user)` for data isolation
- Category dropdown for inline editing (already wired)
- No filtering, sorting, or pagination controls exist
- TransactionListView is a standard Django `ListView` (no custom query logic)

**Roadmap context:**
- S-05 depends on S-02 (CSV import, ✓ done) and S-03 (category correction, ✓ done)
- S-04 (date-range dashboard, ✓ done) showed the transaction volume will grow into hundreds per user

**Constraints:**
- Single category filter at a time (not multi-select)
- URL params are the single source of truth (no localStorage)
- Auto-submit on filter/sort change (no "Apply" button)
- Pagination required to handle growth beyond MVP's initial 100-200 transactions per account

## Desired End State

When complete:
- User lands on `/transactions/` and sees filter dropdown, two sort buttons (Date ↕, Amount ↕), and "Clear Filters" button in the header next to the title
- Clicking the category dropdown shows "All Transactions" and a list of active categories; selecting one re-filters immediately, updating the URL to `?category=Food`
- Clicking "Date" or "Amount" toggles sort direction; first click sorts ascending, second descending, third clears sort (returns to default). URL updates to `?sort_by=date&sort_order=asc`
- Simultaneous filter + sort works: user selects "Food" category and sort by "Amount descending" → URL is `?category=Food&sort_by=amount&sort_order=desc`
- Empty result: "No transactions in Food category found." message with a "Clear Filters" link inline
- Pagination: if >50 results after filter/sort, show numbered page buttons (1, 2, 3...) at bottom; clicking page 2 → URL becomes `?category=Food&sort_by=date&sort_order=asc&page=2`
- Browser back/forward and bookmarked URLs restore the exact filter/sort/page state

### Verification Checklist

✓ All automated tests pass (lint, type-check, unit tests on modified components, integration tests for filtering/sorting)  
✓ Manual testing: filter + sort combinations work, pagination persists filter/sort, empty state displays correctly, URL params match browser state, back/forward works, bookmarked links restore state  
✓ Data isolation verified: no leakage between user accounts in filtered queries

## What We're NOT Doing

- **Multi-select filtering** — One category at a time to keep the UI and implementation simple
- **Merchant/Description sorting** — These are textual and less actionable than amount/date
- **Category sorting** — Category is already the primary filter; sorting by it is redundant
- **Search/full-text lookup** — Out of scope; would require a separate search feature
- **Custom date-range filtering** — The dashboard already handles date ranges; transaction list is focused on category and amount visibility
- **Client-side state (localStorage)** — URL params are the single source of truth for reproducibility and sharability
- **Inline sort indicators (up/down arrows on column headers)** — Sort buttons in the header are sufficient for clarity

## Implementation Approach

**Backend (Django):**
1. Update `TransactionListView.get_queryset()` to parse `category`, `sort_by`, and `sort_order` from request GET params
2. Chain `.filter(category__name=category)` if category param is present
3. Chain `.order_by(sort_field)` if sort_by param is present; prepend `-` for descending order
4. Use Django Paginator to split results into pages of 50 transactions
5. Pass filter/sort/page state to template context for form pre-population and pagination links

**Frontend (Django template + minimal JavaScript):**
1. Add category dropdown and sort buttons to the header (next to title)
2. Update form on dropdown change / button click
3. Auto-submit form to GET (not POST), which updates the URL
4. Pre-populate dropdown/buttons from URL params on page load
5. Display page navigation links at bottom; each link preserves filter/sort params

**Data Model:** No schema changes — filtering and sorting operate on existing querysets

## Critical Implementation Details

**URL parameter format**: Use lowercase, underscore-separated names for clarity and consistency. E.g., `?category=Food&sort_by=date&sort_order=asc&page=2`. Ignore unknown params (forward compatibility).

**Sort order semantics**: "asc" = 1→100 for amount, oldest→newest for date. "desc" = opposite. Clicking a sort button twice flips order; clicking a third time clears sort (no URL param for that column).

**Empty querysets**: After filtering, check `paginator.count == 0` to trigger the empty message. Display "(Category Name)" in the message so user knows what they filtered by.

**Pagination state after filter change**: When user changes filter or sort, reset to page 1 automatically (do not keep them on page 3 if the new filtered set has only 2 pages). This avoids "No results on page 5" confusion.

---

## Phase 1: Backend Filtering & Sorting in TransactionListView

### Overview

Update `TransactionListView` in `transactions/views.py` to:
- Parse `category`, `sort_by`, `sort_order` from request GET parameters
- Apply category filtering to the queryset (if param present)
- Apply sorting by date or amount (if param present)
- Pass filter/sort/pagination state to the template context

### Changes Required

#### 1. TransactionListView in transactions/views.py

**File**: `transactions/views.py`

**Intent**: Update `TransactionListView.get_queryset()` to parse and apply filter/sort params from the URL, and add a `get_context_data()` method to include filter/sort state and pagination in the template context.

**Contract**:
- `get_queryset()` returns a filtered, sorted QuerySet with `.filter(user=self.request.user)` always applied
- Parse `category` GET param: if present and non-empty, apply `.filter(category__name=category)`. Ignore if "all" or missing.
- Parse `sort_by` GET param: if "date", sort by `-transaction_date` or `transaction_date` depending on `sort_order`; if "amount", sort by `-amount` or `amount`
- Parse `sort_order` GET param: "asc" or "desc" (default: "asc"). Prepend `-` to field name for descending.
- Add `get_context_data()` to pass:
  - `selected_category`: the category name from URL param (or None for "All")
  - `sort_by`: current sort column ("date", "amount", or None)
  - `sort_order`: current sort direction ("asc" or "desc")
  - `page_obj`: Django paginator result
  - `paginator`: paginator instance (for template to check if count > 0)
  - `categories`: list of active category names (for dropdown options)
- Wire up Django `Paginator` and `EmptyPage` handling to split results into pages of 50 transactions

#### 2. Database Index (optional, but recommended)

**File**: `transactions/models.py` + migration

**Intent**: Add a database index on `(user, category, transaction_date)` to speed up filtered queries as transaction volume grows.

**Contract**:
- Create a migration that adds `db_index=True` to the composite index via `Meta.indexes`
- Test: migration applies cleanly with no data loss

### Success Criteria

#### Automated Verification

- Linting passes: `pdm run ruff check . --fix`
- Type checking passes: `pdm run basedpyright`
- All existing unit tests pass: `pdm run python manage.py test transactions.tests`
- New unit tests for filtering and sorting pass (see Phase 1 test additions below)
- Migration applies cleanly: `pdm run python manage.py makemigrations && pdm run python manage.py migrate`

#### Manual Verification

- Access `/transactions/?category=Food` and verify only Food transactions display
- Access `/transactions/?sort_by=date&sort_order=desc` and verify transactions are sorted by date, newest first
- Access `/transactions/?category=Food&sort_by=amount&sort_order=asc` and verify both filter and sort are applied
- Access `/transactions/?page=2` and verify pagination works (shows correct page)
- Access `/transactions/` with no params and verify default ordering (assume: by creation date, newest first)
- Verify cross-user isolation: log in as user B and confirm they do not see user A's filtered transactions

**Implementation Note**: After completing this phase, pause here for manual confirmation before proceeding to Phase 2. The backend logic must be correct before wiring it to the frontend.

---

## Phase 2: Frontend UI Controls & Form Wiring

### Overview

Add filter dropdown and sort buttons to the transaction list header, wire them to auto-submit form changes that update URL params, and pre-populate controls from URL params on page load.

### Changes Required

#### 1. transaction_list.html Template

**File**: `templates/transactions/transaction_list.html`

**Intent**: Add HTML for category filter dropdown, sort buttons (Date, Amount), and Clear Filters button. Wire them to a form that auto-submits on change.

**Contract**:
- Add a filter-controls section immediately below the page title (before the table)
- Include:
  - Category dropdown (`<select>` name="category") with "All Transactions" as first option, then list of category names
  - Sort buttons: "Date ↑↓" and "Amount ↑↓" (indicate current direction with CSS class, e.g., `.sort-asc`, `.sort-desc`)
  - "Clear Filters" button to reset all params
- Form method="GET", action="/transactions/", no submit button (auto-submit via JavaScript)
- Pre-populate dropdown from context variable `selected_category` (if None, show "All Transactions")
- Highlight active sort button with visual indicator (different color/icon for ascending vs descending)
- Hidden input fields for `sort_by`, `sort_order`, `page` (initialized from context)

#### 2. JavaScript for Auto-Submit (inline or separate)

**File**: `templates/transactions/transaction_list.html` (inline `<script>` or `static/js/transaction_list.js`)

**Intent**: Automatically submit the filter form when user changes the category dropdown or clicks a sort button, and reset to page 1 when filter/sort changes.

**Contract**:
- On category dropdown change: set `page` input to "1", submit form
- On sort button click: toggle `sort_order` (asc → desc → clear), update `sort_by` field, set `page` to "1", submit form
- If sort is already set and user clicks the same button, toggle the direction; if user clicks a different sort button, change to that column with "asc"
- Clear Filters button: reset category to "All", clear sort_by and sort_order, set page to "1", submit form

#### 3. Pagination Links in Template

**File**: `templates/transactions/transaction_list.html`

**Intent**: Display page navigation links (1, 2, 3...) at the bottom of the transaction table, each preserving filter and sort params.

**Contract**:
- Show page links only if `paginator.num_pages > 1`
- Link format: `/transactions/?category={selected_category}&sort_by={sort_by}&sort_order={sort_order}&page={page_num}`
- Highlight the current page (e.g., bold or different CSS class)
- Include "Previous" and "Next" links if applicable

### Success Criteria

#### Automated Verification

- Linting passes: `pdm run ruff check .`
- No JavaScript errors in browser console when page loads or form is submitted
- Template renders without syntax errors: `pdm run python manage.py runserver` and check `/transactions/` in browser

#### Manual Verification

- Filter dropdown changes immediately update the URL and table contents
- Sort buttons toggle direction (click once → asc, click twice → desc, visual indicator changes)
- Combining filter + sort works: select a category and click a sort button, URL reflects both
- Clear Filters button resets all controls and shows all transactions
- Pagination links preserve filter/sort params (clicking page 2 keeps the current filter/sort)
- Empty result state (covered in Phase 4) displays correctly with Clear Filters option

**Implementation Note**: After this phase, the UI should be fully functional. Proceed to Phase 3 to refine pagination and handling of edge cases.

---

## Phase 3: Pagination & State Persistence Refinement

### Overview

Ensure pagination behaves correctly when combined with filtering and sorting, handle edge cases (e.g., user navigates to page 5 then changes filter and only gets 1 page), and verify state persists correctly across page reloads and browser back/forward.

### Changes Required

#### 1. Pagination Reset Logic in TransactionListView.get_context_data()

**File**: `transactions/views.py`

**Intent**: When filter or sort params change, reset to page 1 automatically to avoid "empty page" errors.

**Contract**:
- After applying filter and sort, check the requested page number
- If requested page exceeds `paginator.num_pages`, silently reset to page 1
- This prevents "No results on page 5 after filtering" confusing behavior

#### 2. Test URL Param Combinations

**File**: `transactions/tests.py`

**Intent**: Add integration tests for common filter/sort/pagination combinations to ensure state persists correctly.

**Contract**:
- Test: `/transactions/?category=Food&sort_by=date&sort_order=desc&page=1` returns 50 Food transactions sorted by date descending
- Test: `/transactions/?page=5` without filter/sort works or resets gracefully if fewer than 5 pages
- Test: Changing from `/transactions/?category=Food&page=2` to `/transactions/?category=Groceries` resets to page 1
- Test: Back button in browser (simulated via GET request with same params) returns to previous state

### Success Criteria

#### Automated Verification

- Pagination/filter/sort integration tests pass: `pdm run python manage.py test transactions.tests.PaginationAndFilterSortTests`
- URL param handling and regressions pass: `pdm run python manage.py test transactions.tests`
- No regressions in existing transaction tests: `pdm run python manage.py test transactions.tests`

#### Manual Verification

- Filter to a category with 5+ pages, then click page 5 (or manually navigate to `?category=X&page=5`)
- Change the filter to a different category with only 2 pages; verify the page number resets to 1 and the new filtered results display
- Bookmark a URL like `?category=Food&sort_by=date&sort_order=desc&page=2`; close browser, reopen link, verify page restores the exact state

**Implementation Note**: Pagination logic is typically straightforward in Django; this phase is mainly about testing edge cases. After manual verification, proceed to Phase 4 for empty state messaging and final polish.

---

## Phase 4: Empty State, Polish & Final Integration

### Overview

Add contextual empty-result messaging, finalize form controls and styling, ensure responsive design, and run full end-to-end testing to verify all features work together.

### Changes Required

#### 1. Empty Result Message in Template

**File**: `templates/transactions/transaction_list.html`

**Intent**: Display a helpful message when a filter returns zero transactions, with an option to clear filters.

**Contract**:
- Check `paginator.count == 0` in template
- If true, display: "No transactions found in [Category Name] category." (or "No transactions found." if no filter applied)
- Include an inline "Clear Filters" link that resets the form and reloads
- Position the message where the transaction table would normally appear
- Use Bootstrap alert styling (e.g., `.alert .alert-info`)

#### 2. Responsive Design & Styling

**File**: `templates/transactions/transaction_list.html` + CSS

**Intent**: Ensure filter controls and pagination links adapt to mobile screens (tablets, phones).

**Contract**:
- Filter dropdown and sort buttons stack vertically on screens < 768px
- Pagination links wrap and remain clickable on small screens
- Sort buttons include accessible labels (e.g., `title="Sort by date, currently ascending"`)
- Keyboard navigation: Tab through controls, Enter to submit, Escape to clear (optional but nice-to-have)

#### 3. "All Categories" Dropdown Entry

**File**: `transactions/views.py` (context data for categories list)

**Intent**: Ensure the category list in the dropdown explicitly shows "All Transactions" as the first entry so users have a clear way to reset the category filter.

**Contract**:
- In `get_context_data()`, prepend a special entry (e.g., `{"name": "All", "label": "All Transactions"}`) to the categories list
- Template option: `<option value="">All Transactions</option>`
- When value is empty, the filter param is omitted from the URL (or explicitly stripped in JavaScript)

#### 4. Accessibility & Keyboard Navigation

**File**: `templates/transactions/transaction_list.html`

**Intent**: Ensure form controls are keyboard accessible and screen-reader friendly.

**Contract**:
- All buttons and dropdowns have `aria-label` attributes where text alone might be unclear
- Sort buttons indicate current direction: e.g., `aria-label="Sort by date, currently descending"`
- Links and buttons have sufficient color contrast (WCAG AA minimum)
- Tab order is logical (category → Date sort → Amount sort → Clear Filters)

### Success Criteria

#### Automated Verification

- Linting and type checking pass: `pdm run ruff check . && pdm run basedpyright`
- All tests pass: `pdm run python manage.py test transactions.tests`
- Template renders without errors: `pdm run python manage.py runserver`
- Accessibility check: use browser DevTools or axe-core to verify no critical violations

#### Manual Verification

- Filter to a category with no transactions; verify empty message displays with category name
- Clear Filters link works and shows all transactions again
- Responsive design: view on mobile (narrow browser window or actual phone); controls and pagination remain usable
- Keyboard navigation: Tab through all controls without using mouse; all controls are reachable and functional
- Sort buttons show visual indicator (up/down arrow or color change) for current direction
- Pagination links work and preserve filter/sort state
- Full end-to-end scenario: log in, import transactions (or use existing), filter by category, sort by amount, navigate to page 2, bookmark the URL, close browser, reopen bookmark → verify state is restored

**Implementation Note**: This is the final phase. After all manual checks pass, the feature is complete and ready for review or deployment.

---

## Testing Strategy

### Unit Tests

- **Category filtering**: Test that `.filter(category__name=category)` returns only matching transactions
- **Sorting logic**: Test that `order_by("transaction_date")` and `order_by("-amount")` sort correctly
- **URL param parsing**: Test that malformed or missing params are handled gracefully (defaults to no filter, no sort)
- **Cross-user isolation**: Test that filters do not leak between users

### Integration Tests

- **Filter + Sort + Pagination**: Make a GET request with all three params; verify response includes correct transactions in correct order on correct page
- **Empty results**: Filter to a category with no matching transactions; verify empty message displays
- **Page navigation**: Request page 2 of a paginated set; verify correct page displays and pagination links are correct
- **State persistence**: Request `/transactions/?category=X&sort_by=Y&page=2`; verify URL params appear unchanged in response links (for back/forward test)

### Manual Testing Steps

1. **Filter scenario**: Log in as a test user, navigate to `/transactions/`, select a category from the dropdown, verify only those transactions display, verify URL updated to include `?category=X`
2. **Sort scenario**: Click "Date" sort button, verify transactions sorted by date ascending, URL shows `?sort_by=date&sort_order=asc`; click "Date" again, verify descending, URL shows `?sort_order=desc`
3. **Combined scenario**: Select a category, sort by amount descending, navigate to page 2; verify all three params in URL and correct transactions on page
4. **Empty state**: Select a category with no transactions (or add a test category with no transactions); verify empty message with category name and Clear Filters link
5. **Pagination edge case**: Filter to a set that has 5 pages, navigate to page 5, then change filter to a set with 2 pages; verify auto-reset to page 1 or graceful handling
6. **Bookmarking**: Construct a complex URL like `?category=Food&sort_by=date&sort_order=desc&page=2`; bookmark it, close browser, reopen bookmark, verify page restores exact state
7. **Browser back/forward**: Navigate to filtered view, click through pages, use back button, verify state is restored

## Performance Considerations

- **Query optimization**: The database index on `(user, category, transaction_date)` from Phase 1 will significantly speed up filtered and sorted queries, especially as transaction volume grows
- **Pagination**: Limit to 50 transactions per page to avoid large response bodies and DOM rendering delays
- **URL param validation**: Sanitize category names and sort params to prevent injection attacks (Django's ORM parameterization handles this, but validate param names)

## Migration Notes

- **Schema migration**: Phase 1 adds a database index; this is a safe, non-blocking change that can be deployed independently
- **Backward compatibility**: URLs without filter/sort params still work (defaults to "All Transactions" unsorted)
- **No data migration needed**: Filtering and sorting operate on existing transaction records; no fields are added or changed

## References

- PRD requirements: `context/foundation/prd.md` (FR-013: filter by category, FR-014: sort by column)
- Roadmap: `context/foundation/roadmap.md` (S-05, depends on S-02, S-03, S-04)
- Current transaction list template: `templates/transactions/transaction_list.html`
- Current view logic: `transactions/views.py` (TransactionListView)
- Django QuerySet filtering: [Django ORM Filtering](https://docs.djangoproject.com/en/stable/topics/db/models/queries/)
- Django Paginator: [Django Pagination](https://docs.djangoproject.com/en/stable/topics/pagination/)

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Backend Filtering & Sorting in TransactionListView

#### Automated

- [x] 1.1 Update TransactionListView.get_queryset() to parse and apply filter/sort params — fe44e36
- [x] 1.2 Add get_context_data() to pass filter/sort state and pagination to template — fe44e36
- [x] 1.3 Add database index on (user, category, transaction_date) and create migration — fe44e36
- [x] 1.4 Linting and type checking pass — fe44e36
- [x] 1.5 All unit and integration tests pass — fe44e36

#### Manual

- [x] 1.6 Verify filtering works: `/transactions/?category=Food` shows only Food transactions — fe44e36
- [x] 1.7 Verify sorting works: `/transactions/?sort_by=date&sort_order=desc` sorts by date descending — fe44e36
- [x] 1.8 Verify combined filter + sort: `/transactions/?category=Food&sort_by=amount&sort_order=asc` works — fe44e36
- [x] 1.9 Verify pagination param works: `/transactions/?page=2` displays page 2 — fe44e36
- [x] 1.10 Verify default state (no params) displays all transactions — fe44e36
- [x] 1.11 Verify cross-user isolation: different users don't see each other's filtered results — fe44e36

### Phase 2: Frontend UI Controls & Form Wiring

#### Automated

- [x] 2.1 Update transaction_list.html with category dropdown, sort buttons, Clear Filters button
- [x] 2.2 Add JavaScript to auto-submit form on dropdown change or button click
- [x] 2.3 Implement pagination links that preserve filter/sort params
- [x] 2.4 Pre-populate controls from URL params on page load
- [x] 2.5 Linting and template validation pass

#### Manual

- [x] 2.6 Verify filter dropdown auto-submits and updates URL on category change
- [x] 2.7 Verify sort buttons toggle direction and update URL
- [x] 2.8 Verify Clear Filters button resets all controls
- [x] 2.9 Verify pagination links work and preserve filter/sort state
- [x] 2.10 Verify no JavaScript errors in browser console

### Phase 3: Pagination & State Persistence Refinement

#### Automated

- [x] 3.1 Add pagination reset logic to handle edge cases (page > num_pages) — a279bbc
- [x] 3.2 Add integration tests for filter/sort/pagination combinations — a279bbc
- [x] 3.3 Test URL param combinations and state persistence — a279bbc
- [x] 3.4 All tests pass — a279bbc

#### Manual

- [x] 3.5 Verify page reset on filter change (go to page 5, change filter, auto-reset to page 1) — a279bbc
- [x] 3.6 Verify bookmarking a complex URL restores exact state — a279bbc
- [x] 3.7 Verify browser back/forward navigation preserves state — a279bbc

### Phase 4: Empty State, Polish & Final Integration

#### Automated

- [x] 4.1 Add empty result message to template — 03e95ae
- [x] 4.2 Ensure "All Categories" entry in category dropdown — 03e95ae
- [x] 4.3 Add accessibility attributes (aria-labels, color contrast checks) — 03e95ae
- [x] 4.4 Implement responsive design for mobile screens — 03e95ae
- [x] 4.5 Linting and accessibility checks pass — 03e95ae
- [x] 4.6 All tests pass (including accessibility) — 03e95ae

#### Manual

- [x] 4.7 Verify empty result message displays with category name when filter returns no results — 03e95ae
- [x] 4.8 Verify Clear Filters link in empty message works — 03e95ae
- [x] 4.9 Verify responsive design on mobile (narrow browser, actual phone) — 03e95ae
- [x] 4.10 Verify keyboard navigation works (Tab through all controls) — 03e95ae
- [x] 4.11 Verify sort button visual indicators (up/down arrow) are clear — 03e95ae
- [x] 4.12 Full end-to-end scenario: import data, filter, sort, paginate, bookmark, close/reopen browser, verify state restored — 03e95ae
