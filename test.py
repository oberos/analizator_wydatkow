# $env:DEBUG="True" ; pdm run python manage.py shell

from django.contrib.auth.models import User

from transactions.categorization import categorize_transaction

# Create a test user
user, created = User.objects.get_or_create(username="testuser")
# Test cases
test_cases = [
    ("ROSSMANN SKLEP 1337 SWIETOCHLOWIC", "Beauty"),
    ("ORLEN STACJA NR 100 MIKOLOW - BOR", "Transportation"),
    ("CIRCLE K RUDA SLAS RUDA SLLSKA 417", "Transportation"),
    ("APTEKA HYGIEIA SWIETOCHLOWIC POL", "Health"),
    (' FHU "AGA"-LEWIATAN 2  Ruda Slaska ', "Food and Household Chemicals"),
    ("Netflix", "Bills"),
    ("Unknown Merchant", None),  # Expect None for unknown merchant
    ("SHOPPINGBPARK", None),  # Must not match short "BP" token from transportation
]
for raw_merchant, expected_category_name in test_cases:
    category = categorize_transaction(user, raw_merchant)
    category_name = category.name if category else None
    print(f"Raw Merchant: '{raw_merchant}' -> Category: '{category_name}' (Expected: '{expected_category_name}')")

# Results:
# Raw Merchant: 'ROSSMANN SKLEP 1337 SWIETOCHLOWIC' -> Category: 'Beauty' (Expected: 'Beauty')
# Raw Merchant: 'ORLEN STACJA NR 100 MIKOLOW - BOR' -> Category: 'Transportation' (Expected: 'Transportation')
# Raw Merchant: 'CIRCLE K RUDA SLAS RUDA SLLSKA 417' -> Category: 'Transportation' (Expected: 'Transportation')
# Raw Merchant: 'APTEKA HYGIEIA SWIETOCHLOWIC POL' -> Category: 'Health' (Expected: 'Health')
# Raw Merchant: ' FHU "AGA"-LEWIATAN 2  Ruda Slaska '
# -> Category: 'Food and Household Chemicals' (Expected: 'Food and Household Chemicals')
# Raw Merchant: 'Netflix' -> Category: 'Bills' (Expected: 'Bills')
# Raw Merchant: 'Unknown Merchant' -> Category: 'None' (Expected: 'None')
# Raw Merchant: 'SHOPPINGBPARK' -> Category: 'None' (Expected: 'None')
