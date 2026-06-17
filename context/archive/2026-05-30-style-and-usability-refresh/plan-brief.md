# Style and Usability Refresh - Plan Brief

> Full plan: `context/changes/style-and-usability-refresh/plan.md`

## What & Why

We are refreshing the app's UI to make the existing budgeting workflows feel cleaner, more consistent, and easier to use. Core functionality is already working, but the interface quality is currently the main user-facing gap. This plan focuses on visual and interaction consistency without changing business behavior.

## Starting Point

The app has working auth, category management, and CSV import flows, but templates are mostly minimally styled and inconsistent. `base.html` is very thin, while transactions currently rely on extensive inline styles and duplicated message handling.

## Desired End State

Users can move through auth, dashboard, categories, and transactions screens in one coherent Bootstrap-based experience. Shared navigation, alerts, and confirmation interactions behave consistently, and the transactions table remains practical on mobile through horizontal scroll. All existing flows continue to work as before.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
|----------|--------|------------------|
| Scope | Whole app templates including auth pages | The user asked for full UI improvement, and cross-page consistency needs full-surface coverage. |
| Styling base | Local Bootstrap assets via Django staticfiles | Fits current WhiteNoise/static setup while avoiding runtime CDN dependency. |
| Navigation | Shared top navbar in base template | Centralizes orientation and removes repeated page-level link patterns. |
| Feedback messages | Single global messages component in base | Removes current duplication and enforces one alert language/style. |
| Destructive confirmations | Standardize on custom Bootstrap modals | Provides one interaction model instead of mixed confirm page/browser confirm behavior. |
| Transactions mobile behavior | Keep table layout with horizontal scroll | Preserves existing desktop data density with low-risk mobile usability improvement. |
| Accessibility target | Minimal baseline for this slice | Keeps this change scoped to visual polish while preserving basic semantics. |
| Verification strategy | Full manual smoke on desktop + one mobile viewport | Needed because this change is cross-template and interaction-heavy. |

## Scope

**In scope:**
- Shared UI shell (base layout, navbar, messages, confirmation modal partials)
- Styling refresh for auth, dashboard, categories, and transactions templates
- Standardized destructive-action UX for touched pages
- Mobile usability improvement for transactions table

**Out of scope:**
- Model/view/business-logic changes
- New product capabilities (filtering logic, reports logic, bulk edit logic)
- Full accessibility compliance initiative
- Framework migration away from Django templates

## Architecture / Approach

Introduce local Bootstrap + app-level CSS/JS as a shared foundation, then refactor templates phase-by-phase from low-risk screens to high-risk transactions UI. Reusable partials in `templates/partials/` will centralize navbar/messages/confirm modal, while existing URLs, views, forms, and data behaviors remain unchanged.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|------|-------------------|----------|
| 1. UI Foundation and Shared Shell | Local Bootstrap assets, base shell, navbar/messages/modal partials | Breaking base template contracts across pages |
| 2. Authentication and Dashboard Refresh | Consistent auth + dashboard layout/forms/actions | Regressing auth flow UX or message visibility |
| 3. Categories UX Refresh | Modernized categories screens + standardized confirmation UX | Destructive-action regression if modal wiring is wrong |
| 4. Transactions UX Refresh | Reworked transactions UI without inline styling, mobile table usability | Regressing upload/delete interaction and visual semantics |
| 5. Full Regression and Polish | Cross-flow desktop/mobile smoke + consistency pass | Late-found regressions across many touched templates |

**Prerequisites:** S-02 completed (already done); current auth/categories/transactions behavior remains source of truth.
**Estimated effort:** ~3-4 implementation sessions across 5 phases.

## Open Risks & Assumptions

- Assumes local Bootstrap asset vendoring is acceptable for repository and deployment workflow.
- Confirmation standardization via modal may expose edge-case interaction bugs in JS-disabled scenarios.
- Scope creep risk is high in UI polish work; plan must stay anchored to existing flows.

## Success Criteria (Summary)

- Existing user workflows remain fully functional end-to-end after UI refresh.
- Shared UI patterns (navigation, alerts, buttons, forms, confirmations) are consistent across all app pages.
- Transactions view is both cleaner on desktop and practically usable on mobile.
