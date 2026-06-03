---
date: 2026-06-03T19:21:17+02:00
researcher: GitHub Copilot
git_commit: 2c2d232f958ebfae82606ef3ac9f9041cd59b691
branch: master
repository: oberos/analizator_wydatkow
topic: "testing-categorization-reliability"
tags: [research, codebase, transactions, categorization, merchant-mapping]
status: complete
last_updated: 2026-06-03
last_updated_by: GitHub Copilot
---

# Research: testing-categorization-reliability

**Date**: 2026-06-03T19:21:17+02:00  
**Researcher**: GitHub Copilot  
**Git Commit**: 2c2d232f958ebfae82606ef3ac9f9041cd59b691  
**Branch**: master  
**Repository**: oberos/analizator_wydatkow

## Research Question

How to ground Phase 2 rollout (`Categorization reliability`) for risk #3 so integration + contract fixture tests prove that manual corrections deterministically affect future categorization for matching merchants, without implementation-mirror assertions.

## Summary

Risk #3 is implemented through a clear correction-learning chain: manual category correction calls `apply_category_correction`, which updates the transaction and synchronizes a normalized merchant mapping via `update_or_create`; later imports categorize by normalized exact match first, then token-boundary prefix matching. Existing tests already cover the happy path for "learned mapping applies on future import" and "reset to Unknown removes mapping", but they do not yet deeply challenge mapping correctness edges (variant normalization, precedence conflicts, and false-positive assumptions).

Phase 2 should therefore target contract-level outcomes across two boundaries: (1) correction write-back to `MerchantCategoryMapping`, and (2) future import categorization behavior for semantically equivalent merchant variants.

## Detailed Findings

### Categorization and matching engine

- Categorization executes exact normalized match first, then regex token-boundary fallback ([transactions/categorization.py:90-116](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/categorization.py#L90-L116)).
- Prefix fallback sorts mapping keys by descending length before matching, so "longer key wins" in ambiguous cases ([transactions/categorization.py:18-25](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/categorization.py#L18-L25)).
- Normalization strips company/location/store-number suffixes and can collapse multiple merchant spellings into one normalized key ([transactions/categorization.py:28-87](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/categorization.py#L28-L87)).

### Correction-learning write boundary

- Manual correction endpoint validates user-scoped form data and runs correction in a transaction ([transactions/views.py:121-144](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/views.py#L121-L144)).
- `apply_category_correction` updates transaction category and synchronizes mapping for the normalized merchant ([transactions/refinement.py:42-62](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/refinement.py#L42-L62)).
- Mapping sync removes mapping on `None`/`Unknown` and otherwise upserts with `update_or_create` ([transactions/refinement.py:12-39](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/refinement.py#L12-L39)).
- Model uniqueness enforces one mapping per `(user, normalized_merchant)`, making correction deterministic at key level ([transactions/models.py:37-56](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/models.py#L37-L56)).

### Existing regression coverage and current gaps

- Existing integration test confirms corrected category is applied on next import for same merchant key ([transactions/tests.py:417-437](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/tests.py#L417-L437)).
- Existing test confirms resetting to Unknown prevents future auto-categorization ([transactions/tests.py:439-463](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/tests.py#L439-L463)).
- Existing matching tests validate punctuation variants and basic false-positive cases, but they are not centered on correction-learned mappings ([transactions/tests.py:64-99](https://github.com/oberos/analizator_wydatkow/blob/2c2d232f958ebfae82606ef3ac9f9041cd59b691/transactions/tests.py#L64-L99)).
- Main Phase 2 gap: no contract test proving that correction of one merchant spelling deterministically applies to normalized variants in later imports.

## Code References

- `transactions/categorization.py:13-25` - Prefix/token-boundary matching logic and ordering.
- `transactions/categorization.py:28-87` - Merchant normalization rules.
- `transactions/categorization.py:90-116` - Category lookup contract (exact first, fallback second).
- `transactions/refinement.py:12-39` - Mapping removal/upsert behavior.
- `transactions/refinement.py:42-62` - Correction service boundary.
- `transactions/views.py:121-144` - HTTP correction entrypoint and transaction boundary.
- `transactions/models.py:37-56` - Mapping uniqueness model contract.
- `transactions/tests.py:417-463` - Existing correction-learning and reset tests.
- `transactions/tests.py:64-99` - Existing matching contract tests (punctuation/false positives/cache).
- `context/foundation/test-plan.md:51-70` - Risk #3 protection contract and Phase 2 rollout row.

## Architecture Insights

- Categorization behavior is intentionally data-driven via persisted merchant mappings, not hardwired in views.
- Determinism is anchored by normalized merchant keys + per-user uniqueness.
- Correction and import are separated boundaries: correction writes model state; import consumes model state through categorization engine.
- Best regression signal comes from end-to-end contract assertions on import outcomes, not from reproducing regex/normalization internals in test logic.

## Historical Context (from prior changes)

- Test-plan defines Risk #3 contract explicitly: prove correction-to-learning determinism and challenge "mapping hit == correctness" assumptions (`context/foundation/test-plan.md:55`, `context/foundation/test-plan.md:69`).
- Prior rollout review documented orchestration drift risk (stale rollout status), reinforcing strict artifact/status synchronization (`context/changes/testing-critical-path-data-correctness/reviews/impl-review.md:23-31`).
- Prior phase plan enforced strict in-scope discipline per rollout risk set, which applies here as well (`context/changes/testing-critical-path-data-correctness/plan.md:29-34`).

## Related Research

- `context/changes/testing-critical-path-data-correctness/research.md`

## Open Questions

- Should Phase 2 contract explicitly require normalized-variant equivalence tests (same semantic merchant, different raw format)?
- Should contract fixtures include a precedence scenario where overlapping mapping keys compete, to prevent accidental behavior changes in fallback ordering?
