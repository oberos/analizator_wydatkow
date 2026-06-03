# Critical-path data correctness implementation plan

## Overview

Implement Phase 1 of the test rollout by closing coverage gaps for risks #1, #2, and #4: account isolation, CSV import integrity, and summary correctness. The plan is test-first and only introduces targeted production refactor if tests prove a contract mismatch.

## Current State Analysis

Ownership, import, and summary behavior already exist in production code, with partial regression coverage. Main risk is uncovered edge behavior rather than missing features.

- Isolation protections are layered in views/forms/services (`transactions/views.py:27-29`, `categories/views.py:43-55`, `transactions/refinement.py:49-52`).
- CSV pipeline is strict parser + atomic persistence with duplicate skip (`transactions/csv_parser.py:223-240`, `transactions/views.py:81-95`, `transactions/models.py:29-31`).
- Summary is user-scoped and expense-only today (`transactions/summary.py:12-30`), but current contract must be aligned to the chosen rule: expenses minus income by category.

## Desired End State

Phase 1 delivers deterministic regression protection for the approved risks:

1. Foreign-resource access/edit attempts are denied at HTTP and service boundaries.
2. CSV import fails fast on malformed content and does not silently persist partial bad data.
3. Summary behavior is explicitly tested and aligned to the agreed category total rule (expenses minus income), with user scoping preserved.

### Key Discoveries:

- Existing tests already cover many isolation paths and income-exclusion baseline (`transactions/tests.py:294-340`, `transactions/tests.py:467-494`, `accounts/tests.py:18-63`).
- Direct URL foreign category edit/delete denial is enforced by queryset scoping but not explicitly tested (`categories/views.py:43-55`).
- Duplicate semantics are implemented via DB uniqueness + `ignore_conflicts`, so integrity tests should assert counts and messages, not internal ORM behavior (`transactions/views.py:81-95`, `transactions/models.py:29-31`).

## What We're NOT Doing

