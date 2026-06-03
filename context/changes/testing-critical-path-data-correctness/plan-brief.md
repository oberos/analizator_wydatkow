# Critical-path data correctness — Plan Brief

> Full plan: `context/changes/testing-critical-path-data-correctness/plan.md`
> Research: `context/changes/testing-critical-path-data-correctness/research.md`

## What & Why

We are delivering Phase 1 of the test rollout for critical data correctness risks: account isolation, CSV import integrity, and summary correctness. The code already implements core protections, but coverage gaps remain at risk-heavy edges (foreign URL access, malformed CSV paths, and summary contract semantics). This plan closes those gaps with test-first changes and only allows minimal production refactor when tests prove contract mismatch.

## Starting Point

Current implementation already enforces user scoping in key query paths and ownership checks in service logic, with partial regression coverage in `transactions/tests.py` and `accounts/tests.py`. CSV import uses strict parsing and duplicate skipping, and summary currently treats totals as expense-only.

## Desired End State

After this plan, critical-path behaviors are explicitly protected by regression tests for risks #1, #2, and #4 from `test-plan.md`. Foreign-resource access/update attempts are denied, malformed CSV content does not silently persist partial bad data, and dashboard/category totals follow the approved summary contract. The phase is complete only after targeted tests and final full-suite gates are green.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|---|---|---|---|
| Phase scope | Cover only risks #1, #2, #4 | Keeps rollout aligned with approved Phase 1 boundaries and avoids phase drift | Research |
| Foreign category URL behavior | Enforce 404-style denial | Minimizes resource enumeration and matches queryset-scoped CBV pattern | Plan |
| Malformed CSV handling | Fail whole import on first malformed data row | Preserves strongest data integrity guarantee and simple rollback semantics | Plan |
| Verification strategy | Targeted tests per phase + full suite at end | Balances fast iteration with final high-confidence regression gate | Plan |
| Summary contract | Count all transactions; category totals use expenses minus income | Captures explicit business rule and allows targeted refactor only if tests show mismatch | Plan |

## Scope

**In scope:**
- Add/extend tests in `transactions/tests.py`, `categories/tests.py`, and `accounts/tests.py` for Phase 1 risks.
- Conditionally adjust `transactions/summary.py` if new summary contract tests fail.
- Final gate execution (ruff/check/full test suite) and Phase 1 cookbook backfill in `test-plan.md`.

**Out of scope:**
- Risks outside Phase 1 (#3, #5, #6 rollout rows).
- New ingestion formats, API redesigns, or broad UI changes.
- CI pipeline redesign beyond existing command gates.

## Architecture / Approach

Use a test-first, risk-mapped approach: each risk is translated into concrete regression assertions at the nearest cost-effective layer (integration/service). Existing code paths remain the baseline; only proven contract mismatches trigger minimal production changes.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|---|---|---|
| 1. Ownership isolation coverage | Explicit denial tests for foreign-resource access/update paths | Hidden IDOR-style URL path not covered by tests |
| 2. CSV integrity coverage | Malformed/mixed CSV edge tests and duplicate integrity assertions | Silent integrity regressions in parsing/import boundaries |
| 3. Summary correctness contract | Net-per-category summary assertions with scoped conditional refactor | Contract ambiguity between current logic and approved behavior |
| 4. Final verification and rollout handoff | Final lint/check/full-suite gates and cookbook backfill | Regressions outside targeted modules |

**Prerequisites:** `research.md` complete, `test-plan.md` Phase 1 scope fixed, Django test environment runnable via `pdm`.
**Estimated effort:** ~2-3 sessions across 4 phases.

## Open Risks & Assumptions

- Changing summary semantics (expenses minus income) may require query adjustments and dashboard expectation updates.
- URL-denial response shape can vary by Django CBV behavior; tests must enforce contract without overfitting irrelevant internals.
- Existing lessons file has placeholder rules; scope discipline must be enforced manually in this change.

## Success Criteria (Summary)

- Phase 1 risk coverage is implemented with automated regression tests for ownership isolation, import integrity, and summary correctness.
- Targeted phase checks and final full-suite gates pass with no cross-account data leakage regressions.
- Test-plan Phase 1 cookbook placeholders are updated to reflect shipped testing patterns.
