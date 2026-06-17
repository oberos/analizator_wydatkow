# Dashboard Pie Chart Summary — Plan Brief

> Full plan: `context/changes/dashboard-pie-chart-summary/plan.md`

## What & Why

This change adds an optional pie chart to the dashboard, generated from the same category summary totals users already trust. It improves scanability of spending composition without changing reporting semantics. The key constraint is preserving table/chart parity so visualization never conflicts with canonical totals.

## Starting Point

The dashboard already supports date-range summary reporting, with server-side aggregation and strong integration coverage for scope, net totals, and boundary behavior. There is no chart library or chart payload contract yet, and current UI is table-only.

## Desired End State

Users can see a read-only pie chart for the selected date range when there is positive spending data to visualize. Unknown and Uncategorized categories are included as normal slices; non-positive categories are excluded from the pie with a clear explanatory note. If chart rendering fails, dashboard summary table remains fully functional and a non-blocking hint communicates chart unavailability.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
| --- | --- | --- |
| Feature scope | Read-only chart from existing summary rows | Delivers FR-015 with minimal risk and no new business logic path. |
| Rendering strategy | Chart.js via template CDN | Fits existing server-rendered + CDN script pattern used in dashboard today. |
| Empty-range behavior | Hide chart and keep existing range-empty messaging | Avoids misleading visuals while preserving current UX expectations. |
| Unknown handling | Keep Unknown and Uncategorized as regular slices | Maintains parity with table semantics and transparency of unassigned spending. |
| Non-positive totals | Exclude from pie and show explanatory note | Preserves valid pie semantics while making exclusion explicit. |
| Visual stability | Deterministic order and category-name-based color mapping | Improves readability and regression confidence across refreshes/ranges. |
| Verification depth | Integration tests + one manual browser check | Matches project’s current test stack without introducing out-of-scope E2E infrastructure work. |
| Failure mode | Graceful non-blocking fallback to table-only mode | Protects core reporting reliability when chart JS/CDN fails. |

## Scope

**In scope:**
- View-layer chart payload derived from current dashboard summary rows.
- Dashboard template pie chart rendering and conditional states.
- Deterministic slice ordering and stable category color mapping.
- Focused tests for parity, edge cases, and fallback behavior.

**Out of scope:**
- Interactive chart behavior (drill-down/click filtering).
- New frontend bundling/tooling pipeline.
- Changes to summary aggregation math or data model.
- Broad visual snapshot or full E2E framework rollout.

## Architecture / Approach

Keep the existing server-rendered flow: `dashboard_view` resolves date range and summary, then derives chart payload from those same summary rows. Template conditionally renders a Chart.js pie in `extra_js`. Table remains canonical output; chart is an optional visualization layer that can fail independently without degrading core reporting.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| --- | --- | --- |
| 1. Dashboard chart data contract | Deterministic chart payload from current summary context | Drift risk if payload is computed from a separate logic path |
| 2. Dashboard pie chart rendering and UX states | Optional chart UI with empty/non-positive/fallback behavior | Misleading visuals or brittle script behavior |
| 3. Regression hardening for parity and edge cases | Focused tests locking parity and failure branches | Incomplete coverage could let chart/table divergence regressions slip |

**Prerequisites:** S-04 date-range summary reporting is already implemented and stable.  
**Estimated effort:** ~2–3 sessions across 3 phases.

## Open Risks & Assumptions

- Assumes CDN-based Chart.js availability is acceptable for this MVP slice.
- Assumes positive-spending-only pie visualization is acceptable when table contains zero/negative categories.
- Assumes category cardinality remains moderate enough for readable pie slices.

## Success Criteria (Summary)

- Dashboard pie chart appears for eligible ranges and matches table totals for represented categories.
- Empty/no-positive ranges and chart-load failures are handled without breaking summary table usability.
- Existing user isolation, date-range behavior, and summary correctness remain unchanged.
