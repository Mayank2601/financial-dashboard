"""
Financial Dashboard – XLSX statements.
Upload Excel file(s); all sheets are read. Columns: Date, Narration, Chq./Ref.No.,
Value Dt, Withdrawal Amt., Deposit Amt., Closing Balance.
"""

import streamlit as st
import pandas as pd
import io
from typing import List, Optional, Tuple
import plotly.express as px

# ---------------------------------------------------------------------------
# Expected column names (strip and match flexibly)
# ---------------------------------------------------------------------------

EXPECTED_COLUMNS = {
    "date": ["Date", "date", "DATE"],
    "narration": ["Narration", "narration", "NARRATION"],
    "chq_ref": ["Chq./Ref.No.", "Chq./Ref.No", "Chq/Ref.No.", "Ref No"],
    "value_dt": ["Value Dt", "Value Dt.", "Value Date", "value dt"],
    "withdrawn": ["Withdrawal Amt.", "Withdrawal Amt", "Withdrawn Amt.", "Withdrawn Amt", "Withdrawal", "Debit"],
    "deposit": ["Deposit Amt.", "Deposit Amt", "Deposit", "Credit"],
    "balance": ["Closing Balance", "Closing Bal", "Balance"],
}

# Cost heads and keywords (order = first match wins; each transaction counted once – no double counting)
COST_HEADS = [
    (
        "Salary",
        [
            "salary", "advanc", "salar", "bisheshar", "radheshyam", "shiv ram", "sanjay",
            "harsh", "pyare", "somwati", "surinder", "sikander", "amit", "bimal", "mayank", "sheetla", "prahlad", "CNRB0000103",
        ],
    ),
    ("Feed", ["feed", "tudi", "ganna", "rakesh", "seed", "atta", "mineral", "chokar", "HARDEEPSINGH"]),
    ("Rent", ["rent"]),
    ("Fuel and Transportation", ["gas", "refill", "petrol", "cylinder", "auto", "service", "transport", "filling", "fuel", "bike"]),
    ("Expansion (cow, fridge)", ["cow", "refrig", "crockery"]),
    ("Marketing", ["print", "adver"]),
    ("Loan, CC", ["loan", "credit"]),
    ("Miscellaneous", ["ration", "fee", "medical", "ghee", "fees", "netflix", "amazon", "blinkit", "swiggy", "airtel", "jio", "vikram", "ROOPBASANT"]),
]


def _upi_customer_id(narration: str) -> Optional[str]:
    """
    For narrations starting with UPI, return the customer identifier:
    the substring before the second '-'. Same identifier = same customer.
    E.g. UPI-SUBHASHCHANDERBALI-ljksdf@okhdfcbank -> UPI-SUBHASHCHANDERBALI
    Returns None for non-UPI narrations.
    """
    n = (str(narration) if pd.notna(narration) else "").strip()
    if not n.upper().startswith("UPI"):
        return None
    first = n.find("-")
    if first == -1:
        return n
    second = n.find("-", first + 1)
    if second == -1:
        return n
    return n[:second]


def _neft_customer_id(narration: str) -> Optional[str]:
    """
    For narrations starting with NEFT, return the customer identifier:
    the substring before the second '-'. Same identifier = same customer.
    E.g. NEFT CR-SBIN0000583-MRS RASHMI SAXENA -> NEFT CR-SBIN0000583
    Returns None for non-NEFT narrations.
    """
    n = (str(narration) if pd.notna(narration) else "").strip()
    if not n.upper().startswith("NEFT"):
        return None
    first = n.find("-")
    if first == -1:
        return n
    second = n.find("-", first + 1)
    if second == -1:
        return n
    return n[:second]


def _imps_customer_id(narration: str) -> Optional[str]:
    """
    For narrations starting with IMPS, return the customer identifier:
    the substring between the second and third '-'. Same identifier = same customer.
    E.g. IMPS-506016885554-REKHA MITTAL-SBIN-XXXXXXX4686-MILK PAYMENT -> REKHA MITTAL
    Returns None for non-IMPS narrations.
    """
    n = (str(narration) if pd.notna(narration) else "").strip()
    if not n.upper().startswith("IMPS"):
        return None
    first = n.find("-")
    if first == -1:
        return n
    second = n.find("-", first + 1)
    if second == -1:
        return n
    third = n.find("-", second + 1)
    if third == -1:
        return n
    return n[second + 1 : third]


def _excluded_from_expense(narration: str) -> bool:
    """True if this withdrawal should not count as expense (e.g. NEFT DR-CNRB0002374 transfers)."""
    n = (str(narration) if pd.notna(narration) else "").strip().upper()
    return n.startswith("NEFT DR-CNRB0002374")


