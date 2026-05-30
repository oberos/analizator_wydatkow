# CSV Import with Auto-Categorization Implementation Plan

## Overview

Implement the north star feature: CSV import from ING Poland bank with automatic transaction categorization. Users upload a CSV file, the system parses it (handling Windows-1250 encoding and ING-specific format quirks), and auto-proposes categories based on normalized merchant-to-category mappings learned from user corrections.

## Current State Analysis

- **Auth system**: Complete (F-01) — login, registration, session management
- **Categories app**: Complete (S-01) — Category model with user FK, CRUD views, predefined seeding
- **No Transaction model exists** — must create from scratch
- **No file upload handling** — Django forms with FileField needed
- **ING CSV format analyzed** — sample in `context/transactions_example.csv` (166 transactions)

### Key Discoveries:

- ING CSV uses Windows-1250 encoding with semicolon delimiter
- Header row starts at line 19 (`"Data transakcji";...`), metadata rows above
- Footer disclaimer at end must be skipped
- Key columns: `Dane kontrahenta` (merchant), `Tytuł` (description), `Kwota transakcji (waluta rachunku)` (amount)
- Date format: `YYYY-MM-DD`
- Amount format: comma decimal (`-5,00`), negative = expense
- Transaction number in `Nr transakcji` column for duplicate detection

## Desired End State

After this plan is complete:

1. A new `transactions` app exists with `Transaction` and `MerchantCategoryMapping` models
2. Users can upload ING Poland CSV files via a modal on the transaction list page
3. Transactions are parsed, validated, and auto-categorized using normalized merchant matching
4. Transaction list shows all transactions with their assigned categories
5. Uncategorized transactions show "Unknown" badge (seeded category)
6. Users can delete all transactions to start fresh
7. Duplicate transactions (same date + amount + merchant + tx_number) are silently skipped

**Verification**: Upload `context/transactions_example.csv`, see 166 transactions imported with categories assigned based on any existing mappings. Re-upload same file, see 0 new transactions (all duplicates skipped).

## What We're NOT Doing

- **Manual category editing** — that's S-03 scope (category refinement)
- **Learning from corrections** — S-03 will update MerchantCategoryMapping when user edits
- **Budget cycles / date filtering** — S-04/S-05 scope
- **Spending summary / reports** — S-03 scope
- **Multi-bank support** — MVP is ING Poland only
- **Background processing** — synchronous is sufficient for 300 transactions
- **File persistence** — process in memory, don't store CSV
- **Unit tests** — MVP approach, manual verification only

## Implementation Approach

Five phases, each with automated and manual verification gates:

1. **Models & Migration** — Data foundation: Transaction, MerchantCategoryMapping, "Unknown" category
2. **CSV Parser** — ING-specific parsing: encoding, row detection, validation
3. **Auto-categorization Engine** — Merchant normalization and mapping lookup
4. **Views & URLs** — Transaction list, upload endpoint, delete-all action
5. **Templates & Modal UI** — User interface with upload modal and feedback

---

## Phase 1: Models & Migration

### Overview

Create the `transactions` app with two models: `Transaction` (the imported bank transaction) and `MerchantCategoryMapping` (learned merchant→category associations). Seed "Unknown" category for uncategorized transactions.

### Changes Required:

#### 1. Create transactions app

**Command**: `python manage.py startapp transactions`

**Intent**: Scaffold the new Django app following the same structure as `categories` app.

#### 2. Transaction model

**File**: `transactions/models.py`

**Intent**: Define the Transaction model with all fields needed from ING CSV, plus user isolation and category assignment.

