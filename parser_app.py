"""
Streamlit UI for HDFC Bank Statement PDF Parser
Upload PDF(s), optional password, choose format(s), download CSV/XLSX/JSON/OFX.
"""

import io
import json
import os
import streamlit as st
import numpy as np

# Import from statement_parser
from statement_parser import (
    parse_pdfs,
    export_csv,
    export_xlsx,
    export_json,
    export_ofx,
    COL_DATE,
    COL_NARRATION,
    COL_REF,
    COL_VALUE_DT,
    COL_WITHDRAWN,
    COL_DEPOSIT,
    COL_BALANCE,
)

st.set_page_config(page_title="Statement Parser", page_icon="📄", layout="centered")
st.title("📄 HDFC Statement Parser")
st.caption("Upload PDF statement(s) → get CSV, XLSX, JSON, or OFX")

# Password for protected PDFs — shown prominently
st.subheader("🔐 PDF password")
password = st.text_input(
    "Enter password if your statement PDF is password-protected",
    type="password",
    placeholder="Leave blank if PDF is not protected",
    help="HDFC statement PDFs are often password-protected; use the password you received with the statement.",
)
st.divider()

with st.sidebar:
    st.subheader("Options")
    formats = st.multiselect(
        "Export format(s)",
        ["CSV", "XLSX", "JSON", "OFX"],
        default=["CSV", "XLSX"],
    )
    st.divider()
    st.markdown("**Columns extracted:**")
    st.markdown("Date, Narration, Chq./Ref.No., Value Dt, Withdrawn Amt., Deposit Amt., Closing Balance")

uploaded = st.file_uploader("Upload PDF statement(s)", type="pdf", accept_multiple_files=True)

if not uploaded:
    st.info("Upload one or more HDFC bank statement PDFs to begin.")
    st.stop()

# Save uploads to temp dir
import tempfile
tmpdir = tempfile.mkdtemp()
paths = []
for f in uploaded:
    path = os.path.join(tmpdir, f.name)
    with open(path, "wb") as out:
        out.write(f.getvalue())
    paths.append(path)

with st.spinner("Parsing PDF(s)…"):
    try:
        df = parse_pdfs(paths, password or None)
    except FileNotFoundError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"Parse error: {e}")
        st.stop()

if df.empty:
    st.warning("No transactions found. Check PDF format and password.")
    st.stop()

st.success(f"Found **{len(df)}** transactions.")

# Preview
st.subheader("Preview")
st.dataframe(
    df.head(100).style.format({
        COL_WITHDRAWN: "{:,.2f}",
        COL_DEPOSIT: "{:,.2f}",
        COL_BALANCE: "{:,.2f}",
    }, na_rep=""),
    use_container_width=True,
)
if len(df) > 100:
    st.caption(f"Showing first 100 of {len(df)} rows.")

# Export and download
st.subheader("Download")
for fmt in formats:
    buf = io.BytesIO()
    if fmt == "CSV":
        df_exp = df.copy()
        df_exp[COL_DATE] = df_exp[COL_DATE].dt.strftime("%d/%m/%Y")
        df_exp[COL_VALUE_DT] = df_exp[COL_VALUE_DT].dt.strftime("%d/%m/%Y")
        buf = io.BytesIO(df_exp.to_csv(index=False).encode("utf-8"))
        st.download_button(
            f"Download {fmt}",
            data=buf.getvalue(),
            file_name="statement.csv",
            mime="text/csv",
            key=f"dl_{fmt}",
        )
    elif fmt == "XLSX":
        df_exp = df.copy()
        df_exp[COL_DATE] = df_exp[COL_DATE].dt.strftime("%d/%m/%Y")
        df_exp[COL_VALUE_DT] = df_exp[COL_VALUE_DT].dt.strftime("%d/%m/%Y")
        df_exp.to_excel(buf, index=False, engine="openpyxl")
        st.download_button(
            f"Download {fmt}",
            data=buf.getvalue(),
            file_name="statement.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"dl_{fmt}",
        )
    elif fmt == "JSON":
        df_exp = df.copy()
        df_exp[COL_DATE] = df_exp[COL_DATE].dt.strftime("%Y-%m-%d")
        df_exp[COL_VALUE_DT] = df_exp[COL_VALUE_DT].dt.strftime("%Y-%m-%d")
        df_exp[COL_WITHDRAWN] = df_exp[COL_WITHDRAWN].round(2)
        df_exp[COL_DEPOSIT] = df_exp[COL_DEPOSIT].round(2)
        df_exp[COL_BALANCE] = df_exp[COL_BALANCE].round(2)
        records = df_exp.replace({np.nan: None}).to_dict(orient="records")
        buf = io.BytesIO(json.dumps(records, indent=2, ensure_ascii=False).encode("utf-8"))
        st.download_button(
            f"Download {fmt}",
            data=buf.getvalue(),
            file_name="statement.json",
            mime="application/json",
            key=f"dl_{fmt}",
        )
    else:  # OFX
        import tempfile
        t = tempfile.NamedTemporaryFile(suffix=".ofx", delete=False)
        t.close()
        export_ofx(df, t.name)
        with open(t.name, "rb") as f:
            ofx_data = f.read()
        os.unlink(t.name)
        st.download_button(
            f"Download {fmt}",
            data=ofx_data,
            file_name="statement.ofx",
            mime="application/x-ofx",
            key=f"dl_{fmt}",
        )

# Cleanup temp files
for p in paths:
    try:
        os.unlink(p)
    except Exception:
        pass
try:
    os.rmdir(tmpdir)
except Exception:
    pass
