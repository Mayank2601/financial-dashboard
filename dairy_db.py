"""
Database layer for Dairy Business Logging app.
Uses SQLite locally or PostgreSQL (Supabase) when DATABASE_URL is set.
"""

import os
from pathlib import Path
from typing import List, Optional
import pandas as pd

# Constants
PRODUCTS = ["Milk", "Ghee", "Curd", "Paneer"]
COST_HEADS = [
    "Salary",
    "Feed",
    "Logistics",
    "Rent",
    "Expansion",
    "Milk purchasing",
    "Marketing",
    "Miscellaneous",
]

# Use PostgreSQL (Supabase) if DATABASE_URL is set; otherwise SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    # Supabase may provide postgres:// - SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # Supabase/cloud PostgreSQL requires SSL; add sslmode=require
    if "postgresql" in DATABASE_URL and "sslmode=" not in DATABASE_URL.lower():
        sep = "&" if "?" in DATABASE_URL else "?"
        DATABASE_URL = f"{DATABASE_URL}{sep}sslmode=require"
    _DB_PATH = None
else:
    _DB_PATH = Path(__file__).resolve().parent / "dairy_data.db"


def _get_engine():
    """Return SQLAlchemy engine for current database mode."""
    import sqlalchemy as sa
    if DATABASE_URL:
        # Use NullPool for serverless (Streamlit Cloud) - avoids connection pooling issues with Supabase
        return sa.create_engine(
            DATABASE_URL,
            poolclass=sa.pool.NullPool,
            pool_pre_ping=True,
        )
    return sa.create_engine(f"sqlite:///{_DB_PATH}")


