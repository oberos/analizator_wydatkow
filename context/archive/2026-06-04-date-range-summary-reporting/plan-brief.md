# Date-range summary reporting — Plan Brief

> Full plan: `context/changes/date-range-summary-reporting/plan.md`

## What & Why

This change adds date-range filtering to dashboard category totals so reporting reflects the period the user actually wants to analyze. It implements the roadmap’s S-04 slice and FR-010/FR-011 behavior with a default rolling last-30-days window. The goal is decision-ready reporting without expanding into unrelated filtering features.

## Starting Point

Dashboard summary already exists and is user-scoped, but currently aggregates all-time transactions only. The summary pipeline is centralized (`accounts/views.py` → `transactions/summary.py` → `templates/dashboard.html`), which makes this enhancement incremental rather than architectural.

## Desired End State

Users can choose `start_date` and `end_date` on dashboard and see category totals/counts for that inclusive range. When no params are provided, the dashboard defaults to today-30d through today. Invalid ranges show a clear error, and empty ranges show an explicit “no transactions in selected range” state.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| Feature scope | Dashboard summary only | Keeps the slice aligned with S-04 and avoids mixing in transaction-list concerns. |
| Default behavior | Rolling last 30 days (inclusive) | Matches PRD/roadmap requirements and offers immediate useful signal on entry. |
| Date field semantics | Filter on `Transaction.date` only | Preserves current domain semantics and avoids booking-date ambiguity in MVP. |
| State persistence | GET query params | Makes selected range transparent, refresh-safe, and bookmarkable. |
| Invalid range handling | Validation error, no silent correction | Prevents hidden behavior and protects trust in totals. |
| Performance strategy | No cache/materialization | Current scale and architecture favor simple ORM aggregation with lower risk. |

## Scope

**In scope:**
- Date-range form and validation for dashboard filtering.
- Range-aware summary aggregation with inclusive bounds.
- Dashboard UI for range controls, errors, and range-empty state.
- Focused integration tests for defaults, boundaries, invalid input, and isolation.

**Out of scope:**
- Transaction-list date filtering.
- Budget-cycle presets/advanced range builders.
- Caching/materialized reporting layers.
- Pie chart/report visualization work.

## Architecture / Approach

Keep server-rendered Django flow. Parse/validate GET params in dashboard view, resolve defaults, pass normalized bounds to the existing summary helper, and render filtered results in dashboard template. Extend test coverage in `accounts/tests.py` and `transactions/tests.py` to lock behavior and boundary correctness.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Date-range input and dashboard wiring | Validated date-range inputs plus default-range resolution in dashboard flow | Incorrect validation path could produce misleading outputs |
| 2. Range-aware summary aggregation | Inclusive date filtering in summary helper while preserving user isolation/netting | Boundary mistakes could skew totals silently |
| 3. Dashboard range UX and empty/error states | Filter controls, URL-state persistence, and clear range-specific messaging | UX ambiguity may hide whether filtering is active |
| 4. Focused regression coverage for date-range behavior | Integration tests for defaults, invalid ranges, boundaries, and isolation | Gaps in coverage could allow future regression |

**Prerequisites:** S-02 data flow is implemented and dashboard summary baseline is already live.  
**Estimated effort:** ~2–3 sessions across 4 phases.

## Open Risks & Assumptions

- Assumes inclusive boundary semantics on `Transaction.date` are correct for MVP reporting expectations.
- Assumes no caching is needed at current data volume; revisit if dashboard latency regresses.
- Assumes summary-only filtering is sufficient until S-05 transaction-list slice is planned.

## Success Criteria (Summary)

- Dashboard shows correct category totals/counts for selected inclusive date ranges.
- Invalid ranges are rejected visibly without silent correction or fallback behavior.
- Existing user isolation and summary semantics remain intact after range support is added.
