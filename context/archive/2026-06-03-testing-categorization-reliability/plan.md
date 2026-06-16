# Categorization reliability implementation plan

## Overview

Implement Phase 2 of the rollout for risk #3 by adding high-signal, contract-focused integration tests that prove manual category correction deterministically affects future categorization for matching merchant patterns.

## Current State Analysis

Core correction and categorization flows already exist and are covered by baseline happy-path tests, but regression protection is incomplete for normalized merchant variants and overlapping mapping keys.

- Correction is applied via HTTP and persisted through service boundary (`transactions/views.py:121-144`, `transactions/refinement.py:42-62`).
- Learned mapping lifecycle (upsert/remove) is centralized (`transactions/refinement.py:12-39`) and constrained by per-user uniqueness (`transactions/models.py:37-56`).
- Lookup contract is exact-normalized match first, then fallback token-boundary matching (`transactions/categorization.py:90-116`, `transactions/categorization.py:13-25`).
- Existing tests already prove baseline learning and reset behavior (`transactions/tests.py:417-463`) and include baseline matching edge checks (`transactions/tests.py:64-99`).

## Desired End State

Phase 2 provides deterministic regression protection for correction-learning behavior without implementation-mirror assertions:

1. Correcting category for one merchant variant causes future import of equivalent normalized merchant variants to auto-categorize to the corrected category.
2. Overlapping mapping keys have explicit guardrail coverage to prevent accidental precedence regression.
3. Cookbook section for categorization-rule testing is updated with concrete pattern and run command for future contributors.

### Key Discoveries:

- Risk #3 contract is explicitly integration + contract fixtures and requires challenging false-confidence mapping hits (`context/foundation/test-plan.md:55`, `context/foundation/test-plan.md:69`).
- Existing test suite already has reusable correction/import flow shape, minimizing need for production code changes (`transactions/tests.py:417-463`).
- Lessons require strict scope discipline and status/progress synchronization across artifacts (`context/foundation/lessons.md:5-24`).

## What We're NOT Doing

- No production logic changes in `transactions/categorization.py`, `transactions/refinement.py`, or views unless tests prove a contract break.
- No work on risks outside #3 (CSV integrity, ownership abuse, summary totals, paycheck-cycle boundaries).
- No test-helper refactor/migration outside the targeted additions in `transactions/tests.py`.
- No e2e runner or CI-gate infrastructure work in this change.

## Implementation Approach

Add test-only contract coverage in `transactions/tests.py`, anchored to observable outcomes through HTTP correction + CSV import. Reuse existing test scaffolding and avoid reproducing normalization/regex internals in assertions.

## Phase 1: Deterministic correction-learning contracts

### Overview

Add integration tests that prove correction-learning remains deterministic across normalized merchant variants in future imports.

### Changes Required:

#### 1. Expand correction-learning integration cases

**File**: `transactions/tests.py`

**Intent**: Extend `TransactionCategoryCorrectionTests` with normalized-variant determinism cases using existing correction endpoint and import flow pattern.

**Contract**: A correction made for merchant variant A must be reflected when importing merchant variant B that normalizes to the same mapping key; assertions validate final category outcome and expected mapping presence only.

### Success Criteria:

#### Automated Verification:

