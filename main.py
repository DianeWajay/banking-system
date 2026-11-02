#!/usr/bin/env python
"""Command-line interface for the banking system.

Run it with:  python main.py

The menu reads what the user types, calls a method on the ``Bank`` object
and prints the result. All error handling for user mistakes happens here
in one ``try/except`` block inside ``run()``.
"""

from bank.bank import Bank
from bank.exceptions import BankError
from bank.logger_config import get_logger

logger = get_logger()


class BankCLI:
    """Text menu that lets a user work with a ``Bank``."""

    def __init__(self, bank):
        """Store the bank and build the menu.

        The menu is a dict of ``choice -> (label, method)``. Adding a new
        option only means adding one line here and one method below.
        """
        self.bank = bank
        self.menu = {
            "1": ("Add customer", self.add_customer),
            "2": ("Update customer address", self.update_address),
            "3": ("Open account", self.open_account),
            "4": ("Deposit", self.deposit),
            "5": ("Withdraw", self.withdraw),
            "6": ("Transfer", self.transfer),
            "7": ("Show transaction history", self.history),
            "8": ("Issue loan", self.issue_loan),
            "9": ("Pay loan", self.pay_loan),
            "10": ("Issue credit card", self.issue_card),
            "11": ("Charge credit card", self.charge_card),
            "12": ("Pay credit card", self.pay_card),
            "13": ("Add employee", self.add_employee),
            "14": ("List customers and employees", self.list_people),
            "15": ("Customer summary", self.summary),
            "16": ("Apply monthly interest to savings", self.interest),
            "0": ("Exit", None),
        }

    # ----- main loop ------------------------------------------------------
    def run(self):
        """Show the menu until the user chooses Exit."""
        print(f"\n=== Welcome to {self.bank.name} ===")
        while True:
            self.show_menu()
            choice = input("Choose an option: ").strip()
            if choice == "0":
                print("Goodbye!")
                break
            if choice not in self.menu:
                logger.warning("Invalid menu choice: %r", choice)
                continue
            _, action = self.menu[choice]
            try:
                action()
            except BankError as err:
                # Expected problems (bad amount, unknown ID...): log as a
                # warning so it shows on screen and is saved to the file.
                logger.warning(str(err))
            except (KeyboardInterrupt, EOFError):
                print("\nAction cancelled.")
            except Exception:  # pylint: disable=broad-except
                # Anything else is a bug. Log the full traceback but keep
                # the program running instead of crashing.
                logger.exception("Unexpected error. Please try again.")

    def show_menu(self):
        """Print the numbered menu."""
        print()
        for key, (label, _) in self.menu.items():
            print(f"{key:>3}. {label}")

    # ----- small input helpers -------------------------------------------
    @staticmethod
    def ask(prompt):
        """Ask for text and refuse empty answers."""
        value = input(f"{prompt}: ").strip()
        if not value:
            raise BankError(f"{prompt} cannot be empty.")
        return value

    @staticmethod
    def ask_number(prompt, cast=float):
        """Ask for a number; turn bad input into a ``BankError``."""
        raw = input(f"{prompt}: ").strip()
        try:
            return cast(raw)
        except ValueError:
            raise BankError(f"'{raw}' is not a valid number.") from None

    # ----- menu actions ---------------------------------------------------
    def add_customer(self):
        """Menu: add a customer."""
        customer = self.bank.add_customer(
            self.ask("First name"), self.ask("Last name"),
            self.ask("Address"))
        print(f"Created {customer}")

    def update_address(self):
        """Menu: change a customer's address."""
        customer = self.bank.update_customer_address(
            self.ask("Customer ID"), self.ask("New address"))
        print(f"Updated: {customer}")

    def open_account(self):
        """Menu: open a checking or savings account."""
        account = self.bank.open_account(
            self.ask("Customer ID"),
            self.ask("Account type (checking/savings)"),
            self.ask_number("Initial deposit (0 for none)"))
        print(f"Opened {account}")

    def deposit(self):
        """Menu: deposit money."""
        balance = self.bank.deposit(self.ask("Account ID"),
                                    self.ask_number("Amount"))
        print(f"New balance: ${balance:,.2f}")

    def withdraw(self):
        """Menu: withdraw money."""
        balance = self.bank.withdraw(self.ask("Account ID"),
                                     self.ask_number("Amount"))
        print(f"New balance: ${balance:,.2f}")

    def transfer(self):
        """Menu: transfer between accounts."""
        self.bank.transfer(self.ask("From account ID"),
                           self.ask("To account ID"),
                           self.ask_number("Amount"))
        print("Transfer complete.")

    def history(self):
        """Menu: print an account's transactions."""
        account = self.bank.get_account(self.ask("Account ID"))
        print(account)
        if not account.transactions:
            print("  No transactions yet.")
        for t in account.transactions:
            print(f"  {t['timestamp']}  {t['type']:<10} "
                  f"${t['amount']:>10,.2f}  "
                  f"balance ${t['balance_after']:,.2f}")

    def issue_loan(self):
        """Menu: give a customer a loan."""
        loan = self.bank.issue_loan(
            self.ask("Customer ID"), self.ask_number("Loan amount"),
            self.ask_number("Yearly interest rate (e.g. 0.05)"),
            self.ask_number("Term in months", int))
        print(f"Issued {loan}")
        print(f"Monthly payment: ${loan.monthly_payment:,.2f}")

    def pay_loan(self):
        """Menu: pay down a loan."""
        remaining = self.bank.pay_loan(self.ask("Loan ID"),
                                       self.ask_number("Amount"))
        print(f"Remaining on loan: ${remaining:,.2f}")

    def issue_card(self):
        """Menu: give a customer a credit card."""
        card = self.bank.issue_credit_card(self.ask("Customer ID"),
                                           self.ask_number("Credit limit"))
        print(f"Issued {card}")

    def charge_card(self):
        """Menu: make a purchase on a card."""
        balance = self.bank.charge_card(self.ask("Card ID"),
                                        self.ask_number("Amount"))
        print(f"Card balance owed: ${balance:,.2f}")

    def pay_card(self):
        """Menu: pay a card."""
        balance = self.bank.pay_card(self.ask("Card ID"),
                                     self.ask_number("Amount"))
        print(f"Card balance owed: ${balance:,.2f}")

    def add_employee(self):
        """Menu: hire an employee."""
        employee = self.bank.add_employee(
            self.ask("First name"), self.ask("Last name"),
            self.ask("Address"), self.ask("Position"),
            self.ask_number("Yearly salary"))
        print(f"Hired {employee}")

    def list_people(self):
        """Menu: list everyone."""
        print("Customers:")
        for customer in self.bank.customers.values():
            print(f"  {customer}")
        print("Employees:")
        for employee in self.bank.employees.values():
            print(f"  {employee}")

    def summary(self):
        """Menu: show one customer's products."""
        print(self.bank.customer_summary(self.ask("Customer ID")))

    def interest(self):
        """Menu: pay a month of interest."""
        total = self.bank.apply_monthly_interest()
        print(f"Total interest paid: ${total:,.2f}")


def main():
    """Program entry point."""
    try:
        BankCLI(Bank()).run()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
