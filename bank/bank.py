"""The ``Bank`` class: the one object that manages everything.

Design choices:
  * *Composition*: a ``Bank`` **has** customers, employees, accounts, loans
    and credit cards. Each group is a dict keyed by ID, so finding one is
    fast (``self.accounts["A001"]``).
  * Every action that changes data (open account, deposit, ...) saves the
    whole bank to a JSON file straight away. If the program crashes later,
    nothing already done is lost.
  * JSON was chosen for storage because it is built into Python, readable
    in any text editor, and maps naturally onto nested Python dicts/lists.
"""

import json
import os

from bank.accounts import (CheckingAccount, SavingsAccount,
                           account_from_dict)
from bank.exceptions import BankError, NotFoundError
from bank.logger_config import get_logger
from bank.people import Customer, Employee
from bank.services import CreditCard, Loan

logger = get_logger()

DEFAULT_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "bank_data.json")


class Bank:
    """A bank that stores its data in a JSON file."""

    def __init__(self, name="Springboard Bank", data_file=DEFAULT_DATA_FILE):
        """Create the bank and load any saved data.

        Args:
            name (str): Name of the bank.
            data_file (str): Path of the JSON file used for storage.
        """
        self.name = name
        self.data_file = data_file
        self.customers = {}
        self.employees = {}
        self.accounts = {}
        self.loans = {}
        self.credit_cards = {}
        self.load()

    # ===================================================================
    # Saving and loading
    # ===================================================================
    def save(self):
        """Write all bank data to the JSON file.

        We write to a temporary file first and then rename it. Renaming is
        all-or-nothing, so a crash mid-save can't leave a half-written file.
        """
        data = {
            "bank_name": self.name,
            "customers": [c.to_dict() for c in self.customers.values()],
            "employees": [e.to_dict() for e in self.employees.values()],
            "accounts": [a.to_dict() for a in self.accounts.values()],
            "loans": [ln.to_dict() for ln in self.loans.values()],
            "credit_cards": [c.to_dict() for c in self.credit_cards.values()],
        }
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        temp_file = self.data_file + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(temp_file, self.data_file)
        except OSError as err:
            logger.error("Could not save data to %s: %s", self.data_file, err)
            raise BankError("Saving failed; see logs/bank.log.") from err

    def load(self):
        """Read bank data from the JSON file, if it exists."""
        if not os.path.exists(self.data_file):
            logger.info("No saved data found; starting a new bank.")
            return
        try:
            with open(self.data_file, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as err:
            # Don't crash: warn, keep the bad file for inspection, start empty.
            logger.error("Could not read %s: %s. Starting with empty data.",
                         self.data_file, err)
            return

        self.name = data.get("bank_name", self.name)
        self.customers = {c["customer_id"]: Customer.from_dict(c)
                          for c in data.get("customers", [])}
        self.employees = {e["employee_id"]: Employee.from_dict(e)
                          for e in data.get("employees", [])}
        self.accounts = {a["account_id"]: account_from_dict(a)
                         for a in data.get("accounts", [])}
        self.loans = {ln["loan_id"]: Loan.from_dict(ln)
                      for ln in data.get("loans", [])}
        self.credit_cards = {c["card_id"]: CreditCard.from_dict(c)
                             for c in data.get("credit_cards", [])}
        logger.info("Loaded %d customers and %d accounts.",
                    len(self.customers), len(self.accounts))

    # ===================================================================
    # Helpers
    # ===================================================================
    @staticmethod
    def _next_id(prefix, existing):
        """Make the next ID like ``A003`` from the IDs already used."""
        numbers = [int(key[len(prefix):]) for key in existing
                   if key[len(prefix):].isdigit()]
        return f"{prefix}{max(numbers, default=0) + 1:03d}"

    @staticmethod
    def _find(collection, item_id, label):
        """Look up an item by ID or raise ``NotFoundError``."""
        try:
            return collection[item_id.strip().upper()]
        except KeyError:
            raise NotFoundError(f"{label} '{item_id}' not found.") from None

    def get_customer(self, customer_id):
        """Return the customer with this ID."""
        return self._find(self.customers, customer_id, "Customer")

    def get_account(self, account_id):
        """Return the account with this ID."""
        return self._find(self.accounts, account_id, "Account")

    def get_loan(self, loan_id):
        """Return the loan with this ID."""
        return self._find(self.loans, loan_id, "Loan")

    def get_card(self, card_id):
        """Return the credit card with this ID."""
        return self._find(self.credit_cards, card_id, "Credit card")

    # ===================================================================
    # People
    # ===================================================================
    def add_customer(self, first_name, last_name, address):
        """Register a new customer and return it."""
        customer_id = self._next_id("C", self.customers)
        customer = Customer(customer_id, first_name, last_name, address)
        self.customers[customer_id] = customer
        self.save()
        logger.info("Added customer %s (%s).", customer_id,
                    customer.full_name)
        return customer

    def update_customer_address(self, customer_id, new_address):
        """Change a customer's address (uses the ``address`` setter)."""
        customer = self.get_customer(customer_id)
        customer.address = new_address
        self.save()
        logger.info("Updated address for %s.", customer.customer_id)
        return customer

    def add_employee(self, first_name, last_name, address, position, salary):
        """Hire a new employee and return it."""
        employee_id = self._next_id("E", self.employees)
        employee = Employee(employee_id, first_name, last_name, address,
                            position, salary)
        self.employees[employee_id] = employee
        self.save()
        logger.info("Added employee %s (%s).", employee_id, position)
        return employee

    # ===================================================================
    # Accounts
    # ===================================================================
    def open_account(self, customer_id, account_type, initial_deposit=0):
        """Open a checking or savings account for a customer.

        Args:
            customer_id (str): Owner's ID.
            account_type (str): ``"checking"`` or ``"savings"``.
            initial_deposit (float): Optional first deposit.

        Returns:
            Account: The new account.
        """
        customer = self.get_customer(customer_id)
        account_type = account_type.strip().lower()
        classes = {"checking": CheckingAccount, "savings": SavingsAccount}
        if account_type not in classes:
            raise BankError("Account type must be 'checking' or 'savings'.")

        account_id = self._next_id("A", self.accounts)
        account = classes[account_type](account_id, customer.customer_id)
        if float(initial_deposit or 0) > 0:
            account.deposit(initial_deposit)

        self.accounts[account_id] = account
        customer.account_ids.append(account_id)
        self.save()
        logger.info("Opened %s account %s for %s.", account_type,
                    account_id, customer.customer_id)
        return account

    def deposit(self, account_id, amount):
        """Deposit into an account and return the new balance."""
        account = self.get_account(account_id)
        balance = account.deposit(amount)
        self.save()
        logger.info("Deposited %s into %s.", amount, account.account_id)
        return balance

    def withdraw(self, account_id, amount):
        """Withdraw from an account and return the new balance."""
        account = self.get_account(account_id)
        balance = account.withdraw(amount)
        self.save()
        logger.info("Withdrew %s from %s.", amount, account.account_id)
        return balance

    def transfer(self, from_id, to_id, amount):
        """Move money between two accounts.

        The withdrawal happens first; if it fails, the deposit never runs,
        so money can't appear out of nowhere.
        """
        source = self.get_account(from_id)
        target = self.get_account(to_id)
        if source is target:
            raise BankError("Cannot transfer to the same account.")
        source.withdraw(amount)
        target.deposit(amount)
        self.save()
        logger.info("Transferred %s from %s to %s.", amount,
                    source.account_id, target.account_id)

    def apply_monthly_interest(self):
        """Add one month of interest to every savings account."""
        total = 0.0
        for account in self.accounts.values():
            # isinstance checks which class the object belongs to.
            if isinstance(account, SavingsAccount):
                total += account.apply_interest()
        self.save()
        logger.info("Applied $%.2f interest to savings accounts.", total)
        return round(total, 2)

    # ===================================================================
    # Loans and credit cards
    # ===================================================================
    def issue_loan(self, customer_id, principal, interest_rate, term_months):
        """Give a customer a loan and return it."""
        customer = self.get_customer(customer_id)
        loan_id = self._next_id("L", self.loans)
        loan = Loan(loan_id, customer.customer_id, principal, interest_rate,
                    term_months)
        self.loans[loan_id] = loan
        customer.loan_ids.append(loan_id)
        self.save()
        logger.info("Issued loan %s to %s.", loan_id, customer.customer_id)
        return loan

    def pay_loan(self, loan_id, amount):
        """Make a loan payment and return what is still owed."""
        loan = self.get_loan(loan_id)
        remaining = loan.make_payment(amount)
        self.save()
        logger.info("Payment of %s on loan %s.", amount, loan.loan_id)
        return remaining

    def issue_credit_card(self, customer_id, credit_limit):
        """Give a customer a credit card and return it."""
        customer = self.get_customer(customer_id)
        card_id = self._next_id("CC", self.credit_cards)
        card = CreditCard(card_id, customer.customer_id, credit_limit)
        self.credit_cards[card_id] = card
        customer.card_ids.append(card_id)
        self.save()
        logger.info("Issued card %s to %s.", card_id, customer.customer_id)
        return card

    def charge_card(self, card_id, amount):
        """Charge a credit card and return the new balance owed."""
        card = self.get_card(card_id)
        balance = card.charge(amount)
        self.save()
        logger.info("Charged %s to card %s.", amount, card.card_id)
        return balance

    def pay_card(self, card_id, amount):
        """Pay a credit card and return the new balance owed."""
        card = self.get_card(card_id)
        balance = card.pay(amount)
        self.save()
        logger.info("Payment of %s on card %s.", amount, card.card_id)
        return balance

    # ===================================================================
    # Reports
    # ===================================================================
    def customer_summary(self, customer_id):
        """Return a text summary of everything a customer has."""
        customer = self.get_customer(customer_id)
        lines = [str(customer)]
        lines += ["  " + str(self.accounts[a]) for a in customer.account_ids]
        lines += ["  " + str(self.loans[ln]) for ln in customer.loan_ids]
        lines += ["  " + str(self.credit_cards[c]) for c in customer.card_ids]
        if len(lines) == 1:
            lines.append("  (no accounts or services yet)")
        return "\n".join(lines)
