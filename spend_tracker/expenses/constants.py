"""
Centralised message strings so views/serializers never hardcode copy inline.
Keeps wording consistent and makes it trivial to change a message in one place.
"""

# Generic
SUCCESS = "Success"
VALIDATION_FAILED = "Validation failed"
GENERIC_ERROR = "Something went wrong. Please try again later."

# Auth
ACCOUNT_CREATED = "Account created successfully"
LOGIN_SUCCESS = "Login successful"
TOKEN_REFRESHED = "Token refreshed"
PASSWORD_MISMATCH = "Password and confirm password do not match."

# Categories
CATEGORY_CREATED = "Category created"
CATEGORY_ALREADY_EXISTS = "Category already exists."

# Expenses
EXPENSE_CREATED = "Expense added"
AMOUNT_MUST_BE_POSITIVE = "Amount must be greater than 0."
FUTURE_DATE_NOT_ALLOWED = "Expense date cannot be in the future."
CATEGORY_NOT_OWNED = "You can only use categories you own."

# Summary
INVALID_MONTH_FORMAT = "month must be in YYYY-MM format."
NO_PREVIOUS_MONTH_DATA = "No spend recorded last month"
