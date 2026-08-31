<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: Add Subcategories

- **Plan**: `context/changes/add-subcategories/plan.md`
- **Scope**: Full plan — Phases 1–5 of 5
- **Date**: 2026-08-31
- **Verdict**: REJECTED at review time (1 critical) → all findings triaged, critical fixed
- **Findings**: 1 critical, 5 warnings, 4 observations
- **Diff reviewed**: `0ba3738..HEAD` (20 files, +1570/−125)

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | PASS |
| Scope Discipline | PASS |
| Safety & Quality | FAIL (F1) |
| Architecture | PASS |
| Pattern Consistency | WARNING |
| Success Criteria | PASS |

All six "What We're NOT Doing" guardrails were respected. Cross-user isolation was
independently verified as clean across every new queryset. All success-criteria commands
were re-run by the reviewer, not taken on trust.

## Findings

### F1 — CSV import returns 500 for any user with a subcategory named "Unknown"

- **Severity**: ❌ CRITICAL
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `transactions/views.py:126` (`TransactionUploadView.form_valid`)
- **Detail**: Phase 1 replaced `unique_together = ("name","user")` with two `UniqueConstraint`s,
  deliberately allowing a subcategory to reuse a top-level name. That silently invalidated the
  unscoped `Category.objects.get_or_create(user=..., name="Unknown")`, which then matches two rows
  and raises `MultipleObjectsReturned`. Only `CSVParseError` is caught, so this surfaces as a 500 on
  every CSV upload. Confirmed end-to-end with a real windows-1250 ING fixture. No test caught it
  because all fixtures use only the seeded top-level "Unknown".
- **Fix**: Add `parent=None` to the `get_or_create` lookup.
  - Strength: Restores the uniqueness the call always assumed; one-line, no behaviour change otherwise.
  - Tradeoff: None — a subcategory named "Unknown" was never a valid fallback target.
  - Confidence: HIGH — deliberate-break verified.
  - Blind spot: None significant; a repo-wide grep confirmed this was the only unscoped production lookup.
- **Decision**: FIXED — `parent=None` added; `UnknownCategoryLookupRegressionTests` (2 tests) added and
  deliberate-break verified (both fail with `MultipleObjectsReturned` without the fix).

### F2 — Non-ASCII digits in `?category=` crash the transaction list

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `transactions/views.py` (`_get_selected_category`)
- **Detail**: The guard used `str.isdigit()`, which returns True for Unicode `No`-category digits.
  `"²".isdigit()` is True but `int("²")` raises `ValueError` → confirmed 500 on `?category=²`. An
  overlong digit string also raises via Python's integer-conversion digit cap.
- **Fix**: Replace the guard with `_is_primary_key()` requiring `isascii() and isdigit()` plus a
  19-digit cap.
- **Decision**: FIXED — helper added; two regression tests cover `²`, `٣`, and a 5000-digit value
  (all yield an empty result set with HTTP 200).

### F3 — Zero-spend allocations render detached, misattributing subcategories

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: `budgets/summary.py:113-115`
- **Detail**: `display_order` was built from `flatten_category_summary(actual_summary)`, which only
  contains categories that *have* spending. An allocated-but-unspent category fell to the
  `len(display_order)` bucket and sorted to the bottom by name, while `budget_detail.html:34` still
  rendered it indented with `↳` — visually asserting it is a child of whatever unrelated row precedes
  it. Probe confirmed `↳ Groceries` (a child of Food) rendering under `Beauty`. Totals stayed correct;
  the displayed hierarchy did not.
- **Fix A ⭐ Recommended**: Build `display_order` from the user's full category tree.
  - Strength: Fixes every ordering case at the source; sort no longer depends on which categories
    happened to have transactions.
  - Tradeoff: One extra category query per budget page.
  - Confidence: HIGH — reuses the existing `group_categories_by_parent` ordering helper.
  - Blind spot: Whether a test pinned the old bottom placement (checked — none did).
- **Fix B**: Fall back to `display_order[parent_id] + 0.5`.
  - Strength: No extra query; contained edit to the sort key.
  - Tradeoff: Still wrong when the parent also has zero spending; fragile float-index scheme.
  - Confidence: MEDIUM — handles the common case only.
  - Blind spot: Two zero-spend children under one parent would tie.
