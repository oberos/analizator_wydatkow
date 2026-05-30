# Style and Usability Refresh Implementation Plan

## Overview

Refresh the application's user interface across dashboard, authentication, categories, and transactions screens to deliver a consistent, cleaner, and easier-to-use experience. This plan keeps all existing business logic and data behavior intact while improving visual hierarchy, navigation clarity, and interaction consistency.

## Current State Analysis

- Core flows are working and deployed for auth, categories, and CSV import.
- Templates are functional but visually inconsistent and mostly unstyled.
- Styling is concentrated as inline CSS/JS on the transactions page.
- Global UI primitives (navigation, alerts, button system, shared spacing/typography) are not centralized.

## Desired End State

After this plan is complete, users can navigate the app through a consistent Bootstrap-based interface with shared layout/navigation, uniform feedback messages, standardized confirmation interactions, and improved readability across all existing screens.

Verification:
1. All existing flows (register/login/logout, category CRUD, CSV upload, delete actions) still work.
2. UI across pages follows one shared visual system and interaction pattern.
3. Transactions table remains readable on desktop and usable on mobile via horizontal scroll.

### Key Discoveries:

- `templates/base.html:1-19` is minimal and currently the natural centralization point for shared UI shell.
- `templates/transactions/transaction_list.html:11-77` contains most current styling debt (inline styles and inline JS).
- `templates/base.html:9-15` and `templates/transactions/transaction_list.html:41-49` duplicate message rendering patterns.
- `analizator_wydatkow/settings.py:135-143` already supports static assets via WhiteNoise, so local Bootstrap assets fit current deployment style.
- Existing category delete and transaction delete-all flows use different confirmation models (`templates/categories/category_confirm_delete.html`, `templates/transactions/transaction_list.html:16-20`).

## What We're NOT Doing

- No changes to models, migrations, CSV parser, categorization, or transaction persistence behavior.
- No new product capabilities (filtering, sorting logic, reporting logic, bulk edit) beyond UI/UX polish.
- No framework migration away from Django templates.
- No full accessibility audit/compliance project in this slice.
- No mobile-native redesign; mobile support is limited to practical responsive behavior for current pages.

## Implementation Approach

Use local Bootstrap assets served through Django staticfiles, then progressively refactor templates to shared layout/components from lowest-risk pages to highest-risk page (transactions). Keep endpoint contracts, form handling, and view logic unchanged. Validate each phase with automated checks and manual smoke gates.

## Critical Implementation Details

Message rendering must be single-source in `base.html`; page-level custom message blocks are removed to avoid diverging alert behavior.  
Destructive confirmations are standardized with one reusable modal pattern while preserving existing POST endpoints and CSRF handling.  
Transactions page refresh must preserve the existing semantic cues already relied on by users (`Unknown` badge distinction and negative amount emphasis).

## Phase 1: UI Foundation and Shared Shell

### Overview

Establish the shared styling and layout foundation used by all pages: local Bootstrap assets, app-level CSS/JS, global navbar, and one global message component.

### Changes Required:

#### 1. Static vendor and app UI assets

**File**: `accounts/static/vendor/bootstrap/bootstrap.min.css` (new), `accounts/static/vendor/bootstrap/bootstrap.bundle.min.js` (new), `accounts/static/app/ui.css` (new), `accounts/static/app/ui.js` (new)

**Intent**: Provide local Bootstrap resources and a small app-specific layer for project visual identity and reusable interaction helpers.

**Contract**: Local static asset paths are stable and loaded from templates using `{% static %}`; no external CDN dependency.

#### 2. Base template shell expansion

**File**: `templates/base.html`

**Intent**: Convert base template into a shared app shell with common head assets, navbar region, global message rendering, and content container.

**Contract**: Keep existing `{% block title %}` and `{% block content %}` contracts; add shared include points for navbar and messages.

#### 3. Shared UI partials

**File**: `templates/partials/_navbar.html` (new), `templates/partials/_messages.html` (new), `templates/partials/_confirm_destructive_modal.html` (new)

**Intent**: Centralize repeated markup and behavior for navigation, feedback alerts, and destructive confirmation modal.

