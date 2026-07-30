# Preserve Filters on Category Change Implementation Plan

## Overview

Fix redirect after transaction category change to preserve current filter/sort/page state. Currently, changing a transaction's category redirects to base transaction list URL, resetting user to page 1 with no filters. After this fix, user stays in their current context with all filters intact.

## Current State Analysis

Transaction list view (`transactions/views.py:20-93`) extracts and applies filter/sort state from query params:
- `category` — filter by category name (line 29)
- `sort_by` — "date" or "amount" (line 30)
- `sort_order` — "asc" or "desc" (line 31)
- `page` — pagination page number (line 63)

Category change handled by `TransactionSetCategoryView.post()` (`transactions/views.py:190-206`):
- Validates transaction ownership (lines 193-196)
- Applies category correction via `apply_category_correction()` (lines 199-204)
- **Problem (line 206)**: `return redirect("transactions:list")` — loses all query params

Pagination links and filter UI preserve state via template-level query string building with `|urlencode` filter (`transaction_list.html:179-198`).

### Key Discoveries:

- Redirect pattern: `redirect(reverse("transactions:list"))` — simple name-based redirect without query string (line 206)
- Template pattern: `?category={{ selected_category|urlencode }}&sort_by={{ sort_by|urlencode }}&...` — preserves state in links (lines 179-198)
- Test pattern: `f"{reverse('login')}?next={reverse('dashboard')}"` — f-string + `reverse()` for query params in tests (`accounts/tests.py:3`, `categories/tests.py:6-12`)
- Page validation: `TransactionListView.paginate_queryset()` already handles invalid pages by resetting to page 1 via `EmptyPage` exception (lines 61-70)

## Desired End State

After changing transaction category:
- User redirected to transaction list with current filters preserved
- Filter state maintained: `category`, `sort_by`, `sort_order`, `page`
- Changed transaction visible if current filter still matches
- Invalid page number auto-corrects to page 1 (existing pagination logic handles this)
- Unit test verifies redirect URL contains all query params

## What We're NOT Doing

- Not changing filter logic or validation
- Not modifying template rendering or pagination UI
- Not adding JavaScript state management
- Not implementing scroll position restoration
- Not changing how category filter UI works (keep current filter even if changed transaction no longer matches)

## Implementation Approach

Extract query params from `request.GET` in `TransactionSetCategoryView.post()`, build redirect URL with `urllib.parse.urlencode()`, and pass preserved params. Simplest implementation: build dict of non-empty/non-default params, urlencode, append to reversed URL name.

Rely on existing `TransactionListView.paginate_queryset()` to handle invalid page numbers — no need to validate page bounds in redirect logic.

## Phase 1: Update Redirect Logic

### Overview

Modify `TransactionSetCategoryView.post()` to extract current filter/sort/page state from `request.GET` and build redirect URL preserving all params.

### Changes Required:

#### 1. Import `urlencode` Utility

**File**: `transactions/views.py`

**Intent**: Add `urllib.parse.urlencode` import at top of file to support query string building.

**Contract**: Import statement at file top (existing imports at lines 1-14).

#### 2. Build Redirect URL with Preserved Query Params

**File**: `transactions/views.py`

**Intent**: Replace line 206 simple redirect with query-param-preserving redirect. Extract `category`, `sort_by`, `sort_order`, `page` from `request.GET`, build dict of non-empty/non-default values, urlencode, append to reversed URL.

**Contract**: Replace:
```python
return redirect("transactions:list")
```

With query-string-building logic that:
1. Extracts params from `request.GET.get("category")`, `.get("sort_by")`, `.get("sort_order")`, `.get("page")`
2. Filters out empty strings and default values ("asc" for sort_order, "1" for page)
3. Builds params dict with non-empty values only
4. Uses `urlencode(params)` to build query string
5. Returns `redirect(f"{reverse('transactions:list')}?{query_string}")` if params exist, else `redirect("transactions:list")`

Skip including params with default values to keep URLs clean.

### Success Criteria:

#### Automated Verification:

- Unit test passes: `pdm run python manage.py test transactions.tests.TestTransactionSetCategoryView.test_set_category_preserves_filters`
- Linting passes: `pdm run ruff check transactions/views.py`
- Type checking passes: `pdm run basedpyright transactions/views.py`

#### Manual Verification:

