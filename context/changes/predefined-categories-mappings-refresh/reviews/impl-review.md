<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Predefined Categories and Mappings Refresh Implementation Plan

- **Plan**: `context/changes/predefined-categories-mappings-refresh/plan.md`
- **Scope**: Full plan (Phases 1-4)
- **Date**: 2026-06-01
- **Verdict**: NEEDS ATTENTION
- **Findings**: 0 critical, 3 warnings, 1 observation

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | WARNING |
| Scope Discipline | WARNING |
| Safety & Quality | WARNING |
| Architecture | WARNING |
| Pattern Consistency | PASS |
| Success Criteria | PASS |

## Findings

### F1 — Unplanned scope bundled into phase commit

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Scope Discipline
- **Location**: agents.md, context/foundation/roadmap.md, context/foundation/archive/2026-06-01-roadmap.md
- **Detail**: Phase 4 included unrelated documentation/process paths via broad staging, outside planned implementation files.
- **Fix A ⭐ Recommended**: Move unrelated doc/process edits into separate change/commit and keep feature phases scoped.
  - Strength: Restores plan-to-commit traceability for future reviews.
  - Tradeoff: Requires extra coordination and separate commits.
  - Confidence: HIGH — follows existing phase discipline in this repo.
  - Blind spot: Already-merged scope cannot be fully unbundled retroactively.
- **Fix B**: Accept wider scope and amend plan/change docs with explicit addendum.
  - Strength: Fast and transparent for already-landed work.
  - Tradeoff: Weakens strict scope boundaries.
  - Confidence: MEDIUM — documents reality but does not undo history.
  - Blind spot: Does not prevent recurrence without process rule.
- **Decision**: FIXED + ACCEPTED-AS-RULE: Keep phase commits scoped to planned files

### F2 — Historical migration modified with divergent taxonomy risk

- **Severity**: ⚠️ WARNING
- **Impact**: 🔬 HIGH — architectural stakes; think carefully before deciding
- **Dimension**: Architecture
- **Location**: categories/migrations/0002_seed_predefined_categories.py:5-12,21-25
- **Detail**: Legacy migration change in this implementation path increased drift risk vs canonical runtime taxonomy.
- **Fix A ⭐ Recommended**: Revert legacy migration edit and keep alignment in forward paths only.
  - Strength: Preserves migration-history stability.
  - Tradeoff: Historical migration remains legacy-shaped by design.
  - Confidence: HIGH — standard migration hygiene.
  - Blind spot: Mixed-history environments still need explicit policy.
- **Decision**: FIXED via Fix A

### F3 — Registration provisioning can fail mid-flow on contract mismatch

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: transactions/signals.py:22-27
- **Detail**: Signal raised `ValueError` on missing categories during user creation, risking partial provisioning.
- **Fix**: Reconcile missing categories (`get_or_create`) before mapping seed instead of raising.
  - Strength: Keeps onboarding robust and deterministic.
  - Tradeoff: Slightly more logic in signal path.
  - Confidence: HIGH — behavior covered by transactions tests.
  - Blind spot: No explicit DB transaction wrapper across both signals.
- **Decision**: FIXED

### F4 — Phase 4 planned-file drift (tests-only validation path)

- **Severity**: 👀 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: transactions/views.py, templates/transactions/transaction_list.html
- **Detail**: Phase 4 intent listed these files, but acceptance was satisfied via regression tests without direct edits.
- **Fix**: Document tests-only validation path in change record.
- **Decision**: FIXED