**Contract**: 
```python
class Transaction(models.Model):
    user: FK(AUTH_USER_MODEL, CASCADE, related_name="transactions")
    date: DateField  # Data transakcji
    booking_date: DateField(null=True)  # Data księgowania
    merchant: CharField(max_length=200)  # Dane kontrahenta (raw)
    description: CharField(max_length=500)  # Tytuł
    amount: DecimalField(max_digits=12, decimal_places=2)  # Kwota transakcji
    transaction_number: CharField(max_length=50, blank=True)  # Nr transakcji
    category: FK(Category, SET_NULL, null=True, related_name="transactions")
    
    class Meta:
        ordering = ["-date", "-id"]
        # For duplicate detection:
        unique_together = [("user", "date", "amount", "merchant", "transaction_number")]
```

#### 3. MerchantCategoryMapping model

**File**: `transactions/models.py`

**Intent**: Store learned associations between normalized merchant names and categories, per user.

**Contract**:
```python
class MerchantCategoryMapping(models.Model):
    user: FK(AUTH_USER_MODEL, CASCADE, related_name="merchant_mappings")
    normalized_merchant: CharField(max_length=200)  # e.g., "BIEDRONKA"
    category: FK(Category, CASCADE, related_name="merchant_mappings")
    
    class Meta:
        unique_together = [("user", "normalized_merchant")]
```

#### 4. Register app in settings

**File**: `analizator_wydatkow/settings.py`

**Intent**: Add `"transactions"` to INSTALLED_APPS.

**Contract**: Insert after `"categories"` in INSTALLED_APPS list.

#### 5. Seed "Unknown" category

**File**: `transactions/migrations/0002_seed_unknown_category.py`

**Intent**: Data migration to ensure every user has an "Unknown" category for uncategorized transactions.

**Contract**: For each existing user, create `Category(name="Unknown", user=user)` if not exists. Also update `categories/signals.py` to include "Unknown" in PREDEFINED_CATEGORIES for new users.

#### 6. Seed predefined merchant mappings

**File**: `transactions/migrations/0003_seed_predefined_mappings.py`

**Intent**: Data migration to create merchant→category mappings for popular Polish shops, gas stations, restaurants, etc. This helps achieve 80% auto-categorization on first import.

**Contract**: For each existing user, create MerchantCategoryMapping entries:

```python
PREDEFINED_MAPPINGS = {
    # Groceries
    "BIEDRONKA": "Groceries",
    "LIDL": "Groceries",
    "KAUFLAND": "Groceries",
    "AUCHAN": "Groceries",
    "CARREFOUR": "Groceries",
    "ZABKA": "Groceries",
    "LEWIATAN": "Groceries",
    "DINO": "Groceries",
    "NETTO": "Groceries",
    "INTERMARCHE": "Groceries",
    "STOKROTKA": "Groceries",
    "POLO MARKET": "Groceries",
    "FRESHMARKET": "Groceries",
    "DELIKATESY": "Groceries",
    "PIEKARNIA": "Groceries",
    "RZEZNIK": "Groceries",
    
    # Transport / Fuel
    "ORLEN": "Transport",
    "BP": "Transport",
    "SHELL": "Transport",
    "CIRCLE K": "Transport",
    "LOTOS": "Transport",
    "MOYA": "Transport",
    "AMIC": "Transport",
    "BOLT": "Transport",
    "UBER": "Transport",
    "FREENOW": "Transport",
    "FLIXBUS": "Transport",
    "PKP": "Transport",
    "INTERCITY": "Transport",
    "METROPOLIA": "Transport",
    "JAKDOJADE": "Transport",
    
    # Restaurants / Fast food
    "MCDONALDS": "Entertainment",
    "KFC": "Entertainment",
    "BURGER KING": "Entertainment",
    "PIZZA HUT": "Entertainment",
    "STARBUCKS": "Entertainment",
    "COSTA COFFEE": "Entertainment",
    "SUBWAY": "Entertainment",
    "KEBAB": "Entertainment",
    "BISTRO": "Entertainment",
    "RESTAURACJA": "Entertainment",
    
    # Health / Pharmacy
    "ROSSMANN": "Health",
    "HEBE": "Health",
    "DROGERIA": "Health",
    "APTEKA": "Health",
    "SUPERPHARM": "Health",
    "ZIKO": "Health",
    
    # Bills / Subscriptions
    "NETFLIX": "Bills",
    "SPOTIFY": "Bills",
    "YOUTUBE": "Bills",
    "PLAY": "Bills",
    "ORANGE": "Bills",
    "T-MOBILE": "Bills",
    "PLUS": "Bills",
    "UPC": "Bills",
    "VECTRA": "Bills",
    "PGE": "Bills",
    "TAURON": "Bills",
    "ENEA": "Bills",
}
```

