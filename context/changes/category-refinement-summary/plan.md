# Category Refinement and Summary Implementation Plan

## Overview

Implement S-03 so a user can correct a transaction category with one action and view category-level spending totals. This closes the core US-01 loop after CSV import and keeps future auto-categorization aligned with user corrections.

## Current State Analysis

S-02 already provides imported transactions, category assignment, and merchant mapping storage, but the category column in the transactions table is read-only and the dashboard has no spending summary.

The project already has stable user-isolation patterns (queryset scoping by `request.user`) and a normalization function used for merchant matching, which should be reused for correction learning.

## Desired End State

After this plan is complete:

1. User can change a transaction category directly on the Transactions page using a single action.
2. The system updates future auto-categorization behavior for the corrected merchant.
3. Dashboard shows per-category spending totals for the logged-in user.
4. Unknown/uncategorized behavior remains explicit and safe.
5. Cross-user data isolation is preserved for edits, mappings, and summary totals.

Verification is complete when upload -> refine -> summary works end-to-end for one user, and another user cannot observe or mutate any of that data.

### Key Discoveries:

- `Transaction` already supports mutable category assignment and strict per-user uniqueness (`transactions/models.py:7`).
- Merchant-to-category learning primitives already exist and use normalized keys (`transactions/models.py:37`, `transactions/categorization.py:28`).
- Transactions UI currently renders category as read-only text (`templates/transactions/transaction_list.html:73`).
- Dashboard view/template are currently static and contain no summary aggregation (`accounts/views.py:18`, `templates/dashboard.html:11`).
- Established security pattern is user-scoped querysets in class-based views (`categories/views.py:18`).

## What We're NOT Doing

- Bulk category editing (FR-012).
- Transaction filtering/sorting enhancements (S-04).
- Budget-cycle-aware summary slicing (S-05).
- Charting/visual analytics beyond table totals.
- Materialized summary tables or cache-based precomputation.

## Implementation Approach

Use a server-rendered flow with explicit POST actions:

1. Add a correction endpoint that updates a single transaction category with strict ownership checks.
2. Reuse merchant normalization to update learned mappings consistently with existing auto-categorization logic.
3. Render category selector controls in the transactions table for single-action edits.
4. Compute dashboard summary totals on demand from user-scoped transactions.
5. Add focused tests for learning behavior, summary correctness, and isolation boundaries.

## Critical Implementation Details

### State sequencing

Correction handling must persist the transaction category change before applying mapping updates. Mapping writes must use `normalize_merchant(...)` from `transactions/categorization.py` to keep training keys compatible with import-time matching.

### User experience spec

Summary refresh does not need live JS updates. The accepted behavior is correctness on submit + reload, with clear success/error messaging after each correction.

## Phase 1: Correction Backend

### Overview

Add backend contracts for single-transaction category correction and mapping learning/removal with strict per-user ownership validation.

### Changes Required:

#### 1. Correction service

**File**: `transactions/refinement.py` (new)

**Intent**: Centralize correction logic so mapping learning rules and validation are reusable and testable.

**Contract**: Add service functions for applying a category correction to a user-owned transaction and synchronizing merchant mapping (upsert for concrete category, delete when Unknown/empty).

#### 2. Correction form contract

**File**: `transactions/forms.py`

**Intent**: Validate category selection against the current user instead of trusting raw POST values.

**Contract**: Add a user-aware form for transaction category correction that accepts Unknown/clear behavior and rejects foreign category IDs.

#### 3. Correction endpoint + route

**File**: `transactions/views.py`, `transactions/urls.py`

**Intent**: Expose a POST-only action to update one transaction category from the Transactions page.

**Contract**: Add a login-required, user-scoped endpoint (`transactions:<...set_category...>`) that returns to the transactions list with explicit success/error messages.

### Success Criteria:

#### Automated Verification:

