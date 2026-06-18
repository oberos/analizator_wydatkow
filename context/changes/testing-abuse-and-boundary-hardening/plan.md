# Abuse and boundary hardening (Phase 3) Implementation Plan

## Overview

Implement Phase 3 from `context/foundation/test-plan.md` by hardening integration/security-negative tests for ownership abuse (#5), date-boundary correctness (#6), and summary correctness under filter/sort context (#4).  
This plan intentionally strengthens existing behavior contracts without expanding feature scope.

## Current State Analysis

The codebase already enforces ownership in core paths and already tests many high-risk scenarios, but several explicit negative permutations and boundary/context combinations remain uncovered. Summary behavior is currently net-per-category (expenses minus income), and this plan preserves that shipped contract.

## Desired End State

A deterministic integration test floor exists for all Phase 3 target risks:
1. Authenticated foreign-resource abuse attempts are rejected according to current endpoint contracts and never mutate protected data.
2. Date boundaries are validated for inclusive range behavior plus partial-bound handling.
3. Dashboard summary totals remain correct and invariant when list-style filter/sort params are present.

Verification is complete when targeted suites pass per phase and the combined app-level trio passes at rollout close.

### Key Discoveries:

- Category edit/delete ownership relies on user-scoped queryset lookups (`categories/views.py:45-47`, `categories/views.py:56-57`).
- Transaction mutation path re-checks ownership in both view and service layers (`transactions/views.py:184-187`, `transactions/refinement.py:52-56`).
- Summary contract is net-per-category, not expense-only (`transactions/summary.py:33-40`, `accounts/tests.py:138-170`).
- Filter/sort parameters live on transaction list path, while dashboard summary uses date-range inputs (`transactions/views.py:34-62`, `accounts/views.py:77-97`).

## What We're NOT Doing

- Changing production authorization response semantics to force one global status code convention.
- Introducing new paycheck-cycle derivation logic or new domain feature behavior.
- Reworking summary business logic from net-per-category to expense-only.
- Adding e2e/Playwright coverage in this change.

## Implementation Approach

Extend existing Django integration test modules in-place (`categories/tests.py`, `transactions/tests.py`, `accounts/tests.py`) using established setup and assertion patterns.  
Prioritize regression-sensitive, high-signal negatives and boundary/context combinations explicitly mapped in research, then close with targeted and consolidated verification runs.

## Critical Implementation Details

### User experience spec

Foreign-resource rejection assertions must follow current endpoint-specific behavior (404 for queryset-scoped category URLs, redirect/no-mutation patterns for selected transaction mutation flows) instead of forcing a new unified status model in this change.

## Phase 1: Ownership abuse negative-surface hardening

### Overview

Close remaining IDOR-style negative permutations for authenticated users and guarantee non-mutation on foreign-resource attempts.

### Changes Required:

#### 1. Category ownership URL negatives

**File**: `categories/tests.py`

**Intent**: Extend ownership URL tests to cover missing foreign-resource request permutations on existing category routes.

**Contract**: `CategoryOwnershipURLTests` fully covers foreign read/update paths for authenticated users, including explicit foreign POST-to-edit and GET-to-delete-confirm assertions with denial semantics matching current views.

#### 2. Transaction ownership mutation safeguards

**File**: `transactions/tests.py`

**Intent**: Reinforce transaction/category foreign ownership mutation protection with explicit no-mutation guarantees.

**Contract**: `TransactionCategoryCorrectionTests` includes explicit assertions that foreign-resource attempts do not alter target transaction/category state and preserve user-owned data isolation.

### Success Criteria:

#### Automated Verification:

- Targeted ownership tests in categories pass: `pdm run python manage.py test categories.tests.CategoryOwnershipURLTests`
- Targeted ownership negatives in transactions pass: `pdm run python manage.py test transactions.tests.TransactionCategoryCorrectionTests`

#### Manual Verification:

- Confirm denial semantics remain intentionally endpoint-specific (no accidental contract change to a new global status policy).
- Confirm no user-visible ownership leakage appears during authenticated navigation of category/transaction screens.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: Boundary and summary invariance hardening

### Overview

Harden date-boundary and summary correctness assertions around the currently shipped contracts, including context noise from list-style params.

### Changes Required:

#### 1. Dashboard boundary matrix extension

**File**: `accounts/tests.py`

**Intent**: Extend dashboard integration coverage for start/end inclusion and partial-bound behavior while preserving invalid-range fallback expectations.

**Contract**: `DashboardSummaryTests` contains explicit tests for inclusive boundaries, day-before/day-after exclusion, and partial-bound request handling under the current date-range model.

#### 2. Summary invariance under filter/sort context

**File**: `accounts/tests.py`

**Intent**: Add regression checks proving dashboard category totals stay correct when list-style `category`, `sort_by`, `sort_order`, and `page` params are present.

**Contract**: Summary assertions continue to validate exact Decimal totals and transaction counts under net-per-category semantics, unaffected by list-only params.

#### 3. Summary-layer boundary parity reinforcement

**File**: `transactions/tests.py`

**Intent**: Keep aggregation-layer boundary expectations aligned with dashboard-level assertions.

**Contract**: `TransactionSummaryTests` preserves inclusive date-bound behavior and remains consistent with dashboard-facing expectations for range filtering.

### Success Criteria:

#### Automated Verification:

- Targeted dashboard summary and boundary tests pass: `pdm run python manage.py test accounts.tests.DashboardSummaryTests`
- Targeted summary aggregation tests pass: `pdm run python manage.py test transactions.tests.TransactionSummaryTests`

#### Manual Verification:

- Confirm totals remain net-per-category in UI scenarios where both expenses and income exist.
- Confirm date-range behavior matches inclusive boundary expectations in dashboard interactions.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Verification consolidation and rollout closure

### Overview

Run consolidated validation for the hardened Phase 3 surface and align rollout artifacts.

### Changes Required:

#### 1. Consolidated regression pass

**File**: `accounts/tests.py`, `categories/tests.py`, `transactions/tests.py`

**Intent**: Validate cross-surface regression safety after Phase 1-2 additions.

**Contract**: Combined app-level run for the three primary apps completes green on the planned risk surface.

#### 2. Rollout status synchronization

**File**: `context/foundation/test-plan.md`

**Intent**: Keep phase-status documentation aligned with implementation outcome.

**Contract**: Phase 3 status row reflects the actual completion state once tests land, preserving plan/progress consistency.

### Success Criteria:

#### Automated Verification:

- Consolidated app-level test run passes: `pdm run python manage.py test accounts.tests categories.tests transactions.tests`
- Linting passes for touched files: `pdm run ruff check .`

#### Manual Verification:

- Confirm Phase 3 risk statements and shipped test coverage are aligned in planning artifacts.
- Confirm no unintended scope expansion beyond integration/security-negative hardening.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Testing Strategy

### Unit Tests:

- No new unit-test layer required for this change; focus remains on integration/security-negative protection.

### Integration Tests:

- Foreign-resource read/update negatives for category and transaction surfaces.
- Inclusive date boundary and partial-bound scenarios at dashboard and summary layers.
- Dashboard summary invariance under list-style filter/sort context parameters.

### Manual Testing Steps:

1. Log in as user A and attempt foreign category/transaction operations via direct URLs and form submissions.
2. Validate dashboard totals with mixed expense/income data and explicit date boundaries.
3. Retry dashboard requests with list-style filter/sort params and confirm totals consistency.

## Performance Considerations

Test runtime grows modestly due to additional integration cases; command strategy remains phase-targeted first, then consolidated trio run.

## Migration Notes

No schema or data migration is expected.

## References

- Related research: `context/changes/testing-abuse-and-boundary-hardening/research.md`
- Risk strategy source: `context/foundation/test-plan.md`
- Similar implementation references:
  - `categories/tests.py:24-42`
  - `accounts/tests.py:138-255`
  - `transactions/tests.py:370-416`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Ownership abuse negative-surface hardening

#### Automated

- [x] 1.1 Targeted ownership tests in categories pass: `pdm run python manage.py test categories.tests.CategoryOwnershipURLTests` — fc46b16
- [x] 1.2 Targeted ownership negatives in transactions pass: `pdm run python manage.py test transactions.tests.TransactionCategoryCorrectionTests` — fc46b16

#### Manual

- [x] 1.3 Confirm denial semantics remain intentionally endpoint-specific (no accidental contract change to a new global status policy) — fc46b16
- [x] 1.4 Confirm no user-visible ownership leakage appears during authenticated navigation of category/transaction screens — fc46b16

### Phase 2: Boundary and summary invariance hardening

#### Automated

- [x] 2.1 Targeted dashboard summary and boundary tests pass: `pdm run python manage.py test accounts.tests.DashboardSummaryTests`
- [x] 2.2 Targeted summary aggregation tests pass: `pdm run python manage.py test transactions.tests.TransactionSummaryTests`

#### Manual

- [x] 2.3 Confirm totals remain net-per-category in UI scenarios where both expenses and income exist
- [x] 2.4 Confirm date-range behavior matches inclusive boundary expectations in dashboard interactions

### Phase 3: Verification consolidation and rollout closure

#### Automated

- [ ] 3.1 Consolidated app-level test run passes: `pdm run python manage.py test accounts.tests categories.tests transactions.tests`
- [ ] 3.2 Linting passes for touched files: `pdm run ruff check .`

#### Manual

- [ ] 3.3 Confirm Phase 3 risk statements and shipped test coverage are aligned in planning artifacts
- [ ] 3.4 Confirm no unintended scope expansion beyond integration/security-negative hardening
