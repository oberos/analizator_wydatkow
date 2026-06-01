# Predefined Categories and Mappings Refresh Implementation Plan

## Overview

Refresh predefined category taxonomy and merchant mappings so new-user CSV imports achieve higher first-pass categorization quality. The plan keeps classification safety (`Unknown` fallback) and intentionally limits rollout to new-user seeding paths.

## Current State Analysis

Predefined category and mapping definitions currently diverge across runtime and migration paths, which creates taxonomy drift and inconsistent categorization behavior. Matching logic is already safety-oriented, but mapping coverage and category alignment need expansion to support broader merchant variants.

## Desired End State

Newly registered users receive the expanded default category taxonomy and an aligned predefined mapping set that uses those category names consistently. Auto-categorization keeps strict safety behavior (exact + boundary-safe fallback; unresolved merchants stay `Unknown`) while improving first-pass hit-rate for common real-world merchant strings.

Verification is complete when automated tests cover taxonomy/mapping consistency and representative merchant fixtures, and manual checks confirm expected category assignment behavior for new users.

### Key Discoveries:

- Runtime category taxonomy (`categories/signals.py:9-16`) differs from migration taxonomy (`categories/migrations/0002_seed_predefined_categories.py:6-12`), which is a direct drift source.
- Predefined mapping seeds in migration still use `Entertainment` (`transactions/migrations/0003_seed_predefined_mappings.py:42-51`) while runtime mapping signals assume `Restaurants` (`transactions/signals.py:14-24`).
- Import fallback depends on `Unknown` category (`transactions/views.py:61-62`), so removing or renaming `Unknown` would break safe categorization fallback.
- Matching behavior is already based on exact + token-safe fallback (`transactions/categorization.py:17-31`, `transactions/categorization.py:75-77`), so mapping quality and fixture coverage are the primary improvement levers.

## What We're NOT Doing

- No existing-user backfill migration for categories/mappings in this change.
- No new transaction recategorization API/UI workflow.
- No fuzzy matching or ML-based categorization strategy changes.
- No reporting redesign outside taxonomy/mapping consistency impacts.

## Implementation Approach

Define one canonical runtime taxonomy and mapping contract, then align new-user seeding and predefined mapping datasets to it. Preserve `Unknown` as a required fallback category, expand merchant fixtures for new taxonomy coverage, and lock behavior with targeted automated tests plus manual import checks.

## Critical Implementation Details

`transactions.signals.create_predefined_mappings` depends on categories already existing for the same user (`transactions/signals.py:36-44`), so category taxonomy and mapping taxonomy must be updated in coordinated order; otherwise mappings silently skip missing categories.

The user-selected rollout is signals-only for new users. This means plan verification must explicitly confirm expected behavior for both newly created users (updated taxonomy) and existing users (unchanged defaults) to avoid rollout confusion.

## Phase 1: Canonical Taxonomy Contract

### Overview

Establish the expanded default category taxonomy and make runtime category seeding use it consistently, while preserving `Unknown` fallback behavior.

### Changes Required:

#### 1. Runtime default category definition alignment

**File**: `categories/signals.py`

**Intent**: Replace legacy default category list with the agreed taxonomy so newly registered users receive the new category set.

**Contract**: Runtime defaults include `Finance`, `Bills`, `Food and Household Chemicals`, `Transportation`, `Savings`, `Health`, `Beauty`, `Clothing and Footwear`, `Sports`, `Restaurants`, `Recreation`, `Home`, and preserve `Unknown` as required system fallback.

#### 2. Mapping taxonomy contract alignment

**File**: `transactions/mappings/__init__.py`

**Intent**: Ensure mapping category group exports align with the canonical category names used by runtime seeding.

