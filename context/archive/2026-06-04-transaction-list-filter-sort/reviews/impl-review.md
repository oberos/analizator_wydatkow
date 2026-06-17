<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Transaction List Filtering & Sorting

- **Plan**: `context/changes/transaction-list-filter-sort/plan.md`
- **Scope**: Phase 1-4 of 4
- **Date**: 2026-06-16
- **Verdict**: NEEDS ATTENTION
- **Findings**: 0 critical, 5 warnings, 1 observation

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | WARNING |
| Scope Discipline | PASS |
| Safety & Quality | WARNING |
| Architecture | PASS |
| Pattern Consistency | WARNING |
| Success Criteria | WARNING |

## Findings

### F1 — `category=all` behavior drifts from plan

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: transactions/views.py:37-40
- **Detail**: Plan says `"all"` should be ignored for category filter, but logic filters any non-empty value. User confirmed this is acceptable in practice because UI sends empty value for "all".
- **Fix**: Treat `"all"` (case-insensitive) as empty before applying category filter.
- **Decision**: ACCEPTED (user marked as false-positive)

### F2 — Clear Filters keeps a sort-order value instead of fully clearing sort state

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: templates/transactions/transaction_list.html:366-368
- **Detail**: Plan contract says Clear Filters clears `sort_by` and `sort_order`; JS resets `sort_order` to `"asc"`.
- **Fix**: Set `sort_order` to empty on clear and normalize server-side when needed.
- **Decision**: SKIPPED

### F3 — Phase-3 test contract not fully represented in automated tests

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Plan Adherence
- **Location**: transactions/tests.py
- **Detail**: Added explicit tests for filter-change reset and same-params state consistency.
- **Fix**: Add targeted integration tests.
- **Decision**: FIXED

### F4 — Sort state used for query and UI could diverge on invalid GET values

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: transactions/views.py
- **Detail**: Added shared normalization helper and reused normalized values in queryset + context.
- **Fix**: Normalize `sort_by/sort_order` once and reuse.
- **Decision**: FIXED

### F5 — Two plan-listed verification commands referenced non-existent test classes

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Success Criteria
- **Location**: context/changes/transaction-list-filter-sort/plan.md
- **Detail**: Phase 3 automated verification commands now reference existing tests.
- **Fix**: Update commands to `PaginationAndFilterSortTests` and `transactions.tests`.
- **Decision**: FIXED

### F6 — Pagination rendered full page range

- **Severity**: 🔍 OBSERVATION
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Pattern Consistency
- **Location**: templates/transactions/transaction_list.html, transactions/views.py
- **Detail**: Replaced full page range with elided page range from paginator.
- **Fix**: Use `get_elided_page_range()` and render ellipsis tokens.
- **Decision**: FIXED