- Django checks pass after wiring endpoint and form: `$env:DEBUG="True" ; pdm run python manage.py check`
- Targeted correction tests pass (ownership + mapping sync paths): `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests`
- Linting passes: `pdm run ruff check .`

#### Manual Verification:

- Changing one transaction category from Transactions persists immediately after submit.
- Setting a transaction to Unknown/empty removes learned mapping for that merchant.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: Transactions Page Refinement UX

### Overview

Add single-action category editing controls to each transaction row while preserving existing upload/delete functionality and feedback patterns.

### Changes Required:

#### 1. Per-row category edit controls

**File**: `templates/transactions/transaction_list.html`

**Intent**: Let the user correct categories directly in context of each transaction row.

**Contract**: Replace read-only category output with an inline POST form/select control per transaction row that submits to the new correction endpoint and includes CSRF protection.

#### 2. Category options context wiring

**File**: `transactions/views.py`

**Intent**: Provide available category choices for selector rendering.

**Contract**: `TransactionListView` context includes only categories owned by `request.user`, with Unknown included where present.

#### 3. Null/Unknown display consistency

**File**: `templates/transactions/transaction_list.html`

**Intent**: Keep category display explicit even when category is null or Unknown.

**Contract**: Template handling distinguishes normal category values from Unknown/unassigned and avoids rendering errors when `tx.category` is null.

### Success Criteria:

#### Automated Verification:

- Transactions page response contains category selector controls for listed rows in tests.
- Invalid/foreign category submissions are rejected in tests without mutating data.
- Linting passes: `pdm run ruff check .`

#### Manual Verification:

- User can change category in one action without navigating away from Transactions.
- Forged/tampered category selection cannot update another user's data.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Dashboard Category Summary

### Overview

Render per-category spending totals on the Dashboard using on-demand aggregation from user-scoped transactions.

### Changes Required:

#### 1. Summary query helper

**File**: `transactions/summary.py` (new)

**Intent**: Keep summary aggregation logic explicit and reusable.

**Contract**: Provide a function that returns per-category totals (and optional counts) for one user, including Unknown/unassigned handling.

#### 2. Dashboard view context enrichment

**File**: `accounts/views.py`

**Intent**: Supply summary data to dashboard template for logged-in user.

**Contract**: `dashboard_view` passes summary rows built from user-scoped transactions only; no cross-user aggregation.

#### 3. Dashboard summary table UI

**File**: `templates/dashboard.html`

**Intent**: Show a compact summary table alongside existing dashboard actions.

**Contract**: Add a table/card with category name and total amount, with stable behavior when no transactions exist.

### Success Criteria:

#### Automated Verification:

- Summary aggregation tests pass for totals and Unknown/unassigned handling.
- Isolation tests confirm dashboard summary only includes current user's transactions.
- Django checks and linting pass: `$env:DEBUG="True" ; pdm run python manage.py check` and `pdm run ruff check .`

#### Manual Verification:

- Dashboard shows per-category totals for the logged-in user.
- After a category correction on Transactions, dashboard totals reflect the new category on reload.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets - the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 4: Regression Hardening and End-to-End Confidence

### Overview

Lock in behavior with focused regression tests across import, correction learning, summary correctness, and user isolation boundaries.

### Changes Required:

#### 1. Refinement and summary test coverage

**File**: `transactions/tests.py`

**Intent**: Add explicit regression tests for correction workflow and learning behavior.

**Contract**: Add tests for update/removal of `MerchantCategoryMapping` on correction, plus import-after-correction behavior for the same merchant.

#### 2. Dashboard behavior tests

**File**: `accounts/tests.py` (new or extended)

**Intent**: Verify dashboard summary rendering and isolation.

**Contract**: Add authenticated tests asserting summary values, empty-state behavior, and cross-user isolation.

#### 3. End-to-end acceptance coverage

**File**: `transactions/tests.py`, `accounts/tests.py`

**Intent**: Preserve US-01 flow confidence through integrated scenarios.

**Contract**: Ensure upload -> refine -> summary path remains coherent with existing duplicate-skip and delete-all behavior.