- New normalized-variant correction-learning tests pass in `transactions.tests`.
- Existing correction-learning baseline tests remain green in `transactions.tests`.
- Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check`.

#### Manual Verification:

- In UI: set category for one transaction variant and confirm success message.
- Upload CSV with equivalent merchant variant and confirm imported row lands with corrected category.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: Mapping precedence guardrail

### Overview

Add a focused regression guard that protects behavior when learned mapping keys overlap.

### Changes Required:

#### 1. Add explicit overlap/precedence contract test

**File**: `transactions/tests.py`

**Intent**: Add one integration contract scenario with overlapping merchant keys to ensure categorization result stays stable under future refactors.

**Contract**: For an imported merchant string matching overlapping keys, categorization resolves to expected category per current lookup behavior; assertion is on observable categorized result, not on regex internals.

### Success Criteria:

#### Automated Verification:

- New overlap/precedence contract test passes in `transactions.tests`.
- Existing punctuation/false-positive baseline matching tests remain green.
- Lint passes: `pdm run ruff check transactions/tests.py`.

#### Manual Verification:

- Validate test intent in review: expected category is described in business terms (merchant/category outcome), not implementation terms (regex/order internals).

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Cookbook and phase close-out

### Overview

Backfill rollout documentation and finalize this phase with scoped verification.

### Changes Required:

#### 1. Fill cookbook entry for categorization-rule tests

**File**: `context/foundation/test-plan.md`

**Intent**: Replace §6.5 placeholder with concrete guidance for adding categorization reliability tests aligned with this phase.

**Contract**: §6.5 includes location, pattern, at least one reference test, and local run command.

#### 2. Keep rollout state synchronized

**File**: `context/foundation/test-plan.md`, `context/changes/testing-categorization-reliability/change.md`

**Intent**: Ensure phase status transitions are aligned with completion state to avoid orchestration drift.

**Contract**: §3 phase row and `change.md` status reflect implemented state after execution.

### Success Criteria:

#### Automated Verification:

- Targeted suite passes: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests`.
- Lint passes: `pdm run ruff check .`.
- Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check`.

#### Manual Verification:

- Confirm `test-plan.md` §6.5 is no longer placeholder and points to real test patterns.
- Confirm change artifacts remain scoped to this rollout phase.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Testing Strategy

### Unit Tests:

- No new pure unit tests; this phase prioritizes contract-level integration signal.

### Integration Tests:

- Correction endpoint updates mapping and future import behavior for normalized merchant variants.
- Overlapping mapping-key scenario remains stable as categorized outcome guardrail.
- Existing learning/reset and matching baselines remain green to detect regressions.

### Manual Testing Steps:

1. Through UI, correct category for a transaction with merchant variant A.
2. Upload CSV containing merchant variant B (same semantic merchant) and verify categorized result.
3. Confirm rollout docs reflect delivered patterns and status state.

## Performance Considerations

- Scope is test-focused; no runtime production-path changes are planned.
- Keep added tests deterministic and concise to avoid slowing suite disproportionately.

## Migration Notes

- No schema/data migration in this phase.

## References

- Related research: `context/changes/testing-categorization-reliability/research.md`
- Rollout contract: `context/foundation/test-plan.md:55-70`
- Correction boundary: `transactions/views.py:121-144`, `transactions/refinement.py:12-62`
- Categorization lookup: `transactions/categorization.py:13-25`, `transactions/categorization.py:90-116`
- Existing baseline tests: `transactions/tests.py:64-99`, `transactions/tests.py:417-463`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Deterministic correction-learning contracts

#### Automated

- [x] 1.1 New normalized-variant correction-learning tests pass in `transactions.tests` — 5fddb3f
- [x] 1.2 Existing correction-learning baseline tests remain green in `transactions.tests` — 5fddb3f
- [x] 1.3 Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check` — 5fddb3f

#### Manual

- [x] 1.4 In UI: set category for one transaction variant and confirm success message — 5fddb3f
- [x] 1.5 Upload CSV with equivalent merchant variant and confirm imported row lands with corrected category — 5fddb3f

### Phase 2: Mapping precedence guardrail

#### Automated

- [x] 2.1 New overlap/precedence contract test passes in `transactions.tests` — f7669e7
- [x] 2.2 Existing punctuation/false-positive baseline matching tests remain green — f7669e7
- [x] 2.3 Lint passes: `pdm run ruff check transactions/tests.py` — f7669e7

#### Manual

- [x] 2.4 Validate test intent in review: assertions remain business-outcome based, not implementation-mirror based — f7669e7

### Phase 3: Cookbook and phase close-out

#### Automated

- [x] 3.1 Targeted suite passes: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests` — 17ee5c2
- [x] 3.2 Lint passes: `pdm run ruff check .` — 17ee5c2
- [x] 3.3 Django checks pass: `$env:DEBUG="True" ; pdm run python manage.py check` — 17ee5c2

#### Manual

- [x] 3.4 Confirm `test-plan.md` §6.5 is no longer placeholder and points to real test patterns — 17ee5c2
- [x] 3.5 Confirm change artifacts remain scoped to this rollout phase — 17ee5c2