Also update `transactions/signals.py` to copy predefined mappings for new users (parallel to category seeding pattern).

#### 6. Generate and apply migrations

**Command**: `python manage.py makemigrations transactions && python manage.py migrate`

### Success Criteria:

#### Automated Verification:

- App created: `ls transactions/` shows models.py, views.py, etc.
- Migrations apply cleanly: `python manage.py migrate`
- Django check passes: `python manage.py check`
- Linting passes: `pdm run ruff check .`

#### Manual Verification:

- In Django shell: `from transactions.models import Transaction, MerchantCategoryMapping` works
- Existing users have "Unknown" category: `Category.objects.filter(name="Unknown").exists()`
- Existing users have predefined mappings: `MerchantCategoryMapping.objects.filter(normalized_merchant="BIEDRONKA").exists()`
- New user registration creates "Unknown" category and predefined mappings

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: CSV Parser

### Overview

Implement ING-specific CSV parsing: handle Windows-1250 encoding, detect header row, skip metadata/footer, validate required fields, parse amounts and dates.

### Changes Required:

#### 1. Parser module

**File**: `transactions/csv_parser.py`

**Intent**: Create a dedicated module for ING CSV parsing logic, isolated from Django views for clarity.

**Contract**:
```python
@dataclass
class ParsedTransaction:
    date: date
    booking_date: date | None
    merchant: str
    description: str
    amount: Decimal
    transaction_number: str

class CSVParseError(Exception):
    """Raised when CSV parsing fails with user-friendly message."""
    line_number: int
    message: str

def parse_ing_csv(file_content: bytes) -> list[ParsedTransaction]:
    """
    Parse ING Poland CSV export.
    
    Raises CSVParseError with line number and message on validation failure.
    Returns list of ParsedTransaction dataclasses on success.
    """
```

#### 2. Encoding handling

**File**: `transactions/csv_parser.py`

**Intent**: Decode CSV content from Windows-1250 (primary) with UTF-8 fallback.

**Contract**: Try `windows-1250` first, then `utf-8-sig`, then `utf-8`. Raise CSVParseError if all fail.

#### 3. Header/footer detection

**File**: `transactions/csv_parser.py`

**Intent**: Find the data section by detecting header row (`"Data transakcji"`) and footer (`"Dokument ma charakter informacyjny"`).

**Contract**: Return only rows between header and footer. Raise CSVParseError if header not found.

#### 4. Field parsing

**File**: `transactions/csv_parser.py`

**Intent**: Parse individual fields with validation.

**Contract**:
- Date: Parse `YYYY-MM-DD` format, raise on invalid
- Amount: Replace `,` with `.`, strip spaces, convert to Decimal
- Merchant/Description: Strip whitespace and quotes
- Transaction number: Strip apostrophes and spaces

#### 5. Row validation

**File**: `transactions/csv_parser.py`

**Intent**: Validate each row has required fields (date, merchant, amount).

**Contract**: Raise CSVParseError with line number if required field is missing or invalid.

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Module importable: `from transactions.csv_parser import parse_ing_csv`

#### Manual Verification:

- In Django shell, parse sample CSV:
  ```python
  from transactions.csv_parser import parse_ing_csv
  with open("context/transactions_example.csv", "rb") as f:
      transactions = parse_ing_csv(f.read())
  len(transactions)  # Should be ~166
  transactions[0]  # Check first transaction looks correct
  ```