def _expense_mask(df: pd.DataFrame) -> pd.Series:
    """Boolean mask: debit > 0 and not excluded from expense (e.g. NEFT DR-CNRB0002374)."""
    is_debit = df["debit"] > 0
    excluded = df["narration"].fillna("").apply(_excluded_from_expense)
    return is_debit & ~excluded


def _assign_cost_head(narration: str) -> str:
    """Assign exactly one cost head per transaction (counted once).
    First cost head with any matching keyword wins; multiple keyword hits within
    the same cost head do not double-count – we return one label per transaction."""
    text = (str(narration) if pd.notna(narration) else "").lower()
    for name, keywords in COST_HEADS:
        if any(kw.lower() in text for kw in keywords):
            return name  # one return per transaction – no double count
    return "Other"


def _normalize(s: str) -> str:
    """Normalize for flexible matching: strip and lowercase."""
    if not isinstance(s, str):
        s = str(s)
    return s.strip().lower()


def _find_column(columns: list, aliases: list, normalize_fn) -> Optional[str]:
    """Return the first column name that matches any alias (exact or contains)."""
    col_normalized = {c: normalize_fn(c) for c in columns}
    for alias in aliases:
        key = normalize_fn(alias)
        for col, col_norm in col_normalized.items():
            if key == col_norm or key in col_norm or col_norm in key:
                return col
    return None