- **Decision**: FIXED via Fix A — `_category_display_order()` added, reusing
  `group_categories_by_parent`. Regression test
  `test_zero_spend_subcategory_still_sorts_directly_under_its_parent` added and deliberate-break
  verified (`AssertionError: 2 != 1` without the fix).

### F4 — Migration 0005 is not safely reversible

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: `categories/migrations/0005_category_parent.py`
- **Detail**: Reversing restores `unique_together = ("name","user")`, which raises `IntegrityError` on
  any database where a subcategory reuses a top-level name; `RemoveField(parent)` then silently drops
  the whole hierarchy. The forward direction is purely additive and safe.
- **Fix**: Add a module docstring marking the migration forward-only and naming both reverse hazards.
- **Decision**: FIXED — docstring added.

### F5 — `unique_together` → `UniqueConstraint` swap lacks an adaptation note

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: `context/changes/add-subcategories/plan.md` Phase 1 §2; `categories/models.py:36-47`
- **Detail**: The plan specified `unique_together = ("name","user","parent")`; the implementation used
  two explicit `UniqueConstraint`s instead. The deviation was correct — the planned composite tuple
  would *not* have prevented duplicate top-level names, since `parent` is NULL for all of them and
  NULL is distinct per row. But it is the change that caused F1, and four other deviations in this
  plan carry "Adapted during implementation" notes while this one did not.
- **Fix**: Add a Phase 1 §2 adaptation note recording the swap, its rationale, and the F1 fallout.
- **Decision**: FIXED — note added, including the migration renumbering to `0005_`.

### F6 — `_get_validation_exclusions()` overrides a private Django API

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Pattern Consistency
- **Location**: `categories/forms.py:88-95`
- **Detail**: The override is necessary — `user` is injected in `__init__` rather than posted, so
  without it the uniqueness constraints are skipped at form level and raise an uncaught
  `ValidationError` from `save()`. But the leading underscore means no cross-version stability
  guarantee.
- **Fix**: Docstring the Django-version coupling and what to re-check on upgrade.
- **Decision**: FIXED — docstring added noting verification against Django 6.0 and that the form
  validation tests fail loudly if the private API changes.

### F7 — No `assertNumQueries` pin on the summary rollup

- **Severity**: 📋 OBSERVATION
- **Impact**: 🏃 LOW
- **Dimension**: Safety & Quality
- **Location**: `transactions/summary.py`
- **Detail**: The rollup was verified by probe to be 1 aggregation + 1 category query (no N+1), but
  nothing pins that; a future change could reintroduce per-category queries unnoticed.
- **Decision**: ACCEPTED — no user-visible defect today.

### F8 — Unused `select_related("parent")`

- **Severity**: 📋 OBSERVATION
- **Impact**: 🏃 LOW
- **Dimension**: Pattern Consistency
- **Detail**: A `select_related("parent")` is applied on a queryset whose consumers never traverse
  `.parent`. Harmless, marginally wasteful.
- **Decision**: ACCEPTED.

### F9 — `order_by("parent__name")` NULL-ordering differs across backends

- **Severity**: 📋 OBSERVATION
- **Impact**: 🏃 LOW
- **Dimension**: Safety & Quality
- **Detail**: SQLite sorts NULLs first, PostgreSQL last by default. Affects only the relative
  placement of childless rows in one dropdown; grouping is rebuilt in Python afterwards, so the
  rendered result is unaffected.
- **Decision**: ACCEPTED.

### F10 — Delete warning omits transaction/mapping consequences

- **Severity**: 📋 OBSERVATION
- **Impact**: 🏃 LOW
- **Dimension**: Safety & Quality
- **Location**: `templates/categories/category_confirm_delete.html`
- **Detail**: The confirmation names the subcategories that will cascade but not that affected
  transactions have their `category_id` set to NULL. Actual behaviour was browser-verified in Phase 5
  and is correct — only the copy is incomplete.
- **Decision**: ACCEPTED.

## Post-triage verification

All gates re-run after the fixes:

| Gate | Result |
|------|--------|
| `pdm run python manage.py test` | 134 tests OK (was 129; +5 regression tests) |
| `pdm run ruff check .` | All checks passed |
| `pdm run ruff format --check .` | 75 files already formatted |
| `pdm run basedpyright` | 0 errors, 0 warnings, 0 notes |
| `pdm run python manage.py makemigrations --check --dry-run` | No changes detected |

Both F1 and F3 fixes were confirmed by deliberate-break check: the new regression tests fail with the
fix reverted and pass with it restored.
