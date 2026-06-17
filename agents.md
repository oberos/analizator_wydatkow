# Analizator Wydatków — Repository Guidelines

Expense analyzer web app: CSV import from Polish banks → auto-categorization → spending reports.

## Key Domain Rules

- Transaction data must **never leak between user accounts**
- MVP targets **ING Poland CSV format only**
- Budget cycles are **paycheck-to-paycheck** (custom date ranges), not calendar months
- Success metric: **80% of transactions** should auto-categorize (not land in "Unknown")

## Commands

```bash
pdm run python manage.py runserver     # Dev server at localhost:8000
pdm run python manage.py test          # Run all tests
pdm run python manage.py test transactions.tests # Run tests in specific app
pdm run python manage.py test app.tests.TestClassName.test_method  # Single test
pdm run python manage.py makemigrations
pdm run python manage.py migrate
playwright-cli open http://localhost:8000/accounts/login/ --headed  # Run e2e tests
pdm run ruff check .                   # Lint
pdm run ruff format .                  # Format
pdm run basedpyright                   # Typechecking
```

## Local environment bootstrap

- Create a local `.env` file (not committed; `.gitignore` already excludes it) from `.env.example`.
- Source `.env` once per shell session before running local commands.

```bash
# PowerShell
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
    [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
  }
}
```

## Local static troubleshooting

- Expected local static URLs are prefixed with `/static/` (for example `/static/app/ui.css`).
- If local CSS/JS is missing after sourcing `.env`, run:

```bash
Remove-Item -Recurse -Force .\staticfiles -ErrorAction SilentlyContinue ; pdm run python manage.py collectstatic --noinput
```

## Isolation mismatch remediation

- Ownership guard migration (`transactions.0006_access_isolation_ownership_guard`) blocks deploy/local migrate if any transaction or merchant mapping points to a category owned by a different user.
- To preview and fix offending rows, run:

```bash
pdm run python manage.py shell -c "from django.db.models import F; from transactions.models import Transaction, MerchantCategoryMapping; print('Transactions:', list(Transaction.objects.filter(category__isnull=False).exclude(user_id=F('category__user_id')).values('id','user_id','category_id','category__user_id')[:20])); print('Mappings:', list(MerchantCategoryMapping.objects.exclude(user_id=F('category__user_id')).values('id','user_id','category_id','category__user_id')[:20]))"
```

- Remediation rules:
  1. For mismatched `Transaction` rows, either set `category=None` or assign a category owned by the same `transaction.user`.
  2. For mismatched `MerchantCategoryMapping` rows, delete the row or re-point it to a category owned by `mapping.user`.
- After remediation, rerun:

```bash
pdm run python manage.py migrate
$env:DEBUG="True" ; pdm run python manage.py test accounts.tests categories.tests transactions.tests
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
