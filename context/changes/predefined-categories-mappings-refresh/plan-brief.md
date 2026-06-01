# Predefined Categories and Mappings Refresh — Plan Brief

> Full plan: `context/changes/predefined-categories-mappings-refresh/plan.md`

## What & Why

We are improving default category taxonomy and predefined merchant mappings so new users get better first-pass auto-categorization after CSV import. The current setup has runtime/migration taxonomy drift and uneven merchant coverage, which causes avoidable `Unknown` results or inconsistent category assignments. This change focuses on accuracy and consistency while keeping safe fallback behavior.

## Starting Point

Category names and mapping categories are currently split across signals, migrations, and mapping lists, and they do not fully agree (for example, `Restaurants` vs `Entertainment`). Matching is already boundary-safe and deterministic, so the highest-leverage delta is taxonomy/mapping alignment and better fixtures.

## Desired End State

A newly registered user receives the expanded agreed default categories and aligned predefined mappings using those names consistently. Merchant variants from real imports classify correctly more often without increasing false positives. Any non-confident merchant still falls back to `Unknown`.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| Scope | Categories + mappings + matching safety + tests | Solves your reported failures directly without expanding into new recategorization UX/API work. |
| Rollout policy | Signals-only for new users; no existing-user backfill | Keeps rollout lower-risk and incremental per your explicit preference. |
| Fallback behavior | Keep `Unknown` unchanged | Preserves current safety contract and avoids silent misclassification. |
| Matching model | Exact + token-boundary fallback (longest-key first) | Improves recall for merchant variants while preserving precision guardrails. |
| Taxonomy | Expand defaults to 12 user categories plus required `Unknown` fallback | Aligns naming with your requested category set and supports broader mapping coverage. |

## Scope

**In scope:**
- Canonical runtime default category taxonomy update.
- Mapping dataset refresh aligned to new taxonomy.
- New-user seeding alignment for categories and mappings.
- Targeted automated regression tests for mapping/matching behavior.

**Out of scope:**
- Existing-user backfill migrations.
- New recategorization endpoint/UI workflow.
- Fuzzy/ML categorization strategies.

## Architecture / Approach

Use one runtime taxonomy contract for category seeding and mapping grouping, then align `transactions.signals` and mapping modules to that contract. Keep the existing deterministic categorization flow and validate expanded merchant fixtures through targeted tests and import smoke checks.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Canonical taxonomy contract | New default category contract and runtime alignment | Naming mismatch can break downstream mapping resolution. |
| 2. New-user mapping seed alignment | Updated mapping seeding with taxonomy consistency | Missing category references can silently skip mappings. |
| 3. Matching safety and coverage refresh | Better merchant coverage with guarded matching behavior | Over-broad mappings can increase false positives. |
| 4. Regression gate and rollout validation | End-to-end confidence and rollout-scope verification | Scope drift into existing-user migration or UX changes. |

**Prerequisites:** Existing auth/category/import flows are operational (already implemented in F-01/S-01/S-02).
**Estimated effort:** ~2-3 sessions across 4 phases.

## Open Risks & Assumptions

- Signals-only rollout means existing users do not automatically receive new defaults.
- Taxonomy expansion assumes reports tolerate renamed/re-grouped categories for new users.
- Mapping growth must stay precision-safe; accuracy cannot come from forced categorization.

## Success Criteria (Summary)

- New users receive the expanded default category taxonomy and aligned predefined mappings.
- Reported problematic merchant variants map to expected categories in automated and manual checks.
- Unknown fallback behavior remains intact for unresolved merchants.
