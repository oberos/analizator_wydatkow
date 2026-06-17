# Move chart palette to categories model Implementation Plan

## Overview

Persist chart colors on `Category` rows and move dashboard color selection to a domain-owned contract so color behavior is deterministic across seeding, runtime category creation, and dashboard rendering.

## Current State Analysis

Dashboard chart colors are currently computed in `accounts/views.py` from hardcoded constants, while category creation and lifecycle live in the `categories` and `transactions` apps. This split creates drift risk: category taxonomy and creation are domain-level, but chart color source-of-truth is view-local. Summary rows are already the dashboard data contract, so extending them with color is the cleanest integration point.

## Desired End State

Each persisted category has a deterministic hex color, existing rows are backfilled via migration, and new categories created by any path (signals/import fallback) always receive a color. Dashboard no longer owns palette constants; it renders `chart_colors` from summary-provided `category_color` values. Synthetic `Uncategorized` remains supported with a deterministic fallback color.

### Key Discoveries:

- View-local palette currently lives in `accounts/views.py:17` and is applied during chart payload build in `accounts/views.py:69`.
- Category taxonomy source is already domain-level in `categories/signals.py:9`, while runtime missing-category creation happens in `transactions/signals.py:23` and `transactions/views.py:120`.
- Summary is the existing dashboard contract in `transactions/summary.py:24` and can be safely extended additively with `category_color`.
- Prior chart review explicitly flagged color mapping drift risk and pushed mapping server-side (`context/archive/2026-06-17-dashboard-pie-chart-summary/reviews/impl-review.md:33`).

## What We're NOT Doing

- No chart UX redesign, interactions, or Chart.js behavior changes.
- No category-management UI for manually choosing/editing colors in this change.
- No changes to transaction aggregation math or date-range semantics.
- No refactor of historical migrations beyond required new color migrations.

## Implementation Approach

Add a persisted `Category.color` field and centralize deterministic color generation in a categories-domain helper reused by model/runtime paths and migrations. Backfill existing categories with predefined-category colors and deterministic hashed fallback for custom/legacy names. Extend summary rows with `category_color`, then simplify dashboard chart payload generation to consume that contract.

## Critical Implementation Details

### Timing & lifecycle

Use a staged migration sequence: add nullable `color`, run data backfill, then enforce non-null. Backfill migration must run after `transactions.0002_seed_unknown_category` so seeded `Unknown` rows are included.

### Performance constraints

Do not add extra dashboard lookups for colors. Extend the existing summary query to include `category_color` so chart payload stays single-path and query-local.

## Phase 1: Persist category colors with deterministic backfill

### Overview

Introduce `Category.color` as persisted data and make existing rows color-complete with deterministic rules.

### Changes Required:

#### 1. Category model color field and domain helper

**File**: `categories/models.py`  
**File**: `categories/colors.py` (new)

**Intent**: Move palette ownership into categories domain and make color generation reusable across model, migration, and runtime creation paths.

**Contract**: `Category` gains a validated hex `color` field; categories domain exposes deterministic color resolution for predefined names and hashed fallback for unknown/custom names.

#### 2. Schema + data migration chain

**File**: `categories/migrations/0003_*.py` (new)  
**File**: `categories/migrations/0004_*.py` (new)

**Intent**: Safely roll forward existing databases without leaving null/missing colors.

**Contract**: First migration adds nullable color; second migration backfills all rows using domain mapping/fallback (including legacy names), then enforces non-null.

### Success Criteria:

#### Automated Verification:

- Category migrations apply cleanly on current data: `$env:DEBUG="True" ; pdm run python manage.py migrate`
- Category seeding invariants still pass after field addition: `$env:DEBUG="True" ; pdm run python manage.py test categories.tests.PredefinedCategorySeedingTests`
- Type and lint checks pass after model/migration updates: `pdm run basedpyright` and `pdm run ruff check .`

#### Manual Verification:

- Existing users’ categories show non-empty valid hex colors after migration.
- Legacy/custom category names receive deterministic fallback colors (stable across repeated runs).

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that manual testing was successful before proceeding to the next phase.

---

## Phase 2: Enforce color invariants on runtime category creation paths

### Overview

Ensure every code path that creates categories assigns color automatically and consistently.

### Changes Required:

#### 1. Signal-driven category creation paths

**File**: `categories/signals.py`  
**File**: `transactions/signals.py`

**Intent**: Keep registration/mapping bootstrapping paths color-complete without requiring post-fixes.

**Contract**: Bulk and `get_or_create` category creation paths set `color` deterministically from categories-domain helper.

#### 2. Transaction upload fallback path

**File**: `transactions/views.py`

**Intent**: Preserve import UX while guaranteeing `Unknown` creation also satisfies color invariant.

**Contract**: `Unknown` category fallback creation includes color default so no null-color categories can be created during upload.

### Success Criteria:

#### Automated Verification:

