# Abuse and boundary hardening (Phase 3) — Plan Brief

> Full plan: `context/changes/testing-abuse-and-boundary-hardening/plan.md`
> Research: `context/changes/testing-abuse-and-boundary-hardening/research.md`

## What & Why

We are hardening Phase 3 test coverage for three high-risk failure modes: authenticated ownership abuse, boundary-date regressions, and summary-total correctness under filter/sort context noise.  
The goal is to convert known uncovered permutations into deterministic integration/security negatives without changing shipped runtime behavior.

## Starting Point

The project already has meaningful ownership and summary test coverage in `categories/tests.py`, `transactions/tests.py`, and `accounts/tests.py`, plus a research map of remaining gaps.  
Current summary semantics are net-per-category, and date filtering is inclusive by start/end bounds.

## Desired End State

After implementation, authenticated foreign-resource abuse paths are fully guarded by explicit negative tests, including non-mutation guarantees.  
Boundary coverage includes inclusive edges plus partial-bound scenarios under the current range model.  
Dashboard totals remain correct and invariant even when list-style filter/sort params are present, preserving net summary semantics.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Income handling contract | Keep net-per-category | It matches shipped logic and current test suite, minimizing accidental contract drift. | Research / Plan |
| Ownership denial assertions | Preserve endpoint-specific responses | Existing views intentionally differ by flow, and hardening should not force a behavior refactor. | Research / Plan |
| Boundary scope for Phase 3 | Harden inclusive/edge/partial bounds only | High-signal guardrails now, without expanding into new paycheck-cycle feature design. | Research / Plan |
| Filter/sort interaction coverage | Add focused dashboard invariance tests | It directly targets the risk seam with low maintenance overhead. | Research / Plan |
| Assertion strictness | Exact totals/counts + non-mutation | Financial correctness and isolation regressions require deterministic assertions. | Plan |
| Verification cadence | Targeted suites per phase + consolidated trio run | Fast iteration with strong end-of-phase confidence. | Plan |

## Scope

**In scope:**  
- Extend ownership/security negatives in category and transaction integration tests.  
- Extend boundary and summary invariance tests in dashboard/summary suites.  
- Run targeted and consolidated verification commands and synchronize rollout status artifacts.

**Out of scope:**  
- New paycheck-cycle derivation feature logic.  
- Runtime auth behavior redesign to unify all denial response codes.  
- E2E/browser-test expansion.

## Architecture / Approach

Use existing Django integration test architecture and helper patterns in app-level `tests.py` modules. The change is test-surface-first: reinforce existing view/service/model contracts by adding missing negative/boundary/context combinations, then close with consolidated app-level verification.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Ownership abuse negative-surface hardening | Missing foreign-resource permutations and non-mutation guarantees are covered | False confidence if only status is checked without state invariants |
| 2. Boundary and summary invariance hardening | Inclusive/partial-bound and filter/sort-context summary correctness checks | Semantic drift between plan wording and shipped net behavior |
| 3. Verification consolidation and rollout closure | Consolidated validation and status synchronization | Drift between implementation progress and test-plan phase state |

**Prerequisites:** Existing Phase 3 change folder and research artifact remain the canonical baseline.  
**Estimated effort:** ~2-3 sessions across 3 phases.

## Open Risks & Assumptions

- Assumes Phase 3 keeps current net-per-category summary contract.
- Assumes paycheck-cycle-specific algorithm work is deferred to a separate feature change.

## Success Criteria (Summary)

- Authenticated foreign-resource attempts are rejected and never mutate protected data.
- Boundary-date tests prove inclusive edge behavior and partial-bound handling.
- Dashboard totals remain correct under net semantics and invariant to list-style filter/sort params.