**Contract**: Exported predefined mapping groups map only to category names from the canonical runtime taxonomy.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`
- Category seed tests for new users pass: `pdm run python manage.py test categories.tests`

#### Manual Verification:

- Registering a new user creates the expanded default category list.
- `Unknown` category still exists and remains available as fallback.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 2: New-User Mapping Seed Alignment

### Overview

Align predefined merchant-to-category seeding paths with the new taxonomy for newly registered users.

### Changes Required:

#### 1. Runtime mapping seeding update

**File**: `transactions/signals.py`

**Intent**: Update runtime predefined mapping seed logic to use the expanded taxonomy categories and prevent skipped mappings from category-name mismatches.

**Contract**: Every predefined mapping category name resolves against the canonical runtime categories for the same user; unresolved category names are treated as contract failures in tests.

#### 2. Predefined mapping dataset update

**File**: `transactions/mappings/*.py`

**Intent**: Expand and rebalance merchant lists to cover the new taxonomy while preserving safe defaults for uncertain merchants.

**Contract**: Mapping datasets remain plain deterministic merchant keys grouped by canonical category; no fuzzy scoring or probabilistic rules are introduced.

### Success Criteria:

#### Automated Verification:

- Mapping seed consistency tests pass: `pdm run python manage.py test transactions.tests`
- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`

#### Manual Verification:

- New user registration seeds mappings without missing-category skips.
- Representative merchants from each new category group classify to expected category on import.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 3: Matching Safety and Coverage Refresh

### Overview

Keep boundary-safe matching behavior and refresh fixture coverage to improve classification hit-rate without increasing false positives.

### Changes Required:

#### 1. Matching behavior guardrails

**File**: `transactions/categorization.py`

**Intent**: Preserve layered exact + token-boundary fallback behavior while validating compatibility with expanded mapping datasets.

**Contract**: Matching remains deterministic and boundary-safe; unresolved merchants still return `None` for fallback to `Unknown`.

#### 2. Merchant fixture and edge-case coverage

**File**: `transactions/tests.py`, `test.py`

**Intent**: Add representative fixtures for new categories and known edge merchants (including punctuation/location variants) so behavior stays stable.

**Contract**: Tests assert both positive matches and negative safeguards (similar-looking merchants that must not be falsely categorized).

### Success Criteria:

#### Automated Verification:

- Categorization behavior tests pass: `pdm run python manage.py test transactions.tests`
- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`

#### Manual Verification:

- Provided problematic merchants (e.g., `FHU "AGA"-LEWIATAN ...`) resolve to expected category.
- Non-mapped merchants still fall back to `Unknown` instead of forced classification.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Phase 4: Regression Gate and Rollout Validation

### Overview

Run full regression for import/categorization flows and confirm rollout constraints (new users updated, existing users unchanged) are respected.

### Changes Required:

#### 1. End-to-end regression pass

**File**: `transactions/views.py`, `transactions/tests.py`, `templates/transactions/transaction_list.html`

**Intent**: Validate that taxonomy/mapping updates improve categorization outcomes without breaking import behavior, duplicate handling, or delete-all flows.

**Contract**: Existing transaction import and safety behavior stay unchanged apart from intended category mapping improvements.

#### 2. Rollout-scope validation

**File**: `categories/signals.py`, `transactions/signals.py`

**Intent**: Confirm user-selected rollout policy is implemented exactly: signals-only for new users, no existing-user backfill.

**Contract**: Existing users are not implicitly migrated in this change; new users consistently receive updated defaults.

### Success Criteria:

#### Automated Verification:

- Full Django tests pass: `pdm run python manage.py test`
- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`

#### Manual Verification:

- New-user journey: register → upload CSV → expected categories are assigned for mapped merchants.
- Existing-user account behavior remains unchanged unless manually recategorized outside this scope.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase. Phase blocks use plain bullets — the corresponding `- [ ]` checkboxes for these items live in the `## Progress` section at the bottom of the plan.

---

## Testing Strategy

### Unit Tests:

- Category seeding tests for new-user default taxonomy.
- Mapping dataset consistency tests (all mapping categories exist in runtime defaults).
- Matching behavior tests for exact, boundary-safe fallback, and non-match guardrails.

### Integration Tests:

- New user registration followed by CSV import verifies seeded mappings are active.
- Import flow still handles duplicates, fallback to `Unknown`, and delete-all behavior correctly.

### Manual Testing Steps:

1. Register a new user and verify new default categories are present.
2. Upload representative CSV transactions covering new taxonomy categories.
3. Confirm problematic known merchants classify as expected.
4. Confirm unknown merchants remain `Unknown`.
5. Validate an existing user account is not backfilled automatically.

## Performance Considerations

- Keep matching deterministic and boundary-safe; avoid fuzzy matching to limit false positives and unpredictable runtime costs.
- Mapping list growth should remain manageable through grouped constants and targeted tests rather than dynamic runtime scoring.

## Migration Notes

- No existing-user backfill migration is included in this change (explicitly out of scope by decision).
- Legacy migrations remain historical snapshots; this change focuses on runtime seeding and categorization behavior for newly registered users.

## References

- Roadmap: `context/foundation/roadmap.md` (S-07)
- PRD: `context/foundation/prd.md` (US-01, FR-004, FR-006)
- Category seeds: `categories/signals.py:9-31`
- Legacy category migration: `categories/migrations/0002_seed_predefined_categories.py:6-12`
- Mapping seeds (runtime): `transactions/signals.py:12-55`
- Mapping seeds (legacy migration): `transactions/migrations/0003_seed_predefined_mappings.py:8-90`
- Matching logic: `transactions/categorization.py:17-77`
- Unknown fallback usage: `transactions/views.py:61-62`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Canonical Taxonomy Contract

#### Automated

- [x] 1.1 Linting passes
- [x] 1.2 Django checks pass
- [x] 1.3 Category seed tests for new users pass

#### Manual

- [x] 1.4 New user registration creates the expanded default category list
- [x] 1.5 Unknown category remains available as fallback

### Phase 2: New-User Mapping Seed Alignment

#### Automated

- [ ] 2.1 Mapping seed consistency tests pass
- [ ] 2.2 Linting passes
- [ ] 2.3 Django checks pass

#### Manual

- [ ] 2.4 New user registration seeds mappings without missing-category skips
- [ ] 2.5 Representative merchants from each new category group classify as expected

### Phase 3: Matching Safety and Coverage Refresh

#### Automated

- [ ] 3.1 Categorization behavior tests pass
- [ ] 3.2 Linting passes
- [ ] 3.3 Django checks pass

#### Manual

- [ ] 3.4 Known problematic merchants classify as expected
- [ ] 3.5 Non-mapped merchants still fall back to Unknown

### Phase 4: Regression Gate and Rollout Validation

#### Automated

- [ ] 4.1 Full Django tests pass
- [ ] 4.2 Linting passes
- [ ] 4.3 Django checks pass

#### Manual

- [ ] 4.4 New-user register-upload journey reflects updated taxonomy and mappings
- [ ] 4.5 Existing-user account behavior remains unchanged by this rollout
