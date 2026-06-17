# Access isolation hardening implementation plan

## Overview

Harden user-data isolation guarantees so cross-user access remains blocked across persistence, service, and endpoint layers while preserving current auth UX semantics.

## Current State Analysis

The application already enforces user scoping in most views and summary services, and existing tests verify key cross-user isolation paths. Remaining risk centers on persistence-level ownership invariants not being fully encoded at the database boundary, which leaves non-view write paths (future scripts/admin/internal integrations) more fragile than intended.

## Desired End State

The system guarantees that user-owned records cannot be linked across accounts in unsafe ways, protected routes keep current auth semantics (redirect for anonymous, non-leaky handling for foreign objects), and targeted regression tests prove these guarantees for critical entry points.

### Key Discoveries:

- Auth guards are already present on core protected views: `accounts/views.py:101`, `categories/views.py:13`, `transactions/views.py:24`.
- Query-level user scoping is consistently applied in current read/write flows: `categories/views.py:21`, `transactions/views.py:47`, `transactions/summary.py:18`.
- Service-level ownership checks exist for category correction: `transactions/refinement.py:49-52`.
- Data-model ownership equality across related records is not fully enforced at DB boundary today: `transactions/models.py:7-60`.
- Isolation tests exist but unauthenticated route regression coverage is relatively thin in app suites: `accounts/tests.py`, `categories/tests.py`, `transactions/tests.py`.

## What We're NOT Doing

- No RBAC/roles redesign.
- No multi-tenant architecture redesign.
- No admin panel overhaul.
- No token/auth-stack modernization in this change.
- No unrelated feature work outside F-01 isolation guarantees.

## Implementation Approach

Implement a defense-in-depth hardening sequence: first add migration-time data guardrails and enforceable runtime ownership validation; then tighten endpoint contracts to documented auth behavior; finally add targeted cross-user and unauthenticated regression coverage. Use DB-native constraints only where safely portable; do not ship brittle backend-specific invariants as required paths.

## Critical Implementation Details

### Timing & lifecycle

Apply migration guardrails before endpoint behavior tightening so invalid existing data is detected early and cannot be masked by later service changes.

### Debug & observability

Migration failures for ownership mismatches must be explicit and actionable (clear offending row identifiers), because the selected strategy intentionally blocks rollout until isolation-violating rows are remediated.

## Phase 1: Data-layer ownership invariant hardening

### Overview

Establish migration and model/service guardrails that prevent cross-user ownership mismatches from being introduced or retained.

### Changes Required:

#### 1. Ownership invariant guards in transaction data models

**File**: `transactions/models.py`

**Intent**: Add hardening at the model/persistence boundary so category and mapping relations cannot silently violate user ownership assumptions.

**Contract**: Transaction/category and mapping/category ownership consistency is validated as a required invariant; DB-native constraints are applied only where safely portable across supported environments.

#### 2. Migration-time isolation safety gate

**File**: `transactions/migrations/<new_migration>.py`

**Intent**: Block rollout when legacy rows violate ownership invariants, with explicit remediation guidance.

**Contract**: Migration fails loudly when mismatch rows exist; it does not auto-repair ownership by mutating user/category identity links.

#### 3. Service invariants remain explicit and aligned

**File**: `transactions/refinement.py`

**Intent**: Keep service-layer ownership checks aligned with model/migration invariants as defense-in-depth.

**Contract**: Unauthorized cross-user mutation attempts remain rejected via explicit permission exceptions.

### Success Criteria:

#### Automated Verification:

- New migration applies cleanly on valid datasets: `$env:DEBUG="True" ; pdm run python manage.py migrate`
- Targeted transaction isolation tests pass: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests.TransactionRefinementServiceSafetyTests`
- Django system checks pass after model/migration changes: `$env:DEBUG="True" ; pdm run python manage.py check`

#### Manual Verification:

- Remediation instructions are clear and actionable when migration guard intentionally blocks invalid rows.
- Existing user flows (import, category correction, summary) still work for valid ownership data.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Endpoint access-contract hardening

### Overview

Standardize endpoint behavior to current secure semantics and remove ambiguity in auth/ownership handling for protected routes.

### Changes Required:

#### 1. Protected-route contract alignment

**File**: `accounts/views.py`

**Intent**: Ensure dashboard/authenticated entry behavior remains explicit and consistent with isolation expectations.

**Contract**: Authenticated dashboard access remains user-scoped; anonymous requests follow established login redirect behavior.

#### 2. Category and transaction endpoint contract checks

**File**: `categories/views.py`

**Intent**: Preserve non-leaky handling for foreign-object mutation attempts.

**Contract**: Foreign category edit/delete attempts remain denied via current scoped-query contract.

**File**: `transactions/views.py`

**Intent**: Preserve user-scoped read/mutation behavior for list/upload/delete/set-category endpoints.

**Contract**: Protected transaction endpoints maintain authenticated access gating and reject foreign-object category operations without leaking unrelated data.

### Success Criteria:

#### Automated Verification:

- Accounts/category/transaction test suites pass after endpoint contract alignment: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests categories.tests transactions.tests`
- Lint and type-check pass: `pdm run ruff check .` and `pdm run basedpyright`

