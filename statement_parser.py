#!/usr/bin/env python3
"""
HDFC Bank Statement PDF Parser
Extracts transactions and exports to CSV, XLSX, OFX, or JSON.
Columns: Date, Narration, Chq./Ref.No., Value Dt, Withdrawn Amt., Deposit Amt., Closing Balance
"""

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# Optional: pdfplumber for better table extraction
try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False


EXPECTED_HEADERS = [
    "Date",
    "Narration",
    "Chq./Ref.No.",
    "Value Dt",
    "Withdrawn Amt. ",
    "Deposit Amt. ",
    "Closing Balance",
]

# Normalized column names for internal use
COL_DATE = "Date"
COL_NARRATION = "Narration"
COL_REF = "Chq./Ref.No."
COL_VALUE_DT = "Value Dt"
COL_WITHDRAWN = "Withdrawn Amt."
COL_DEPOSIT = "Deposit Amt."
COL_BALANCE = "Closing Balance"


def _clean_amount(s):
    """Parse amount string like '3,070.00' or '' to float."""
    if s is None or (isinstance(s, str) and not s.strip()):
        return 0.0
    s = str(s).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _parse_date(s):
    """Parse DD/MM/YY to date object."""
    if s is None or not str(s).strip():
        return None
    s = str(s).strip()
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%d-%m-%y"):
        try:
            dt = datetime.strptime(s, fmt)
            if dt.year < 2000:
                dt = dt.replace(year=dt.year + 100)
            return dt.date()
        except ValueError:
            continue
    return None


def _normalize_columns(table_rows):
    """Normalize table so first row is headers; align to expected columns."""
    if not table_rows or len(table_rows) < 2:
        return []
    # Find header row (row containing "Date" and "Closing Balance" or similar)
    header_row_idx = None
    for i, row in enumerate(table_rows):
        row_str = " ".join(str(c or "").strip() for c in row if c)
        if "Date" in row_str and ("Closing" in row_str or "Balance" in row_str):
            header_row_idx = i
            break
    if header_row_idx is None:
        # Assume first row is header
        header_row_idx = 0
    headers = [str(h or "").strip() for h in table_rows[header_row_idx]]
    data_rows = table_rows[header_row_idx + 1 :]
    # Map to standard columns by position: Date, Narration, Chq/Ref, Value Dt, Withdrawn, Deposit, Balance
    # HDFC order is: Date | Narration | Chq./Ref.No. | Value Dt | Withdrawn Amt. | Deposit Amt. | Closing Balance
    def map_row(row):
        while len(row) < 7:
            row.append("")
        return {
            COL_DATE: (row[0] or "").strip(),
            COL_NARRATION: (row[1] or "").strip(),
            COL_REF: (row[2] or "").strip(),
            COL_VALUE_DT: (row[3] or "").strip(),
            COL_WITHDRAWN: (row[4] or "").strip(),
            COL_DEPOSIT: (row[5] or "").strip(),
            COL_BALANCE: (row[6] or "").strip(),
        }
    out = []
    for row in data_rows:
        if not any(str(c or "").strip() for c in row):
            continue
        # Skip if first cell is not a date (e.g. page header)
        first = (row[0] or "").strip()
        if not re.match(r"^\d{2}/\d{2}/\d{2}", first):
            continue
        out.append(map_row(row))
    return out


def extract_with_pdfplumber(pdf_path, password=None):
    """Extract transaction rows using pdfplumber tables."""
    if not HAS_PDFPLUMBER:
        return []
    all_data_rows = []
    header_used = False
    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables or []:
                    if not table:
                        continue
                    rows = [list(c or "" for c in row) for row in table if row and any(c for c in row)]
                    if not rows:
                        continue
                    if not header_used:
                        norm = _normalize_columns(rows)
                        all_data_rows.extend(norm)
                        header_used = True
                    else:
                        # Subsequent tables: treat as data only (no header), same column order
                        for row in rows:
                            first = (row[0] or "").strip()
                            if re.match(r"^\d{2}/\d{2}/\d{2}", first):
                                while len(row) < 7:
                                    row.append("")
                                all_data_rows.append({
                                    COL_DATE: (row[0] or "").strip(),
                                    COL_NARRATION: (row[1] or "").strip(),
                                    COL_REF: (row[2] or "").strip(),
                                    COL_VALUE_DT: (row[3] or "").strip(),
                                    COL_WITHDRAWN: (row[4] or "").strip(),
                                    COL_DEPOSIT: (row[5] or "").strip(),
                                    COL_BALANCE: (row[6] or "").strip(),
                                })
    except Exception:
        return []
    return all_data_rows