- Transaction import/mapping tests pass with color invariant changes: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests.ImportFlowAndRolloutTests transactions.tests.PredefinedMappingSeedTests`
- Category and transaction auth/ownership tests remain green: `$env:DEBUG="True" ; pdm run python manage.py test categories.tests transactions.tests.TransactionCategoryCorrectionTests`

#### Manual Verification:

- Registering a new user creates predefined categories with colors.
- Import flow that creates/fetches `Unknown` continues to work and produces colored category rows.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that manual testing was successful before proceeding to the next phase.

---

## Phase 3: Switch dashboard to summary-provided colors and lock regressions

### Overview

Remove view-local palette logic and make dashboard chart consume color from summary contract, with targeted regression coverage.

### Changes Required:

#### 1. Summary contract extension

**File**: `transactions/summary.py`

**Intent**: Provide chart-ready color data via existing summary contract to avoid extra dashboard lookups and drift.

**Contract**: Summary rows include `category_color`, preserving current totals/count semantics and synthetic `Uncategorized` handling.

#### 2. Dashboard payload simplification

**File**: `accounts/views.py`

**Intent**: Eliminate chart palette ownership from views and consume summary-provided color values.

**Contract**: Dashboard payload builder uses `category_color` from summary rows for `chart_colors`; local palette constants/helper are removed.

#### 3. Regression coverage for color contract

**File**: `accounts/tests.py`  
**File**: `transactions/tests.py`  
**File**: `categories/tests.py`

**Intent**: Prevent regressions in color parity across DB, summary, and dashboard rendering paths.

**Contract**: Tests assert summary exposes color, dashboard chart colors align with summary rows, and seeded/runtime-created categories are color-complete.

### Success Criteria:

#### Automated Verification:

- Dashboard summary tests pass with explicit chart-color assertions: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests.DashboardSummaryTests`
- Summary and category tests pass with new color contract: `$env:DEBUG="True" ; pdm run python manage.py test transactions.tests.TransactionSummaryTests categories.tests`
- Full suite and quality gates pass: `$env:DEBUG="True" ; pdm run python manage.py test`, `pdm run basedpyright`, `pdm run ruff check .`

#### Manual Verification:

- Dashboard pie chart colors remain stable across reloads for the same selected date range.
- Table/chart parity remains intact while using summary-provided colors.

**Implementation Note**: After completing this phase, all automated verification passes, and manual testing is successful, the change is complete.

---

## Testing Strategy

### Unit Tests:

- Categories-domain color resolver returns fixed colors for predefined names.
- Deterministic fallback produces stable hex for unknown/custom names.

### Integration Tests:

- Migration + runtime creation paths guarantee non-null `Category.color`.
- Summary rows include `category_color` while preserving amount/count behavior.
- Dashboard `chart_colors` derives from summary contract and stays aligned with chart labels/values.

### Manual Testing Steps:

1. Run migrations on local data and inspect category rows for valid non-null colors.
2. Create a new user and verify predefined categories are created with colors.
3. Upload CSV with uncategorized rows and verify `Unknown` remains functional and color-complete.
4. Open dashboard with chart-renderable range and verify color stability + table/chart parity.

## Performance Considerations

- Keep summary query single-path by adding color projection directly in aggregation output.
- Avoid per-row color lookups in `dashboard_view`; chart payload should remain in-memory transformation of summary rows.

## Migration Notes

- Requires new `categories` migrations for schema + backfill + non-null enforcement.
- Backfill must account for historical names (`Groceries`, `Transport`, `Entertainment`) and custom names via deterministic fallback.

## References

- Palette currently in view layer: `accounts/views.py:17`
- Dashboard chart payload contract: `accounts/views.py:69`
- Summary query source: `transactions/summary.py:24`
- Category seeding source: `categories/signals.py:9`
- Runtime missing-category creation: `transactions/signals.py:23`, `transactions/views.py:120`
- Prior implementation review note: `context/archive/2026-06-17-dashboard-pie-chart-summary/reviews/impl-review.md:33`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Persist category colors with deterministic backfill

#### Automated

- [x] 1.1 Category migrations apply cleanly on current data — a643690
- [x] 1.2 Category seeding invariants still pass after field addition — a643690
- [x] 1.3 Type and lint checks pass after model/migration updates — a643690

#### Manual

- [x] 1.4 Existing users’ categories show non-empty valid hex colors after migration
- [x] 1.5 Legacy/custom category names receive deterministic fallback colors

### Phase 2: Enforce color invariants on runtime category creation paths

#### Automated

- [x] 2.1 Transaction import and mapping tests pass with color invariant changes — 3a5bf41
- [x] 2.2 Category and transaction auth/ownership tests remain green — 3a5bf41

#### Manual

- [x] 2.3 New-user predefined categories are created with colors
- [x] 2.4 Import flow keeps Unknown functional and color-complete

### Phase 3: Switch dashboard to summary-provided colors and lock regressions

#### Automated

- [x] 3.1 Dashboard summary tests pass with explicit chart-color assertions
- [x] 3.2 Summary and category tests pass with new color contract
- [x] 3.3 Full suite and quality gates pass

#### Manual

- [x] 3.4 Dashboard pie chart colors remain stable across reloads for the same range
- [x] 3.5 Table/chart parity remains intact while using summary-provided colors
