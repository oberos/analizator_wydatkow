# Analizator Wydatków — Repository Guidelines

Expense analyzer web app: CSV import from Polish banks → auto-categorization → spending reports.

## Key Domain Rules

- Transaction data must **never leak between user accounts**
- MVP targets **ING Poland CSV format only**
- Budget cycles are **paycheck-to-paycheck** (custom date ranges), not calendar months
- Success metric: **80% of transactions** should auto-categorize (not land in "Unknown")

## Commands

```bash
$env:DEBUG="True" ; pdm run python manage.py runserver     # Dev server at localhost:8000
pdm run python manage.py test          # Run all tests
pdm run python manage.py test app.tests.TestClassName.test_method  # Single test
pdm run python manage.py makemigrations
pdm run python manage.py migrate
pdm run ruff check .                   # Lint
pdm run ruff format .                  # Format
```

## Code Style

Follow **ruff** linter rules. Config: `@pyproject.toml` `[tool.ruff]` section.

Key settings:
- Line length: 120 chars
- Type annotations required (ANN rules enabled)
- Security checks enabled (Bandit/S rules)
- Double quotes, space indentation

## Architecture

- **Django 6.0** with SQLite (dev) — deploy target is Render
- **Single-user model**: each account isolated, no sharing/roles
- **CSV-only ingestion**: no direct bank API connections (security constraint)
- **Auto-categorization**: learns merchant→category mappings from user corrections

### Planned App Structure

```
transactions/       # CSV import, transaction model, auto-categorization
categories/         # Category CRUD, predefined + custom categories  
reports/            # Summary tables, budget cycles, filtering
accounts/           # Auth (registration, login) — uses Django's built-in auth
```

## Project Context

Full requirements: `@context/foundation/prd.md`
Tech stack rationale: `@context/foundation/tech-stack.md`
