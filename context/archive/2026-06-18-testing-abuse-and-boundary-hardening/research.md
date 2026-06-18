---
date: 2026-06-18T07:34:57.8746182+02:00
researcher: Copilot CLI (GPT-5.3-Codex)
git_commit: 926e4cb79faa654e8cab838f36fa936f05365401
branch: master
repository: oberos/analizator_wydatkow
topic: "testing-abuse-and-boundary-hardening"
tags: [research, codebase, security, integration-tests, boundaries, reporting]
status: complete
last_updated: 2026-06-18
last_updated_by: Copilot CLI (GPT-5.3-Codex)
---

# Research: testing-abuse-and-boundary-hardening

**Date**: 2026-06-18T07:34:57.8746182+02:00  
**Researcher**: Copilot CLI (GPT-5.3-Codex)  
**Git Commit**: 926e4cb79faa654e8cab838f36fa936f05365401  
**Branch**: master  
**Repository**: oberos/analizator_wydatkow

## Research Question

Rollout Phase 3 for abuse and boundary hardening from `context/foundation/test-plan.md`, focused on risks:
- #5 IDOR-style foreign-resource read/update abuse with valid session.
- #6 Paycheck-cycle/date-boundary correctness.
- #4 Summary totals correctness under filter/sort interactions and income semantics.

## Summary

Ownership protections are already present on key category/transaction paths and partially covered by integration negatives, but a few foreign-resource request permutations remain untested. Date filtering is implemented as inclusive `start <= date <= end` over `DateField` data, with no paycheck-specific cycle algorithm currently present; boundary behavior is covered in part but still misses partial-bound and cycle-specific scenarios. Summary totals are implemented as net-per-category (expenses minus income), and dashboard summary uses only date-range inputs; filter/sort controls in transaction list are separate, so Phase 3 should explicitly test summary invariance when such params are present and settle the plan-vs-code semantic tension ("exclude income" wording vs current net implementation).

## Detailed Findings

### Ownership / IDOR hardening (#5)

