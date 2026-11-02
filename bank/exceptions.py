"""Custom exceptions for the banking system.

Defining our own exception classes lets the rest of the program tell
"expected" banking problems (like not enough money) apart from real bugs.
The command-line menu catches ``BankError`` and shows a friendly message,
while unexpected errors are logged with a full traceback.
"""


class BankError(Exception):
    """Base class for every error raised on purpose by the bank."""


class InsufficientFundsError(BankError):
    """Raised when a withdrawal or transfer is bigger than the balance."""


class InvalidAmountError(BankError):
    """Raised when an amount is zero, negative, or not a number."""


class NotFoundError(BankError):
    """Raised when an ID (customer, account, loan, card...) is unknown."""


class CreditLimitExceededError(BankError):
    """Raised when a credit card purchase would go over the card's limit."""