def extract_with_text(pdf_path, password=None):
    """Fallback: extract text with PyPDF2 and parse line-by-line."""
    if not HAS_PYPDF2:
        return []
    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            if reader.is_encrypted:
                reader.decrypt(password or "")
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception:
        return []
    return _parse_transactions_from_text(text)


def _parse_transactions_from_text(text):
    """Parse HDFC-style lines: Date ... Narration ... Ref ... ValueDt ... Withdrawn ... Deposit ... Balance."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    date_pattern = re.compile(r"^(\d{2}/\d{2}/\d{2})\s+")
    amount_pattern = re.compile(r"[\d,]+\.\d{2}")
    transactions = []
    current = None

    for line in lines:
        if "Statement of account" in line or "Page No" in line or "Account Branch" in line:
            continue
        if "Date" in line and "Narration" in line and "Closing" in line:
            continue
        date_match = date_pattern.match(line)
        if date_match:
            if current and current.get(COL_BALANCE) not in (None, ""):
                transactions.append(current)
            date_str = date_match.group(1)
            rest = line[len(date_match.group(0)) :].strip()
            amounts = amount_pattern.findall(rest)
            if len(amounts) >= 1:
                balance = amounts[-1].replace(",", "")
                withdrawn = ""
                deposit = ""
                value_dt = date_str
                ref = ""
                if len(amounts) >= 3:
                    withdrawn = amounts[-3].replace(",", "")
                    deposit = amounts[-2].replace(",", "")
                elif len(amounts) == 2:
                    # one of withdrawal or deposit
                    a = amounts[0].replace(",", "")
                    if _clean_amount(amounts[0]) > _clean_amount(amounts[1]):
                        withdrawn = a
                    else:
                        deposit = a
                # Narration: between date and first amount
                narration = rest
                for a in reversed(amounts):
                    idx = narration.rfind(a)
                    if idx != -1:
                        narration = narration[:idx].strip()
                narration = re.sub(r"\s+", " ", narration).strip()
                current = {
                    COL_DATE: date_str,
                    COL_NARRATION: narration,
                    COL_REF: ref,
                    COL_VALUE_DT: value_dt,
                    COL_WITHDRAWN: withdrawn,
                    COL_DEPOSIT: deposit,
                    COL_BALANCE: balance,
                }
            else:
                current = None
        else:
            if current:
                # Continuation of narration
                amounts = amount_pattern.findall(line)
                if amounts and len(amounts) >= 2:
                    current[COL_BALANCE] = amounts[-1].replace(",", "")
                    if len(amounts) >= 3:
                        current[COL_WITHDRAWN] = amounts[-3].replace(",", "")
                        current[COL_DEPOSIT] = amounts[-2].replace(",", "")
                    rest = line
                    for a in reversed(amounts):
                        idx = rest.rfind(a)
                        if idx != -1:
                            rest = rest[:idx].strip()
                    current[COL_NARRATION] = (current.get(COL_NARRATION) or "") + " " + rest
                else:
                    current[COL_NARRATION] = (current.get(COL_NARRATION) or "") + " " + line
    if current and current.get(COL_BALANCE):
        transactions.append(current)
    return transactions


def load_statement(pdf_path, password=None):
    """Load one PDF; try pdfplumber first, then text fallback. Returns list of dicts."""
    rows = extract_with_pdfplumber(pdf_path, password)
    if not rows:
        rows = extract_with_text(pdf_path, password)
    # Merge continuation rows (same date+balance can appear from table split)
    return _dedupe_and_clean(rows)


def _dedupe_and_clean(rows):
    """Remove duplicates and ensure numeric/date fields are consistent."""
    seen = set()
    out = []
    for r in rows:
        key = (r.get(COL_DATE), r.get(COL_NARRATION)[:80], r.get(COL_BALANCE))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def to_dataframe(transactions):
    """Convert list of transaction dicts to DataFrame with proper types."""
    if not transactions:
        return pd.DataFrame(columns=[COL_DATE, COL_NARRATION, COL_REF, COL_VALUE_DT, COL_WITHDRAWN, COL_DEPOSIT, COL_BALANCE])
    df = pd.DataFrame(transactions)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], format="%d/%m/%y", errors="coerce")
    df[COL_VALUE_DT] = pd.to_datetime(df[COL_VALUE_DT], format="%d/%m/%y", errors="coerce")
    df[COL_WITHDRAWN] = df[COL_WITHDRAWN].apply(lambda x: _clean_amount(x) if isinstance(x, str) else (float(x) if pd.notna(x) else 0.0))
    df[COL_DEPOSIT] = df[COL_DEPOSIT].apply(lambda x: _clean_amount(x) if isinstance(x, str) else (float(x) if pd.notna(x) else 0.0))
    df[COL_BALANCE] = df[COL_BALANCE].apply(lambda x: _clean_amount(x) if isinstance(x, str) else (float(x) if pd.notna(x) else 0.0))
    df = df.sort_values(COL_DATE).reset_index(drop=True)
    return df


def export_csv(df, path):
    """Export DataFrame to CSV."""
    df_export = df.copy()
    df_export[COL_DATE] = df_export[COL_DATE].dt.strftime("%d/%m/%Y")
    df_export[COL_VALUE_DT] = df_export[COL_VALUE_DT].dt.strftime("%d/%m/%Y")
    df_export.to_csv(path, index=False, encoding="utf-8")
    return path


def export_xlsx(df, path):
    """Export DataFrame to Excel."""
    df_export = df.copy()
    df_export[COL_DATE] = df_export[COL_DATE].dt.strftime("%d/%m/%Y")
    df_export[COL_VALUE_DT] = df_export[COL_VALUE_DT].dt.strftime("%d/%m/%Y")
    df_export.to_excel(path, index=False, engine="openpyxl")
    return path


def export_json(df, path):
    """Export DataFrame to JSON (list of objects)."""
    df_export = df.copy()
    df_export[COL_DATE] = df_export[COL_DATE].dt.strftime("%Y-%m-%d")
    df_export[COL_VALUE_DT] = df_export[COL_VALUE_DT].dt.strftime("%Y-%m-%d")
    df_export[COL_WITHDRAWN] = df_export[COL_WITHDRAWN].round(2)
    df_export[COL_DEPOSIT] = df_export[COL_DEPOSIT].round(2)
    df_export[COL_BALANCE] = df_export[COL_BALANCE].round(2)
    records = df_export.to_dict(orient="records")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    return path


def export_ofx(df, path, account_id="", bank_id="HDFC0000061", org="HDFC Bank"):
    """Export to OFX 2.0 (SGML-style) bank statement."""
    # OFX header
    lines = [
        "OFXHEADER:100",
        "DATA:OFXSGML",
        "VERSION:200",
        "SECURITY:NONE",
        "ENCODING:UTF-8",
        "CHARSET:ISO-8859-1",
        "COMPRESSION:NONE",
        "OLDFILEUID:NONE",
        "NEWFILEUID:NONE",
        "",
        "<OFX>",
        "  <SIGNONMSGSRSV1>",
        "    <SONRS>",
        "      <STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>",
        "      <DTSERVER>" + datetime.now().strftime("%Y%m%d%H%M%S") + "</DTSERVER>",
        "      <LANGUAGE>ENG</LANGUAGE>",
        "    </SONRS>",
        "  </SIGNONMSGSRSV1>",
        "  <BANKMSGSRSV1>",
        "    <STMTTRNRS>",
        "      <TRNUID>1</TRNUID>",
        "      <STATUS><CODE>0</CODE><SEVERITY>INFO</SEVERITY></STATUS>",
        "      <STMTRS>",
        "        <CURDEF>INR</CURDEF>",
        "        <BANKACCTFROM>",
        "          <BANKID>" + bank_id + "</BANKID>",
        "          <ACCTID>" + (account_id or "Account") + "</ACCTID>",
        "          <ACCTTYPE>CHECKING</ACCTTYPE>",
        "        </BANKACCTFROM>",
        "        <BANKTRANLIST>",
    ]
    for idx, row in df.iterrows():
        dt = row[COL_DATE].strftime("%Y%m%d")
        name = (row[COL_NARRATION] or "")[:255].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        fitid = f"{dt}{idx:06d}"
        if row[COL_WITHDRAWN] and float(row[COL_WITHDRAWN]) > 0:
            trntype = "DEBIT"
            trnamt = -float(row[COL_WITHDRAWN])
        else:
            trntype = "CREDIT"
            trnamt = float(row[COL_DEPOSIT]) if row[COL_DEPOSIT] else 0
        if trnamt == 0:
            continue
        lines.append("          <STMTTRN>")
        lines.append("            <TRNTYPE>" + trntype + "</TRNTYPE>")
        lines.append("            <DTPOSTED>" + dt + "</DTPOSTED>")
        lines.append("            <TRNAMT>" + f"{trnamt:.2f}" + "</TRNAMT>")
        lines.append("            <FITID>" + fitid + "</FITID>")
        lines.append("            <NAME>" + name + "</NAME>")
        lines.append("          </STMTTRN>")
    lines.extend([
        "        </BANKTRANLIST>",
        "      </STMTRS>",
        "    </STMTTRNRS>",
        "  </BANKMSGSRSV1>",
        "</OFX>",
    ])
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def parse_pdfs(pdf_paths, password=None):
    """Parse one or more PDFs and return combined DataFrame."""
    all_txns = []
    for path in pdf_paths:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            raise FileNotFoundError(f"PDF not found: {path}")
        rows = load_statement(path, password)
        all_txns.extend(rows)
    return to_dataframe(all_txns)


def main():
    parser = argparse.ArgumentParser(
        description="Parse HDFC Bank statement PDF(s) to CSV, XLSX, OFX, or JSON."
    )
    parser.add_argument(
        "pdf",
        nargs="+",
        help="Path(s) to PDF statement file(s)",
    )
    parser.add_argument(
        "-p", "--password",
        default=None,
        help="PDF password if protected",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default=".",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["csv", "xlsx", "json", "ofx", "all"],
        default="all",
        help="Output format (default: all)",
    )
    parser.add_argument(
        "--base-name",
        default="statement",
        help="Base name for output files (default: statement)",
    )
    args = parser.parse_args()

    if not HAS_PYPDF2 and not HAS_PDFPLUMBER:
        print("Error: Install PyPDF2 or pdfplumber. Run: pip install PyPDF2 pdfplumber openpyxl pandas")
        return 1

    os.makedirs(args.output_dir, exist_ok=True)
    base = os.path.join(args.output_dir, args.base_name)

    print("Parsing PDF(s)...")
    try:
        df = parse_pdfs(args.pdf, args.password)
    except FileNotFoundError as e:
        print(e)
        return 1
    except Exception as e:
        print("Parse error:", e)
        return 1

    if df.empty:
        print("No transactions found. Check PDF format.")
        if not args.password:
            print("If your PDF is password-protected, use: -p YOUR_PASSWORD")
        return 1

    print(f"Found {len(df)} transactions.")

    formats_to_do = ["csv", "xlsx", "json", "ofx"] if args.format == "all" else [args.format]
    for fmt in formats_to_do:
        if fmt == "csv":
            path = export_csv(df, base + ".csv")
        elif fmt == "xlsx":
            path = export_xlsx(df, base + ".xlsx")
        elif fmt == "json":
            path = export_json(df, base + ".json")
        else:
            path = export_ofx(df, base + ".ofx")
        print(f"  Exported: {path}")

    return 0


if __name__ == "__main__":
    exit(main())