- Category edit/delete views scope object lookup by `user=self.request.user`, preventing foreign resource retrieval in CBVs ([categories/views.py:45-47](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/categories/views.py#L45-L47), [categories/views.py:56-57](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/categories/views.py#L56-L57)).
- Transaction list/query and category option sets are user-scoped, reducing foreign read leakage in UI paths ([transactions/views.py:49](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/views.py#L49), [transactions/views.py:54](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/views.py#L54), [transactions/forms.py:49](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/forms.py#L49)).
- `set_category` transaction mutation fetches transaction with user scope and service-layer checks category ownership again ([transactions/views.py:184-187](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/views.py#L184-L187), [transactions/refinement.py:52-56](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/refinement.py#L52-L56)).
- Model-level guard prevents cross-user category assignment as an invariant backstop ([transactions/models.py:48-50](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/models.py#L48-L50), [transactions/models.py:91-94](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/models.py#L91-L94)).
- Existing negatives already cover core abuse paths, including foreign category edit/delete and foreign transaction category-change attempts ([categories/tests.py:31-42](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/categories/tests.py#L31-L42), [transactions/tests.py:370-416](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/tests.py#L370-L416)).
- Gap for Phase 3 security negatives: explicit POST foreign category edit, explicit GET foreign delete confirmation view, and category-list visibility assertions in categories app tests.

### Date boundaries / paycheck-cycle semantics (#6)

- Dashboard resolves date range from request/form and delegates to summary; default is `today-30` through `today` ([accounts/views.py:27-31](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/views.py#L27-L31), [accounts/views.py:77-97](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/views.py#L77-L97)).
- Summary applies inclusive lower/upper date bounds via `date__gte` and `date__lte` ([transactions/summary.py:20-24](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/summary.py#L20-L24)).
- Invalid `start > end` is rejected in form cleaning and view falls back to default range ([transactions/forms.py:80-87](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/forms.py#L80-L87), [accounts/views.py:86-91](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/views.py#L86-L91)).
- Transaction date input is normalized to `date` at parser/model boundaries, reducing timezone drift surfaces for persisted values ([transactions/csv_parser.py:67-83](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/csv_parser.py#L67-L83), [transactions/csv_parser.py:161-166](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/csv_parser.py#L161-L166), [transactions/models.py:19-20](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/models.py#L19-L20)).
- Existing tests assert inclusive/exclusive edge behavior around start/end boundaries, but no paycheck-cycle-specific algorithm tests are present ([accounts/tests.py:226-255](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/tests.py#L226-L255), [transactions/tests.py:709-747](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/tests.py#L709-L747)).

### Summary totals under filtering/sorting (#4)

- Dashboard summary is built from `get_user_category_summary(user, start_date, end_date)` and rendered from `category_summary` context ([accounts/views.py:72-108](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/views.py#L72-L108)).
- Aggregation semantics are net-per-category: expenses add positively, income offsets totals ([transactions/summary.py:20-47](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/summary.py#L20-L47)).
- Chart intentionally excludes non-positive totals, while table remains full summary source ([accounts/views.py:54-68](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/views.py#L54-L68), [templates/dashboard.html:89-116](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/templates/dashboard.html#L89-L116)).
- Transaction list filtering/sorting (`category`, `sort_by`, `sort_order`, `page`) is implemented on a separate endpoint path from dashboard summary ([transactions/views.py:34-62](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/views.py#L34-L62)).
- Coverage exists for net summary behavior and list filtering/sorting separately, but not for combined "active filter/sort params + dashboard totals invariant" regression checks ([accounts/tests.py:138-255](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/accounts/tests.py#L138-L255), [transactions/tests.py:847-999](https://github.com/oberos/analizator_wydatkow/blob/926e4cb79faa654e8cab838f36fa936f05365401/transactions/tests.py#L847-L999)).

## Code References

- `analizator_wydatkow/urls.py:27-29` - Route mounting for categories and transactions feature surfaces.
- `categories/views.py:45-47` - User-scoped category edit object lookup.
- `categories/views.py:56-57` - User-scoped category delete object lookup.
- `transactions/views.py:184-187` - User-scoped transaction lookup in set-category mutation.
- `transactions/refinement.py:52-56` - Ownership validation in category assignment service.
- `transactions/models.py:48-50,91-94` - Model-level ownership invariants.
- `accounts/views.py:27-31,77-97` - Default and request-derived date range behavior.
- `transactions/summary.py:20-24,20-47` - Inclusive date filtering and net summary aggregation.
- `transactions/forms.py:80-87` - Invalid range validation.
- `accounts/tests.py:226-255` - Integration assertions for date-boundary include/exclude behavior.
- `transactions/tests.py:709-747` - Summary-layer date-range boundary assertions.
- `accounts/tests.py:138-255` - Dashboard summary/income-net behavior.
- `transactions/tests.py:847-999` - Transaction list filter/sort behavior and isolation.

## Architecture Insights

- Ownership safety is layered: view-level user-scoped lookup + service guard + model invariant.
- Summary/reporting logic is centralized and deterministic, but semantics are "net" rather than literal "expense-only exclusion."
- Date handling is plain-date based and inclusive at both ends; Phase 3 risk is mainly boundary contract drift and missing paycheck-specific tests, not timezone math in datetime arithmetic.
- Filter/sort UI state currently belongs to transaction list flow, so summary correctness regressions are likely to come from accidental coupling changes rather than existing intended design.

## Historical Context (from prior changes)

- `context/foundation/test-plan.md:45-47,56-58,68-71` - Phase 3 explicitly targets #5, #6, and #4.
- `context/archive/2026-06-03-testing-critical-path-data-correctness/research.md:26-34,86-90,108-109` - Prior baseline covered ownership isolation and summary behavior framing.
- `context/archive/2026-06-03-testing-critical-path-data-correctness/plan.md:54-61,128-143,285-293` - Historical completion of ownership negatives and summary integrity checks.
- `context/archive/2026-06-04-date-range-summary-reporting/plan.md:77,87,107,165,255` - Prior decision and checks for inclusive date boundaries.
- `context/archive/2026-06-04-transaction-list-filter-sort/plan.md:102-105,142,353,414` - Filter/sort history useful for risk #4 interaction analysis.

## Related Research

- `context/archive/2026-06-03-testing-critical-path-data-correctness/research.md`
- `context/archive/2026-06-04-date-range-summary-reporting/research.md`
- `context/archive/2026-06-04-transaction-list-filter-sort/research.md`

## Open Questions

- Should risk #4 intent be enforced as "exclude income entirely" or retain the currently shipped "net per category" contract?
- Should Phase 3 include explicit paycheck-cycle domain logic tests now, or only boundary-hardening around current generic range semantics?