- No work on risks outside Phase 1 scope (#3, #5, #6 rollout rows).
- No new ingestion formats beyond ING CSV.
- No CI pipeline redesign; only plan-level gates and test coverage changes.
- No broad UI redesign or feature additions unrelated to data correctness testing.

## Implementation Approach

Add focused integration/service tests around known risk boundaries, then enforce the chosen summary contract through tests. If summary contract differs from current logic, apply a minimal, localized refactor in `transactions/summary.py` only after failing tests establish the delta. Run targeted app tests during each phase and full-suite gate at final phase.

## Critical Implementation Details

### State sequencing

For summary contract changes, write assertions first in `transactions/tests.py` and `accounts/tests.py`, then adjust `transactions/summary.py` only if those assertions fail. This keeps the phase behavior-driven and prevents speculative refactor.

## Phase 1: Ownership isolation coverage

### Overview

Close missing HTTP-level ownership denial coverage and reinforce existing isolation boundaries with explicit, user-visible contracts.

### Changes Required:

#### 1. Category URL ownership denial tests

**File**: `categories/tests.py`

**Intent**: Add direct URL access tests for foreign category edit/delete attempts, matching expected 404-style denial.

**Contract**: GET/POST against foreign category edit/delete endpoints must deny access and must not mutate foreign records.

#### 2. Transaction isolation regression reinforcement

**File**: `transactions/tests.py`

**Intent**: Extend existing correction/isolation tests to ensure no cross-account mutation or leakage path is left unverified for this phase.

**Contract**: Foreign transaction/category operations remain blocked at HTTP and service boundaries; existing user-scoped options remain enforced.

### Success Criteria:

#### Automated Verification:

- New ownership URL denial tests pass in `categories.tests`.
- Isolation regression tests pass in `transactions.tests`.
- Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check`.

#### Manual Verification:

- As user A, attempting to access/edit user B category URL does not expose or modify user B data.
- Transaction/category operations for one account do not alter another account's dashboard summary.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: CSV integrity coverage

### Overview

Add coverage for malformed and mixed CSV scenarios while preserving fail-fast, all-or-nothing import behavior.

### Changes Required:

#### 1. CSV malformed-row and structural failure tests

**File**: `transactions/tests.py`

**Intent**: Add edge-case import tests validating that malformed data rows trigger parse errors and prevent partial persistence.

**Contract**: Import aborts on malformed input; no partial data writes occur when parser raises `CSVParseError`.

#### 2. Duplicate/integrity edge-case tests

**File**: `transactions/tests.py`

**Intent**: Extend duplicate coverage to include mixed valid/duplicate scenarios and transaction identity boundary cases.

**Contract**: Imported/skipped counts and persisted row count reflect per-user uniqueness rules from model constraints.

### Success Criteria:

#### Automated Verification:

- CSV edge-case tests pass in `transactions.tests`.
- Targeted import flow tests confirm duplicate count behavior.
- Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check`.

#### Manual Verification:

- Uploading a malformed CSV reports parse error and leaves transaction list unchanged.
- Re-upload behavior still communicates duplicate skips clearly to the user.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Summary correctness contract

### Overview

Lock the summary contract to the approved rule: count all transactions, compute category total as expenses minus income by category, and keep user scoping intact.

### Changes Required:

#### 1. Summary contract tests

**File**: `transactions/tests.py`

**Intent**: Add/adjust summary tests to express the approved total semantics and verify user scoping remains intact.

**Contract**: Summary assertions explicitly validate net-per-category behavior (expenses minus income) and expected transaction count behavior.

#### 2. Dashboard summary alignment tests

**File**: `accounts/tests.py`

**Intent**: Ensure dashboard rendering remains consistent with summary contract changes and isolation guarantees.

**Contract**: Dashboard category summary values match updated backend summary contract for the authenticated user only.

#### 3. Targeted summary logic refactor (conditional)

**File**: `transactions/summary.py`

**Intent**: Apply minimal logic changes only if new tests fail against current behavior.

**Contract**: Summary query semantics satisfy approved contract without altering unrelated transaction/report flows.

### Success Criteria:

#### Automated Verification:

- Summary contract tests pass in `transactions.tests`.
- Dashboard summary alignment tests pass in `accounts.tests`.
- Linting passes: `pdm run ruff check .`.

#### Manual Verification:

- Dashboard totals for categories with both expenses and income match expected net values.
- Cross-user summary isolation remains unchanged after summary contract updates.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 4: Final verification and rollout handoff

### Overview

Apply final quality gates for this change and prepare handoff for implementation execution tracking.

### Changes Required:

#### 1. Full-suite gate and consistency checks

**File**: `transactions/tests.py`

**Intent**: Validate no regressions outside targeted test modules by running full suite after phase-level targeted checks are green.

**Contract**: Full Django test suite passes after Phase 1 changes.

#### 2. Test-plan cookbook backfill for Phase 1

**File**: `context/foundation/test-plan.md`

**Intent**: Record the Phase 1 shipped test patterns in §6 cookbook placeholders.

**Contract**: Relevant §6 entries for integration/API/summary patterns are no longer TBD for Phase 1.

### Success Criteria:

#### Automated Verification:

- Full suite passes: `$env:DEBUG="True" ; pdm run python manage.py test`.
- Linting passes: `pdm run ruff check .`.
- Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check`.

#### Manual Verification:

- Core flow (upload -> list -> refine -> dashboard summary) behaves correctly for two separate users.
- Messages and denial behavior remain understandable after test-driven changes.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

## Testing Strategy

### Unit Tests:

- Service-level ownership denial in category correction.
- Parser error-path behavior for malformed values and required-column failures.

### Integration Tests:

- Foreign resource access/update denial through HTTP endpoints.
- CSV upload fail-fast behavior and duplicate count semantics.
- Dashboard summary contract and user scoping coherence.

### Manual Testing Steps:

1. Log in as user A and user B; verify foreign category URLs are denied for user A.
2. Upload malformed CSV as user A; confirm no partial transactions are persisted.
3. Validate category totals on dashboard for mixed expense/income cases and verify user B data never appears for user A.

## Performance Considerations

Test additions should avoid large fixture files and keep data setup minimal per test method. Summary contract tests should use small, explicit datasets to preserve fast feedback in targeted test runs.

## Migration Notes

No schema migration is expected. If summary logic changes, it is query-level behavior only.

## References

- Related research: `context/changes/testing-critical-path-data-correctness/research.md`
- Rollout contract: `context/foundation/test-plan.md`
- Isolation/query patterns: `transactions/views.py:27-29`, `categories/views.py:43-55`, `transactions/refinement.py:49-52`
- Import pipeline: `transactions/csv_parser.py:223-240`, `transactions/views.py:81-95`, `transactions/models.py:29-31`
- Summary baseline: `transactions/summary.py:12-30`, `transactions/tests.py:467-494`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Ownership isolation coverage

#### Automated

- [x] 1.1 Ownership URL denial tests pass in `categories.tests` — fd7c7be
- [x] 1.2 Isolation regression tests pass in `transactions.tests` — fd7c7be
- [x] 1.3 Django checks pass — fd7c7be

#### Manual

- [x] 1.4 Foreign category URL access is denied without mutation — fd7c7be
- [x] 1.5 Cross-account transaction/category actions do not leak into another user's summary — fd7c7be

### Phase 2: CSV integrity coverage

#### Automated

- [x] 2.1 CSV malformed-row and structural failure tests pass — 84d2b63
- [x] 2.2 Duplicate and mixed integrity edge-case tests pass — 84d2b63
- [x] 2.3 Django checks pass — 84d2b63

#### Manual

- [x] 2.4 Malformed CSV upload shows parse error and persists no partial data — 84d2b63
- [x] 2.5 Duplicate re-upload messaging remains clear and accurate — 84d2b63

### Phase 3: Summary correctness contract

#### Automated

- [x] 3.1 Summary contract tests pass in `transactions.tests` — d05e695
- [x] 3.2 Dashboard summary alignment tests pass in `accounts.tests` — d05e695
- [x] 3.3 Ruff linting passes — d05e695

#### Manual

- [x] 3.4 Mixed expense/income category totals match approved net rule — d05e695
- [x] 3.5 Cross-user summary isolation remains intact after contract updates — d05e695

### Phase 4: Final verification and rollout handoff

#### Automated

- [x] 4.1 Full Django test suite passes — 18619ee
- [x] 4.2 Ruff linting passes — 18619ee
- [x] 4.3 Django checks pass — 18619ee

#### Manual

- [x] 4.4 End-to-end core flow works for two separate users without data leakage — 18619ee
- [x] 4.5 User-facing denial and import error messaging remains understandable — 18619ee