- Verify amounts are Decimal, dates are date objects
- Verify merchant names are cleaned (no leading/trailing spaces)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Auto-categorization Engine

### Overview

Implement merchant normalization and category lookup. Normalize merchant names (strip numbers, locations, suffixes) and match against MerchantCategoryMapping for the user.

### Changes Required:

#### 1. Normalization function

**File**: `transactions/categorization.py`

**Intent**: Create a function to normalize raw merchant names for consistent matching.

**Contract**:
```python
def normalize_merchant(raw_merchant: str) -> str:
    """
    Normalize merchant name for matching.
    
    Rules:
    - Uppercase
    - Strip leading/trailing whitespace
    - Remove location suffixes (POL, KATOWICE, etc.)
    - Remove store numbers (4936, 1337, etc.)
    - Remove common suffixes (SP.ZO.O, S.A., etc.)
    
    Example: "JMP S.A. BIEDRONKA 4936  SWIETOCHLO" -> "BIEDRONKA"
    """
```

#### 2. Categorization function

**File**: `transactions/categorization.py`

**Intent**: Look up category for a normalized merchant from user's mappings.

**Contract**:
```python
def categorize_transaction(
    user: User,
    raw_merchant: str,
    mappings_cache: dict[str, Category] | None = None
) -> Category | None:
    """
    Find category for merchant using user's MerchantCategoryMapping.
    
    Returns Category if mapping exists, None otherwise (caller assigns "Unknown").
    Optional mappings_cache for bulk operations (dict of normalized_merchant -> Category).
    """
```

#### 3. Bulk categorization

**File**: `transactions/categorization.py`

**Intent**: Efficiently categorize multiple transactions with single DB query for mappings.

**Contract**:
```python
def categorize_transactions(
    user: User,
    parsed_transactions: list[ParsedTransaction]
) -> list[tuple[ParsedTransaction, Category | None]]:
    """
    Categorize a batch of transactions efficiently.
    
    Loads all user's MerchantCategoryMappings once, then matches each transaction.
    Returns list of (ParsedTransaction, Category or None) tuples.
    """
```

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Module importable: `from transactions.categorization import normalize_merchant, categorize_transactions`

#### Manual Verification:

- Test normalization in shell:
  ```python
  from transactions.categorization import normalize_merchant
  normalize_merchant("JMP S.A. BIEDRONKA 4936  SWIETOCHLO")  # "BIEDRONKA"
  normalize_merchant("ZABKA Z0307 K.2  RUDA SLASKA 41717")  # "ZABKA"
  normalize_merchant("LIDL SLASKA  Swietochlowic  POL")  # "LIDL"
  ```
- Verify categorization returns None when no mapping exists
- Create a test mapping, verify it matches

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 4: Views & URLs

### Overview

Create views for transaction list, CSV upload handling, and delete-all action. Wire up URL patterns.

### Changes Required:

#### 1. Transaction list view

**File**: `transactions/views.py`

**Intent**: Display all user's transactions with their categories, ordered by date descending.

**Contract**:
```python
class TransactionListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/transaction_list.html"
    context_object_name = "transactions"
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related("category")
```

#### 2. CSV upload view

**File**: `transactions/views.py`

**Intent**: Handle CSV file upload, parse, categorize, and save transactions.

**Contract**:
```python
class CSVUploadView(LoginRequiredMixin, FormView):
    """
    POST: Accept CSV file, parse, categorize, save transactions.
    On success: Redirect to transaction list with success message (N imported, M skipped).
    On error: Redirect with error message (line number + issue).
    """
    form_class = CSVUploadForm
    
    def form_valid(self, form):
        # 1. Parse CSV (may raise CSVParseError)
        # 2. Categorize transactions
        # 3. Bulk create, skip duplicates (IntegrityError or get_or_create)
        # 4. Count imported vs skipped
        # 5. Add success message, redirect
```