def _normalize_columns(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Rename columns to standard names: date, narration, debit, credit, balance.
    Returns None if required columns are missing.
    Uses flexible matching (strip, lowercase, substring) so slight name differences still match.
    """
    def strip(s):
        return s.strip() if isinstance(s, str) else str(s).strip()

    columns = list(df.columns)
    mapping = {}

    date_col = _find_column(columns, EXPECTED_COLUMNS["date"], _normalize)
    if date_col is not None:
        mapping[date_col] = "date"

    narr_col = _find_column(columns, EXPECTED_COLUMNS["narration"], _normalize)
    if narr_col is not None:
        mapping[narr_col] = "narration"

    debit_col = _find_column(columns, EXPECTED_COLUMNS["withdrawn"], _normalize)
    if debit_col is not None:
        mapping[debit_col] = "debit"

    credit_col = _find_column(columns, EXPECTED_COLUMNS["deposit"], _normalize)
    if credit_col is not None:
        mapping[credit_col] = "credit"

    balance_col = _find_column(columns, EXPECTED_COLUMNS["balance"], _normalize)
    if balance_col is not None:
        mapping[balance_col] = "balance"

    required = {"date", "debit", "credit"}
    if not required.issubset(set(mapping.values())):
        return None

    out = df.rename(columns=mapping)
    use = [c for c in ["date", "narration", "debit", "credit", "balance"] if c in out.columns]
    return out[use].copy()


def _parse_date(val) -> Optional[pd.Timestamp]:
    if pd.isna(val):
        return None
    if isinstance(val, pd.Timestamp):
        return val
    if hasattr(val, "date"):
        return pd.Timestamp(val)
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


def _parse_amount(val) -> float:
    if pd.isna(val) or val == "" or val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _header_row_to_columns(raw_df: pd.DataFrame, header_row: int) -> Optional[List[str]]:
    """Return list of column names from header_row; None if invalid."""
    if header_row >= len(raw_df) or header_row < 0:
        return None
    header_vals = raw_df.iloc[header_row]
    cols = []
    for i, v in enumerate(header_vals):
        c = str(v).strip() if pd.notna(v) and str(v).strip().lower() != "nan" else f"_col_{i}"
        cols.append(c)
    return cols


def _has_date_value(val) -> bool:
    """True if the value looks like a present date (not empty/NaN)."""
    if pd.isna(val):
        return False
    s = str(val).strip().lower()
    if s in ("", "nan", "nat", "none"):
        return False
    return True


def _merge_narration_rows(norm: pd.DataFrame) -> pd.DataFrame:
    """
    Merge continuation rows into the previous transaction.
    Rows without a date are treated as narration continuation of the previous row;
    their narration text is appended to the previous row's narration.
    Returns a DataFrame with one row per transaction and complete merged narration.
    """
    if norm.empty or "date" not in norm.columns:
        return norm.copy()
    norm = norm.copy()
    if "narration" not in norm.columns:
        norm["narration"] = ""
    rows_out: List[dict] = []
    current: Optional[dict] = None

    for _, row in norm.iterrows():
        if _has_date_value(row.get("date")):
            if current is not None:
                rows_out.append(current)
            current = row.to_dict()
            nar = current.get("narration")
            current["narration"] = "" if pd.isna(nar) or str(nar).strip() == "" else str(nar).strip()
        else:
            # Continuation row: append this row's narration to current transaction
            if current is not None:
                extra = row.get("narration")
                if pd.notna(extra) and str(extra).strip():
                    current["narration"] = (current.get("narration") or "") + str(extra).strip()

    if current is not None:
        rows_out.append(current)

    if not rows_out:
        return pd.DataFrame(columns=norm.columns)
    return pd.DataFrame(rows_out).reindex(columns=norm.columns)


def _process_norm(norm: pd.DataFrame) -> pd.DataFrame:
    """Parse dates/amounts and return cleaned norm. Works on a copy to avoid SettingWithCopyWarning."""
    norm = norm.copy()
    norm["date"] = norm["date"].apply(_parse_date)
    norm = norm.dropna(subset=["date"])
    if len(norm) == 0:
        return norm
    if "debit" in norm.columns:
        norm["debit"] = norm["debit"].apply(_parse_amount)
    else:
        norm["debit"] = 0.0
    if "credit" in norm.columns:
        norm["credit"] = norm["credit"].apply(_parse_amount)
    else:
        norm["credit"] = 0.0
    if "balance" in norm.columns:
        norm["balance"] = norm["balance"].apply(_parse_amount)
    if "narration" not in norm.columns:
        norm["narration"] = ""
    else:
        norm["narration"] = norm["narration"].fillna("").astype(str)
    return norm


def load_xlsx_all_sheets(file_bytes: bytes) -> Tuple[List[pd.DataFrame], int, int]:
    """
    Read ALL sheets. Only the first sheet has a header row; all other sheets use the same columns (no header).
    Returns (list of normalized DataFrames, total_sheets_count, loaded_sheets_count).
    """
    buf = io.BytesIO(file_bytes)
    try:
        all_sheets = pd.read_excel(buf, sheet_name=None, header=None, engine="openpyxl")
    except Exception:
        buf.seek(0)
        all_sheets = pd.read_excel(buf, sheet_name=None, header=None)

    total = len(all_sheets)
    loaded = []
    header_names: Optional[List[str]] = None

    for sheet_index, (sheet_name, raw_df) in enumerate(all_sheets.items()):
        if raw_df.empty:
            continue

        if sheet_index == 0:
            # First sheet: row 0 is header, rest is data
            cols = _header_row_to_columns(raw_df, 0)
            if cols is None:
                continue
            data_df = raw_df.iloc[1:].copy()
            data_df.columns = cols
            norm = _normalize_columns(data_df)
            if norm is None or len(norm.columns) < 3:
                continue
            header_names = cols
            norm = _merge_narration_rows(norm)
            norm = _process_norm(norm)
            if len(norm) > 0:
                loaded.append(norm)
        else:
            # Other sheets: no header, reuse column names from first sheet
            if header_names is None:
                continue
            if raw_df.shape[1] != len(header_names):
                continue
            data_df = raw_df.copy()
            data_df.columns = header_names
            norm = _normalize_columns(data_df)
            if norm is None:
                continue
            norm = _merge_narration_rows(norm)
            norm = _process_norm(norm)
            if len(norm) > 0:
                loaded.append(norm)

    return loaded, total, len(loaded)


def build_dataframe_from_xlsx(uploaded_files: List) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Read all uploaded XLSX files, ALL sheets each, normalize and combine.
    Returns (combined DataFrame or None, status_message).
    """
    all_dfs: List[pd.DataFrame] = []
    total_sheets = 0
    loaded_sheets = 0

    for f in uploaded_files:
        raw = f.read()
        f.seek(0)
        try:
            sheets_list, total, loaded = load_xlsx_all_sheets(raw)
            all_dfs.extend(sheets_list)
            total_sheets += total
            loaded_sheets += loaded
        except Exception:
            pass

    if not all_dfs:
        return None, f"No transaction data found. Total sheets read: {total_sheets}, loaded: {loaded_sheets}."

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)
    msg = f"Total sheets in file(s): {total_sheets}, sheets loaded: {loaded_sheets}, total rows: {len(combined)}."
    return combined, msg


