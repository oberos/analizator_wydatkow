# Category Management — Plan Brief

> Full plan: `context/changes/category-management/plan.md`

## What & Why

Implement CRUD operations for spending categories so users can organize transactions by custom labels. The PRD requires users to create/edit/delete categories (FR-006, FR-007, FR-008) and have predefined starter categories available. This is a prerequisite for the north star feature (CSV import with auto-categorization).

## Starting Point

The codebase has authentication working (auth-scaffold complete) but no models beyond Django's built-in User. The `accounts` app exists with registration/login views. Project-level templates use `base.html` inheritance with minimal styling.

## Desired End State

Users can manage their categories at `/categories/` — view a list, create new ones, edit names, delete unwanted ones. New users automatically receive 5 predefined starter categories (Groceries, Transport, Entertainment, Bills, Health) on registration. Categories are per-user and isolated.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) |
|----------|--------|------------------|
| App structure | New `categories` app | Separation of concerns — categories are a distinct domain from auth |
| Category ownership | Per-user with FK | PRD requires no data leakage between accounts |
| Predefined categories | Copy to user on registration | Maintains per-user isolation; users can edit/delete their copies |
| UI placement | Dedicated `/categories/` page | Keeps dashboard clean for main workflow |
| Tests | Skip for MVP | Consistent with auth-scaffold decision; straightforward CRUD |

## Scope

**In scope:**
- Category model with name + user FK
- List/Create/Update/Delete views
- Predefined category seeding (signal + data migration)
- Dashboard link to category management

**Out of scope:**
- "Unknown" as stored category (runtime fallback only)
- Category icons, colors, ordering
- Bulk operations or merge
- Tests

## Architecture / Approach

```
categories/
├── models.py      # Category model (name, user FK, unique_together)
├── views.py       # CBVs: List, Create, Update, Delete
├── urls.py        # /categories/, /categories/create/, etc.
├── signals.py     # post_save on User → create predefined categories
└── migrations/
    ├── 0001_initial.py
    └── 0002_seed_predefined_categories.py  # data migration

templates/categories/
├── category_list.html
├── category_form.html
└── category_confirm_delete.html
```

## Phases at a Glance

| Phase | What it delivers | Key risk |
|-------|------------------|----------|
| 1. Model & Migration | Category model + seeded data for existing users | None significant |
| 2. Views & URLs | Full CRUD at `/categories/` | User isolation in views |
| 3. Templates & Integration | UI + dashboard link + signal for new users | Signal registration |

**Prerequisites:** F-01 auth-scaffold complete ✓
**Estimated effort:** ~1-2 sessions across 3 phases

## Open Risks & Assumptions

- Assumes User model is Django's default (no custom user) — confirmed in auth-scaffold
- Signal must be registered via `apps.py ready()` — easy to miss

## Success Criteria (Summary)

- User can CRUD categories at `/categories/`
- New user registration automatically creates 5 predefined categories
- Categories are per-user isolated (User A cannot see User B's categories)
