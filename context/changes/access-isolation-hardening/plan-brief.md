# Access isolation hardening — Plan Brief

> Full plan: `context/changes/access-isolation-hardening/plan.md`

## What & Why

This change hardens user-data isolation so downstream reporting and categorization can safely assume strict ownership boundaries. The goal is to eliminate cross-user linkage risk at persistence and runtime layers while preserving current auth UX semantics.

## Starting Point

The codebase already uses login gates and user-scoped query patterns in major flows, with existing isolation tests for key paths. The remaining gap is that ownership equality between related records is not fully guaranteed at the persistence boundary.

## Desired End State

Cross-user ownership mismatches are blocked by migration/model/service guardrails, protected endpoints keep current secure behavior, and targeted regression tests cover unauthenticated and foreign-object scenarios. The team also has remediation instructions for migration guard failures.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Scope boundary | Harden existing endpoints/invariants only | Keeps F-01 focused and avoids RBAC/auth redesign scope creep | Plan |
| Invariant strategy | Migration guard + model/service validation baseline, DB-native constraints when portable | Maximizes safety without brittle backend-specific migrations | Plan |
| Legacy mismatch policy | Block migration and require explicit remediation | Prevents silent mutation of ownership identity | Plan |
| Endpoint behavior contract | Keep current secure semantics (login redirect for anonymous, non-leaky foreign-object handling) | Aligns with existing UX and avoids resource-leak signals | Plan |
| Verification depth | Targeted cross-user + unauthenticated regressions per protected surface | Gives strong confidence with bounded maintenance overhead | Plan |

## Scope

**In scope:** migration/model/service ownership hardening, endpoint contract alignment, targeted isolation regressions, remediation docs.

**Out of scope:** RBAC roles redesign, multi-tenant architecture redesign, admin overhaul, auth-stack modernization.

## Architecture / Approach

Apply hardening in three layers: first data-layer invariants and migration guardrails, then endpoint contract consistency, then regression and operational hardening. This sequence minimizes rollout risk by failing early on bad legacy data and proving behavior with focused tests.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Data-layer invariant hardening | Ownership guardrails in migration/model/service boundaries | Migration may surface legacy invalid rows requiring cleanup |
| 2. Endpoint contract hardening | Consistent auth/ownership behavior on protected surfaces | Unintended behavior drift in existing endpoint semantics |
| 3. Regression net + docs | Durable isolation test coverage and remediation runbook | Test overreach or brittle assertions |

**Prerequisites:** Current auth and user-scoped query behavior remains stable in `accounts`, `categories`, `transactions`.
**Estimated effort:** ~2-3 sessions across 3 phases.

## Open Risks & Assumptions

- Cross-table ownership equality may not be fully expressible as portable DB constraints in all environments.
- Migration-guard failures depend on clear diagnostics to avoid rollout delays.

## Success Criteria (Summary)

- Ownership mismatch rows are blocked at migration/runtime boundaries.
- Protected endpoints preserve secure auth and foreign-object handling contracts.
- Isolation regressions (cross-user + unauthenticated) are covered by targeted automated tests.
