"""Bank services: loans and credit cards.

Both are things the bank gives a customer that the customer later pays
back. They are separate classes because they behave differently: a loan
is a fixed amount paid back over time, a credit card can be used again and
again up to a limit.
"""

from bank.accounts import validate_amount
from bank.exceptions import CreditLimitExceededError, InvalidAmountError


class Loan:
    """A loan given to a customer."""

    def __init__(self, loan_id, customer_id, principal, interest_rate,
                 term_months, remaining_balance=None, status="active"):
        """Create a loan.

        Args:
            loan_id (str): Unique ID such as ``"L001"``.
            customer_id (str): ID of the borrower.
            principal (float): Amount borrowed.
            interest_rate (float): Yearly rate, e.g. ``0.05`` for 5%.
            term_months (int): Number of months to pay it back.
            remaining_balance (float): What is still owed. Defaults to the
                principal plus simple interest for the whole term.
            status (str): ``"active"`` or ``"paid"``.
        """
        self.loan_id = loan_id
        self.customer_id = customer_id
        self.principal = validate_amount(principal)
        self.interest_rate = float(interest_rate)
        self.term_months = int(term_months)
        if remaining_balance is None:
            # Simple interest keeps the math easy to follow.
            years = self.term_months / 12
            remaining_balance = self.principal * (
                1 + self.interest_rate * years)
        self.remaining_balance = round(float(remaining_balance), 2)
        self.status = status

    @property
    def monthly_payment(self):
        """float: Suggested monthly payment (total owed / months)."""
        total = self.principal * (1 + self.interest_rate * self.term_months
                                  / 12)
        return round(total / self.term_months, 2)

    def make_payment(self, amount):
        """Pay part of the loan back.

        Args:
            amount (float): Amount paid. Cannot be more than what is owed.

        Returns:
            float: The remaining balance after the payment.
        """
        amount = validate_amount(amount)
        if amount > self.remaining_balance:
            raise InvalidAmountError(
                f"Payment is more than the ${self.remaining_balance:,.2f} "
                "still owed.")
        self.remaining_balance = round(self.remaining_balance - amount, 2)
        if self.remaining_balance == 0:
            self.status = "paid"
        return self.remaining_balance

    def to_dict(self):
        """Turn the loan into a plain dict for JSON."""
        return {
            "loan_id": self.loan_id,
            "customer_id": self.customer_id,
            "principal": self.principal,
            "interest_rate": self.interest_rate,
            "term_months": self.term_months,
            "remaining_balance": self.remaining_balance,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a loan from a dict."""
        return cls(**data)

    def __str__(self):
        return (f"[{self.loan_id}] Loan ${self.principal:,.2f} at "
                f"{self.interest_rate:.1%} - owes "
                f"${self.remaining_balance:,.2f} ({self.status})")


class CreditCard:
    """A credit card with a spending limit."""

    def __init__(self, card_id, customer_id, credit_limit, balance=0.0):
        """Create a credit card.

        Args:
            card_id (str): Unique ID such as ``"CC001"``.
            customer_id (str): ID of the card holder.
            credit_limit (float): Most the customer may owe at once.
            balance (float): Amount currently owed.
        """
        self.card_id = card_id
        self.customer_id = customer_id
        self.credit_limit = validate_amount(credit_limit)
        self.balance = round(float(balance), 2)

    @property
    def available_credit(self):
        """float: How much more can be charged."""
        return round(self.credit_limit - self.balance, 2)

    def charge(self, amount):
        """Make a purchase on the card.

        Raises:
            CreditLimitExceededError: If the purchase is over the limit.
        """
        amount = validate_amount(amount)
        if amount > self.available_credit:
            raise CreditLimitExceededError(
                f"Charge of ${amount:,.2f} exceeds available credit of "
                f"${self.available_credit:,.2f}.")
        self.balance = round(self.balance + amount, 2)
        return self.balance

    def pay(self, amount):
        """Pay off part of the card balance."""
        amount = validate_amount(amount)
        if amount > self.balance:
            raise InvalidAmountError(
                f"Payment is more than the ${self.balance:,.2f} owed.")
        self.balance = round(self.balance - amount, 2)
        return self.balance

    def to_dict(self):
        """Turn the card into a plain dict for JSON."""
        return {
            "card_id": self.card_id,
            "customer_id": self.customer_id,
            "credit_limit": self.credit_limit,
            "balance": self.balance,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a card from a dict."""
        return cls(**data)

    def __str__(self):
        return (f"[{self.card_id}] Credit card - owes ${self.balance:,.2f}"
                f" of ${self.credit_limit:,.2f} limit")
