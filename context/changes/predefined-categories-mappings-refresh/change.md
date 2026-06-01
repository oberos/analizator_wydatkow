# Change: predefined-categories-mappings-refresh

- **Status**: impl_reviewed
- **Created**: 2026-06-01
- **Updated**: 2026-06-01
- **Roadmap ref**: S-07
- **PRD refs**: US-01, FR-004, FR-006

## Summary

Improve predefined category taxonomy and merchant mapping quality for new users so CSV imports classify more transactions correctly on first pass while preserving safe fallback to `Unknown`.

## Key Decisions

| Decision | Choice |
|----------|--------|
| Scope | Predefined categories + predefined mappings + matching safety + tests |
| Rollout | Signals-only for new users (no existing-user backfill migration) |
| Fallback behavior | Keep `Unknown` fallback unchanged |
| Matching strategy | Layered exact + token-boundary fallback (longest key first) |
| Taxonomy | Expand to Finance, Bills, Food and Household Chemicals, Transportation, Savings, Health, Beauty, Clothing and Footwear, Sports, Restaurants, Recreation, Home |

## Scope Addendum

- Phase 4 commit included roadmap and agent-doc updates via a broad staging decision.
- These paths are treated as process/documentation updates and should be isolated from feature-phase commits in future runs.

## Phase 4 Validation Note

- Phase 4 acceptance criteria were satisfied through full regression and integration coverage in `transactions/tests.py`, without direct source edits in `transactions/views.py` or `templates/transactions/transaction_list.html`.
