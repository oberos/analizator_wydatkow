# Auth Scaffold Implementation Plan

## Overview

Wire Django's built-in authentication (login, registration, logout) with routes at `/accounts/`, project-level templates, and redirect to `/` on login. This is the foundation that unlocks all user-facing slices (S-01 through S-05).

## Current State Analysis

**What exists:**
- Django auth framework enabled (`django.contrib.auth` in INSTALLED_APPS)
- Auth middleware configured (`AuthenticationMiddleware`)
- Session middleware configured
- Password validators configured
- Default User model (email + password)

**What's missing:**
- No auth views or routes
- No templates (TEMPLATES `DIRS` is empty)
- No `LOGIN_URL`, `LOGIN_REDIRECT_URL`, `LOGOUT_REDIRECT_URL` settings
- No landing page for authenticated users

### Key Discoveries:

- `analizator_wydatkow/settings.py:43-50` — auth app already in INSTALLED_APPS
- `analizator_wydatkow/settings.py:58` — AuthenticationMiddleware present
- `analizator_wydatkow/settings.py:68` — TEMPLATES `DIRS` is empty, needs project-level templates
- `analizator_wydatkow/urls.py:20-22` — only admin route exists

## Desired End State

After this plan:
1. User can visit `/accounts/register/` and create a new account
2. User can visit `/accounts/login/` and log in with email/password
3. Authenticated user is redirected to `/` (placeholder dashboard showing "Hello, {username}")
4. User can log out via `/accounts/logout/`
5. Unauthenticated user visiting `/` is redirected to `/accounts/login/`

**Verification:**
- `pdm run python manage.py runserver` starts without errors
- Manual test: register → login → see dashboard → logout → redirect to login

## What We're NOT Doing

- Password reset/change flows (can add post-MVP)
- Email verification (single-user app, not needed)
- OAuth/social login (PRD specifies email+password)
- Custom User model (default User is sufficient)
- Styled templates (minimal functional for MVP)
- Automated tests (manual verification sufficient for foundation)

## Implementation Approach

Use Django's built-in auth views (`LoginView`, `LogoutView`) and forms (`UserCreationForm`) with minimal customization. Create an `accounts` app to hold the registration view and URL configuration. Templates live at project level in `templates/` for reuse across future apps.

---

## Phase 1: Settings & Routes

### Overview

Configure auth-related settings and wire URL routes for login, logout, and registration.

### Changes Required:

#### 1. Auth settings

**File**: `analizator_wydatkow/settings.py`

**Intent**: Add auth redirect settings and register project-level templates directory so Django knows where to find auth templates and where to redirect after login/logout.

**Contract**: Add to end of settings:
- `LOGIN_URL = "/accounts/login/"`
- `LOGIN_REDIRECT_URL = "/"`
- `LOGOUT_REDIRECT_URL = "/accounts/login/"`

Update `TEMPLATES[0]["DIRS"]` to include `BASE_DIR / "templates"`.

#### 2. Create accounts app

**File**: `accounts/` (new app)

**Intent**: Create a Django app to hold the registration view. Django's built-in auth provides login/logout but not registration.

**Contract**: Run `python manage.py startapp accounts`. Register `"accounts"` in `INSTALLED_APPS`.

#### 3. Registration view

**File**: `accounts/views.py`

**Intent**: Create a registration view using Django's `UserCreationForm` that creates a new user and redirects to login.

**Contract**: Class-based view `RegisterView(CreateView)` with:
- `form_class = UserCreationForm`
- `template_name = "registration/register.html"`
- `success_url = reverse_lazy("login")`

#### 4. Accounts URLs

**File**: `accounts/urls.py` (new file)

**Intent**: Define URL patterns for the accounts app including registration.

**Contract**: 
- `path("register/", RegisterView.as_view(), name="register")`

#### 5. Root URL configuration

**File**: `analizator_wydatkow/urls.py`

**Intent**: Include Django's built-in auth URLs and the accounts app URLs under `/accounts/`.

**Contract**: Add:
- `path("accounts/", include("django.contrib.auth.urls"))`
- `path("accounts/", include("accounts.urls"))`

### Success Criteria:

#### Automated Verification:

- Server starts: `pdm run python manage.py runserver` exits cleanly
- URL resolution works: `pdm run python manage.py show_urls` shows `/accounts/login/`, `/accounts/logout/`, `/accounts/register/`

#### Manual Verification:

- Navigate to `/accounts/login/` shows login form (may 404 on template, that's Phase 2)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the routing is correct before proceeding to Phase 2.

---

## Phase 2: Templates

### Overview

Create the template directory structure and minimal functional templates for auth flows.

### Changes Required:

#### 1. Base template

**File**: `templates/base.html` (new file)

**Intent**: Create a base template that all other templates extend, providing consistent page structure.

**Contract**: Minimal HTML5 boilerplate with:
- `{% block title %}` for page title
- `{% block content %}` for main content
- Display `{{ messages }}` for Django messages (login errors, etc.)

#### 2. Login template

**File**: `templates/registration/login.html` (new file)

**Intent**: Login form template extending base.html. Django's `LoginView` expects this path by convention.

**Contract**: 
- Extends `base.html`
- Renders `{{ form.as_p }}`
- CSRF token
- Link to registration page

#### 3. Registration template

**File**: `templates/registration/register.html` (new file)

**Intent**: Registration form template for the custom RegisterView.

**Contract**:
- Extends `base.html`
- Renders `{{ form.as_p }}`
- CSRF token
- Link to login page

#### 4. Logged out template

**File**: `templates/registration/logged_out.html` (new file)

**Intent**: Confirmation page after logout (Django's LogoutView renders this by default).

**Contract**:
- Extends `base.html`
- Shows "You have been logged out" message
- Link to login page

### Success Criteria:

#### Automated Verification:

- Templates exist: `ls templates/registration/` shows login.html, register.html, logged_out.html
- Server starts without template errors

#### Manual Verification:

- `/accounts/login/` renders login form
- `/accounts/register/` renders registration form

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that templates render correctly before proceeding to Phase 3.

---

## Phase 3: Placeholder Dashboard

### Overview

Create a root view (`/`) that requires authentication and shows a simple "Hello, {username}" message. This proves the full auth flow works end-to-end.

### Changes Required:

#### 1. Dashboard view

**File**: `accounts/views.py`

**Intent**: Add a simple dashboard view that requires login and displays the authenticated user's name.

**Contract**: Function or class-based view decorated with `@login_required` that renders `dashboard.html` with `request.user` in context.

#### 2. Dashboard template

**File**: `templates/dashboard.html` (new file)

**Intent**: Simple landing page for authenticated users.

**Contract**:
- Extends `base.html`
- Shows "Hello, {{ user.username }}!"
- Logout link

#### 3. Dashboard URL

**File**: `analizator_wydatkow/urls.py`

**Intent**: Wire the root URL to the dashboard view.

**Contract**: `path("", dashboard_view, name="dashboard")` — importing from accounts.views.

### Success Criteria:

#### Automated Verification:

- Server starts: `pdm run python manage.py runserver`
- Lint passes: `pdm run ruff check .`

#### Manual Verification:

- Unauthenticated: visiting `/` redirects to `/accounts/login/?next=/`
- Register new user at `/accounts/register/`
- Log in at `/accounts/login/`
- After login, redirected to `/` showing "Hello, {username}!"
- Click logout, see logged out page, redirected to login

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the full auth flow works end-to-end.

---

## Testing Strategy

### Manual Testing Steps:

1. Start server: `pdm run python manage.py runserver`
2. Visit `http://localhost:8000/` — expect redirect to `/accounts/login/`
3. Click "Register" link, create account with username/password
4. After registration, log in with credentials
5. Verify redirect to `/` with "Hello, {username}" message
6. Click logout, verify redirect to login page
7. Try accessing `/` again — should redirect to login

## Performance Considerations

None — auth scaffold is lightweight. Django's built-in auth is well-optimized.

## Migration Notes

No migrations needed — using Django's default User model which is already migrated.

## References

- PRD: `context/foundation/prd.md` (FR-001, FR-002, Access Control section)
- Roadmap: `context/foundation/roadmap.md` (F-01: Auth scaffold)
- Django auth docs: https://docs.djangoproject.com/en/6.0/topics/auth/

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Settings & Routes

#### Automated

- [ ] 1.1 Server starts without errors
- [ ] 1.2 URL resolution shows auth routes

#### Manual

- [ ] 1.3 Login URL accessible (template 404 is OK)

### Phase 2: Templates

#### Automated

- [ ] 2.1 Template files exist
- [ ] 2.2 Server starts without template errors

#### Manual

- [ ] 2.3 Login and register forms render correctly

### Phase 3: Placeholder Dashboard

#### Automated

- [ ] 3.1 Server starts
- [ ] 3.2 Lint passes

#### Manual

- [ ] 3.3 Full auth flow works (register → login → dashboard → logout)