def init_db() -> None:
    """Create tables if they don't exist."""
    from sqlalchemy import text
    engine = _get_engine()
    is_sqlite = "sqlite" in str(engine.url)

    # PostgreSQL uses SERIAL, SQLite uses INTEGER PRIMARY KEY AUTOINCREMENT
    if is_sqlite:
        orders_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                product TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                amount REAL NOT NULL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        income_sql = """
            CREATE TABLE IF NOT EXISTS income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                customer_name TEXT,
                payment_method TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        expenses_sql = """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                cost_head TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
    else:
        orders_sql = """
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                product TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit_price REAL NOT NULL,
                amount REAL NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        income_sql = """
            CREATE TABLE IF NOT EXISTS income (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                customer_name TEXT,
                payment_method TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        expenses_sql = """
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                cost_head TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """

    with engine.connect() as conn:
        conn.execute(text(orders_sql))
        conn.execute(text(income_sql))
        conn.execute(text(expenses_sql))
        conn.commit()


def add_order(
    date: str,
    customer_name: str,
    product: str,
    quantity: float,
    unit_price: float,
    notes: str = "",
) -> int:
    """Add an order. Returns the new row id."""
    amount = quantity * unit_price
    engine = _get_engine()
    is_sqlite = "sqlite" in str(engine.url)
    with engine.connect() as conn:
        from sqlalchemy import text
        if is_sqlite:
            conn.execute(
                text("""
                    INSERT INTO orders (date, customer_name, product, quantity, unit_price, amount, notes)
                    VALUES (:date, :customer_name, :product, :quantity, :unit_price, :amount, :notes)
                """),
                {
                    "date": date,
                    "customer_name": customer_name.strip(),
                    "product": product,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "amount": amount,
                    "notes": notes.strip(),
                },
            )
            conn.commit()
            cur = conn.execute(text("SELECT last_insert_rowid()"))
            return cur.scalar()
        else:
            r = conn.execute(
                text("""
                    INSERT INTO orders (date, customer_name, product, quantity, unit_price, amount, notes)
                    VALUES (:date, :customer_name, :product, :quantity, :unit_price, :amount, :notes)
                    RETURNING id
                """),
                {
                    "date": date,
                    "customer_name": customer_name.strip(),
                    "product": product,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "amount": amount,
                    "notes": notes.strip(),
                },
            )
            row = r.fetchone()
            conn.commit()
            return row[0]


def add_income(
    date: str,
    amount: float,
    customer_name: str = "",
    payment_method: str = "",
    notes: str = "",
) -> int:
    """Add an income entry. Returns the new row id."""
    from sqlalchemy import text
    engine = _get_engine()
    is_sqlite = "sqlite" in str(engine.url)
    with engine.connect() as conn:
        if is_sqlite:
            conn.execute(
                text("""
                    INSERT INTO income (date, amount, customer_name, payment_method, notes)
                    VALUES (:date, :amount, :customer_name, :payment_method, :notes)
                """),
                {
                    "date": date,
                    "amount": amount,
                    "customer_name": customer_name.strip() or None,
                    "payment_method": payment_method or None,
                    "notes": notes.strip(),
                },
            )
            conn.commit()
            cur = conn.execute(text("SELECT last_insert_rowid()"))
            return cur.scalar()
        else:
            r = conn.execute(
                text("""
                    INSERT INTO income (date, amount, customer_name, payment_method, notes)
                    VALUES (:date, :amount, :customer_name, :payment_method, :notes)
                    RETURNING id
                """),
                {
                    "date": date,
                    "amount": amount,
                    "customer_name": customer_name.strip() or None,
                    "payment_method": payment_method or None,
                    "notes": notes.strip(),
                },
            )
            row = r.fetchone()
            conn.commit()
            return row[0]


def add_expense(
    date: str,
    amount: float,
    cost_head: str,
    description: str = "",
) -> int:
    """Add an expense entry. Returns the new row id."""
    from sqlalchemy import text
    engine = _get_engine()
    is_sqlite = "sqlite" in str(engine.url)
    with engine.connect() as conn:
        if is_sqlite:
            conn.execute(
                text("""
                    INSERT INTO expenses (date, amount, cost_head, description)
                    VALUES (:date, :amount, :cost_head, :description)
                """),
                {"date": date, "amount": amount, "cost_head": cost_head, "description": description.strip()},
            )
            conn.commit()
            cur = conn.execute(text("SELECT last_insert_rowid()"))
            return cur.scalar()
        else:
            r = conn.execute(
                text("""
                    INSERT INTO expenses (date, amount, cost_head, description)
                    VALUES (:date, :amount, :cost_head, :description)
                    RETURNING id
                """),
                {"date": date, "amount": amount, "cost_head": cost_head, "description": description.strip()},
            )
            row = r.fetchone()
            conn.commit()
            return row[0]


def get_orders() -> List[dict]:
    """Return all orders as list of dicts."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM orders ORDER BY date ASC")).fetchall()
        return [dict(r._mapping) for r in rows]


def get_income() -> List[dict]:
    """Return all income entries as list of dicts."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM income ORDER BY date ASC")).fetchall()
        return [dict(r._mapping) for r in rows]


def get_expenses() -> List[dict]:
    """Return all expenses as list of dicts."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT * FROM expenses ORDER BY date ASC")).fetchall()
        return [dict(r._mapping) for r in rows]


def get_orders_df() -> pd.DataFrame:
    """Return orders as DataFrame for analysis."""
    engine = _get_engine()
    return pd.read_sql_query("SELECT * FROM orders ORDER BY date ASC", engine)


def get_income_df() -> pd.DataFrame:
    """Return income as DataFrame for analysis."""
    engine = _get_engine()
    return pd.read_sql_query("SELECT * FROM income ORDER BY date ASC", engine)


def get_expenses_df() -> pd.DataFrame:
    """Return expenses as DataFrame for analysis."""
    engine = _get_engine()
    return pd.read_sql_query("SELECT * FROM expenses ORDER BY date ASC", engine)


def get_unique_customers() -> List[str]:
    """Return list of unique customer names from orders."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT DISTINCT customer_name FROM orders
                WHERE customer_name IS NOT NULL AND customer_name != ''
                ORDER BY customer_name
            """)
        ).fetchall()
        return [r[0] for r in rows]


def get_all_customer_names() -> List[str]:
    """Return unique customer names from both orders and income tables."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT customer_name FROM orders WHERE customer_name IS NOT NULL AND customer_name != ''
            UNION
            SELECT DISTINCT customer_name FROM income WHERE customer_name IS NOT NULL AND customer_name != ''
            ORDER BY customer_name
        """)).fetchall()
        return [r[0] for r in rows]


def get_order_by_id(order_id: int) -> Optional[dict]:
    """Return a single order by id."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}).fetchone()
        return dict(row._mapping) if row else None