#### 3. Upload form

**File**: `transactions/forms.py`

**Intent**: Simple form with FileField for CSV upload.

**Contract**:
```python
class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="ING CSV File",
        help_text="Export from ING Bank Śląski"
    )
```

#### 4. Delete all view

**File**: `transactions/views.py`

**Intent**: Delete all user's transactions for fresh start.

**Contract**:
```python
class DeleteAllTransactionsView(LoginRequiredMixin, View):
    """POST only. Delete all user's transactions, redirect to list with message."""
    
    def post(self, request):
        count = Transaction.objects.filter(user=request.user).delete()[0]
        messages.success(request, f"Deleted {count} transactions.")
        return redirect("transactions:list")
```

#### 5. URL configuration

**File**: `transactions/urls.py`

**Intent**: Wire up views with app namespace.

**Contract**:
```python
app_name = "transactions"
urlpatterns = [
    path("", TransactionListView.as_view(), name="list"),
    path("upload/", CSVUploadView.as_view(), name="upload"),
    path("delete-all/", DeleteAllTransactionsView.as_view(), name="delete_all"),
]
```

#### 6. Include in main URLs

**File**: `analizator_wydatkow/urls.py`

**Intent**: Mount transactions app at `/transactions/`.

**Contract**: Add `path("transactions/", include("transactions.urls"))` to urlpatterns.

### Success Criteria:

#### Automated Verification:

- Django check passes: `python manage.py check`
- Linting passes: `pdm run ruff check .`
- Server starts: `python manage.py runserver`

#### Manual Verification:

- Visit `/transactions/` — see empty list (or login redirect if not authenticated)
- Upload `context/transactions_example.csv` via form — see success message
- Refresh list — see 166 transactions
- Re-upload same file — see "0 imported, 166 skipped" message
- Click delete all — see empty list again

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 5: Templates & Modal UI

### Overview

Create templates for transaction list with upload modal, styling for "Unknown" badge, and navigation integration.

### Changes Required:

#### 1. Transaction list template

**File**: `templates/transactions/transaction_list.html`

**Intent**: Display transactions in a table with date, merchant, description, amount, and category columns.

**Contract**: 
- Extends `base.html`
- Table with columns: Date, Merchant, Description, Amount, Category
- "Unknown" category shows distinct badge/styling
- "Upload CSV" button opens modal
- "Delete All" button with confirmation
- Link back to dashboard

#### 2. Upload modal

**File**: `templates/transactions/transaction_list.html` (inline) or `templates/transactions/_upload_modal.html`

**Intent**: Modal dialog for CSV upload without leaving the page.

**Contract**:
- HTML dialog or Bootstrap-style modal
- Form with file input and submit button
- Close button / click-outside to dismiss
- Minimal JS to toggle modal visibility

#### 3. Dashboard navigation link

**File**: `templates/dashboard.html`

**Intent**: Add "Transactions" link to dashboard for easy access.

**Contract**: Add link to `transactions:list` alongside existing "Manage Categories" link.

#### 4. Amount formatting

**File**: `templates/transactions/transaction_list.html`

**Intent**: Display amounts with proper formatting (negative in red, PLN suffix).

**Contract**: 
- Negative amounts styled red/danger
- Positive amounts styled green/success (or default)
- Format: `-5,00 PLN` (Polish locale display)

### Success Criteria:

#### Automated Verification:

- Linting passes: `pdm run ruff check .`
- Server starts without template errors: `python manage.py runserver`

#### Manual Verification:

- Dashboard shows "Transactions" link
- Click link → see transaction list page
- Click "Upload CSV" → modal opens
- Select file, submit → modal closes, page shows imported transactions
- "Unknown" category transactions have distinct visual style
- Amount column shows negative values in red
- "Delete All" asks for confirmation before deleting