#### Manual Verification:

- Anonymous user is redirected to login on protected routes.
- Foreign-object access attempts do not expose or mutate another user’s data.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Isolation regression net and remediation documentation

### Overview

Add focused regression coverage and operational docs so isolation hardening is durable and maintainable.

### Changes Required:

#### 1. Targeted unauthenticated and cross-user regression tests

**File**: `accounts/tests.py`

**Intent**: Add unauthenticated-route and cross-user isolation assertions for dashboard/auth entry constraints.

**Contract**: Tests explicitly codify redirect and user-scoped rendering behavior for protected account surfaces.

**File**: `categories/tests.py`

**Intent**: Expand isolation coverage beyond current foreign edit/delete checks where needed.

**Contract**: Category list/create/update/delete flows are asserted for both ownership and unauthenticated access contracts.

**File**: `transactions/tests.py`

**Intent**: Expand isolation and route-level auth coverage for transaction endpoints and mutation paths.

**Contract**: Tests verify no cross-user leakage or mutation and preserve current secure status/redirect semantics.

#### 2. Isolation remediation and runbook notes

**File**: `agents.md`

**Intent**: Document migration guard failure remediation path and isolation verification commands for local workflows.

**Contract**: Team has a deterministic checklist for isolating/fixing ownership mismatch rows discovered by migration guardrails.

### Success Criteria:

#### Automated Verification:

- New targeted isolation regressions pass: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests categories.tests transactions.tests`
- Full test suite remains green: `$env:DEBUG="True" ; pdm run python manage.py test`
- Query-count sanity checks (where added) pass without introducing avoidable extra lookups.

#### Manual Verification:

- Security checklist walkthrough confirms all critical protected surfaces behave per contract.
- Migration-remediation documentation is sufficient for a developer to resolve a simulated mismatch scenario.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Ownership invariant validation tests for model/service boundaries.
- Focused tests for migration guard behavior on invalid ownership records.

### Integration Tests:

- Cross-user and unauthenticated access behavior across dashboard, categories, and transaction endpoints.
- Mutation-path safety tests for category correction and transaction category reassignment.

### Manual Testing Steps:

1. Validate protected-route behavior as anonymous vs authenticated users.
2. Validate foreign-object mutation attempts do not alter or reveal another user’s records.
3. Validate migration guard remediation flow on intentionally injected mismatch data in a local test fixture.

## Performance Considerations

Isolation hardening should remain query-local and avoid broad query amplification. Add query-count assertions only where new validation/contract checks could introduce extra lookups.

## Migration Notes

- Introduce one migration for ownership invariant guardrails and mismatch detection.
- Migration must fail with explicit diagnostics when cross-user mismatches are present; no silent auto-fix of ownership identity.

## References

- Roadmap foundation target: `context/foundation/roadmap.md:64`
- Auth/dashboard boundary: `accounts/views.py:101`
- Category ownership scoping: `categories/views.py:21`
- Transaction ownership scoping: `transactions/views.py:47`
- Service ownership checks: `transactions/refinement.py:49`
- Summary user scoping: `transactions/summary.py:18`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Data-layer ownership invariant hardening

#### Automated

- [x] 1.1 New migration applies cleanly on valid datasets
- [x] 1.2 Targeted transaction isolation tests pass
- [x] 1.3 Django system checks pass after model/migration changes

#### Manual

- [ ] 1.4 Remediation instructions are clear and actionable when migration guard blocks invalid rows
- [ ] 1.5 Existing user flows still work for valid ownership data

### Phase 2: Endpoint access-contract hardening

#### Automated

- [ ] 2.1 Accounts/category/transaction test suites pass after endpoint contract alignment
- [ ] 2.2 Lint and type-check pass

#### Manual

- [ ] 2.3 Anonymous user is redirected to login on protected routes
- [ ] 2.4 Foreign-object access attempts do not expose or mutate another user’s data

### Phase 3: Isolation regression net and remediation documentation

#### Automated

- [ ] 3.1 New targeted isolation regressions pass
- [ ] 3.2 Full test suite remains green
- [ ] 3.3 Query-count sanity checks (where added) pass without avoidable extra lookups

#### Manual

- [ ] 3.4 Security checklist walkthrough confirms all critical protected surfaces behave per contract
- [ ] 3.5 Migration-remediation documentation supports resolving a simulated mismatch scenario