**Contract**: Partials are include-safe from all existing pages and do not embed page-specific business logic.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`
- Server starts without template/static errors: `pdm run python manage.py runserver`

#### Manual Verification:

- Shared navbar appears on authenticated pages with links to Dashboard, Transactions, and Categories.
- Feedback messages render through one consistent global alert style.
- Base layout spacing/typography is consistent across at least dashboard + login + transactions.

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation from the human before proceeding to the next phase.

---

## Phase 2: Authentication and Dashboard Template Refresh

### Overview

Refresh auth and dashboard pages to the new shared visual system while preserving current auth flow behavior.

### Changes Required:

#### 1. Login/registration/logout template styling

**File**: `templates/registration/login.html`, `templates/registration/register.html`, `templates/registration/logged_out.html`

**Intent**: Apply consistent Bootstrap form/container styling and improve readability/action clarity on auth screens.

**Contract**: Existing form submission behavior and URL targets remain unchanged.

#### 2. Dashboard structure and actions

**File**: `templates/dashboard.html`

**Intent**: Align dashboard with shared shell and clear action hierarchy for navigating to key app flows.

**Contract**: Existing links to transactions/categories and logout action remain functionally identical.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`
- Server starts without template errors: `pdm run python manage.py runserver`

#### Manual Verification:

- Register -> login -> dashboard -> logout flow remains unchanged functionally.
- Auth pages and dashboard share consistent visual hierarchy (headings, spacing, form/button styles).
- Error/success feedback on auth pages uses global alert style from base layout.

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation from the human before proceeding to the next phase.

---

## Phase 3: Categories UX Refresh and Confirmation Standardization

### Overview

Refresh categories screens and standardize destructive-action experience to reusable Bootstrap modal confirmation patterns.

### Changes Required:

#### 1. Category list and form template modernization

**File**: `templates/categories/category_list.html`, `templates/categories/category_form.html`

**Intent**: Improve discoverability and readability of category actions with consistent layout, button hierarchy, and list/form presentation.

**Contract**: Existing create/edit URL contracts and form submission behavior remain unchanged.

#### 2. Delete confirmation flow standardization

**File**: `templates/categories/category_confirm_delete.html`, shared partial/modal assets in `templates/partials/` and `accounts/static/app/ui.js`

**Intent**: Align category delete interaction with the chosen modal confirmation pattern while preserving safe fallback behavior.

**Contract**: Destructive actions continue to use POST + CSRF; no delete-by-GET behavior is introduced.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`
- Server starts without template errors: `pdm run python manage.py runserver`

#### Manual Verification:

- Category list/create/edit/delete pages are visually consistent with auth/dashboard screens.
- Delete interaction follows the standardized modal confirmation UX.
- Category CRUD behavior remains unchanged end-to-end.

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation from the human before proceeding to the next phase.

---

## Phase 4: Transactions UX Refresh

### Overview

Refactor the transactions page from inline styling to shared components/classes while preserving CSV upload, duplicate handling, and delete-all behavior.

### Changes Required:

#### 1. Transactions layout and styling refactor

**File**: `templates/transactions/transaction_list.html`, `accounts/static/app/ui.css`

**Intent**: Replace inline styles with reusable Bootstrap/app classes and improve table readability and action grouping.

**Contract**: Preserve existing functional elements: upload control, transaction table columns, category display, and messages.

#### 2. Responsive table behavior

**File**: `templates/transactions/transaction_list.html`, `accounts/static/app/ui.css`

**Intent**: Keep table-based presentation with mobile usability through horizontal scroll and compact typography.

**Contract**: Desktop layout remains full-table; mobile uses scroll container rather than alternative card rendering.

#### 3. Confirmation and modal interaction alignment

**File**: `templates/transactions/transaction_list.html`, `accounts/static/app/ui.js`, shared modal partial(s)

**Intent**: Align upload and destructive action interaction patterns with shared modal conventions selected for this change.

**Contract**: Transaction upload/delete endpoints and CSRF behavior in `transactions/views.py` remain untouched.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`
- Server starts without template errors: `pdm run python manage.py runserver`

#### Manual Verification:

- Upload CSV modal opens and submits successfully.
- Delete-all action uses standardized confirmation UX and still deletes data correctly.
- `Unknown` category remains clearly distinguished from regular categories.
- Negative amounts remain visually emphasized and consistent.
- Transactions table is usable on one mobile viewport via horizontal scrolling.

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation from the human before proceeding to the next phase.

---

## Phase 5: Full Regression and UI Polish Pass

### Overview

Run end-to-end manual smoke coverage across all touched flows and apply final consistency polish fixes without changing feature scope.

### Changes Required:

#### 1. End-to-end UI regression sweep

**File**: Touched templates/static assets from phases 1-4

**Intent**: Validate that refreshed UI does not regress user-critical flows and interactions.

**Contract**: Full smoke includes auth, dashboard navigation, category CRUD, transaction upload/list/delete, and key responsive checks.

#### 2. Consistency and polish fixes

**File**: Touched templates/static assets from phases 1-4

**Intent**: Resolve inconsistencies discovered during regression (spacing, alerts, button hierarchy, modal wording) while staying in-scope.

