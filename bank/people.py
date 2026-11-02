"""People in the bank: customers and employees.

Design choice: ``Customer`` and ``Employee`` share a first name, last name
and address, so both inherit from a common ``Person`` base class. This is
*inheritance*: shared code lives in one place.
"""

from bank.exceptions import BankError


class Person:
    """A person with a name and an address.

    Attributes are stored with a leading underscore (``_first_name``) to
    signal "private, please use the property". The ``@property`` getters and
    ``@x.setter`` setters let us validate data whenever it changes. This is
    *encapsulation*.
    """

    def __init__(self, first_name, last_name, address):
        """Create a person.

        Args:
            first_name (str): Given name.
            last_name (str): Family name.
            address (str): Mailing address.
        """
        # These assignments go through the setters below, so even the
        # first values get validated.
        self.first_name = first_name
        self.last_name = last_name
        self.address = address

    # ----- getters and setters -------------------------------------------
    @property
    def first_name(self):
        """str: The person's first name."""
        return self._first_name

    @first_name.setter
    def first_name(self, value):
        self._first_name = self._clean_name(value, "First name")

    @property
    def last_name(self):
        """str: The person's last name."""
        return self._last_name

    @last_name.setter
    def last_name(self, value):
        self._last_name = self._clean_name(value, "Last name")

    @property
    def address(self):
        """str: The person's address."""
        return self._address

    @address.setter
    def address(self, value):
        self._address = str(value).strip()

    @property
    def full_name(self):
        """str: First and last name together (read only, no setter)."""
        return f"{self.first_name} {self.last_name}"

    # ----- helpers --------------------------------------------------------
    @staticmethod
    def _clean_name(value, label):
        """Strip spaces and make sure a name is not empty."""
        value = str(value).strip()
        if not value:
            raise BankError(f"{label} cannot be empty.")
        return value


class Customer(Person):
    """A bank customer who can own accounts, loans and credit cards.

    The customer only stores the *IDs* of their products, not the objects
    themselves. The ``Bank`` class looks the objects up by ID. Keeping IDs
    makes saving to JSON simple and avoids storing the same data twice.
    """

    def __init__(self, customer_id, first_name, last_name, address,
                 account_ids=None, loan_ids=None, card_ids=None):
        """Create a customer.

        Args:
            customer_id (str): Unique ID such as ``"C001"``.
            first_name (str): Given name.
            last_name (str): Family name.
            address (str): Mailing address.
            account_ids (list[str]): IDs of accounts this customer owns.
            loan_ids (list[str]): IDs of this customer's loans.
            card_ids (list[str]): IDs of this customer's credit cards.
        """
        super().__init__(first_name, last_name, address)
        self.customer_id = customer_id
        # "or []" avoids the classic bug of using a mutable default argument.
        self.account_ids = account_ids or []
        self.loan_ids = loan_ids or []
        self.card_ids = card_ids or []

    def to_dict(self):
        """Turn the customer into a plain dict so it can be saved as JSON."""
        return {
            "customer_id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address,
            "account_ids": self.account_ids,
            "loan_ids": self.loan_ids,
            "card_ids": self.card_ids,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild a customer from a dict loaded out of the JSON file."""
        return cls(**data)

    def __str__(self):
        return f"[{self.customer_id}] {self.full_name}, {self.address}"


class Employee(Person):
    """A bank employee, e.g. a teller or loan officer."""

    def __init__(self, employee_id, first_name, last_name, address,
                 position, salary):
        """Create an employee.

        Args:
            employee_id (str): Unique ID such as ``"E001"``.
            first_name (str): Given name.
            last_name (str): Family name.
            address (str): Mailing address.
            position (str): Job title, e.g. ``"Teller"``.
            salary (float): Yearly salary.
        """
        super().__init__(first_name, last_name, address)
        self.employee_id = employee_id
        self.position = position
        self.salary = salary

    @property
    def salary(self):
        """float: Yearly salary. Must not be negative."""
        return self._salary

    @salary.setter
    def salary(self, value):
        value = float(value)
        if value < 0:
            raise BankError("Salary cannot be negative.")
        self._salary = value

    def to_dict(self):
        """Turn the employee into a plain dict for JSON."""
        return {
            "employee_id": self.employee_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "address": self.address,
            "position": self.position,
            "salary": self.salary,
        }

    @classmethod
    def from_dict(cls, data):
        """Rebuild an employee from a dict."""
        return cls(**data)

    def __str__(self):
        return f"[{self.employee_id}] {self.full_name} - {self.position}"
