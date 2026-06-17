# Move chart palette to categories model — Plan Brief

> Full plan: `context/changes/move-chart-pallete-to-categories-model/plan.md`

## What & Why

This change moves dashboard chart palette ownership from `accounts/views.py` into the categories domain, with colors persisted on `Category` rows. The goal is to eliminate drift between category lifecycle and chart rendering by making color a first-class domain invariant instead of view-local constants.

## Starting Point

Chart colors are currently hardcoded in `accounts/views.py`, while categories are created in multiple domain/runtime paths (`categories/signals.py`, `transactions/signals.py`, `transactions/views.py`). Dashboard already depends on summary rows from `transactions/summary.py`, so extending that contract is the natural integration seam.

## Desired End State

All persisted categories have a deterministic hex color, existing rows are backfilled by migration, and new categories always get color automatically. Dashboard chart colors come from summary-provided `category_color`, with synthetic `Uncategorized` still supported via deterministic fallback. User-visible chart behavior and summary math remain unchanged.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| Palette ownership | Persist color on `Category` DB field | Aligns source-of-truth with category lifecycle and removes view drift risk. |
| Backfill strategy | Deterministic name-based map + hashed fallback | Covers predefined, legacy, and custom names without manual cleanup. |
| `Uncategorized` handling | Keep synthetic fallback | Preserves current semantics without introducing fake persisted rows. |
| Runtime invariant | Auto-fill missing color on create paths | Ensures no null-color categories from signal/import fallback flows. |
| Dashboard contract | Extend summary with `category_color` | Keeps chart data single-path and avoids extra view-layer lookups. |
| Test depth | Targeted + flow coverage | Adds confidence at migration/runtime/dashboard boundaries without over-scoping. |

## Scope

**In scope:**
- Add `Category.color` with validation and migration backfill.
- Ensure seeded/runtime-created categories always receive color.
- Extend summary output with `category_color`.
- Remove view-local palette logic and assert color parity in tests.

**Out of scope:**
- Manual color editing UI.
- Chart interaction/visual redesign.
- Aggregation math changes.
- Historical migration rewrites beyond new forward migrations.

## Architecture / Approach

Introduce a categories-domain color resolver reused by model/migration/runtime paths. Migrate in stages (nullable field → backfill → non-null). Extend `get_user_category_summary` to include `category_color`, then make dashboard payload consume that value directly. This preserves current rendering flow while relocating ownership to the correct domain boundary.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Persist category colors with deterministic backfill | New `Category.color` field + complete backfill for existing rows | Migration ordering/backfill mistakes could leave null/invalid colors |
| 2. Enforce color invariants on runtime creation paths | Signals/import fallback always create color-complete categories | Missing one creation path could reintroduce null colors |
| 3. Switch dashboard to summary-provided colors and lock regressions | View no longer owns palette; tests enforce color contract | Contract drift between summary rows and chart payload |

**Prerequisites:** Existing dashboard pie-chart implementation is already stable and archived.  
**Estimated effort:** ~2–3 sessions across 3 phases.

## Open Risks & Assumptions

- Assumes hex colors should remain deterministic by category name (no manual override UI in this change).
- Assumes additive summary contract (`category_color`) won’t break downstream consumers.
- Assumes legacy category names will be handled by deterministic fallback, not curated mapping.

## Success Criteria (Summary)

- Every category row has a valid non-null color after migration and runtime creation.
- Dashboard chart colors are sourced from summary contract, not view-local constants.
- Existing reporting behavior remains intact with added color-parity regression coverage.