### Success Criteria:

#### Automated Verification:

- End-to-end refinement-to-future-import behavior tests pass.
- Existing import/delete regression tests remain green.
- Full suite passes: `$env:DEBUG="True" ; pdm run python manage.py test`

#### Manual Verification:

- Full US-01 flow (upload -> refine -> summary) behaves as expected for primary user.
- Validation and error messaging are clear for invalid correction inputs.

**Implementation Note**: After completing this phase, all automated verification passes, and manual testing is successful, the feature is complete.

---

## Testing Strategy

### Unit Tests:

- Correction service behavior for upsert vs remove mapping.
- User-scoped category validation for correction requests.
- Summary aggregation helper output for normal, Unknown, and null-category transactions.

### Integration Tests:

- Transaction correction endpoint updates transaction and mapping consistently.
- Dashboard summary reflects corrected categories.
- Cross-user isolation: neither corrections nor summaries cross account boundaries.

### Manual Testing Steps:

1. Upload an ING CSV and confirm transactions appear.
2. Change categories for several rows on Transactions page and confirm success feedback.
3. Reload Dashboard and verify totals move between categories as expected.
4. Set one transaction to Unknown and confirm mapping removal behavior on later import.
5. Log in as a second user and confirm no visibility or mutation crossover.

## Performance Considerations

- Keep summary computation on-demand with one scoped aggregation query per dashboard load.
- Reuse existing list-query efficiency patterns (`select_related`) where needed for transaction rendering.
- Target MVP scale (hundreds to low-thousands of transactions per user) without introducing cache invalidation complexity.

## Migration Notes

- No schema migrations are required for this slice if implemented with existing models.
- If a helper module is introduced (`transactions/refinement.py`, `transactions/summary.py`), ensure import paths do not create circular dependencies.

## References

- Product requirements: `context/foundation/prd.md` (FR-005, FR-009, US-01)
- Slice definition: `context/foundation/roadmap.md` (S-03)
- Existing transaction flow: `transactions/views.py`, `templates/transactions/transaction_list.html`
- Existing categorization primitives: `transactions/categorization.py`, `transactions/models.py`
- Existing user-scoping pattern: `categories/views.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Correction Backend

#### Automated

- [x] 1.1 Django checks pass after correction endpoint/form wiring — 0447e13
- [x] 1.2 Targeted correction and mapping-sync tests pass — 0447e13
- [x] 1.3 Linting passes — 0447e13

#### Manual

- [x] 1.4 Single transaction category change persists from Transactions page — 0447e13
- [x] 1.5 Setting category to Unknown/empty removes learned mapping — 0447e13

### Phase 2: Transactions Page Refinement UX

#### Automated

- [x] 2.1 Transactions page renders per-row category selector controls
- [x] 2.2 Invalid or foreign category submissions are rejected without data mutation
- [x] 2.3 Linting passes

#### Manual

- [x] 2.4 Single-action category editing works without leaving Transactions page
- [x] 2.5 Forged update attempt cannot modify another user's transaction

### Phase 3: Dashboard Category Summary

#### Automated

- [ ] 3.1 Summary aggregation tests pass for totals and Unknown/unassigned handling
- [ ] 3.2 Dashboard summary isolation tests pass for per-user scoping
- [ ] 3.3 Django checks and linting pass

#### Manual

- [ ] 3.4 Dashboard displays per-category spending totals for current user
- [ ] 3.5 Category corrections are reflected in dashboard totals after reload

### Phase 4: Regression Hardening and End-to-End Confidence

#### Automated

- [ ] 4.1 Refinement-to-future-import behavior tests pass
- [ ] 4.2 Existing import/delete regression tests remain green
- [ ] 4.3 Full project test suite passes

#### Manual

- [ ] 4.4 Upload -> refine -> summary works end-to-end for primary user
- [ ] 4.5 Invalid correction inputs show clear validation/error feedback
