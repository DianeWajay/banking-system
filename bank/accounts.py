"""Bank accounts: a general ``Account`` plus checking and savings types.

Design choices:
  * ``Account`` holds everything every account needs: balance, deposit,
    withdraw and a transaction history.
  * ``CheckingAccount`` and ``SavingsAccount`` *inherit* from ``Account``
    and change only what is different. Checking allows a small overdraft;
    savings earns interest. Overriding a method in a child class is called
    *polymorphism*: the bank can call ``withdraw()`` on any account and the
    right version runs.
  * The balance has a getter but **no setter**. The only way to change it
    is through ``deposit()`` and ``withdraw()``, so every change is checked
    and recorded in the history.
"""

from datetime import datetime

from bank.exceptions import InsufficientFundsError, InvalidAmountError


def validate_amount(amount):
    """Convert ``amount`` to a positive float or raise ``InvalidAmountError``.

    Shared by accounts, loans and credit cards so the rule lives in one place.
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise InvalidAmountError(f"'{amount}' is not a valid number.")
    if amount <= 0:
        raise InvalidAmountError("Amount must be greater than zero.")
    return round(amount, 2)


class Account:
    """A general bank account owned by one customer."""

    account_type = "general"  # class attribute, overridden by subclasses

    def __init__(self, account_id, customer_id, balance=0.0,
                 transactions=None):
        """Create an account.

        Args:
            account_id (str): Unique ID such as ``"A001"``.
            customer_id (str): ID of the customer who owns the account.
            balance (float): Starting balance.
            transactions (list[dict]): Earlier transactions (used when
                loading from the JSON file).
        """
        self.account_id = account_id
        self.customer_id = customer_id
        self._balance = round(float(balance), 2)
        self.transactions = transactions or []

    @property
    def balance(self):
        """float: Current balance. Read only; use deposit/withdraw."""
        return self._balance

    def deposit(self, amount):
        """Add money to the account.

        Args:
            amount (float): Amount to add. Must be positive.

        Returns:
            float: The new balance.
        """
        amount = validate_amount(amount)
        self._balance = round(self._balance + amount, 2)
        self._record("deposit", amount)
        return self._balance

    def withdraw(self, amount):
        """Take money out of the account.

        Args:
            amount (float): Amount to remove. Must be positive and not
                more than the money available.

        Returns:
            float: The new balance.

        Raises:
            InsufficientFundsError: If there isn't enough money.
        """
        amount = validate_amount(amount)
        if amount > self.available_funds():
            raise InsufficientFundsError(
                f"Cannot withdraw ${amount:,.2f}; only "
                f"${self.available_funds():,.2f} available.")
        self._balance = round(self._balance - amount, 2)
        self._record("withdrawal", amount)
        return self._balance

    def available_funds(self):
        """Return how much can be withdrawn. Subclasses may change this."""
        return self._balance

    def _record(self, kind, amount):
        """Add one entry to the transaction history."""
        self.transactions.append({
            "type": kind,
            "amount": amount,
            "balance_after": self._balance,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        })

    def to_dict(self):
        """Turn the account into a plain dict for JSON."""
        return {
            "account_id": self.account_id,
            "customer_id": self.customer_id,
            "account_type": self.account_type,
            "balance": self._balance,
            "transactions": self.transactions,
        }

    def __str__(self):
        return (f"[{self.account_id}] {self.account_type.title()} "
                f"account - balance ${self._balance:,.2f}")


class CheckingAccount(Account):
    """An everyday account that allows a small overdraft."""

    account_type = "checking"

    def __init__(self, account_id, customer_id, balance=0.0,
                 transactions=None, overdraft_limit=100.0):
        """Create a checking account.

        Args:
            overdraft_limit (float): How far below zero the balance may go.
            Other args: see ``Account``.
        """
        super().__init__(account_id, customer_id, balance, transactions)
        self.overdraft_limit = float(overdraft_limit)

    def available_funds(self):
        """Balance plus the overdraft the bank allows."""
        return self._balance + self.overdraft_limit

    def to_dict(self):
        """Add the overdraft limit to the parent's dict."""
        data = super().to_dict()
        data["overdraft_limit"] = self.overdraft_limit
        return data


class SavingsAccount(Account):
    """An account that earns interest and cannot be overdrawn."""

    account_type = "savings"

    def __init__(self, account_id, customer_id, balance=0.0,
                 transactions=None, interest_rate=0.02):
        """Create a savings account.

        Args:
            interest_rate (float): Yearly rate, e.g. ``0.02`` for 2%.
            Other args: see ``Account``.
        """
        super().__init__(account_id, customer_id, balance, transactions)
        self.interest_rate = interest_rate

    @property
    def interest_rate(self):
        """float: Yearly interest rate between 0 and 1."""
        return self._interest_rate

    @interest_rate.setter
    def interest_rate(self, value):
        value = float(value)
        if not 0 <= value <= 1:
            raise InvalidAmountError("Interest rate must be between 0 and 1.")
        self._interest_rate = value

    def apply_interest(self):
        """Add one month of interest to the balance.

        Returns:
            float: The interest that was added.
        """
        interest = round(self._balance * self.interest_rate / 12, 2)
        if interest > 0:
            self._balance = round(self._balance + interest, 2)
            self._record("interest", interest)
        return interest

    def to_dict(self):
        """Add the interest rate to the parent's dict."""
        data = super().to_dict()
        data["interest_rate"] = self.interest_rate
        return data


# Maps the "account_type" text stored in JSON back to the right class.
ACCOUNT_CLASSES = {
    "checking": CheckingAccount,
    "savings": SavingsAccount,
}


def account_from_dict(data):
    """Rebuild the correct account subclass from a saved dict.

    This is a small *factory function*: it reads ``account_type`` and picks
    which class to create.
    """
    data = dict(data)  # copy so we don't change the caller's dict
    cls = ACCOUNT_CLASSES[data.pop("account_type")]
    return cls(**data)
