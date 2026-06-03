# CSV Import with Auto-Categorization — Plan Brief

> Full plan: `context/changes/csv-import-autocategorize/plan.md`

## What & Why

The north star feature for Analizator Wydatków: users upload their ING Poland bank CSV export and see transactions with auto-proposed categories. This is the core differentiator vs Excel — automatic categorization based on learned merchant→category mappings.

## Starting Point

- Auth system complete (F-01): login, registration, session management
- Categories app complete (S-01): Category model with user FK, CRUD views, predefined seeding
- No Transaction model exists — must create from scratch
- No file upload handling — Django forms with FileField needed
- ING CSV format analyzed: Windows-1250 encoding, semicolon delimiter, 166 sample transactions

## Desired End State

Users can upload ING Poland CSV files via a modal on the transaction list page. Transactions are parsed, validated, and auto-categorized using normalized merchant prefix matching. All transactions display in a list with their assigned categories. Uncategorized transactions show "Unknown" badge. Users can delete all transactions to start fresh. Duplicate detection prevents re-importing the same transactions.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
|----------|--------|------------------|--------|
| App structure | New `transactions` app | Clean separation, follows Django convention | Plan |
| Amount storage | DecimalField (2 decimal places) | Accurate currency representation | Plan |
| Matching algorithm | Normalized merchant prefix | Strip store numbers/locations for higher recall | Plan |
| Mapping storage | Separate MerchantCategoryMapping model | Clean separation, queryable, editable later | Plan |
| Duplicates | Skip silently | Match on (date, amount, merchant, tx_number) | Plan |
| Malformed CSV | Abort with clear error | Show line number + issue for user to fix | Plan |
| Upload UI | Modal from transaction list | Transaction list is primary view | Plan |
| Processing | Synchronous (no Celery) | <5s for 300 transactions, avoids infra complexity | Plan |
| Manual editing | Out of scope | S-03's responsibility per roadmap | Plan |
| File persistence | Process in memory | Simpler, no storage costs, user keeps original | Plan |
| Testing | Skip for MVP | Manual verification, tests in Module 3 | Plan |
| Delete transactions | "Delete All" button | Simple fresh start option | Plan |
| Predefined mappings | Seed ~60 Polish merchants | Achieve 80% target on first import | Plan |

## Scope

**In scope:**
- Transaction and MerchantCategoryMapping models
- ING Poland CSV parser (Windows-1250, semicolon, header/footer handling)
- Merchant normalization (strip numbers, locations, company suffixes)
- Auto-categorization via mapping lookup
- **Predefined merchant mappings for ~60 popular Polish merchants (Biedronka, Lidl, Orlen, McDonald's, etc.)**
- Transaction list view with category display
- Upload modal UI
- Delete all transactions action
- Duplicate detection and skip
- "Unknown" category seeding

**Out of scope:**
- Manual category editing (S-03)
- Learning from corrections (S-03)
- Budget cycles / date filtering (S-04/S-05)
- Spending summary / reports (S-03)
- Multi-bank support (MVP is ING only)
- Background processing (Celery)
- File persistence
- Unit tests (MVP)

## Architecture / Approach

New `transactions` app with two models:
- `Transaction`: user FK, date, merchant, description, amount, category FK
- `MerchantCategoryMapping`: user FK, normalized_merchant, category FK

Three-layer separation:
1. `csv_parser.py` — ING-specific parsing logic (encoding, format quirks)
2. `categorization.py` — merchant normalization and mapping lookup
3. `views.py` — Django views orchestrating parse → categorize → save

Upload flow: Modal form → POST CSV file → parse in memory → categorize batch → bulk_create transactions → redirect with success/error message.

## Phases at a Glance

| Phase | What it delivers | Key risk |
|-------|------------------|----------|
| 1. Models & Migration | Transaction, MerchantCategoryMapping, "Unknown" seeding | FK relationships, unique constraints |
| 2. CSV Parser | ING-specific parsing with validation | Encoding edge cases, format variations |
| 3. Auto-categorization Engine | Merchant normalization, mapping lookup | Normalization accuracy (80% target) |
| 4. Views & URLs | List view, upload endpoint, delete-all | Duplicate detection, error handling UX |
| 5. Templates & Modal UI | Transaction list, upload modal, styling | Modal JS, responsive layout |

**Prerequisites:** F-01 (auth) ✓, S-01 (categories) ✓  
**Estimated effort:** ~2-3 sessions across 5 phases

## Open Risks & Assumptions

- Normalization accuracy: assumes "strip numbers/locations" covers 80%+ of merchants — may need tuning
- ING format stability: assumes format from sample is representative — may vary by export date/method
- Windows-1250 encoding: assumes primary encoding — UTF-8 fallback included

## Success Criteria (Summary)

- Upload `transactions_example.csv` → 166 transactions imported, most auto-categorized via predefined mappings
- Re-upload same file → 0 new transactions (all skipped as duplicates)
- Transaction list shows date, merchant, amount, category with "Unknown" badge for uncategorized
- Common merchants (Biedronka, Lidl, Rossmann, etc.) auto-categorized correctly
- Delete All clears all transactions, allowing fresh re-import
