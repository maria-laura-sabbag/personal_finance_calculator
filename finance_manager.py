import tkinter as tk
from tkinter import ttk, messagebox

from finance_core import FinanceManager, ValidationError


class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Personal Finance Manager (Week 7)")
        self.geometry("980x620")

        self.manager = FinanceManager(json_path="finance_data.json", txt_path="finance_data.txt")

        # Load existing data on start (data persistence requirement)
        try:
            self.manager.load()
        except Exception:
            # if load fails, we still keep the app running
            pass

        self._build_ui()
        self._refresh_lists_and_summary()

    def _build_ui(self):
        # Main layout frames
        container = ttk.Frame(self, padding=12)
        container.pack(fill="both", expand=True)

        top = ttk.Frame(container)
        top.pack(fill="x")

        left = ttk.Frame(container)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = ttk.Frame(container)
        right.pack(side="right", fill="both", expand=True)

        # -------------------------
        # Income Entry Section
        # -------------------------
        income_box = ttk.LabelFrame(top, text="Add Income", padding=10)
        income_box.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ttk.Label(income_box, text="Source:").grid(row=0, column=0, sticky="w")
        self.income_source_var = tk.StringVar()
        ttk.Entry(income_box, textvariable=self.income_source_var, width=28).grid(row=0, column=1, padx=6)

        ttk.Label(income_box, text="Amount:").grid(row=0, column=2, sticky="w")
        self.income_amount_var = tk.StringVar()
        ttk.Entry(income_box, textvariable=self.income_amount_var, width=12).grid(row=0, column=3, padx=6)

        ttk.Button(income_box, text="Add Income", command=self.add_income).grid(row=0, column=4, padx=6)

        # -------------------------
        # Expense Entry Section
        # -------------------------
        expense_box = ttk.LabelFrame(top, text="Add Expense", padding=10)
        expense_box.pack(side="right", fill="x", expand=True)

        ttk.Label(expense_box, text="Description:").grid(row=0, column=0, sticky="w")
        self.exp_desc_var = tk.StringVar()
        ttk.Entry(expense_box, textvariable=self.exp_desc_var, width=22).grid(row=0, column=1, padx=6)

        ttk.Label(expense_box, text="Category:").grid(row=0, column=2, sticky="w")
        self.exp_cat_var = tk.StringVar()
        ttk.Entry(expense_box, textvariable=self.exp_cat_var, width=14).grid(row=0, column=3, padx=6)

        ttk.Label(expense_box, text="Amount:").grid(row=0, column=4, sticky="w")
        self.exp_amount_var = tk.StringVar()
        ttk.Entry(expense_box, textvariable=self.exp_amount_var, width=10).grid(row=0, column=5, padx=6)

        ttk.Label(expense_box, text="Date (YYYY-MM-DD):").grid(row=0, column=6, sticky="w")
        self.exp_date_var = tk.StringVar()
        ttk.Entry(expense_box, textvariable=self.exp_date_var, width=12).grid(row=0, column=7, padx=6)

        ttk.Button(expense_box, text="Add Expense", command=self.add_expense).grid(row=0, column=8, padx=6)

        # -------------------------
        # Income list & controls
        # -------------------------
        incomes_frame = ttk.LabelFrame(left, text="Incomes (select an item to delete)", padding=10)
        incomes_frame.pack(fill="both", expand=True)

        self.income_list = tk.Listbox(incomes_frame, height=12)
        self.income_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        ttk.Button(incomes_frame, text="Delete Selected Income", command=self.delete_selected_income).pack(pady=(0, 6))

        # -------------------------
        # Expense list & controls
        # -------------------------
        expenses_frame = ttk.LabelFrame(right, text="Expenses (select an item to delete)", padding=10)
        expenses_frame.pack(fill="both", expand=True)

        self.expense_list = tk.Listbox(expenses_frame, height=12)
        self.expense_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        ttk.Button(expenses_frame, text="Delete Selected Expense", command=self.delete_selected_expense).pack(pady=(0, 6))

        # -------------------------
        # Summary section
        # -------------------------
        summary = ttk.LabelFrame(container, text="Summary", padding=12)
        summary.pack(fill="x", pady=(12, 0))

        self.total_income_lbl = ttk.Label(summary, text="Total Income: $0.00", font=("Arial", 12))
        self.total_income_lbl.grid(row=0, column=0, sticky="w", padx=6, pady=3)

        self.total_expenses_lbl = ttk.Label(summary, text="Total Expenses: $0.00", font=("Arial", 12))
        self.total_expenses_lbl.grid(row=0, column=1, sticky="w", padx=6, pady=3)

        self.balance_lbl = ttk.Label(summary, text="Remaining Balance: $0.00", font=("Arial", 12, "bold"))
        self.balance_lbl.grid(row=0, column=2, sticky="w", padx=6, pady=3)

        # Save button (explicit save, plus auto-save after add/delete)
        ttk.Button(summary, text="Save Now", command=self.save_data).grid(row=0, column=3, padx=10)

        # Make columns expand nicely
        summary.columnconfigure(0, weight=1)
        summary.columnconfigure(1, weight=1)
        summary.columnconfigure(2, weight=1)
        summary.columnconfigure(3, weight=0)

    # -------------------------
    # UI Actions
    # -------------------------
    def add_income(self):
        try:
            self.manager.add_income(self.income_source_var.get(), self.income_amount_var.get())
            self.manager.save()  # persistence requirement
            self.income_source_var.set("")
            self.income_amount_var.set("")
            self._refresh_lists_and_summary()
        except ValidationError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error adding income: {e}")

    def add_expense(self):
        try:
            self.manager.add_expense(
                self.exp_desc_var.get(),
                self.exp_cat_var.get(),
                self.exp_amount_var.get(),
                self.exp_date_var.get()
            )
            self.manager.save()  # persistence requirement
            self.exp_desc_var.set("")
            self.exp_cat_var.set("")
            self.exp_amount_var.set("")
            self.exp_date_var.set("")
            self._refresh_lists_and_summary()
        except ValidationError as e:
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error adding expense: {e}")

    def delete_selected_income(self):
        idx = self.income_list.curselection()
        if not idx:
            messagebox.showwarning("No selection", "Please select an income entry to delete.")
            return
        try:
            self.manager.delete_income(idx[0])
            self.manager.save()
            self._refresh_lists_and_summary()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete income: {e}")

    def delete_selected_expense(self):
        idx = self.expense_list.curselection()
        if not idx:
            messagebox.showwarning("No selection", "Please select an expense entry to delete.")
            return
        try:
            self.manager.delete_expense(idx[0])
            self.manager.save()
            self._refresh_lists_and_summary()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete expense: {e}")

    def save_data(self):
        try:
            self.manager.save()
            messagebox.showinfo("Saved", "Data saved to finance_data.json and finance_data.txt")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _refresh_lists_and_summary(self):
        # Refresh income listbox
        self.income_list.delete(0, tk.END)
        for i in self.manager.incomes:
            self.income_list.insert(tk.END, f"Source: {i.source} | Amount: ${i.amount:.2f}")

        # Refresh expense listbox
        self.expense_list.delete(0, tk.END)
        for e in self.manager.expenses:
            self.expense_list.insert(tk.END, f"{e.date} | {e.category} | {e.description} | ${e.amount:.2f}")

        # Refresh summary labels
        ti = self.manager.total_income()
        te = self.manager.total_expenses()
        bal = self.manager.balance()

        self.total_income_lbl.config(text=f"Total Income: ${ti:.2f}")
        self.total_expenses_lbl.config(text=f"Total Expenses: ${te:.2f}")
        self.balance_lbl.config(text=f"Remaining Balance: ${bal:.2f}")


if __name__ == "__main__":
    app = FinanceApp()
    app.mainloop()