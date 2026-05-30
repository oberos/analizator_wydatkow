# Category Management Implementation Plan

## Overview

Implement CRUD operations for spending categories. Users can create, edit, and delete custom categories to organize their transactions. A starter set of predefined categories (Groceries, Transport, Entertainment, Bills, Health) is copied to each user on registration — users own these copies and can rename or delete them freely.

## Current State Analysis

- **No models exist**: `accounts/models.py` is empty; this is a clean-slate implementation
- **Auth in place**: Registration via `RegisterView` (CreateView), `@login_required` decorator for protected views
- **URL pattern**: Apps have own `urls.py`, included via `include()` from main URLconf
- **Templates**: Project-level `templates/` with `base.html` inheritance, minimal styling (matches auth-scaffold)

### Key Discoveries:

- `accounts/views.py:9-14` — RegisterView uses `CreateView` with `form_class` and `success_url`
- `analizator_wydatkow/urls.py:24-26` — Pattern: `path("prefix/", include("app.urls"))`
- `templates/base.html:9-15` — Messages block ready for success/error feedback
- PRD Business Logic — Categories are user-specific; "Unknown" is a fallback for uncategorized transactions

## Desired End State

Users can:
1. View a list of their categories at `/categories/`
2. Create new custom categories
3. Edit existing category names
4. Delete categories they no longer need
5. New users automatically receive 5 predefined starter categories on registration

Verification: Navigate to `/categories/`, see the 5 predefined categories, create/edit/delete a category, logout/login and confirm persistence.

## What We're NOT Doing

- No "Unknown" category in the model — it's a runtime fallback label, not a stored category
- No category icons or colors — text names only for MVP
- No category merge/bulk operations
- No category ordering/sorting — alphabetical display only
- No tests — consistent with auth-scaffold MVP decision

## Implementation Approach

1. **New `categories` app** with a single `Category` model (name + user FK)
2. **Django CBVs** (ListView, CreateView, UpdateView, DeleteView) matching existing patterns
3. **Signal-based seeding** — post_save signal on User creates predefined categories on registration
4. **Data migration** — seed predefined categories for existing users
5. **Dashboard integration** — add link to `/categories/` from dashboard

## Phase 1: Model & Migration

### Overview

Create the `categories` Django app with a `Category` model and data migration to seed predefined categories for existing users.

### Changes Required:

#### 1. Create categories app

**Command**: `python manage.py startapp categories`

**Intent**: Scaffold the new Django app structure.

#### 2. Category model

**File**: `categories/models.py`

**Intent**: Define the `Category` model with `name` (CharField) and `user` (ForeignKey to User). The model enforces unique category names per user via `unique_together`.

**Contract**:
```python
class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")

    class Meta:
        unique_together = ("name", "user")
        ordering = ["name"]
```

#### 3. Register in INSTALLED_APPS

**File**: `analizator_wydatkow/settings.py`

**Intent**: Add `"categories"` to `INSTALLED_APPS` so Django discovers the app.

**Contract**: Append to `INSTALLED_APPS` list.

#### 4. Create migration

**Command**: `python manage.py makemigrations categories`

**Intent**: Generate the initial migration for the Category model.

#### 5. Data migration for existing users

**File**: `categories/migrations/0002_seed_predefined_categories.py`

**Intent**: Create a data migration that seeds the 5 predefined categories (Groceries, Transport, Entertainment, Bills, Health) for all existing users. New users will receive these via a signal (Phase 3).

**Contract**: Use `RunPython` with forwards/backwards functions. Query all users and bulk-create categories.

#### 6. Apply migrations

**Command**: `python manage.py migrate`

**Intent**: Apply schema and data migrations.

### Success Criteria:

#### Automated Verification:

- Migration applies cleanly: `python manage.py migrate`
- Django system check passes: `python manage.py check`
- Linting passes: `pdm run ruff check .`

#### Manual Verification:

- In Django shell, create a Category and query it back
- Existing test user has 5 predefined categories in DB

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Views & URLs

### Overview

Implement CRUD views using Django class-based views and wire them to `/categories/` URLs.

### Changes Required:

#### 1. Category views

**File**: `categories/views.py`

**Intent**: Implement 4 views using Django CBVs:
- `CategoryListView` (ListView) — list user's categories
- `CategoryCreateView` (CreateView) — create new category
- `CategoryUpdateView` (UpdateView) — edit category name
- `CategoryDeleteView` (DeleteView) — delete category

All views must filter by the logged-in user (`request.user`) and use `LoginRequiredMixin`.

**Contract**:
- ListView filters queryset to `user=self.request.user`
- CreateView sets `form.instance.user = self.request.user` in `form_valid()`
- UpdateView/DeleteView filter queryset to user's categories only (security)
- Success URLs use `reverse_lazy("categories:list")`

#### 2. Category URLs

**File**: `categories/urls.py`

**Intent**: Define URL patterns with `app_name = "categories"` namespace.

**Contract**:
```python
app_name = "categories"
urlpatterns = [
    path("", CategoryListView.as_view(), name="list"),
    path("create/", CategoryCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", CategoryUpdateView.as_view(), name="edit"),
    path("<int:pk>/delete/", CategoryDeleteView.as_view(), name="delete"),
]
```

