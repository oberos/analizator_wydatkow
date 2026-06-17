# Local static assets restoration implementation plan

## Overview

Fix missing local CSS/JS by restoring correct Django static URL generation in local development, while preserving current Render production behavior.

## Current State Analysis

The app loads CSS/JS via `{% static %}` in the base template, but local requests resolve to `/app/...` and `/vendor/...` instead of `/static/app/...` and `/static/vendor/...`, causing 404s. Production behavior should remain unchanged.

## Desired End State

When running locally, dashboard and auth pages load Bootstrap and app UI assets from `/static/...` paths without 404s. Render deployment behavior remains unchanged.

### Key Discoveries:

- Base template loads static assets via Django static tag: `templates/base.html:8-9`, `templates/base.html:21-22`.
- Local static URL generation currently resolves to broken paths (validated via shell output for `static('app/ui.css')` and `static('vendor/bootstrap/bootstrap.min.css')`).
- Static config currently sets `STATIC_URL = "static/"` and DEBUG storage override to `FileSystemStorage`: `analizator_wydatkow/settings.py:135-149`.
- URLConf does not add explicit debug static routes, relying on staticfiles behavior: `analizator_wydatkow/urls.py:23-30`.
- Static assets exist at expected app paths: `accounts/static/app/ui.css`, `accounts/static/app/ui.js`, `accounts/static/vendor/bootstrap/*`.

## What We're NOT Doing

- No changes to production Render runtime configuration.
- No CDN fallback behavior for missing local assets.
- No frontend asset pipeline refactor.
- No redesign of dashboard summary logic or UI semantics.

## Implementation Approach

Use a dedicated local settings module for local-only static behavior, wire local commands to that module, and add targeted tests that assert generated static URLs include the `/static/` prefix. Keep static failures visible and document a deterministic local recovery command.

## Phase 1: Introduce dedicated local settings module

### Overview

Create explicit local-only Django settings entrypoint so local static behavior can diverge safely from production defaults.

### Changes Required:

#### 1. Add local settings module

**File**: `analizator_wydatkow/settings_local.py`

**Intent**: Create a local-only settings module that imports base settings and overrides static-related behavior needed for local development.

**Contract**: Module exports full Django settings and sets local static configuration so `django.templatetags.static.static(...)` resolves URLs under `/static/`.

#### 2. Route local management commands to local settings

**File**: `manage.py`

**Intent**: Ensure local run/test commands can use the local settings module without impacting production deployment entrypoints.

**Contract**: Local command path resolves `DJANGO_SETTINGS_MODULE` to `analizator_wydatkow.settings_local` for local workflow, while still allowing explicit override via environment variable.

### Success Criteria:

#### Automated Verification:

- Django checks pass with local settings module: `$env:DEBUG="True" ; $env:DJANGO_SETTINGS_MODULE="analizator_wydatkow.settings_local" ; pdm run python manage.py check`
- Static URL helper returns `/static/...` prefixed URLs under local settings: `$env:DEBUG="True" ; $env:DJANGO_SETTINGS_MODULE="analizator_wydatkow.settings_local" ; pdm run python manage.py shell -c "from django.templatetags.static import static; print(static('app/ui.css')); print(static('vendor/bootstrap/bootstrap.min.css'))"`

#### Manual Verification:

- Visiting `/` in local dev loads CSS/JS with no 404 entries for `/app/*` or `/vendor/*` in server log.
- Page styling appears correctly on dashboard/login pages.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Add regression tests for static path generation

### Overview

Add focused automated coverage so future settings changes cannot silently regress local static URL generation.

### Changes Required:

#### 1. Add settings-level regression tests

**File**: `accounts/tests.py` (or new focused settings test module if project convention prefers)

**Intent**: Verify local settings produce `/static/...` URLs for app and vendor assets.

**Contract**: Tests assert generated static URLs include `/static/` prefix and do not regress to `/app/...` or `/vendor/...` root paths.

#### 2. Keep existing summary tests behavior-safe

**File**: `accounts/tests.py`

**Intent**: Ensure static settings test additions do not alter existing dashboard summary and chart assertions.

**Contract**: Existing `DashboardSummaryTests` continue to pass unchanged.

### Success Criteria:

#### Automated Verification:

- Targeted account tests pass including new static URL assertions: `$env:DEBUG="True" ; pdm run python manage.py test accounts.tests`
- Full project test suite still passes: `$env:DEBUG="True" ; pdm run python manage.py test`
- Lint and type-check pass: `pdm run ruff check .` and `pdm run basedpyright`

#### Manual Verification:

- Local dashboard reload still shows expected summary table and chart behavior after settings/test changes.
- Login page and dashboard both load Bootstrap styling locally.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Document local recovery and run command path

### Overview

Document local static behavior and one deterministic recovery command when static assets fail.

### Changes Required:

#### 1. Update developer command guidance

**File**: `agents.md` (and other local-run command docs if duplicated)

**Intent**: Make local run/test commands explicitly compatible with the local settings module and static behavior.

**Contract**: Documentation includes canonical local command(s) and one recovery command for static issues (e.g., local collectstatic/clean workflow).

#### 2. Add concise static troubleshooting note

**File**: `agents.md` (or nearest existing troubleshooting section)

**Intent**: Keep static failures visible while giving developers a deterministic remediation step.

**Contract**: Note explains expected static path shape (`/static/...`) and recovery command, without introducing silent fallback logic.

### Success Criteria:

#### Automated Verification:

- Documentation-referenced local command executes successfully: `$env:DEBUG="True" ; $env:DJANGO_SETTINGS_MODULE="analizator_wydatkow.settings_local" ; pdm run python manage.py runserver --help`
- Django checks still pass after docs-aligned command path: `$env:DEBUG="True" ; $env:DJANGO_SETTINGS_MODULE="analizator_wydatkow.settings_local" ; pdm run python manage.py check`

#### Manual Verification:

- Developer can follow docs commands and load styled local UI without additional implicit steps.
- Recovery command reproduces and resolves static mismatch scenario when applied.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Settings-level static URL generation assertions for app and vendor assets.
- Negative assertion that generated paths are not rooted at `/app/` or `/vendor/`.

### Integration Tests:

- Existing `accounts.tests.DashboardSummaryTests` remains green as regression guard for dashboard rendering path.

### Manual Testing Steps:

1. Run local server with documented local settings command.
2. Open dashboard and login pages; confirm styles/scripts are applied.
3. Confirm dev server logs do not show 404s for `/app/ui.css`, `/app/ui.js`, `/vendor/bootstrap/*`.

## Performance Considerations

No performance-sensitive code paths are changed; this is settings and test coverage work only.

## Migration Notes

- No database migration required.
- No data backfill required.

## References

- Static asset usage: `templates/base.html:8-9`, `templates/base.html:21-22`
- Static settings configuration: `analizator_wydatkow/settings.py:135-149`
- URL routing baseline: `analizator_wydatkow/urls.py:23-30`
- Existing static assets: `accounts/static/app/ui.css`, `accounts/static/app/ui.js`, `accounts/static/vendor/bootstrap/bootstrap.min.css`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Introduce dedicated local settings module

#### Automated

- [x] 1.1 Django checks pass with local settings module — fd80f6d
- [x] 1.2 Static URL helper returns `/static/...` prefixed URLs under local settings — fd80f6d

#### Manual

- [x] 1.3 Visiting `/` in local dev loads CSS/JS with no 404 entries for `/app/*` or `/vendor/*` — fd80f6d
- [x] 1.4 Page styling appears correctly on dashboard/login pages — fd80f6d

### Phase 2: Add regression tests for static path generation

#### Automated

- [x] 2.1 Targeted account tests pass including new static URL assertions — 9b647fe
- [x] 2.2 Full project test suite still passes — 9b647fe
- [x] 2.3 Lint and type-check pass — 9b647fe

#### Manual

- [x] 2.4 Local dashboard reload still shows expected summary table and chart behavior — 9b647fe
- [x] 2.5 Login page and dashboard both load Bootstrap styling locally — 9b647fe

### Phase 3: Document local recovery and run command path

#### Automated

- [x] 3.1 Documentation-referenced local command executes successfully
- [x] 3.2 Django checks still pass after docs-aligned command path

#### Manual

- [x] 3.3 Developer can follow docs commands and load styled local UI without additional implicit steps
- [x] 3.4 Recovery command reproduces and resolves static mismatch scenario when applied