def format_currency(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """Convert to dtypes safe for Streamlit (avoids Arrow LargeUtf8 serialization error)."""
    df = df.copy()
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(object)
    return df


def main():
    st.set_page_config(
        page_title="Financial Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    if "df" not in st.session_state:
        st.session_state.df = None
    if "process_error" not in st.session_state:
        st.session_state.process_error = None

    # ---- Upload (on every page, at top) ----
    st.title("📊 Financial Dashboard (XLSX)")
    st.subheader("Upload statement(s)")
    uploaded = st.file_uploader(
        "Upload XLSX file(s)",
        type=["xlsx", "xls"],
        accept_multiple_files=True,
        help="Upload one or more Excel files. All sheets in each file will be read.",
    )
    process_clicked = st.button("Process files")

    if process_clicked:
        st.session_state.process_error = None
        st.session_state.df = None
        if not uploaded:
            st.session_state.process_error = "Please upload at least one XLSX file."
        else:
            with st.spinner("Reading all sheets from uploaded file(s)..."):
                df, msg = build_dataframe_from_xlsx(uploaded)
            if df is None or df.empty:
                st.session_state.process_error = (
                    "No transaction rows found. " + msg
                    + " Check that each sheet has columns: Date, Narration, Withdrawal Amt., Deposit Amt., Closing Balance."
                )
            else:
                st.session_state.df = df
                st.session_state.load_msg = msg
                st.success(f"Loaded **{len(df)}** transactions. {msg}")

    if st.session_state.process_error:
        st.error(st.session_state.process_error)

    df = st.session_state.df
    if df is None or df.empty:
        st.info(
            "Upload XLSX file(s) with columns: **Date**, **Narration**, **Chq./Ref.No.**, "
            "**Value Dt**, **Withdrawal Amt.**, **Deposit Amt.**, **Closing Balance** — then click **Process files**."
        )
        return

    # ---- Page selector ----
    page = st.sidebar.radio(
        "Go to",
        ["Summary", "Income", "Expense"],
        label_visibility="collapsed",
    )
    st.sidebar.caption(f"View: **{page}**")

    # ---- Page: Summary ----
    if page == "Summary":
        st.header("Summary")
        total_income = df["credit"].sum()
        expense_mask = _expense_mask(df)
        total_expense = df.loc[expense_mask, "debit"].sum()
        expense_count = expense_mask.sum()
        total_profit = total_income - total_expense
        margin_pct = (total_profit / total_income * 100) if total_income > 0 else 0.0
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Income (Deposits)", format_currency(total_income))
        with c2:
            st.metric("Total Expense (Withdrawals)", format_currency(total_expense))
        with c3:
            st.metric("Total Profit", format_currency(total_profit))
        with c4:
            st.metric("Margin %", f"{margin_pct:.1f}%")
        st.caption(f"Total transactions: **{len(df)}** (Income: {(df['credit'] > 0).sum()}, Expense: **{expense_count}** — excludes NEFT DR-CNRB0002374 from expense). Profit = Income − Expense; Margin % = Profit / Income.")
        # Monthly income vs expense bar chart
        df_summary = df.copy()
        df_summary["month"] = pd.to_datetime(df_summary["date"]).dt.to_period("M").astype(str)
        monthly_income = df_summary.groupby("month")["credit"].sum().reset_index()
        monthly_income = monthly_income.rename(columns={"credit": "income"})
        expense_df_summary = df_summary[expense_mask].copy()
        monthly_expense = expense_df_summary.groupby("month")["debit"].sum().reset_index()
        monthly_expense = monthly_expense.rename(columns={"debit": "expense"})
        monthly_ie = monthly_income.merge(monthly_expense, on="month", how="outer").fillna(0)
        if not monthly_ie.empty:
            monthly_ie = monthly_ie.sort_values("month").reset_index(drop=True)
            monthly_ie["income"] = monthly_ie["income"].astype(float)
            monthly_ie["expense"] = monthly_ie["expense"].astype(float)
            monthly_ie_long = monthly_ie.melt(id_vars=["month"], value_vars=["income", "expense"], var_name="Type", value_name="Amount (₹)")
            fig_monthly = px.bar(
                monthly_ie_long,
                x="month",
                y="Amount (₹)",
                color="Type",
                title="Monthly income vs expense",
                labels={"month": "Month"},
                barmode="group",
                color_discrete_map={"income": "#2ecc71", "expense": "#e74c3c"},
            )
            fig_monthly.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_monthly, use_container_width=True)
        # Cost head pie chart (exclude Other; expense excludes NEFT DR-CNRB0002374)
        expense_summary = df[expense_mask].copy()
        expense_summary["cost_head"] = expense_summary["narration"].apply(_assign_cost_head)
        cost_totals_summary = expense_summary.groupby("cost_head", sort=False)["debit"].sum()
        cost_heads_only = [name for name, _ in COST_HEADS]
        pie_summary = cost_totals_summary[cost_totals_summary.index.isin(cost_heads_only)]
        pie_summary = pie_summary[pie_summary > 0]
        if not pie_summary.empty:
            st.subheader("Cost head distribution")
            fig_pie_summary = px.pie(
                values=pie_summary.values.astype(float).tolist(),
                names=pie_summary.index.astype(str).tolist(),
                title="Cost head distribution",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig_pie_summary, use_container_width=True)
        # Customer analysis (UPI + NEFT + IMPS from income)
        st.subheader("Customer analysis")
        income_summary = df[df["credit"] > 0].copy()
        income_summary["upi_customer_id"] = income_summary["narration"].apply(_upi_customer_id)
        income_summary["neft_customer_id"] = income_summary["narration"].apply(_neft_customer_id)
        income_summary["imps_customer_id"] = income_summary["narration"].apply(_imps_customer_id)
        upi_income_s = income_summary[income_summary["upi_customer_id"].notna()]
        neft_income_s = income_summary[income_summary["neft_customer_id"].notna()]
        imps_income_s = income_summary[income_summary["imps_customer_id"].notna()]
        upi_totals_s = upi_income_s.groupby("upi_customer_id", as_index=False).agg(transactions=("credit", "count"), total_amount=("credit", "sum")) if not upi_income_s.empty else pd.DataFrame(columns=["upi_customer_id", "transactions", "total_amount"])
        neft_totals_s = neft_income_s.groupby("neft_customer_id", as_index=False).agg(transactions=("credit", "count"), total_amount=("credit", "sum")) if not neft_income_s.empty else pd.DataFrame(columns=["neft_customer_id", "transactions", "total_amount"])
        imps_totals_s = imps_income_s.groupby("imps_customer_id", as_index=False).agg(transactions=("credit", "count"), total_amount=("credit", "sum")) if not imps_income_s.empty else pd.DataFrame(columns=["imps_customer_id", "transactions", "total_amount"])
        total_unique_s = len(upi_totals_s) + len(neft_totals_s) + len(imps_totals_s)
        repeat_s = ((upi_totals_s["transactions"] > 2).sum() if not upi_totals_s.empty else 0) + ((neft_totals_s["transactions"] > 2).sum() if not neft_totals_s.empty else 0) + ((imps_totals_s["transactions"] > 2).sum() if not imps_totals_s.empty else 0)
        pct_repeat_s = (repeat_s / total_unique_s * 100) if total_unique_s > 0 else 0.0
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total unique customers (UPI + NEFT + IMPS)", total_unique_s)
        with col2:
            st.metric("Repeat customers (3+ transactions)", repeat_s)
        with col3:
            st.metric("% repeat customers", f"{pct_repeat_s:.1f}%")
        st.caption("From income (deposits). UPI/NEFT: unique = text before 2nd dash; IMPS: text between 2nd and 3rd dash. Repeat = more than 2 transactions.")
        return

    # ---- Page: Income ----
    if page == "Income":
        st.header("Income – all deposit transactions")
        income_df = df[df["credit"] > 0].copy()

        # Cash vs Digital (narration starts with CASHDEPOSIT or CASH DEPOSIT -> Cash; rest -> Digital)
        def _income_type(narration: str) -> str:
            n = (str(narration) if pd.notna(narration) else "").strip().upper()
            if n.startswith("CASHDEPOSIT") or n.startswith("CASH DEPOSIT"):
                return "Cash"
            return "Digital"

        income_df["income_type"] = income_df["narration"].apply(_income_type)
        cash_vs_digital = income_df.groupby("income_type")["credit"].sum()
        if not cash_vs_digital.empty:
            st.subheader("Cash vs Digital")
            fig_cash = px.pie(
                values=cash_vs_digital.values.astype(float).tolist(),
                names=cash_vs_digital.index.astype(str).tolist(),
                title="Cash vs Digital income",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            st.plotly_chart(fig_cash, use_container_width=True)

        # Customer analysis (UPI + NEFT + IMPS: unique and repeat)
        st.subheader("Customer analysis")
        income_df["upi_customer_id"] = income_df["narration"].apply(_upi_customer_id)
        income_df["neft_customer_id"] = income_df["narration"].apply(_neft_customer_id)
        income_df["imps_customer_id"] = income_df["narration"].apply(_imps_customer_id)
        upi_income = income_df[income_df["upi_customer_id"].notna()].copy()
        neft_income = income_df[income_df["neft_customer_id"].notna()].copy()
        imps_income = income_df[income_df["imps_customer_id"].notna()].copy()

        upi_totals = (
            upi_income.groupby("upi_customer_id", as_index=False)
            .agg(transactions=("credit", "count"), total_amount=("credit", "sum"))
        ) if not upi_income.empty else pd.DataFrame(columns=["upi_customer_id", "transactions", "total_amount"])
        neft_totals = (
            neft_income.groupby("neft_customer_id", as_index=False)
            .agg(transactions=("credit", "count"), total_amount=("credit", "sum"))
        ) if not neft_income.empty else pd.DataFrame(columns=["neft_customer_id", "transactions", "total_amount"])
        imps_totals = (
            imps_income.groupby("imps_customer_id", as_index=False)
            .agg(transactions=("credit", "count"), total_amount=("credit", "sum"))
        ) if not imps_income.empty else pd.DataFrame(columns=["imps_customer_id", "transactions", "total_amount"])

        total_unique = len(upi_totals) + len(neft_totals) + len(imps_totals)
        repeat_upi = (upi_totals["transactions"] > 2).sum() if not upi_totals.empty else 0
        repeat_neft = (neft_totals["transactions"] > 2).sum() if not neft_totals.empty else 0
        repeat_imps = (imps_totals["transactions"] > 2).sum() if not imps_totals.empty else 0
        repeat_customers_count = repeat_upi + repeat_neft + repeat_imps
        pct_repeat = (repeat_customers_count / total_unique * 100) if total_unique > 0 else 0.0

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total unique customers (UPI + NEFT + IMPS)", total_unique)
        with col2:
            st.metric("Repeat customers (3+ transactions)", repeat_customers_count)
        with col3:
            st.metric("% repeat customers", f"{pct_repeat:.1f}%")
        st.caption("UPI/NEFT: unique = same text before 2nd dash. IMPS: unique = text between 2nd and 3rd dash. Repeat = more than 2 transactions.")

        # Unique customers table (UPI, NEFT & IMPS combined)
        st.subheader("Unique customers (UPI, NEFT & IMPS)")
        if upi_income.empty and neft_income.empty and imps_income.empty:
            st.info("No UPI, NEFT or IMPS income transactions found. Unique customers: **UPI/NEFT** = part before 2nd dash; **IMPS** = part between 2nd and 3rd dash.")
        else:
            parts = []
            if not upi_totals.empty:
                u = upi_totals.copy()
                u["customer_id"] = u["upi_customer_id"]
                u["type"] = "UPI"
                parts.append(u[["customer_id", "type", "transactions", "total_amount"]])
            if not neft_totals.empty:
                n = neft_totals.copy()
                n["customer_id"] = n["neft_customer_id"]
                n["type"] = "NEFT"
                parts.append(n[["customer_id", "type", "transactions", "total_amount"]])
            if not imps_totals.empty:
                i = imps_totals.copy()
                i["customer_id"] = i["imps_customer_id"]
                i["type"] = "IMPS"
                parts.append(i[["customer_id", "type", "transactions", "total_amount"]])
            customer_totals = pd.concat(parts, ignore_index=True).sort_values("total_amount", ascending=False)
            customer_display = customer_totals.copy()
            customer_display["total_amount"] = customer_display["total_amount"].apply(format_currency)
            customer_display = customer_display.rename(
                columns={"customer_id": "Customer ID", "type": "Type", "transactions": "Transactions", "total_amount": "Total amount"}
            )
            st.dataframe(_dataframe_for_display(customer_display), use_container_width=True)

        # Search by keyword (income)
        st.subheader("Search by keyword")
        income_keyword = st.text_input(
            "Enter a keyword to filter income (deposits)",
            key="income_keyword_search",
            placeholder="Type a word and press Enter",
        )
        if income_keyword and income_keyword.strip():
            kw = income_keyword.strip().lower()
            nar = income_df["narration"].fillna("").astype(str).str.lower()
            mask = nar.str.contains(kw, na=False)
            matches_inc = income_df.loc[mask][["date", "narration", "credit"]].copy()
            if len(matches_inc) == 0:
                st.info(f"No income found containing **{income_keyword.strip()}**.")
            else:
                st.metric("Total income (matching keyword)", format_currency(matches_inc["credit"].sum()))
                matches_inc["month"] = pd.to_datetime(matches_inc["date"]).dt.to_period("M").astype(str)
                monthly_inc = matches_inc.groupby("month")["credit"].sum().reset_index()
                monthly_inc = monthly_inc.sort_values("month").reset_index(drop=True)
                monthly_inc["credit"] = monthly_inc["credit"].astype(float)
                fig_inc_kw = px.bar(
                    monthly_inc,
                    x="month",
                    y="credit",
                    title=f"Monthly income for keyword: {income_keyword.strip()}",
                    labels={"credit": "Amount (₹)", "month": "Month"},
                )
                fig_inc_kw.update_layout(xaxis_tickangle=-45, showlegend=False)
                st.plotly_chart(fig_inc_kw, use_container_width=True)
                matches_inc["date"] = pd.to_datetime(matches_inc["date"]).dt.strftime("%Y-%m-%d")
                matches_inc_display = matches_inc.rename(columns={"narration": "Narration", "credit": "Amount"})
                matches_inc_display["Amount"] = matches_inc_display["Amount"].apply(format_currency)
                matches_inc_display = matches_inc_display.rename(columns={"date": "Date"})
                st.caption(f"**{len(matches_inc)}** transaction(s) matching **{income_keyword.strip()}**.")
                st.dataframe(_dataframe_for_display(matches_inc_display[["Date", "Narration", "Amount"]]), use_container_width=True)
        st.markdown("---")

        income = income_df[["date", "narration", "credit"]].copy()
        income = income.rename(columns={"narration": "Narration", "credit": "Amount"})
        income["date"] = pd.to_datetime(income["date"]).dt.strftime("%Y-%m-%d")
        income_sort = st.radio(
            "Sort by",
            ["Date (newest first)", "Date (oldest first)", "Amount (highest first)", "Amount (lowest first)"],
            key="income_sort",
            horizontal=True,
        )
        if income_sort == "Date (newest first)":
            income = income.sort_values("date", ascending=False)
        elif income_sort == "Date (oldest first)":
            income = income.sort_values("date", ascending=True)
        elif income_sort == "Amount (highest first)":
            income = income.sort_values("Amount", ascending=False)
        else:
            income = income.sort_values("Amount", ascending=True)

        income_display = income.copy()
        income_display["Amount"] = income_display["Amount"].apply(format_currency)
        income_display = income_display.rename(columns={"date": "Date"})
        st.caption(f"Showing all **{len(income_display)}** deposit transactions.")
        st.dataframe(_dataframe_for_display(income_display), use_container_width=True)
        return

    # ---- Page: Expense ----
    if page == "Expense":
        st.header("Expense – all withdrawal transactions")
        expense_mask_exp = _expense_mask(df)
        expense = df[expense_mask_exp][["date", "narration", "debit"]].copy()
        expense = expense.rename(columns={"narration": "Narration", "debit": "Amount"})
        expense["date"] = pd.to_datetime(expense["date"]).dt.strftime("%Y-%m-%d")
        st.caption("Excludes withdrawals with narration starting with **NEFT DR-CNRB0002374** (not counted as expense).")

        # Cost heads (grouped keywords; each transaction counted once – first match wins)
        st.subheader("Costs")
        expense_for_costs = df[expense_mask_exp].copy()
        expense_for_costs["cost_head"] = expense_for_costs["narration"].apply(_assign_cost_head)
        cost_totals = expense_for_costs.groupby("cost_head", sort=False)["debit"].sum()
        cost_order = [name for name, _ in COST_HEADS] + ["Other"]
        cost_totals = cost_totals.reindex(cost_order).fillna(0)
        row1 = st.columns(4)
        for i in range(min(4, len(cost_order))):
            with row1[i]:
                st.metric(cost_order[i], format_currency(cost_totals.iloc[i]))
        row2 = st.columns(4)
        for i in range(4, min(8, len(cost_order))):
            with row2[i - 4]:
                st.metric(cost_order[i], format_currency(cost_totals.iloc[i]))
        if len(cost_order) > 8:
            row3 = st.columns(4)
            for i in range(8, len(cost_order)):
                with row3[i - 8]:
                    st.metric(cost_order[i], format_currency(cost_totals.iloc[i]))
        # Monthly cost by cost head (stacked bar chart; exclude Other)
        expense_for_costs["month"] = pd.to_datetime(expense_for_costs["date"]).dt.to_period("M").astype(str)
        monthly_by_head = expense_for_costs.groupby(["month", "cost_head"])["debit"].sum().reset_index()
        cost_heads_only = [name for name, _ in COST_HEADS]
        monthly_by_head = monthly_by_head[monthly_by_head["cost_head"].isin(cost_heads_only)]
        if not monthly_by_head.empty:
            monthly_by_head = monthly_by_head.sort_values("month").reset_index(drop=True)
            monthly_by_head["debit"] = monthly_by_head["debit"].astype(float)
            fig_costs = px.bar(
                monthly_by_head,
                x="month",
                y="debit",
                color="cost_head",
                title="Monthly cost by cost head",
                labels={"debit": "Amount (₹)", "month": "Month", "cost_head": "Cost head"},
                barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig_costs.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_costs, use_container_width=True)
        # Pie chart for cost heads (exclude Other)
        cost_heads_only = [name for name, _ in COST_HEADS]
        pie_totals = cost_totals[cost_totals.index.isin(cost_heads_only)]
        pie_totals = pie_totals[pie_totals > 0]
        if not pie_totals.empty:
            fig_pie = px.pie(
                values=pie_totals.values.astype(float).tolist(),
                names=pie_totals.index.astype(str).tolist(),
                title="Cost head distribution",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        # Search by cost keyword (below pie chart)
        st.subheader("Search by cost keyword")
        cost_keyword = st.text_input(
            "Enter a keyword to filter expenses (e.g. salary, feed, cow)",
            key="cost_keyword_search",
            placeholder="Type a word and press Enter",
        )
        if cost_keyword and cost_keyword.strip():
            expense_all = df[expense_mask_exp][["date", "narration", "debit"]].copy()
            nar = expense_all["narration"].fillna("").astype(str).str.lower()
            mask = nar.str.contains(cost_keyword.strip().lower(), na=False)
            matches = expense_all.loc[mask].copy()
            if len(matches) == 0:
                st.info(f"No expenses found containing **{cost_keyword.strip()}**.")
            else:
                total_withdrawn = matches["debit"].sum()
                st.metric("Total withdrawn (matching keyword)", format_currency(total_withdrawn))
                matches["month"] = pd.to_datetime(matches["date"]).dt.to_period("M").astype(str)
                monthly_kw = matches.groupby("month")["debit"].sum().reset_index()
                monthly_kw = monthly_kw.sort_values("month").reset_index(drop=True)
                monthly_kw["debit"] = monthly_kw["debit"].astype(float)
                fig_kw = px.bar(
                    monthly_kw,
                    x="month",
                    y="debit",
                    title=f"Monthly expense for keyword: {cost_keyword.strip()}",
                    labels={"debit": "Amount (₹)", "month": "Month"},
                )
                fig_kw.update_layout(xaxis_tickangle=-45, showlegend=False)
                st.plotly_chart(fig_kw, use_container_width=True)
                matches["date"] = pd.to_datetime(matches["date"]).dt.strftime("%Y-%m-%d")
                matches_display = matches.rename(columns={"narration": "Narration", "debit": "Amount"})
                matches_display["Amount"] = matches_display["Amount"].apply(format_currency)
                matches_display = matches_display.rename(columns={"date": "Date"})
                st.caption(f"**{len(matches)}** transaction(s) matching **{cost_keyword.strip()}**.")
                st.dataframe(_dataframe_for_display(matches_display[["Date", "Narration", "Amount"]]), use_container_width=True)
        st.markdown("---")

        expense_sort = st.radio(
            "Sort by",
            ["Date (newest first)", "Date (oldest first)", "Amount (highest first)", "Amount (lowest first)"],
            key="expense_sort",
            horizontal=True,
        )
        if expense_sort == "Date (newest first)":
            expense = expense.sort_values("date", ascending=False)
        elif expense_sort == "Date (oldest first)":
            expense = expense.sort_values("date", ascending=True)
        elif expense_sort == "Amount (highest first)":
            expense = expense.sort_values("Amount", ascending=False)
        else:
            expense = expense.sort_values("Amount", ascending=True)

        expense_display = expense.copy()
        expense_display["Amount"] = expense_display["Amount"].apply(format_currency)
        expense_display = expense_display.rename(columns={"date": "Date"})
        st.caption(f"Showing all **{len(expense_display)}** withdrawal transactions.")
        st.dataframe(_dataframe_for_display(expense_display), use_container_width=True)

        # Cost heads vs keywords reference
        st.markdown("---")
        st.subheader("Cost heads vs keywords")
        cost_head_map = pd.DataFrame(
            [(name, ", ".join(keywords)) for name, keywords in COST_HEADS],
            columns=["Cost head", "Keywords (first match wins)"],
        )
        st.caption("Transactions are assigned to a cost head when narration contains any of these keywords. **Other** = no keyword match.")
        st.dataframe(_dataframe_for_display(cost_head_map), use_container_width=True)
        return


if __name__ == "__main__":
    main()
