# Categorization reliability — Plan Brief

> Full plan: `context/changes/testing-categorization-reliability/plan.md`  
> Research: `context/changes/testing-categorization-reliability/research.md`

## What & Why

This plan delivers Phase 2 of the rollout for risk #3: categorization reliability.  
We are strengthening regression protection so a manual correction reliably influences future auto-categorization for matching merchant patterns, and so mapping collisions do not silently degrade categorization quality.

## Starting Point

The correction-learning path already exists end-to-end (`set_category` → `apply_category_correction` → mapping sync → future import categorization), and baseline tests cover happy-path learning and reset.  
The missing piece is stronger contract coverage for normalized merchant variants and overlap/precedence edge behavior.

## Desired End State

After completion, the suite will explicitly protect deterministic correction-learning for equivalent merchant variants and include a guardrail for overlapping mapping keys.  
The cookbook will also contain concrete guidance for future categorization-rule tests, so new tests follow the same risk-first pattern.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| --- | --- | --- | --- |
| Scope breadth | Test-only rollout in `transactions/tests.py` | Fastest high-signal path with least risk of unrelated side effects. | Plan |
| Primary risk focus | Normalized-variant determinism first | This is the highest-impact uncovered regression path for risk #3. | Plan |
| Correction boundary depth | Validate through HTTP + import flow | Confirms real user-visible behavior without brittle fault-injection. | Plan |
| Overlap behavior coverage | Add one explicit precedence guardrail test | Protects against subtle matching regressions during refactors. | Plan |
| Manual gate depth | Two concise UI checks | Keeps human verification focused and repeatable per phase. | Plan |
| Assertion style | Business-outcome assertions only | Matches test-plan anti-pattern rule against implementation-mirror tests. | Research |

## Scope

**In scope:**
- New integration contract tests for correction-learning determinism across merchant variants.
- One explicit overlap/precedence guardrail test.
- Cookbook update in `test-plan.md` §6.5 and rollout-state synchronization.

**Out of scope:**
- Production logic changes unless tests prove a contract mismatch.
- Risk areas outside #3 (CSV integrity, ownership abuse, summary totals, cycle boundaries).
- Helper refactors and e2e infrastructure work.

## Architecture / Approach

Use existing correction and import integration flow as the verification spine: trigger category correction through endpoint, then validate future import outcome for targeted merchant scenarios. Keep tests outcome-driven (categorized result + mapping state) rather than asserting normalization/regex internals.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Deterministic correction-learning contracts | Variant-based learning regression tests | False confidence from happy-path-only coverage |
| 2. Mapping precedence guardrail | Explicit overlap/precedence contract test | Silent behavior drift in matching resolution |
| 3. Cookbook and phase close-out | §6.5 cookbook backfill + synchronized rollout state | Orchestration drift and future inconsistency |

**Prerequisites:** Existing `research.md` for this change and current Phase 2 rollout status in `test-plan.md`.  
**Estimated effort:** ~2-3 sessions across 3 phases.

## Open Risks & Assumptions

- Assumes current production categorization behavior is correct and gaps are mainly in test coverage.
- Overlap scenario is represented by one guardrail test; additional variants may be needed if new mapping groups are introduced.

## Success Criteria (Summary)

- Correction of merchant variant A consistently affects future import categorization of equivalent variant B.
- Overlapping mapping behavior remains stable under regression tests.
- `test-plan.md` cookbook/state artifacts reflect delivered Phase 2 patterns without drift.
