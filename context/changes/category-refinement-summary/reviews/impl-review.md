<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Category Refinement and Summary

- **Plan**: `context/changes/category-refinement-summary/plan.md`
- **Scope**: Phases 1-4 of 4
- **Date**: 2026-06-02
- **Verdict**: NEEDS ATTENTION
- **Findings**: 0 critical, 4 warnings, 0 observations

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | WARNING |
| Scope Discipline | PASS |
| Safety & Quality | WARNING |
| Architecture | PASS |
| Pattern Consistency | WARNING |
| Success Criteria | PASS |

## Findings

### F1 - Service-level ownership invariants not enforced

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW - quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `transactions/refinement.py:41-55`
- **Detail**: `apply_category_correction()` does not assert transaction/category ownership at service layer; current view path is safe, but invariant is not encoded in service.
- **Fix**: Add explicit ownership validation in service before save/mapping sync; reject mismatches.
- **Decision**: FIXED

### F2 - Summary computes absolute net, not true spend

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM - real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: `transactions/summary.py:17-23`
- **Detail**: `Abs(Sum("amount"))` reports absolute of net category amount, which can underreport spend when refunds/inflows exist in same category.
- **Fix A ⭐ Recommended**: Sum only expense rows as positive spend (e.g., `Case/When` on negative amounts).
  - Strength: Matches FR-009 spending semantics.
  - Tradeoff: Slightly more complex aggregation.
  - Confidence: HIGH - fits current negative-expense data convention.
  - Blind spot: Separate income metric may still be needed later.
- **Fix B**: Keep net logic and relabel metric to "Net amount".
  - Strength: Minimal code change.
  - Tradeoff: Conflicts with "spending totals" expectation.
  - Confidence: MEDIUM - technically valid, potentially product-misaligned.
  - Blind spot: User expectation for label semantics not validated.
- **Decision**: FIXED (Fix A)

### F3 - Missing explicit dashboard empty-state test from plan contract

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW - quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: `accounts/tests.py:18-84` (expected by plan contract at `plan.md:230`)
- **Detail**: Dashboard summary/isolation tests exist, but no explicit zero-transactions empty-state assertion.
- **Fix**: Add a dedicated dashboard empty-state test asserting empty summary and fallback text.
- **Decision**: SKIPPED

### F4 - No single integrated upload->refine->summary acceptance test

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM - real tradeoff; pause to reason through it
- **Dimension**: Plan Adherence
- **Location**: `transactions/tests.py:114-131,339-385`; `accounts/tests.py:54-84` (expected by plan contract at `plan.md:238-239`)
- **Detail**: Flow is covered in pieces, but no one test chains upload, correction, and dashboard summary validation end-to-end.
- **Fix**: Add one integration test method that performs full US-01 path in sequence.
- **Decision**: SKIPPED