#### 3. Include in main URLconf

**File**: `analizator_wydatkow/urls.py`

**Intent**: Add `path("categories/", include("categories.urls"))` to wire the categories app.

**Contract**: Add before the dashboard catch-all route.

#### 4. Apps config

**File**: `categories/apps.py`

**Intent**: Add `default_auto_field = "django.db.models.BigAutoField"` per Django best practice (from auth-scaffold review).

### Success Criteria:

#### Automated Verification:

- Django system check passes: `python manage.py check`
- Linting passes: `pdm run ruff check .`
- Server starts without errors: `python manage.py runserver`

#### Manual Verification:

- Navigate to `/categories/` — see list (may be empty or have seeded categories)
- Create a category — redirected to list, new category appears
- Edit a category — name updates
- Delete a category — removed from list

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Templates & Integration

### Overview

Create category templates and integrate with dashboard and registration flow (signal for predefined categories).

### Changes Required:

#### 1. Category list template

**File**: `templates/categories/category_list.html`

**Intent**: Display user's categories as a list with edit/delete links per item and a "Create new" button.

**Contract**: Extends `base.html`, iterates `object_list`, links use `{% url 'categories:...' %}`.

#### 2. Category form template

**File**: `templates/categories/category_form.html`

**Intent**: Shared template for create/edit forms (Django CBVs use `<model>_form.html` by default).

**Contract**: Extends `base.html`, displays `form.as_p` with CSRF token and submit button.

#### 3. Category delete confirmation template

**File**: `templates/categories/category_confirm_delete.html`

**Intent**: Confirmation page before deleting a category.

**Contract**: Extends `base.html`, POST form to confirm deletion.

#### 4. Dashboard link

**File**: `templates/dashboard.html`

**Intent**: Add a link to `/categories/` from the dashboard so users can access category management.

**Contract**: Add `<a href="{% url 'categories:list' %}">Manage Categories</a>` link.

#### 5. Signal for new user categories

**File**: `categories/signals.py`

**Intent**: Create a `post_save` signal on User that copies the 5 predefined categories when a new user is created.

**Contract**:
```python
@receiver(post_save, sender=User)
def create_predefined_categories(sender, instance, created, **kwargs):
    if created:
        # Bulk create predefined categories for new user
```

#### 6. Register signal in apps.py

**File**: `categories/apps.py`

**Intent**: Import the signals module in `ready()` to register the signal handler.

**Contract**: Override `ready()` method to import `categories.signals`.

### Success Criteria:

#### Automated Verification:

- Django system check passes: `python manage.py check`
- Linting passes: `pdm run ruff check .`
- Server starts without errors: `python manage.py runserver`

#### Manual Verification:

- Dashboard shows "Manage Categories" link
- Category list/create/edit/delete pages render correctly
- Register a new user, login, see 5 predefined categories
- All CRUD operations work end-to-end

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Skipped for MVP per user decision

### Integration Tests:

- Skipped for MVP per user decision

### Manual Testing Steps:

1. Login as existing user → navigate to `/categories/` → see 5 predefined categories
2. Create a new category "Subscriptions" → appears in list
3. Edit "Subscriptions" to "Monthly Subscriptions" → name updates
4. Delete "Monthly Subscriptions" → removed from list
5. Register a new user → login → see 5 predefined categories
6. Verify categories are user-isolated: User A's categories not visible to User B

## Performance Considerations

- `unique_together` constraint prevents duplicate category names per user at DB level
- `ordering = ["name"]` in model Meta avoids repeated `order_by()` in views
- No pagination needed — typical user has <20 categories

## Migration Notes

- Data migration (0002) seeds existing users with predefined categories
- Signal handles new users automatically after deploy
- No breaking changes to existing data (new table only)

## References

- PRD: `context/foundation/prd.md` — FR-006, FR-007, FR-008
- Roadmap: `context/foundation/roadmap.md` — S-01
- Auth pattern: `accounts/views.py:9-14` (CreateView example)
- URL pattern: `analizator_wydatkow/urls.py:24-26`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Model & Migration

#### Automated

- [x] 1.1 Migration applies cleanly
- [x] 1.2 Django system check passes
- [x] 1.3 Linting passes

#### Manual

- [x] 1.4 Category model works in Django shell
- [x] 1.5 Existing user has 5 predefined categories

### Phase 2: Views & URLs

#### Automated

- [ ] 2.1 Django system check passes
- [ ] 2.2 Linting passes
- [ ] 2.3 Server starts without errors

#### Manual

- [ ] 2.4 Category list page renders
- [ ] 2.5 Create category works
- [ ] 2.6 Edit category works
- [ ] 2.7 Delete category works

### Phase 3: Templates & Integration

#### Automated

- [ ] 3.1 Django system check passes
- [ ] 3.2 Linting passes
- [ ] 3.3 Server starts without errors

#### Manual

- [ ] 3.4 Dashboard shows Manage Categories link
- [ ] 3.5 All category pages render correctly
- [ ] 3.6 New user registration creates predefined categories
- [ ] 3.7 Full CRUD workflow works end-to-end
