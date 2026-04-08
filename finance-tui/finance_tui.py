from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, DataTable, Static, Input, Button, Collapsible


DB_PATH = Path("finance.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def valid_month(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m")
        return True
    except ValueError:
        return False


def normalize_amount(category: str, amount: float) -> float:
    category = category.strip().lower()
    if category == "income":
        return abs(amount)
    return -abs(amount)


def bucket_for_category(category: str) -> str:
    c = category.strip().lower()

    if c == "income":
        return "income"
    if c == "plati bancare":
        return "bank"
    if c == "plati facturi":
        return "bills"
    return "other"


class ConfirmDeleteScreen(ModalScreen[bool]):
    CSS = """
    ConfirmDeleteScreen {
        align: center middle;
    }

    #dialog {
        width: 72;
        height: auto;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }

    #buttons {
        height: auto;
        align: center middle;
        padding-top: 1;
    }

    Button {
        margin: 0 1;
        min-width: 12;
    }
    """

    def __init__(self, label: str) -> None:
        super().__init__()
        self.label = label

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Confirm delete")
            yield Static(self.label)
            yield Static("Are you sure you want to delete this transaction?")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Delete", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")


class SummaryBox(Static):
    def update_summary(self, month_filter: str = "", category_filter: str = "") -> None:
        conn = get_connection()
        cur = conn.cursor()

        where_clauses = []
        params: list[str] = []

        if month_filter:
            where_clauses.append("substr(date, 1, 7) = ?")
            params.append(month_filter)

        if category_filter:
            where_clauses.append("LOWER(category) LIKE ?")
            params.append(f"%{category_filter.lower()}%")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        cur.execute(
            f"""
            SELECT
                COALESCE(SUM(amount), 0) AS current_income,
                COALESCE(SUM(CASE WHEN LOWER(category) = 'income' THEN amount ELSE 0 END), 0) AS total_income,
                COALESCE(SUM(CASE WHEN LOWER(category) != 'income' THEN ABS(amount) ELSE 0 END), 0) AS total_expenses
            FROM transactions
            {where_sql}
            """,
            params,
        )
        row = cur.fetchone()
        conn.close()

        current_income = float(row["current_income"])
        total_income = float(row["total_income"])
        total_expenses = float(row["total_expenses"])

        active_month = month_filter if month_filter else "all"
        active_category = category_filter if category_filter else "all"

        self.update(
            "\n".join(
                [
                    "Summary",
                    "",
                    f"Month:          {active_month}",
                    f"Category:       {active_category}",
                    "",
                    f"Income curent:  {current_income:.2f} RON",
                    f"Venituri totale:{total_income:.2f} RON",
                    f"Cheltuieli:     {total_expenses:.2f} RON",
                ]
            )
        )


