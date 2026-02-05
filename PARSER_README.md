# HDFC Statement PDF Parser

Parse HDFC Bank account statement PDFs into readable formats: **CSV**, **XLSX**, **OFX**, or **JSON**.

## Columns Extracted

| Column           | Description                    |
|------------------|--------------------------------|
| Date             | Transaction date (DD/MM/YY)    |
| Narration        | Description / memo             |
| Chq./Ref.No.     | Cheque or reference number     |
| Value Dt         | Value date                     |
| Withdrawn Amt.   | Debit amount                   |
| Deposit Amt.     | Credit amount                  |
| Closing Balance  | Balance after transaction      |

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Required for parser: `PyPDF2` or `pdfplumber`, `pandas`, `openpyxl` (for XLSX).

### 2. Command line

```bash
# Parse one or more PDFs; export all formats (CSV, XLSX, JSON, OFX) to current directory
python statement_parser.py statement.pdf

# With password (required if PDF is protected)
python statement_parser.py statement.pdf --password "YOUR_PASSWORD"
python statement_parser.py statement.pdf -p "YOUR_PASSWORD"

# Choose output directory and base name
python statement_parser.py statement.pdf -o ./exports --base-name my_statement

# Export only specific format(s)
python statement_parser.py statement.pdf --format csv
python statement_parser.py statement.pdf --format xlsx
python statement_parser.py statement.pdf --format json
python statement_parser.py statement.pdf --format ofx
python statement_parser.py statement.pdf --format all   # default
```

### 3. Web UI (Streamlit)

```bash
streamlit run parser_app.py
```

Then upload PDF(s), enter password if needed, pick format(s), and download.

## Output Formats

- **CSV** – UTF-8, comma-separated; dates as DD/MM/YYYY.
- **XLSX** – Excel workbook; dates as DD/MM/YYYY.
- **JSON** – Array of transaction objects; dates as YYYY-MM-DD; amounts as numbers.
- **OFX** – OFX 2.0 bank statement (e.g. for import into accounting software).

## Multiple PDFs

You can pass several statement PDFs; transactions are merged, sorted by date, and exported once:

```bash
python statement_parser.py jan.pdf feb.pdf mar.pdf -o ./output --base-name Q1_statement
```

## Notes

- **Password:** HDFC statement PDFs are often password-protected. Use `-p YOUR_PASSWORD` (CLI) or enter the password in the app when prompted. Leave blank only if your PDF is not protected.
- The parser uses **pdfplumber** when available (better table detection), and falls back to **PyPDF2** text extraction.
- If no transactions are found, check that the PDF is not scanned (must be text-based) and that the password is correct.
- OFX export uses a generic account/bank id; you can edit `statement_parser.py` and the `export_ofx()` call to set your account id and bank id if needed.