**Contract**: No new business behaviors or route/model changes introduced in this pass.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Django checks pass: `pdm run python manage.py check`
- Existing automated test command passes: `pdm run python manage.py test`

#### Manual Verification:

- Desktop smoke pass: register/login/logout, dashboard navigation, categories CRUD, transactions upload/re-upload/delete-all.
- Mobile smoke pass (single viewport): key pages readable and actionable, especially transaction table actions.
- UI patterns are consistent across all app pages (navbar, alerts, buttons, forms, destructive confirmation interactions).

**Implementation Note**: After completing this phase and all automated verification passes, pause for manual confirmation from the human that manual testing is successful before closing the change.

---

## Testing Strategy

### Unit Tests:

- Keep existing backend unit test surface unchanged for this UI-focused slice.
- Add targeted template rendering tests only if needed to guard critical includes/blocks.

### Integration Tests:

- Use existing Django test command to ensure no framework-level regressions.
- Prioritize manual integration checks for modal interactions and workflow continuity.

### Manual Testing Steps:

1. Register new user -> login -> navigate to dashboard.
2. Navigate to categories, create/edit/delete category, verify confirmation UX.
3. Navigate to transactions, upload sample CSV, verify messages and table rendering.
4. Re-upload sample CSV and confirm duplicate-skip messaging still appears.
5. Delete all transactions and confirm destructive flow + resulting empty state.
6. Repeat key navigation/actions in one mobile viewport and verify practical usability.

## Performance Considerations

- UI changes must avoid adding heavyweight custom JavaScript beyond minimal interaction wiring.
- Keep static payload practical by using minified local Bootstrap assets and limited app custom CSS/JS.
- Preserve server-side query/load behavior in `transactions/views.py` and `categories/views.py`.

## Migration Notes

- No database migrations are expected for this change.
- Local static vendor assets become part of repository history and deployment artifact set.

## References

- Roadmap slice: `context/foundation/roadmap.md` (S-06)
- PRD: `context/foundation/prd.md` (US-01, FR-004, FR-009, FR-013, FR-014)
- Existing templates: `templates/base.html`, `templates/dashboard.html`, `templates/categories/*.html`, `templates/transactions/transaction_list.html`, `templates/registration/*.html`
- Existing views (behavior constraints): `accounts/views.py`, `categories/views.py`, `transactions/views.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: UI Foundation and Shared Shell

#### Automated

- [x] 1.1 Linting passes
- [x] 1.2 Django checks pass
- [x] 1.3 Server starts without template/static errors

#### Manual

- [x] 1.4 Shared navbar appears on authenticated pages
- [x] 1.5 Global messages render in one consistent style
- [x] 1.6 Base layout consistency verified on representative pages

### Phase 2: Authentication and Dashboard Template Refresh

#### Automated

- [ ] 2.1 Linting passes
- [ ] 2.2 Django checks pass
- [ ] 2.3 Server starts without template errors

#### Manual

- [ ] 2.4 Register login dashboard logout flow remains functional
- [ ] 2.5 Auth pages and dashboard match shared visual hierarchy
- [ ] 2.6 Auth feedback messages use global alert style

### Phase 3: Categories UX Refresh and Confirmation Standardization

#### Automated

- [ ] 3.1 Linting passes
- [ ] 3.2 Django checks pass
- [ ] 3.3 Server starts without template errors

#### Manual

- [ ] 3.4 Categories pages are visually consistent with refreshed app shell
- [ ] 3.5 Category delete uses standardized confirmation UX
- [ ] 3.6 Category CRUD behavior remains unchanged end-to-end

### Phase 4: Transactions UX Refresh

#### Automated

- [ ] 4.1 Linting passes
- [ ] 4.2 Django checks pass
- [ ] 4.3 Server starts without template errors

#### Manual

- [ ] 4.4 Upload CSV modal opens and submits successfully
- [ ] 4.5 Delete-all uses standardized confirmation and still deletes transactions
- [ ] 4.6 Unknown category remains visually distinct
- [ ] 4.7 Negative amounts remain clearly emphasized
- [ ] 4.8 Transactions table is usable on mobile via horizontal scroll

### Phase 5: Full Regression and UI Polish Pass

#### Automated

- [ ] 5.1 Linting passes
- [ ] 5.2 Django checks pass
- [ ] 5.3 Django test command passes

#### Manual

- [ ] 5.4 Full desktop smoke passes across auth categories and transactions
- [ ] 5.5 Mobile smoke passes for key pages and actions
- [ ] 5.6 Cross-page UI consistency confirmed for shared patterns
