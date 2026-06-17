<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Critical-path data correctness implementation plan

- **Plan**: context/changes/testing-critical-path-data-correctness/plan.md
- **Scope**: Full plan (all completed phases)
- **Date**: 2026-06-03
- **Verdict**: APPROVED AFTER TRIAGE
- **Findings**: 0 critical, 0 warnings, 0 observations (all triaged)

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | PASS |
| Scope Discipline | WARNING |
| Safety & Quality | PASS |
| Architecture | PASS |
| Pattern Consistency | PASS |
| Success Criteria | WARNING |

## Findings

### F1 — Phase status in test-plan is stale

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Scope Discipline
- **Location**: context/foundation/test-plan.md:68
- **Detail**: Rollout row for "Critical-path data correctness" still shows `change opened` even though all Phase 1 progress items are complete and committed.
- **Fix**: Update §3 Status for Phase 1 in `context/foundation/test-plan.md` from `change opened` to `complete` and keep Change folder unchanged.
- **Decision**: FIXED + ACCEPTED-AS-RULE: Keep test-plan phase status synchronized with progress

### F2 — Quality gate requires e2e before e2e tooling exists

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Success Criteria
- **Location**: context/foundation/test-plan.md:104, context/foundation/test-plan.md:131-132
- **Detail**: §5 marks "e2e on critical flows" as `required after §3 Phase 1`, while §6.3 states no dedicated e2e runner is wired and integration is fallback.
- **Fix A ⭐ Recommended**: Downgrade the e2e gate to `planned after e2e runner is introduced` and keep current integration fallback as the enforceable gate.
  - Strength: Aligns policy with what the repo can actually execute right now.
  - Tradeoff: Defers strict e2e enforcement until infrastructure work lands.
  - Confidence: HIGH — current repo has no e2e harness configured.
  - Blind spot: Does not set an exact phase/date for enabling e2e.
- **Fix B**: Keep gate as required and immediately add minimal e2e tooling in a follow-up change.
  - Strength: Preserves stricter quality floor intent.
  - Tradeoff: Expands scope beyond current completed change and delays archive readiness.
  - Confidence: MEDIUM — feasible, but not scoped in this implementation.
  - Blind spot: Follow-up effort estimate and CI cost were not analyzed here.
- **Decision**: FIXED (Fix B)

### F3 — Net-summary contract lacks income-only category assertion

- **Severity**: ℹ️ OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Success Criteria
- **Location**: transactions/tests.py:543, accounts/tests.py:85
- **Detail**: Net-per-category behavior is covered for mixed expense/income, but no explicit assertion exists for an income-only category case.
- **Fix**: Add one test asserting expected total for a category containing only positive amounts.
- **Decision**: FIXED
