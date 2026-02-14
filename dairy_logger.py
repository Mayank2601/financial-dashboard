"""
Dairy Business Logging and Analysis App.
Manual entry for orders, income, expenses with SQLite persistence.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

import dairy_db as db

# Initialize database
db.init_db()


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


# Default unit prices per product
DEFAULT_PRICES = {"Milk": 120.0, "Ghee": 0.0, "Curd": 0.0, "Paneer": 0.0}


def _render_customer_selector(key_prefix: str) -> str:
    """Render customer dropdown with '+ Add new' option. Returns selected/entered customer name.
    Shows 'Enter new customer' text input only when '+ Add new customer' is selected."""
    customers = db.get_all_customer_names()
    options = ["+ Add new customer"] + sorted(customers) if customers else ["+ Add new customer"]
    selected = st.selectbox("Customer", options, key=f"{key_prefix}_cust_select")
    if selected == "+ Add new customer":
        return st.text_input("Enter new customer name", key=f"{key_prefix}_cust_new", placeholder="Type name")
    # Hide text input when existing customer selected - return selected name directly
    return selected


def render_add_order():
    st.header("Add Order")
    # Date and Customer first (outside form so customer dropdown show/hide works)
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", value=datetime.today(), key="order_date")
    with col2:
        customer_choice = _render_customer_selector("order")
    # Product, quantity, unit_price outside form so Amount updates in real-time
    product = st.selectbox("Product", options=db.PRODUCTS, key="order_product")
    default_price = DEFAULT_PRICES.get(product, 0.0)
    col_qty, col_price = st.columns(2)
    with col_qty:
        quantity = st.number_input("Quantity", min_value=0.1, step=0.1, format="%.2f", key="order_qty")
    with col_price:
        unit_price = st.number_input("Unit price (₹)", min_value=0.0, step=1.0, format="%.2f", value=default_price, key=f"order_price_{product}")
    amount = quantity * unit_price
    st.metric("Amount", format_currency(amount))
    with st.form("add_order_form", clear_on_submit=True):
        notes = st.text_area("Notes (optional)", placeholder="Optional notes")
        submitted = st.form_submit_button("Save Order")
        if submitted:
            customer_name = customer_choice.strip() if customer_choice else ""
            if not customer_name:
                st.error("Please enter or select a customer name.")
            elif unit_price <= 0 or quantity <= 0:
                st.error("Quantity and unit price must be positive.")
            else:
                row_id = db.add_order(
                    date=str(date),
                    customer_name=customer_name,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    notes=notes,
                )
                st.success(f"Order saved! (ID: {row_id})")


def render_add_income():
    st.header("Add Income")
    # Date and Customer first (outside form so customer dropdown show/hide works)
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", value=datetime.today(), key="income_date")
    with col2:
        customer_choice = _render_customer_selector("income")
    with st.form("add_income_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0, format="%.2f")
        payment_method = st.selectbox("Payment method", options=["", "Cash", "Digital"])
        notes = st.text_area("Notes (optional)", key="income_notes", placeholder="Optional notes")
        submitted = st.form_submit_button("Save Income")
        if submitted:
            customer_name = customer_choice.strip() if customer_choice else ""
            if amount <= 0:
                st.error("Amount must be positive.")
            else:
                row_id = db.add_income(
                    date=str(date),
                    amount=amount,
                    customer_name=customer_name,
                    payment_method=payment_method,
                    notes=notes,
                )
                st.success(f"Income saved! (ID: {row_id})")


def render_view_edit_logs():
    st.header("View & Edit Logs")
    log_tab = st.radio("Log type", ["Orders", "Income", "Expenses"], key="log_tab", horizontal=True)

    if log_tab == "Orders":
        orders = db.get_orders()
        if not orders:
            st.info("No orders yet.")
            return
        df = pd.DataFrame(orders)
        display_df = df[["id", "date", "customer_name", "product", "quantity", "unit_price", "amount"]].copy()
        display_df = display_df.rename(columns={"id": "ID", "date": "Date", "customer_name": "Customer", "product": "Product", "quantity": "Qty", "unit_price": "Unit price", "amount": "Amount"})
        display_df["Amount"] = display_df["Amount"].apply(format_currency)
        st.dataframe(display_df, width="stretch", hide_index=True)
        edit_options = [f"#{o['id']} | {o['date']} | {o['customer_name']} | {o['product']} | ₹{o['amount']}" for o in orders]
        selected = st.selectbox("Select entry to edit or delete", edit_options, key="edit_order_select")
        if selected:
            order_id = int(selected.split("|")[0].replace("#", "").strip())
            with st.expander("Edit or delete", expanded=True):
                if st.button("Delete this order", type="secondary", key=f"del_order_btn_{order_id}"):
                    if db.delete_order(order_id):
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete.")
                st.markdown("---")
                rec = db.get_order_by_id(order_id)
                if rec:
                    with st.form(f"edit_order_form_{order_id}"):
                        edate = st.date_input("Date", value=pd.to_datetime(rec["date"]).date(), key=f"e_order_date_{order_id}")
                        ecust = st.text_input("Customer", value=rec["customer_name"], key=f"e_order_cust_{order_id}")
                        eproduct = st.selectbox("Product", db.PRODUCTS, index=db.PRODUCTS.index(rec["product"]) if rec["product"] in db.PRODUCTS else 0, key=f"e_order_prod_{order_id}")
                        eqty = st.number_input("Quantity", value=float(rec["quantity"]), min_value=0.1, step=0.1, format="%.2f", key=f"e_order_qty_{order_id}")
                        eprice = st.number_input("Unit price", value=float(rec["unit_price"]), min_value=0.0, step=1.0, format="%.2f", key=f"e_order_price_{order_id}")
                        enotes = st.text_area("Notes", value=rec["notes"] or "", key=f"e_order_notes_{order_id}")
                        if st.form_submit_button("Save changes"):
                            if ecust.strip() and eprice > 0 and eqty > 0:
                                if db.update_order(order_id, str(edate), ecust.strip(), eproduct, eqty, eprice, enotes):
                                    st.success("Updated.")
                                    st.rerun()

    elif log_tab == "Income":
        income_list = db.get_income()
        if not income_list:
            st.info("No income entries yet.")
            return
        df = pd.DataFrame(income_list)
        display_df = df[["id", "date", "amount", "customer_name", "payment_method"]].copy()
        display_df = display_df.rename(columns={"id": "ID", "date": "Date", "amount": "Amount", "customer_name": "Customer", "payment_method": "Method"})
        display_df["Amount"] = display_df["Amount"].apply(lambda x: format_currency(float(x)))
        st.dataframe(display_df, width="stretch", hide_index=True)
        edit_options = [f"#{i['id']} | {i['date']} | ₹{i['amount']} | {(i['customer_name'] or '-')}" for i in income_list]
        selected = st.selectbox("Select entry to edit or delete", edit_options, key="edit_income_select")
        if selected:
            income_id = int(selected.split("|")[0].replace("#", "").strip())
            with st.expander("Edit or delete", expanded=True):
                if st.button("Delete this entry", type="secondary", key=f"del_income_btn_{income_id}"):
                    if db.delete_income(income_id):
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete.")
                st.markdown("---")
                rec = db.get_income_by_id(income_id)
                if rec:
                    with st.form(f"edit_income_form_{income_id}"):
                        edate = st.date_input("Date", value=pd.to_datetime(rec["date"]).date(), key=f"e_income_date_{income_id}")
                        eamt = st.number_input("Amount", value=float(rec["amount"]), min_value=0.0, step=1.0, format="%.2f", key=f"e_income_amt_{income_id}")
                        ecust = st.text_input("Customer", value=rec["customer_name"] or "", key=f"e_income_cust_{income_id}")
                        _methods = ["", "Cash", "Digital"]
                        _midx = _methods.index(rec["payment_method"] or "") if (rec["payment_method"] or "") in _methods else 0
                        emethod = st.selectbox("Payment method", _methods, index=_midx, key=f"e_income_method_{income_id}")
                        enotes = st.text_area("Notes", value=rec["notes"] or "", key=f"e_income_notes_{income_id}")
                        if st.form_submit_button("Save changes"):
                            if eamt > 0:
                                if db.update_income(income_id, str(edate), eamt, ecust.strip(), emethod, enotes):
                                    st.success("Updated.")
                                    st.rerun()

    else:  # Expenses
        expenses = db.get_expenses()
        if not expenses:
            st.info("No expenses yet.")
            return
        df = pd.DataFrame(expenses)
        display_df = df[["id", "date", "amount", "cost_head", "description"]].copy()
        display_df = display_df.rename(columns={"id": "ID", "date": "Date", "amount": "Amount", "cost_head": "Cost head", "description": "Description"})
        display_df["Amount"] = display_df["Amount"].apply(lambda x: format_currency(float(x)))
        st.dataframe(display_df, width="stretch", hide_index=True)
        edit_options = [f"#{e['id']} | {e['date']} | ₹{e['amount']} | {e['cost_head']}" for e in expenses]
        selected = st.selectbox("Select entry to edit or delete", edit_options, key="edit_expense_select")
        if selected:
            expense_id = int(selected.split("|")[0].replace("#", "").strip())
            with st.expander("Edit or delete", expanded=True):
                if st.button("Delete this expense", type="secondary", key=f"del_expense_btn_{expense_id}"):
                    if db.delete_expense(expense_id):
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.error("Could not delete.")
                st.markdown("---")
                rec = db.get_expense_by_id(expense_id)
                if rec:
                    with st.form(f"edit_expense_form_{expense_id}"):
                        edate = st.date_input("Date", value=pd.to_datetime(rec["date"]).date(), key=f"e_exp_date_{expense_id}")
                        eamt = st.number_input("Amount", value=float(rec["amount"]), min_value=0.0, step=1.0, format="%.2f", key=f"e_exp_amt_{expense_id}")
                        ehead = st.selectbox("Cost head", db.COST_HEADS, index=db.COST_HEADS.index(rec["cost_head"]) if rec["cost_head"] in db.COST_HEADS else 0, key=f"e_exp_head_{expense_id}")
                        edesc = st.text_area("Description", value=rec["description"] or "", key=f"e_exp_desc_{expense_id}")
                        if st.form_submit_button("Save changes"):
                            if eamt > 0:
                                if db.update_expense(expense_id, str(edate), eamt, ehead, edesc):
                                    st.success("Updated.")
                                    st.rerun()


def render_add_expense():
    st.header("Add Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", value=datetime.today(), key="expense_date")
        with col2:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=1.0, format="%.2f", key="expense_amount")
        cost_head = st.selectbox("Cost head", options=db.COST_HEADS)
        description = st.text_area("Description (optional)", key="expense_desc", placeholder="Optional description")
        submitted = st.form_submit_button("Save Expense")
        if submitted:
            if amount <= 0:
                st.error("Amount must be positive.")
            else:
                row_id = db.add_expense(
                    date=str(date),
                    amount=amount,
                    cost_head=cost_head,
                    description=description,
                )
                st.success(f"Expense saved! (ID: {row_id})")


def render_dashboard():
    st.header("Dashboard")

    orders_df = db.get_orders_df()
    income_df = db.get_income_df()
    expenses_df = db.get_expenses_df()

    if orders_df.empty and income_df.empty and expenses_df.empty:
        st.info("No data yet. Add orders, income, or expenses to see analytics.")
        return

    # --- Summary metrics ---
    total_income = income_df["amount"].sum() if not income_df.empty else 0.0
    total_expense = expenses_df["amount"].sum() if not expenses_df.empty else 0.0
    total_orders_value = orders_df["amount"].sum() if not orders_df.empty else 0.0
    margin_pct = ((total_income - total_expense) / total_income * 100) if total_income > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Revenue (Income)", format_currency(total_income))
    with c2:
        st.metric("Total Expenses", format_currency(total_expense))
    with c3:
        st.metric("Total Orders Value", format_currency(total_orders_value))
    with c4:
        st.metric("Margin %", f"{margin_pct:.1f}%")
    st.caption("Margin % = (Income − Expense) / Income")

    st.divider()

    # --- Cost head pie chart ---
    st.subheader("Cost Head Distribution")
    if not expenses_df.empty:
        cost_totals = expenses_df.groupby("cost_head")["amount"].sum()
        cost_totals = cost_totals[cost_totals > 0]
        if not cost_totals.empty:
            fig_pie = go.Figure(
                data=[go.Pie(labels=cost_totals.index.tolist(), values=cost_totals.values.tolist())]
            )
            fig_pie.update_layout(title="Expenses by cost head")
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.caption("No expenses recorded yet.")
    else:
        st.caption("No expenses recorded yet.")

    st.divider()

    # --- Recurring vs total customers ---
    st.subheader("Customer Metrics")
    if not orders_df.empty:
        cust_counts = orders_df.groupby("customer_name").size()
        total_customers = len(cust_counts)
        recurring = (cust_counts >= 2).sum()
        pct_repeat = (recurring / total_customers * 100) if total_customers > 0 else 0.0
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total unique customers", total_customers)
        with col2:
            st.metric("Recurring customers (2+ orders)", recurring)
        with col3:
            st.metric("% Recurring", f"{pct_repeat:.1f}%")
    else:
        st.caption("No orders yet.")

    st.divider()

    # --- Weekly / Monthly: Orders, Income, Expenses (3 bars per timeframe) ---
    st.subheader("Orders vs Income vs Expenses Over Time")
    period = st.radio("Group by", ["Monthly", "Weekly"], key="income_period", horizontal=True)
    period_suffix = "M" if period == "Monthly" else "W"
    has_any = not orders_df.empty or not income_df.empty or not expenses_df.empty
    if has_any:
        all_periods = set()
        by_orders = pd.DataFrame(columns=["period", "Orders"])
        by_income = pd.DataFrame(columns=["period", "Income"])
        by_expenses = pd.DataFrame(columns=["period", "Expenses"])

        if not orders_df.empty:
            o = orders_df.copy()
            o["date"] = pd.to_datetime(o["date"])
            o["period"] = o["date"].dt.to_period(period_suffix).astype(str)
            by_orders = o.groupby("period")["amount"].sum().reset_index().rename(columns={"amount": "Orders"})
            all_periods.update(by_orders["period"].tolist())
        if not income_df.empty:
            i = income_df.copy()
            i["date"] = pd.to_datetime(i["date"])
            i["period"] = i["date"].dt.to_period(period_suffix).astype(str)
            by_income = i.groupby("period")["amount"].sum().reset_index().rename(columns={"amount": "Income"})
            all_periods.update(by_income["period"].tolist())
        if not expenses_df.empty:
            e = expenses_df.copy()
            e["date"] = pd.to_datetime(e["date"])
            e["period"] = e["date"].dt.to_period(period_suffix).astype(str)
            by_expenses = e.groupby("period")["amount"].sum().reset_index().rename(columns={"amount": "Expenses"})
            all_periods.update(by_expenses["period"].tolist())

        if all_periods:
            merged = pd.DataFrame({"period": sorted(all_periods)})
            merged = merged.merge(by_orders, on="period", how="left").merge(by_income, on="period", how="left").merge(by_expenses, on="period", how="left")
            merged = merged.fillna(0)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=merged["period"], y=merged["Orders"], name="Orders", marker_color="#3498db"))
            fig.add_trace(go.Bar(x=merged["period"], y=merged["Income"], name="Income", marker_color="#2ecc71"))
            fig.add_trace(go.Bar(x=merged["period"], y=merged["Expenses"], name="Expenses", marker_color="#e74c3c"))
            fig.update_layout(barmode="group", title="Orders vs Income vs Expenses", xaxis_tickangle=-45, yaxis_title="Amount (₹)")
            st.plotly_chart(fig, width="stretch")
        else:
            st.caption("No data to display.")
    else:
        st.caption("No data recorded yet.")

    st.divider()

    # --- Orders vs income (pending) ---
    st.subheader("Orders vs Income (Pending)")
    if not orders_df.empty or not income_df.empty:
        orders_pending = orders_df.copy()
        income_pending = income_df.copy()
        months = set()
        if not orders_pending.empty:
            orders_pending["date"] = pd.to_datetime(orders_pending["date"])
            orders_pending["month"] = orders_pending["date"].dt.to_period("M").astype(str)
            months.update(orders_pending["month"].tolist())
        if not income_pending.empty:
            income_pending["date"] = pd.to_datetime(income_pending["date"])
            income_pending["month"] = income_pending["date"].dt.to_period("M").astype(str)
            months.update(income_pending["month"].astype(str).tolist())

        if months:
            selected_month = st.selectbox("Select month", sorted(months, reverse=True))
            orders_month = (
                orders_pending[orders_pending["month"] == selected_month]["amount"].sum()
                if not orders_pending.empty
                else 0.0
            )
            income_month = (
                income_pending[income_pending["month"] == selected_month]["amount"].sum()
                if not income_pending.empty
                else 0.0
            )
            pending = orders_month - income_month
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(f"Orders value ({selected_month})", format_currency(orders_month))
            with c2:
                st.metric(f"Income credited ({selected_month})", format_currency(income_month))
            with c3:
                st.metric("Pending to be credited", format_currency(max(0, pending)))
            if pending > 0:
                st.warning(f"₹{pending:,.2f} pending from orders this month.")
    else:
        st.caption("Add orders and income to see pending analysis.")

    st.divider()

    # --- Customer analysis ---
    st.subheader("Customer Analysis")
    customers = db.get_unique_customers()
    if not customers:
        st.caption("No customers yet. Add orders with customer names.")
    else:
        selected_customer = st.selectbox("Select customer", customers, key="cust_select")
        if selected_customer:
            cust_orders = db.get_customer_orders_df(selected_customer)
            cust_income = db.get_customer_income_df(selected_customer)

            total_orders = cust_orders["amount"].sum() if not cust_orders.empty else 0.0
            total_paid = cust_income["amount"].sum() if not cust_income.empty else 0.0
            amount_due = max(0.0, total_orders - total_paid)

            st.metric("Amount due", format_currency(amount_due))
            if amount_due == 0 and total_orders > 0:
                st.success("Fully paid.")
            elif amount_due > 0:
                st.warning(f"Outstanding: {format_currency(amount_due)}")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Order history**")
                if cust_orders.empty:
                    st.caption("No orders.")
                else:
                    display_orders = cust_orders[["date", "product", "quantity", "unit_price", "amount"]].copy()
                    display_orders = display_orders.rename(
                        columns={
                            "date": "Date",
                            "product": "Product",
                            "quantity": "Qty",
                            "unit_price": "Unit price",
                            "amount": "Amount",
                        }
                    )
                    display_orders["Amount"] = display_orders["Amount"].apply(format_currency)
                    st.dataframe(display_orders, width="stretch", hide_index=True)

            with col2:
                st.markdown("**Payment history**")
                if cust_income.empty:
                    st.caption("No payments recorded. Add income entries with this customer name.")
                else:
                    display_income = cust_income[["date", "amount", "payment_method"]].copy()
                    display_income = display_income.rename(
                        columns={"date": "Date", "amount": "Amount", "payment_method": "Method"}
                    )
                    display_income["Amount"] = display_income["Amount"].apply(format_currency)
                    st.dataframe(display_income, width="stretch", hide_index=True)


def main():
    st.set_page_config(
        page_title="Dairy Business Logger",
        page_icon="🥛",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🥛 Dairy Business Logging")
    st.caption("Track orders, income, and expenses. Analyze performance.")

    page = st.sidebar.radio(
        "Go to",
        ["Add Order", "Add Income", "Add Expense", "View & Edit Logs", "Dashboard"],
        label_visibility="collapsed",
    )
    st.sidebar.caption(f"View: **{page}**")

    if page == "Add Order":
        render_add_order()
    elif page == "Add Income":
        render_add_income()
    elif page == "Add Expense":
        render_add_expense()
    elif page == "View & Edit Logs":
        render_view_edit_logs()
    elif page == "Dashboard":
        render_dashboard()


if __name__ == "__main__":
    main()
