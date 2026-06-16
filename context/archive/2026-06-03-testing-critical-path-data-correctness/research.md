---
date: 2026-06-03T14:49:00.884+02:00
researcher: GitHub Copilot (GPT-5.3-Codex)
git_commit: a7894929b3e0d051746da3b7670026f9578b501d
branch: master
repository: oberos/analizator_wydatkow
topic: "testing-critical-path-data-correctness"
tags: [research, codebase, transactions, auth, csv-import, summary]
status: complete
last_updated: 2026-06-03
last_updated_by: GitHub Copilot (GPT-5.3-Codex)
---

# Research: testing-critical-path-data-correctness

**Date**: 2026-06-03T14:49:00.884+02:00  
**Researcher**: GitHub Copilot (GPT-5.3-Codex)  
**Git Commit**: a7894929b3e0d051746da3b7670026f9578b501d  
**Branch**: master  
**Repository**: oberos/analizator_wydatkow

## Research Question

Ground Phase 1 of the test rollout (`Critical-path data correctness`) for risks:

1. cross-account data exposure / ownership bypass,
2. CSV import integrity (silent drop/duplication),
3. summary correctness (income exclusion and user scoping).

## Summary

Critical-path protections are implemented in code and partially covered by tests. User isolation is consistently enforced in list/read/write paths via `user=request.user` scoping, plus explicit ownership checks in refinement service logic. CSV import intentionally skips duplicates through `bulk_create(..., ignore_conflicts=True)` and reports imported vs skipped counts; malformed rows fail the import via `CSVParseError`. Summary aggregation explicitly counts only expenses (`amount < 0`) and excludes positive income from totals, while still scoping all rows to a single user.

Primary gaps are test-coverage gaps (not obvious implementation holes): no direct URL-level tests for foreign category edit/delete access, and no integrity tests for malformed/mixed CSV edge cases (e.g., partial malformed rows, transaction-number edge collisions).

## Detailed Findings

### A. Ownership and isolation paths (Risk #1 / #5)

- Authenticated protection is applied at entry points via `LoginRequiredMixin` or `@login_required` (`transactions/views.py`, `categories/views.py`, `accounts/views.py`).  
  - https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/views.py#L20-L21  
  - https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/categories/views.py#L11-L12  
  - https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/accounts/views.py#L19-L21

- Transaction list/read/update/delete flows are user-scoped:
  - list queryset (`filter(user=self.request.user)`):  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/views.py#L27-L29
  - delete-all scoped to current user:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/views.py#L111-L114
  - set-category lookup scoped by `user + pk`:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/views.py#L121-L126

- Category CRUD ownership is enforced through user-scoped querysets in update/delete and user assignment on create:  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/categories/views.py#L30-L32  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/categories/views.py#L43-L45  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/categories/views.py#L54-L55

- Service-layer hard checks prevent cross-account correction/mapping misuse (`PermissionDenied` on foreign transaction/category):  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/refinement.py#L49-L52

### B. CSV import integrity path (Risk #2)

- CSV parser behavior is strict and fail-fast:
  - multi-encoding decode with explicit failure:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/csv_parser.py#L36-L47
  - header/footer detection and required-column validation:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/csv_parser.py#L49-L64  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/csv_parser.py#L223-L227
  - row filtering/parsing loop with parse errors propagated:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/csv_parser.py#L229-L240

- Upload orchestration:
  - parsed rows -> categorization -> bulk insert in transaction:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/views.py#L46-L100
  - duplicate handling is intentional (`ignore_conflicts=True`), with user-facing imported/skipped counts from before/after counts:  
    https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/views.py#L81-L95

- Database deduplication key includes `user` and transaction identity tuple (`unique_together`):  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/models.py#L29-L31

### C. Summary correctness path (Risk #4)

- Summary is generated from user-scoped transactions and grouped by category name with uncategorized fallback:
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/summary.py#L12-L16

- Expense-only total logic is explicit: only negative amounts are included (`When(amount__lt=0, then=Abs(F("amount")))`), positive amounts contribute `0`:  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/transactions/summary.py#L17-L23

- Dashboard uses this summary directly for authenticated users:  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/accounts/views.py#L19-L24

- Transactions list template currently provides rendering and category update forms, but no built-in filter/sort controls (important for future test assumptions):  
  https://github.com/oberos/analizator_wydatkow/blob/a7894929b3e0d051746da3b7670026f9578b501d/templates/transactions/transaction_list.html#L58-L107

## Code References

- `transactions/views.py:27-29` - User-scoped list queryset.
- `transactions/views.py:81-95` - Import counting + duplicate reporting.
- `transactions/views.py:123-126` - Foreign transaction denial at HTTP layer.
- `transactions/csv_parser.py:36-47` - Encoding fallback + parse error.
- `transactions/csv_parser.py:223-240` - Required columns + row parsing loop.
- `transactions/models.py:29-31` - Per-user deduplication constraint.
- `transactions/summary.py:12-30` - Category aggregation and income exclusion.
- `transactions/refinement.py:49-52` - Service-layer ownership enforcement.
- `categories/views.py:43-55` - User-scoped update/delete querysets.
- `transactions/forms.py:42-44` - User-scoped category choice queryset.
- `transactions/tests.py:116-132` - Duplicate skip behavior test.
- `transactions/tests.py:294-340` - Cross-user category/transaction rejection tests.
- `transactions/tests.py:395-494` - Summary grouping, scoping, and income exclusion tests.
- `accounts/tests.py:18-63` - Dashboard summary isolation and no foreign data rendering.

## Architecture Insights

- Ownership checks are layered:
  1. route auth gate (`LoginRequiredMixin` / `@login_required`),
  2. ORM user-scoped querysets in views/forms,
  3. service-level explicit ownership guards in `apply_category_correction`.

- Import integrity follows strict-parse + atomic-write semantics:
  - parse issues abort flow with user-facing parse errors,
  - duplicates are intentionally non-fatal and counted as skipped.

- Summary intentionally represents spending (outflows) only, not net flow:
  - positives (refund/income) are excluded from totals by design.

## Historical Context (from prior changes)

- `context/changes/csv-import-autocategorize/plan.md:5` - ING CSV import and duplicate-skip behavior were explicit design goals.
- `context/changes/csv-import-autocategorize/plan.md:37` - Re-upload duplicate scenario defined in earlier verification.
- `context/changes/category-refinement-summary/plan.md:21` - Cross-user isolation was an explicit acceptance condition for summary/refinement.
- `context/changes/category-refinement-summary/plan.md:49` - Summary correctness and isolation tests were planned as focused coverage.
- `context/changes/category-management/plan.md:38` - Earlier MVP phase intentionally deprioritized automated tests.

No historical `research.md` artifacts were found in `context/changes/**` or `context/archive/**`; this document becomes the first research baseline for this rollout change.

## Related Research

- None currently. This is the first research artifact for `testing-critical-path-data-correctness`.

## Open Questions

- Should duplicate handling remain silent-skip with messaging, or should there be stricter reporting at row-level granularity?
- Should summary `transaction_count` represent all rows or only expense rows, to match `total_amount` semantics?
- Do we want explicit HTTP tests for direct foreign-category edit/delete URL access as a mandatory regression guard in Phase 1?
