# Auth Scaffold — Plan Brief

> Full plan: `context/changes/auth-scaffold/plan.md`

## What & Why

Wire Django's built-in authentication (login, registration, logout) with routes and minimal templates. This is the foundation that unlocks all user-facing slices — every feature needs authenticated users (PRD: FR-001, FR-002).

## Starting Point

Django project scaffold exists with auth framework enabled (`django.contrib.auth` in INSTALLED_APPS, middleware configured). No auth views, routes, or templates exist — clean slate. Using default User model.

## Desired End State

User can register, log in, see a placeholder dashboard ("Hello, {username}"), and log out. Unauthenticated users are redirected to login. Full session-based auth working end-to-end.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
|----------|--------|------------------|
| URL prefix | `/accounts/` | Django default — works with built-in auth URLs out of the box |
| Templates location | Project-level `templates/` | Reusable across future apps, cleaner structure |
| Post-login redirect | `/` (root) | Future dashboard location; keeps UX simple |
| Template styling | Minimal functional | MVP focus — form + messages only, no CSS |
| Automated tests | Skip for MVP | Manual verification sufficient for foundation scaffold |

## Scope

**In scope:**
- Login view + template
- Registration view + template  
- Logout view + logged_out template
- Placeholder dashboard at `/` requiring auth
- Auth settings (LOGIN_URL, redirects)

**Out of scope:**
- Password reset/change flows
- Email verification
- OAuth/social login
- Custom User model
- Styled templates
- Automated tests

## Architecture / Approach

```
accounts/ app (new)
├── views.py      → RegisterView, dashboard_view
├── urls.py       → register route
└── (standard app files)

templates/ (project-level)
├── base.html
├── dashboard.html
└── registration/
    ├── login.html
    ├── register.html
    └── logged_out.html

analizator_wydatkow/
├── settings.py   → add LOGIN_URL, TEMPLATES DIRS, accounts to INSTALLED_APPS
└── urls.py       → include django.contrib.auth.urls + accounts.urls
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
|-------|-----------------|----------|
| 1. Settings & Routes | Auth config + URL wiring | Low — standard Django patterns |
| 2. Templates | Functional login/register/logout templates | Low — minimal HTML |
| 3. Placeholder Dashboard | Root view requiring auth | Low — proves flow works |

**Prerequisites:** None — this is the first foundation slice
**Estimated effort:** ~1 session, 3 small phases

## Open Risks & Assumptions

- Assumes Django's default User model is sufficient (PRD confirms single-user, no roles)
- No email verification — acceptable for single-user MVP

## Success Criteria (Summary)

- User can register a new account at `/accounts/register/`
- User can log in and is redirected to `/` showing "Hello, {username}"
- Unauthenticated access to `/` redirects to login