- Navigate to transaction list page 2 with category filter and sort
- Change one transaction's category via dropdown
- Verify redirect preserves: category filter, sort column, sort order, page number
- Changed transaction visible in list if filter still matches
- Change category from page 10 (invalid page) — verify redirect to page 1 with filters preserved

**Implementation Note**: After completing automated verification, pause for manual confirmation before Phase 2.

---

## Phase 2: Add Unit Test

### Overview

Add test verifying redirect URL contains all query params after category change POST.

### Changes Required:

#### 1. Add Test Method

**File**: `transactions/tests.py`

**Intent**: Add test method `test_set_category_preserves_filters` to `TestTransactionSetCategoryView` class. POST to set_category endpoint with query params in URL, assert redirect response contains all params.

**Contract**: New test method in existing test class:
- Setup: create user, login, create transaction + categories
- Action: POST to `reverse("transactions:set_category", args=[tx.pk]) + "?category=OldCat&sort_by=amount&sort_order=desc&page=2"` with new category
- Assert: `response.url` contains all query params: `category=OldCat&sort_by=amount&sort_order=desc&page=2`

Use `self.assertIn()` or regex to verify query params present in redirect URL (order may vary with urlencode).

### Success Criteria:

#### Automated Verification:

- New test passes: `pdm run python manage.py test transactions.tests.TestTransactionSetCategoryView.test_set_category_preserves_filters`
- All transaction tests pass: `pdm run python manage.py test transactions.tests`
- Linting passes: `pdm run ruff check transactions/tests.py`
- Type checking passes: `pdm run basedpyright transactions/tests.py`

#### Manual Verification:

- Review test code — verify it covers all four params (category, sort_by, sort_order, page)
- Run test in isolation — confirm it fails before Phase 1 implementation, passes after

**Implementation Note**: After completing automated verification, pause for manual confirmation.

---

## Testing Strategy

### Unit Tests:

- `test_set_category_preserves_filters` — verify redirect URL contains all query params
- Cover edge cases:
  - Empty query params (redirect to base URL)
  - Default values (sort_order=asc, page=1) — verify they're excluded from URL
  - Special characters in category name — verify urlencode handles them

### Manual Testing Steps:

1. Open transaction list with filters: `http://localhost:8000/transactions/?category=Groceries&sort_by=amount&sort_order=desc&page=2`
2. Change one transaction's category via dropdown
3. Verify redirect URL preserves all params
4. Verify changed transaction visibility matches current filter
5. Test with invalid page number (e.g., page=999) — verify redirect to page 1 with filters preserved
6. Test with no filters active — verify simple redirect to base URL

## Performance Considerations

Minimal impact — adds 4 `request.GET.get()` calls and one `urlencode()` call per category change POST. Existing pagination logic already handles page validation, no additional queries needed.

## Migration Notes

No data migration required — this is pure redirect logic change.

## References

- Current redirect: `transactions/views.py:206`
- Filter extraction pattern: `transactions/views.py:28-37`
- Pagination links template pattern: `templates/transactions/transaction_list.html:179-198`
- Existing page validation: `transactions/views.py:61-70` (EmptyPage exception handling)

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Update Redirect Logic

#### Automated

- [x] 1.1 Unit test passes: `pdm run python manage.py test transactions.tests.TestTransactionSetCategoryView.test_set_category_preserves_filters` — efc76ac
- [x] 1.2 Linting passes: `pdm run ruff check transactions/views.py` — efc76ac
- [x] 1.3 Type checking passes: `pdm run basedpyright transactions/views.py` — efc76ac

#### Manual

- [x] 1.4 Navigate to transaction list page 2 with category filter and sort, change transaction category, verify redirect preserves all state — efc76ac

### Phase 2: Add Unit Test

#### Automated

- [x] 2.1 New test passes: `pdm run python manage.py test transactions.tests.TestTransactionSetCategoryView.test_set_category_preserves_filters`
- [x] 2.2 All transaction tests pass: `pdm run python manage.py test transactions.tests`
- [x] 2.3 Linting passes: `pdm run ruff check transactions/tests.py`
- [x] 2.4 Type checking passes: `pdm run basedpyright transactions/tests.py`

#### Manual

- [x] 2.5 Review test code, verify it covers all four params (category, sort_by, sort_order, page)
