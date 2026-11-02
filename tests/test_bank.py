"""Unit tests for the banking system. Run with:  python -m unittest"""

import os
import tempfile
import unittest

from bank.bank import Bank
from bank.exceptions import (BankError, CreditLimitExceededError,
                             InsufficientFundsError, InvalidAmountError,
                             NotFoundError)


class BankTests(unittest.TestCase):
    """Tests that use a fresh bank stored in a temporary folder."""

    def setUp(self):
        """Runs before every test: make an empty bank and one customer."""
        self.tmp = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.tmp.name, "bank.json")
        self.bank = Bank(data_file=self.data_file)
        self.customer = self.bank.add_customer("Ada", "Lovelace", "1 Main St")

    def tearDown(self):
        """Runs after every test: delete the temporary folder."""
        self.tmp.cleanup()

    def test_deposit_and_withdraw(self):
        acc = self.bank.open_account("C001", "savings", 100)
        self.assertEqual(self.bank.deposit(acc.account_id, 50), 150)
        self.assertEqual(self.bank.withdraw(acc.account_id, 30), 120)
        self.assertEqual(len(acc.transactions), 3)

    def test_savings_cannot_overdraw(self):
        acc = self.bank.open_account("C001", "savings", 10)
        with self.assertRaises(InsufficientFundsError):
            self.bank.withdraw(acc.account_id, 20)

    def test_checking_allows_overdraft(self):
        acc = self.bank.open_account("C001", "checking", 10)
        self.assertEqual(self.bank.withdraw(acc.account_id, 60), -50)
        with self.assertRaises(InsufficientFundsError):
            self.bank.withdraw(acc.account_id, 100)

    def test_invalid_amounts(self):
        acc = self.bank.open_account("C001", "checking")
        for bad in (-5, 0, "abc"):
            with self.assertRaises(InvalidAmountError):
                self.bank.deposit(acc.account_id, bad)

    def test_transfer(self):
        a = self.bank.open_account("C001", "checking", 100)
        b = self.bank.open_account("C001", "savings")
        self.bank.transfer(a.account_id, b.account_id, 40)
        self.assertEqual((a.balance, b.balance), (60, 40))

    def test_unknown_ids(self):
        with self.assertRaises(NotFoundError):
            self.bank.deposit("A999", 10)
        with self.assertRaises(NotFoundError):
            self.bank.open_account("C999", "checking")

    def test_setter_validation(self):
        with self.assertRaises(BankError):
            self.customer.first_name = "   "
        self.bank.update_customer_address("c001", "2 Oak Ave")
        self.assertEqual(self.customer.address, "2 Oak Ave")

    def test_loan(self):
        loan = self.bank.issue_loan("C001", 1200, 0.10, 12)
        self.assertEqual(loan.remaining_balance, 1320)
        self.assertEqual(loan.monthly_payment, 110)
        self.bank.pay_loan(loan.loan_id, 1320)
        self.assertEqual(loan.status, "paid")

    def test_credit_card(self):
        card = self.bank.issue_credit_card("C001", 500)
        self.bank.charge_card(card.card_id, 400)
        with self.assertRaises(CreditLimitExceededError):
            self.bank.charge_card(card.card_id, 200)
        self.assertEqual(self.bank.pay_card(card.card_id, 100), 300)

    def test_interest(self):
        acc = self.bank.open_account("C001", "savings", 1200)
        self.assertEqual(self.bank.apply_monthly_interest(), 2.0)
        self.assertEqual(acc.balance, 1202)

    def test_data_is_saved_and_reloaded(self):
        acc = self.bank.open_account("C001", "checking", 75)
        self.bank.issue_loan("C001", 500, 0.05, 6)
        self.bank.add_employee("Grace", "Hopper", "HQ", "Teller", 50000)

        reloaded = Bank(data_file=self.data_file)
        self.assertEqual(reloaded.get_account(acc.account_id).balance, 75)
        self.assertEqual(reloaded.get_customer("C001").loan_ids, ["L001"])
        self.assertIn("E001", reloaded.employees)

    def test_corrupt_file_does_not_crash(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            f.write("{not json")
        bank = Bank(data_file=self.data_file)
        self.assertEqual(bank.customers, {})


if __name__ == "__main__":
    unittest.main()