**Implementation Note**: After completing this phase, all automated verification passes, and manual testing is successful, the feature is complete.

---

## Testing Strategy

### Manual Testing Steps:

1. **Fresh import flow**:
   - Log in as existing user
   - Navigate to Transactions
   - Upload `context/transactions_example.csv`
   - Verify 166 transactions appear
   - Verify all show "Unknown" category (no mappings yet)

2. **Duplicate handling**:
   - Re-upload same CSV
   - Verify message shows 0 imported, 166 skipped
   - Verify still 166 transactions (no duplicates)

3. **Delete all flow**:
   - Click "Delete All"
   - Confirm deletion
   - Verify list is empty
   - Verify can re-import

4. **Error handling**:
   - Try uploading a non-CSV file
   - Try uploading malformed CSV (edit a row to have invalid date)
   - Verify clear error message with line number

5. **User isolation**:
   - Create second user account
   - Verify they don't see first user's transactions
   - Upload same CSV as second user
   - Verify both users have their own copy

## Performance Considerations

- **Bulk operations**: Use `bulk_create()` for transactions to minimize DB round-trips
- **Mapping cache**: Load all user's mappings once before categorizing (single query)
- **Select related**: Use `select_related("category")` in list view query
- **Target**: <30s for 300 transactions (should be <5s in practice)

## Migration Notes

- No data migration needed (new models)
- "Unknown" category seeded for existing users
- Existing category signal updated to include "Unknown" for new users

## References

- ING CSV sample: `context/transactions_example.csv`
- PRD requirements: FR-003, FR-004, US-01 in `context/foundation/prd.md`
- Categories app pattern: `categories/models.py`, `categories/views.py`
- Roadmap: S-02 in `context/foundation/roadmap.md`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles. See `references/progress-format.md`.

### Phase 1: Models & Migration

#### Automated

- [x] 1.1 App created with models.py, views.py, etc.
- [x] 1.2 Migrations apply cleanly
- [x] 1.3 Django check passes
- [x] 1.4 Linting passes

#### Manual

- [ ] 1.5 Models importable in Django shell
- [ ] 1.6 Existing users have "Unknown" category
- [ ] 1.7 New user registration creates "Unknown" category and predefined mappings
- [ ] 1.8 Existing users have predefined mappings (BIEDRONKA, LIDL, etc.)

### Phase 2: CSV Parser

#### Automated

- [ ] 2.1 Linting passes
- [ ] 2.2 Module importable

#### Manual

- [ ] 2.3 Parse sample CSV returns ~166 transactions
- [ ] 2.4 Amounts are Decimal, dates are date objects
- [ ] 2.5 Merchant names are cleaned

### Phase 3: Auto-categorization Engine

#### Automated

- [ ] 3.1 Linting passes
- [ ] 3.2 Module importable

#### Manual

- [ ] 3.3 Normalization produces expected results
- [ ] 3.4 Categorization returns None when no mapping
- [ ] 3.5 Test mapping matches correctly

### Phase 4: Views & URLs

#### Automated

- [ ] 4.1 Django check passes
- [ ] 4.2 Linting passes
- [ ] 4.3 Server starts

#### Manual

- [ ] 4.4 Transaction list page loads
- [ ] 4.5 Upload imports 166 transactions
- [ ] 4.6 Re-upload shows 0 imported, 166 skipped
- [ ] 4.7 Delete all clears transactions

### Phase 5: Templates & Modal UI

#### Automated

- [ ] 5.1 Linting passes
- [ ] 5.2 Server starts without template errors

#### Manual

- [ ] 5.3 Dashboard shows Transactions link
- [ ] 5.4 Upload modal opens and works
- [ ] 5.5 Unknown category has distinct styling
- [ ] 5.6 Amounts show negative in red
- [ ] 5.7 Delete All asks for confirmation
