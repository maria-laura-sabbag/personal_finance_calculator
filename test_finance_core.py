import os
import json
import unittest
import tempfile

from finance_core import FinanceManager, ValidationError


class TestFinanceManager(unittest.TestCase):

    def setUp(self):
        # Use a temporary folder so your real finance_data files are not affected
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.json_path = os.path.join(self.tmp_dir.name, "finance_data.json")
        self.txt_path = os.path.join(self.tmp_dir.name, "finance_data.txt")
        self.fm = FinanceManager(json_path=self.json_path, txt_path=self.txt_path)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_add_income_valid(self):
        self.fm.add_income("Salary", 1000)
        self.assertEqual(len(self.fm.incomes), 1)
        self.assertEqual(self.fm.total_income(), 1000.00)

    def test_add_expense_valid(self):
        self.fm.add_expense("Lunch", "Food", 15.50, "2026-02-22")
        self.assertEqual(len(self.fm.expenses), 1)
        self.assertEqual(self.fm.total_expenses(), 15.50)

    def test_balance_calculation(self):
        self.fm.add_income("Salary", 2000)
        self.fm.add_expense("Rent", "Housing", 1200, "2026-02-01")
        self.assertEqual(self.fm.total_income(), 2000.00)
        self.assertEqual(self.fm.total_expenses(), 1200.00)
        self.assertEqual(self.fm.balance(), 800.00)

    def test_invalid_income_non_numeric(self):
        with self.assertRaises(ValidationError):
            self.fm.add_income("Salary", "abc")

    def test_invalid_expense_missing_category(self):
        with self.assertRaises(ValidationError):
            self.fm.add_expense("Coffee", "", 5, "2026-02-22")

    def test_invalid_negative_amount(self):
        with self.assertRaises(ValidationError):
            self.fm.add_income("Salary", -100)

        with self.assertRaises(ValidationError):
            self.fm.add_expense("Something", "Other", -10, "2026-02-22")

    def test_invalid_date_format(self):
        with self.assertRaises(ValidationError):
            self.fm.add_expense("Lunch", "Food", 10, "02/22/2026")

    def test_save_creates_files(self):
        self.fm.add_income("Salary", 1500)
        self.fm.add_expense("Groceries", "Food", 100, "2026-02-10")
        self.fm.save()

        self.assertTrue(os.path.exists(self.json_path))
        self.assertTrue(os.path.exists(self.txt_path))

        # Check JSON content basic structure
        with open(self.json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("incomes", data)
        self.assertIn("expenses", data)
        self.assertEqual(len(data["incomes"]), 1)
        self.assertEqual(len(data["expenses"]), 1)

    def test_load_roundtrip(self):
        # Save data
        self.fm.add_income("Freelance", 500)
        self.fm.add_expense("Uber", "Transport", 25, "2026-02-12")
        self.fm.save()

        # Create new instance and load
        fm2 = FinanceManager(json_path=self.json_path, txt_path=self.txt_path)
        fm2.load()

        self.assertEqual(fm2.total_income(), 500.00)
        self.assertEqual(fm2.total_expenses(), 25.00)
        self.assertEqual(fm2.balance(), 475.00)


if __name__ == "__main__":
    unittest.main()