class FinanceApp(App):
    CSS = """
    Screen {
        layout: vertical;
        padding: 0;
        margin: 0;
    }

    Header {
        padding: 0;
        margin: 0;
    }

    Footer {
        padding: 0;
        margin: 0;
    }

    #topbar {
        height: auto;
        padding: 0 1 1 1;
        border-bottom: solid $accent;
    }

    #topbar-title {
        margin-bottom: 1;
    }

    #filter-row {
        height: auto;
    }

    #filter-month {
        width: 18;
        margin-right: 1;
    }

    #filter-category {
        width: 20;
        margin-right: 1;
    }

    #main {
        height: 1fr;
        margin: 0;
        padding: 0;
    }

    #left {
        width: 3fr;
        padding: 0;
        margin: 0;
        overflow-y: auto;
    }

    #right {
        width: 34;
        min-width: 34;
        max-width: 34;
        padding: 1 1 1 0;
        margin: 0;
    }

    Collapsible {
        margin: 0;
        padding: 0;
        border: none;
    }

    .group-table {
        height: 7;
        margin: 0;
        padding: 0;
        border: none;
    }

    DataTable {
        margin: 0;
        padding: 0;
        border: none;
    }

    #summary {
        height: 10;
        border: round $accent;
        padding: 1;
        margin-bottom: 1;
    }

    #form {
        border: round $accent;
        padding: 1;
    }

    #form-title {
        margin-bottom: 1;
    }

    Input {
        margin-bottom: 1;
    }

    Button {
        margin-right: 1;
    }

    #hint {
        margin-top: 1;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh_data", "Refresh"),
        ("a", "new_transaction", "New"),
        ("e", "edit_selected", "Edit"),
        ("d", "delete_selected", "Delete"),
        ("j", "next_section", "Next section"),
        ("k", "prev_section", "Prev section"),
        ("escape", "clear_form", "Clear form"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.editing_transaction_id: int | None = None
        self.table_order = ["table-income", "table-bank", "table-bills", "table-other"]
        self.last_active_table_id = "table-income"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Vertical(id="topbar"):
            yield Static("Filters", id="topbar-title")
            with Horizontal(id="filter-row"):
                yield Input(placeholder="Month YYYY-MM", id="filter-month")
                yield Input(placeholder="Category", id="filter-category")
                yield Button("Apply", id="apply-filters")
                yield Button("Clear", id="clear-filters")

        with Horizontal(id="main"):
            with Vertical(id="left"):
                with Collapsible(title="Income", collapsed=False, id="group-income"):
                    yield DataTable(id="table-income", classes="group-table")

                with Collapsible(title="Plăți bancare", collapsed=False, id="group-bank"):
                    yield DataTable(id="table-bank", classes="group-table")

                with Collapsible(title="Plăți facturi", collapsed=False, id="group-bills"):
                    yield DataTable(id="table-bills", classes="group-table")

                with Collapsible(title="Alte cheltuieli", collapsed=False, id="group-other"):
                    yield DataTable(id="table-other", classes="group-table")

            with Vertical(id="right"):
                yield SummaryBox(id="summary")

                with Vertical(id="form"):
                    yield Static("Add transaction", id="form-title")
                    yield Input(placeholder="Date YYYY-MM-DD", id="date")
                    yield Input(placeholder="Amount", id="amount")
                    yield Input(placeholder="Category", id="category")
                    yield Input(placeholder="Description", id="description")
                    with Horizontal():
                        yield Button("Save", id="save")
                        yield Button("Clear Form", id="clear-form-button")
                    yield Static(
                        "a = new | e = edit | d = delete | j/k = section | Enter = save | Esc = clear",
                        id="hint",
                    )

        yield Footer()

    def on_mount(self) -> None:
        self.title = "Finance Tracker"
        self.sub_title = "Terminal UI"

        for table_id in self.table_order:
            table = self.query_one(f"#{table_id}", DataTable)
            table.cursor_type = "row"
            table.zebra_stripes = True
            table.add_columns("ID", "Date", "Amount", "Category", "Description")

        self.action_clear_form()
        self.refresh_all()
        self.focus_table("table-income")

    def focus_table(self, table_id: str) -> None:
        table = self.query_one(f"#{table_id}", DataTable)
        self.last_active_table_id = table_id
        table.focus()

    def on_focus(self, event) -> None:
        if isinstance(event.control, DataTable):
            self.last_active_table_id = event.control.id or self.last_active_table_id

    def get_filters(self) -> tuple[str, str]:
        month_filter = self.query_one("#filter-month", Input).value.strip()
        category_filter = self.query_one("#filter-category", Input).value.strip()
        return month_filter, category_filter

    def fetch_rows(self) -> list[sqlite3.Row]:
        month_filter, category_filter = self.get_filters()

        where_clauses = []
        params: list[str] = []

        if month_filter:
            if not valid_month(month_filter):
                self.notify("Month filter invalid. Use YYYY-MM", severity="error")
                return []
            where_clauses.append("substr(date, 1, 7) = ?")
            params.append(month_filter)

        if category_filter:
            where_clauses.append("LOWER(category) LIKE ?")
            params.append(f"%{category_filter.lower()}%")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT id, date, amount, category, description
            FROM transactions
            {where_sql}
            ORDER BY date DESC, id DESC
            """,
            params,
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    def set_group_title(self, group_id: str, base_title: str, rows: list[sqlite3.Row]) -> None:
        total = sum(float(row["amount"]) for row in rows)
        count = len(rows)
        collapsible = self.query_one(f"#{group_id}", Collapsible)
        collapsible.title = f"{base_title} ({count}) | {total:.2f} RON"

    def load_tables(self) -> None:
        grouped = {
            "income": [],
            "bank": [],
            "bills": [],
            "other": [],
        }

        for row in self.fetch_rows():
            grouped[bucket_for_category(row["category"])].append(row)

        mapping = {
            "table-income": grouped["income"],
            "table-bank": grouped["bank"],
            "table-bills": grouped["bills"],
            "table-other": grouped["other"],
        }

        for table_id, rows in mapping.items():
            table = self.query_one(f"#{table_id}", DataTable)
            table.clear(columns=True)
            table.add_columns("ID", "Date", "Amount", "Category", "Description")

            for row in rows:
                table.add_row(
                    str(row["id"]),
                    row["date"],
                    f"{row['amount']:.2f}",
                    row["category"],
                    row["description"],
                )

        self.set_group_title("group-income", "Income", grouped["income"])
        self.set_group_title("group-bank", "Plăți bancare", grouped["bank"])
        self.set_group_title("group-bills", "Plăți facturi", grouped["bills"])
        self.set_group_title("group-other", "Alte cheltuieli", grouped["other"])

    def refresh_all(self) -> None:
        current_table = self.last_active_table_id
        self.load_tables()
        self.update_summary()
        self.focus_table(current_table)

    def update_summary(self) -> None:
        month_filter, category_filter = self.get_filters()
        self.query_one("#summary", SummaryBox).update_summary(month_filter, category_filter)

    def get_active_table(self) -> DataTable | None:
        for table_id in self.table_order:
            table = self.query_one(f"#{table_id}", DataTable)
            if table.has_focus:
                self.last_active_table_id = table_id
                return table

        try:
            return self.query_one(f"#{self.last_active_table_id}", DataTable)
        except Exception:
            return None

    def get_selected_transaction_id(self) -> int | None:
        table = self.get_active_table()
        if table is None or table.row_count == 0 or table.cursor_row is None:
            return None

        try:
            row = table.get_row_at(table.cursor_row)
            return int(row[0])
        except Exception:
            return None

    def get_selected_transaction_label(self) -> str:
        table = self.get_active_table()
        if table is None or table.row_count == 0 or table.cursor_row is None:
            return "No transaction selected"

        try:
            row = table.get_row_at(table.cursor_row)
            return f"#{row[0]} | {row[1]} | {row[2]} RON | {row[3]} | {row[4]}"
        except Exception:
            return "Selected transaction"

    def clear_form_fields(self) -> None:
        self.query_one("#date", Input).value = datetime.now().strftime("%Y-%m-%d")
        self.query_one("#amount", Input).value = ""
        self.query_one("#category", Input).value = ""
        self.query_one("#description", Input).value = ""

    def action_clear_form(self) -> None:
        self.editing_transaction_id = None
        self.query_one("#form-title", Static).update("Add transaction")
        self.clear_form_fields()

    def action_new_transaction(self) -> None:
        self.action_clear_form()
        self.query_one("#amount", Input).focus()
        self.notify("New transaction")

    def action_refresh_data(self) -> None:
        self.refresh_all()
        self.notify("Data refreshed")

    def action_next_section(self) -> None:
        current = self.last_active_table_id
        if current not in self.table_order:
            self.focus_table(self.table_order[0])
            return
        idx = self.table_order.index(current)
        self.focus_table(self.table_order[(idx + 1) % len(self.table_order)])

    def action_prev_section(self) -> None:
        current = self.last_active_table_id
        if current not in self.table_order:
            self.focus_table(self.table_order[0])
            return
        idx = self.table_order.index(current)
        self.focus_table(self.table_order[(idx - 1) % len(self.table_order)])

    def action_edit_selected(self) -> None:
        transaction_id = self.get_selected_transaction_id()

        if transaction_id is None:
            self.notify("Select a row for edit", severity="warning")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, date, amount, category, description
            FROM transactions
            WHERE id = ?
            """,
            (transaction_id,),
        )
        row = cur.fetchone()
        conn.close()

        if row is None:
            self.notify("Transaction not found", severity="error")
            return

        self.editing_transaction_id = row["id"]
        self.query_one("#date", Input).value = row["date"]
        self.query_one("#amount", Input).value = str(abs(float(row["amount"])))
        self.query_one("#category", Input).value = row["category"]
        self.query_one("#description", Input).value = row["description"]
        self.query_one("#form-title", Static).update(f"Edit transaction #{row['id']}")
        self.query_one("#amount", Input).focus()
        self.notify("Transaction loaded into form")

    def action_delete_selected(self) -> None:
        transaction_id = self.get_selected_transaction_id()

        if transaction_id is None:
            self.notify("Select a row for delete", severity="warning")
            return

        label = self.get_selected_transaction_label()

        def after_confirm(confirmed: bool) -> None:
            if not confirmed:
                self.notify("Delete cancelled")
                return

            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            deleted_rows = cur.rowcount
            conn.commit()
            conn.close()

            if deleted_rows == 0:
                self.notify("Transaction not found", severity="error")
                return

            if self.editing_transaction_id == transaction_id:
                self.action_clear_form()

            self.refresh_all()
            self.notify("Transaction deleted")

        self.push_screen(ConfirmDeleteScreen(label), after_confirm)

    def save_form(self) -> None:
        date_input = self.query_one("#date", Input)
        amount_input = self.query_one("#amount", Input)
        category_input = self.query_one("#category", Input)
        description_input = self.query_one("#description", Input)

        date_value = date_input.value.strip()
        category = category_input.value.strip()
        description = description_input.value.strip()

        if not valid_date(date_value):
            self.notify("Date invalid. Use YYYY-MM-DD", severity="error")
            return

        try:
            raw_amount = float(amount_input.value.replace(",", ".").strip())
        except ValueError:
            self.notify("Amount invalid", severity="error")
            return

        if not category:
            self.notify("Category is required", severity="error")
            return

        if not description:
            self.notify("Description is required", severity="error")
            return

        amount = normalize_amount(category, raw_amount)

        conn = get_connection()
        cur = conn.cursor()

        if self.editing_transaction_id is None:
            cur.execute(
                """
                INSERT INTO transactions (date, amount, category, description)
                VALUES (?, ?, ?, ?)
                """,
                (date_value, amount, category, description),
            )
            conn.commit()
            conn.close()

            self.action_clear_form()
            self.refresh_all()
            self.notify("Transaction saved")
        else:
            cur.execute(
                """
                UPDATE transactions
                SET date = ?, amount = ?, category = ?, description = ?
                WHERE id = ?
                """,
                (date_value, amount, category, description, self.editing_transaction_id),
            )
            updated_rows = cur.rowcount
            conn.commit()
            conn.close()

            if updated_rows == 0:
                self.notify("Update failed", severity="error")
                return

            edited_id = self.editing_transaction_id
            self.action_clear_form()
            self.refresh_all()
            self.notify(f"Transaction #{edited_id} updated")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "save":
            self.save_form()
        elif button_id == "clear-form-button":
            self.action_clear_form()
        elif button_id == "apply-filters":
            month_filter = self.query_one("#filter-month", Input).value.strip()
            if month_filter and not valid_month(month_filter):
                self.notify("Month filter invalid. Use YYYY-MM", severity="error")
                return
            self.refresh_all()
            self.notify("Filters applied")
        elif button_id == "clear-filters":
            self.query_one("#filter-month", Input).value = ""
            self.query_one("#filter-category", Input).value = ""
            self.refresh_all()
            self.notify("Filters cleared")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in {"date", "amount", "category", "description"}:
            self.save_form()
        elif event.input.id in {"filter-month", "filter-category"}:
            month_filter = self.query_one("#filter-month", Input).value.strip()
            if month_filter and not valid_month(month_filter):
                self.notify("Month filter invalid. Use YYYY-MM", severity="error")
                return
            self.refresh_all()
            self.notify("Filters applied")


if __name__ == "__main__":
    init_db()
    app = FinanceApp()
    app.run()
