from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import List, Dict, Any, Optional


class ValidationError(ValueError):
    """Raised when user input is invalid (missing fields, negative values, wrong formats)."""


@dataclass
class IncomeEntry:
    source: str
    amount: float


@dataclass
class ExpenseEntry:
    description: str
    category: str
    amount: float
    date: str  # stored as "YYYY-MM-DD"


class FinanceManager:
    """
    Core logic:
      - store income and expenses in lists
      - validate user inputs
      - compute totals and balance
      - save/load to finance_data.json and finance_data.txt
    """

    def __init__(self, json_path: str = "finance_data.json", txt_path: str = "finance_data.txt"):
        self.json_path = json_path
        self.txt_path = txt_path
        self.incomes: List[IncomeEntry] = []
        self.expenses: List[ExpenseEntry] = []

    # -------------------------
    # Validation helpers
    # -------------------------
    @staticmethod
    def _require_non_empty(value: str, field_name: str) -> str:
        if value is None or str(value).strip() == "":
            raise ValidationError(f"Missing required field: {field_name}")
        return str(value).strip()

    @staticmethod
    def _parse_positive_amount(value: Any, field_name: str = "amount") -> float:
        try:
            amount = float(value)
        except (TypeError, ValueError):
            raise ValidationError(f"{field_name} must be a numeric value.")
        if amount <= 0:
            raise ValidationError(f"{field_name} must be greater than 0 (no negatives or zero).")
        return amount

    @staticmethod
    def _normalize_date(value: Optional[str]) -> str:
        # Accept empty -> today, accept YYYY-MM-DD
        if value is None or str(value).strip() == "":
            return date.today().isoformat()
        s = str(value).strip()
        try:
            # Validate format strictly
            datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("Date must be in YYYY-MM-DD format (example: 2026-02-22).")
        return s

    # -------------------------
    # Core operations
    # -------------------------
    def add_income(self, source: str, amount: Any) -> None:
        source_clean = self._require_non_empty(source, "income source")
        amount_clean = self._parse_positive_amount(amount, "income amount")
        self.incomes.append(IncomeEntry(source=source_clean, amount=amount_clean))

    def add_expense(self, description: str, category: str, amount: Any, date_str: Optional[str]) -> None:
        desc_clean = self._require_non_empty(description, "expense description")
        cat_clean = self._require_non_empty(category, "expense category")
        amount_clean = self._parse_positive_amount(amount, "expense amount")
        date_clean = self._normalize_date(date_str)
        self.expenses.append(
            ExpenseEntry(description=desc_clean, category=cat_clean, amount=amount_clean, date=date_clean)
        )

    def delete_income(self, index: int) -> None:
        if index < 0 or index >= len(self.incomes):
            raise IndexError("Invalid income index.")
        del self.incomes[index]

    def delete_expense(self, index: int) -> None:
        if index < 0 or index >= len(self.expenses):
            raise IndexError("Invalid expense index.")
        del self.expenses[index]

    def total_income(self) -> float:
        return round(sum(i.amount for i in self.incomes), 2)

    def total_expenses(self) -> float:
        return round(sum(e.amount for e in self.expenses), 2)

    def balance(self) -> float:
        return round(self.total_income() - self.total_expenses(), 2)

    # -------------------------
    # Persistence (JSON + TXT)
    # -------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "incomes": [asdict(i) for i in self.incomes],
            "expenses": [asdict(e) for e in self.expenses],
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        self.incomes = []
        self.expenses = []

        incomes = data.get("incomes", [])
        expenses = data.get("expenses", [])

        for item in incomes:
            # Be defensive against bad file contents
            source = str(item.get("source", "")).strip()
            amount = item.get("amount", 0)
            if source != "":
                try:
                    amt = float(amount)
                    if amt > 0:
                        self.incomes.append(IncomeEntry(source=source, amount=amt))
                except (TypeError, ValueError):
                    pass

        for item in expenses:
            description = str(item.get("description", "")).strip()
            category = str(item.get("category", "")).strip()
            amount = item.get("amount", 0)
            d = str(item.get("date", "")).strip()

            if description != "" and category != "":
                try:
                    amt = float(amount)
                    if amt > 0:
                        # validate/normalize date
                        try:
                            d_norm = self._normalize_date(d)
                        except ValidationError:
                            d_norm = date.today().isoformat()
                        self.expenses.append(
                            ExpenseEntry(description=description, category=category, amount=amt, date=d_norm)
                        )
                except (TypeError, ValueError):
                    pass

    def save(self) -> None:
        """
        Save to:
          - JSON file (authoritative)
          - TXT file (human-readable export)
        """
        # Save JSON
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
        except OSError as e:
            raise OSError(f"Could not save JSON file: {e}")

        # Save TXT
        try:
            with open(self.txt_path, "w", encoding="utf-8") as f:
                f.write("=== Personal Finance Manager Data Export ===\n\n")
                f.write("[INCOMES]\n")
                for idx, inc in enumerate(self.incomes, start=1):
                    f.write(f"{idx}. Source: {inc.source} | Amount: {inc.amount:.2f}\n")

                f.write("\n[EXPENSES]\n")
                for idx, exp in enumerate(self.expenses, start=1):
                    f.write(
                        f"{idx}. Date: {exp.date} | Category: {exp.category} | "
                        f"Description: {exp.description} | Amount: {exp.amount:.2f}\n"
                    )

                f.write("\n[SUMMARY]\n")
                f.write(f"Total Income: {self.total_income():.2f}\n")
                f.write(f"Total Expenses: {self.total_expenses():.2f}\n")
                f.write(f"Remaining Balance: {self.balance():.2f}\n")
        except OSError as e:
            raise OSError(f"Could not save TXT file: {e}")

    def load(self) -> None:
        """
        Load existing data.
        Preference:
          1) Try JSON file if exists and valid
          2) If JSON missing, try TXT (simple parse fallback)
          3) If none exists, start empty
        """
        # 1) JSON
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.from_dict(data)
                    return
            except (OSError, json.JSONDecodeError):
                # fall back to txt
                pass

        # 2) TXT fallback (very simple; only for persistence requirement)
        if os.path.exists(self.txt_path):
            try:
                self._load_from_txt_fallback()
            except OSError:
                # if txt fails, stay empty
                self.incomes = []
                self.expenses = []

    def _load_from_txt_fallback(self) -> None:
        """
        Minimal parser: tries to recover some entries from exported format.
        If it can't, it still won't crash.
        """
        self.incomes = []
        self.expenses = []

        mode = None
        with open(self.txt_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line == "[INCOMES]":
                    mode = "incomes"
                    continue
                if line == "[EXPENSES]":
                    mode = "expenses"
                    continue
                if line.startswith("[SUMMARY]"):
                    mode = None
                    continue
                if not line or line.startswith("==="):
                    continue

                if mode == "incomes" and "Source:" in line and "| Amount:" in line:
                    # Example: "1. Source: Salary | Amount: 1000.00"
                    try:
                        source_part = line.split("Source:", 1)[1].split("|", 1)[0].strip()
                        amount_part = line.split("Amount:", 1)[1].strip()
                        amt = float(amount_part)
                        if source_part and amt > 0:
                            self.incomes.append(IncomeEntry(source=source_part, amount=amt))
                    except Exception:
                        pass

                if mode == "expenses" and "Date:" in line and "| Category:" in line and "| Description:" in line and "| Amount:" in line:
                    # Example:
                    # "1. Date: 2026-02-22 | Category: Food | Description: Lunch | Amount: 15.50"
                    try:
                        d = line.split("Date:", 1)[1].split("|", 1)[0].strip()
                        category = line.split("Category:", 1)[1].split("|", 1)[0].strip()
                        description = line.split("Description:", 1)[1].split("|", 1)[0].strip()
                        amount_part = line.split("Amount:", 1)[1].strip()
                        amt = float(amount_part)
                        d_norm = self._normalize_date(d)
                        if category and description and amt > 0:
                            self.expenses.append(
                                ExpenseEntry(description=description, category=category, amount=amt, date=d_norm)
                            )
                    except Exception:
                        pass