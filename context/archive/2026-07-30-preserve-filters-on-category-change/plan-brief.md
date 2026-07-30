# Preserve Filters on Category Change — Plan Brief

> Full plan: `context/changes/preserve-filters-on-category-change/plan.md`

## What & Why

Fix transaction list redirect after category change to preserve current filter/sort/page state. Currently, changing a category resets user to page 1 with no filters — this breaks UX flow and forces manual re-filtering.

## Starting Point

`TransactionSetCategoryView.post()` at line 206 in `transactions/views.py` returns `redirect("transactions:list")` — a simple name-based redirect that loses all query params. Transaction list view already extracts and applies filter/sort state from URL query params (`category`, `sort_by`, `sort_order`, `page`), and pagination links preserve state via template-level `|urlencode` filter. Only the category change POST redirect is broken.

## Desired End State

After changing transaction category from list page, user sees same filtered/sorted view at same page number. Changed transaction visible if current filter still matches. Redirect URL contains all preserved query params. Unit test verifies param preservation.

## Key Decisions Made

| Decision                       | Choice                                      | Why (1 sentence)                                                                                 | Source |
| ------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------ |
| Page preservation              | Stay if valid, else page 1                  | Existing pagination logic already handles invalid pages via EmptyPage exception                  | Plan   |
| Filter interaction             | Keep current filter                         | User expects to stay in current context — changed transaction visible if filter still matches    | Plan   |
| State to preserve              | category, sort_by, sort_order, page         | These are all query params currently supported by transaction list view                          | Plan   |
| URL building approach          | Extract from request.GET + urlencode        | Matches existing codebase pattern (template uses urlencode, tests use f-string + reverse)        | Plan   |
| Testing level                  | Unit test only                              | Redirect is pure URL building logic — no need for integration test overhead                      | Plan   |
| Default value handling         | Exclude asc and page=1 from URL             | Keep URLs clean by omitting default values that view will apply anyway                           | Plan   |

## Scope

**In scope:**
- Modify redirect in `TransactionSetCategoryView.post()` to preserve query params
- Add unit test verifying redirect URL param preservation
- Extract category/sort_by/sort_order/page from `request.GET`

**Out of scope:**
- Filter logic changes or validation
- Template rendering modifications
- JavaScript state management
- Scroll position restoration
- Changing category filter UI behavior

## Architecture / Approach

Single-file change in `transactions/views.py`. Extract query params from `request.GET`, build dict of non-empty/non-default values, use `urllib.parse.urlencode()` to build query string, append to reversed URL name. Rely on existing `TransactionListView.paginate_queryset()` to handle invalid page numbers (already does via EmptyPage exception).

## Phases at a Glance

| Phase     | What it delivers                                   | Key risk                                                       |
| --------- | -------------------------------------------------- | -------------------------------------------------------------- |
| 1. Redirect logic | Updated POST handler preserving query params | Query string encoding edge cases (special chars in category) |
| 2. Unit test | Test verifying redirect URL param preservation    | Test assertion needs to handle query param order variation     |

**Prerequisites:** None — pure redirect logic change, no dependencies.
**Estimated effort:** ~1 session, 2 phases

## Open Risks & Assumptions

- **Assumption**: `TransactionListView.paginate_queryset()` will continue to handle invalid pages via EmptyPage exception — no changes to that logic expected.
- **Assumption**: Category names with special characters (spaces, Unicode) will be correctly handled by `urlencode()`.
- **Risk**: Query param order may vary with `urlencode()` — test assertion must check param presence, not full URL string equality.

## Success Criteria (Summary)

- User changes category from filtered/sorted list page — redirect preserves all state (category filter, sort column/order, page number)
- Unit test passes verifying redirect URL contains all query params
- Manual test: change category from page 2 with filters active — stay on page 2 with filters intact