def get_income_by_id(income_id: int) -> Optional[dict]:
    """Return a single income entry by id."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM income WHERE id = :id"), {"id": income_id}).fetchone()
        return dict(row._mapping) if row else None


def get_expense_by_id(expense_id: int) -> Optional[dict]:
    """Return a single expense by id."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        row = conn.execute(text("SELECT * FROM expenses WHERE id = :id"), {"id": expense_id}).fetchone()
        return dict(row._mapping) if row else None


def update_order(
    order_id: int,
    date: str,
    customer_name: str,
    product: str,
    quantity: float,
    unit_price: float,
    notes: str = "",
) -> bool:
    """Update an order. Returns True if updated."""
    from sqlalchemy import text
    amount = quantity * unit_price
    engine = _get_engine()
    with engine.connect() as conn:
        r = conn.execute(
            text("""
                UPDATE orders SET date=:date, customer_name=:customer_name, product=:product,
                quantity=:quantity, unit_price=:unit_price, amount=:amount, notes=:notes
                WHERE id=:id
            """),
            {
                "date": date,
                "customer_name": customer_name.strip(),
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
                "amount": amount,
                "notes": notes.strip(),
                "id": order_id,
            },
        )
        conn.commit()
        return r.rowcount > 0


def update_income(
    income_id: int,
    date: str,
    amount: float,
    customer_name: str = "",
    payment_method: str = "",
    notes: str = "",
) -> bool:
    """Update an income entry. Returns True if updated."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        r = conn.execute(
            text("""
                UPDATE income SET date=:date, amount=:amount, customer_name=:customer_name,
                payment_method=:payment_method, notes=:notes WHERE id=:id
            """),
            {
                "date": date,
                "amount": amount,
                "customer_name": customer_name.strip() or None,
                "payment_method": payment_method or None,
                "notes": notes.strip(),
                "id": income_id,
            },
        )
        conn.commit()
        return r.rowcount > 0


def update_expense(
    expense_id: int,
    date: str,
    amount: float,
    cost_head: str,
    description: str = "",
) -> bool:
    """Update an expense. Returns True if updated."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        r = conn.execute(
            text("""
                UPDATE expenses SET date=:date, amount=:amount, cost_head=:cost_head, description=:description
                WHERE id=:id
            """),
            {
                "date": date,
                "amount": amount,
                "cost_head": cost_head,
                "description": description.strip(),
                "id": expense_id,
            },
        )
        conn.commit()
        return r.rowcount > 0


def delete_order(order_id: int) -> bool:
    """Delete an order. Returns True if deleted."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("DELETE FROM orders WHERE id=:id"), {"id": order_id})
        conn.commit()
        return r.rowcount > 0


def delete_income(income_id: int) -> bool:
    """Delete an income entry. Returns True if deleted."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("DELETE FROM income WHERE id=:id"), {"id": income_id})
        conn.commit()
        return r.rowcount > 0


def delete_expense(expense_id: int) -> bool:
    """Delete an expense. Returns True if deleted."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("DELETE FROM expenses WHERE id=:id"), {"id": expense_id})
        conn.commit()
        return r.rowcount > 0


def get_customer_orders_df(customer_name: str) -> pd.DataFrame:
    """Return orders for a specific customer."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM orders WHERE customer_name = :name ORDER BY date ASC"),
            {"name": customer_name},
        ).fetchall()
        return pd.DataFrame([dict(r._mapping) for r in rows])


def get_customer_income_df(customer_name: str) -> pd.DataFrame:
    """Return income entries for a specific customer."""
    from sqlalchemy import text
    engine = _get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM income WHERE customer_name = :name ORDER BY date ASC"),
            {"name": customer_name},
        ).fetchall()
        return pd.DataFrame([dict(r._mapping) for r in rows])
