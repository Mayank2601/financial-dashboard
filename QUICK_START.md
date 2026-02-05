# Quick Start Guide

## How to Use This Analyzer

### Running the Analysis

1. **First Time Setup** (already done):
```bash
cd "/Users/mayankkaura/Account_statement analyzer"
pip3 install -r requirements.txt
```

2. **Run the Analysis**:
```bash
python3 analyzer.py
```

### View Results

#### Interactive Visualizations (Open in Browser)
- `monthly_analysis.html` - Monthly income vs expenses with net cash flow
- `cost_heads.html` - Expense distribution pie charts
- `customer_analysis.html` - Top customers by revenue and frequency
- `advanced_analytics.html` - Balance trends, daily volumes, weekday patterns

#### Reports
- `ANALYSIS_SUMMARY.md` - Executive summary with key insights and recommendations
- `financial_report.xlsx` - Complete Excel workbook with all data

### Analyzing New Statements

To analyze different PDF files:

1. Open `analyzer.py` in a text editor
2. Find the `main()` function at the bottom
3. Update the `PDF_PATHS` list with your new PDF file paths
4. Update the `PASSWORD` if different
5. Save and run: `python3 analyzer.py`

Example:
```python
PDF_PATHS = [
    "/path/to/your/statement1.pdf",
    "/path/to/your/statement2.pdf"
]
PASSWORD = "your_password"
```

### Understanding the Analysis

#### Key Metrics Explained

- **Burn Rate**: Percentage of income spent on expenses. Lower is better.
  - 100% = Breaking even
  - <100% = Making profit
  - >100% = Losing money

- **Net Profit**: Total income minus total expenses for the entire period

- **Profitability Rate**: Percentage of months that were profitable

- **Repeat Customers**: Customers with more than one transaction

#### Cost Heads Categories

The analyzer automatically categorizes expenses:
- **Utilities**: Electricity, water, gas, internet, phone
- **Salary & Wages**: Employee payments
- **Rent**: Lease payments
- **Bank Charges**: Fees and charges
- **Transportation**: Fuel, travel expenses
- **Marketing**: Advertising, promotions
- **Taxes**: GST, TDS, etc.
- **Other**: Uncategorized expenses

### Customization

#### Add New Expense Categories

Edit the `categorize_expenses()` method in `analyzer.py`:

```python
categories = {
    'Your Category Name': ['keyword1', 'keyword2', 'keyword3'],
    # ... existing categories
}
```

#### Export Additional Data

The Excel file contains multiple sheets:
- **Summary**: Key metrics
- **All Transactions**: Every transaction with date, description, amounts
- **Customers**: Customer analysis
- **Cost Heads**: Expense breakdown
- **Monthly Summary**: Month-by-month totals

### Troubleshooting

**Problem**: No transactions found
- Check if PDF password is correct
- Verify PDF file paths are correct
- The parser is designed for HDFC Bank statements

**Problem**: Wrong credit/debit classification
- Review the `parse_transactions()` method
- Bank statement format may have changed

**Problem**: Customers not properly identified
- Review the `identify_customers()` method
- Adjust the regex patterns for your transaction format

### Tips for Better Analysis

1. **Run monthly**: Regular analysis helps track trends
2. **Compare periods**: Run for different date ranges to see progress
3. **Focus on categories**: Use cost heads to identify major expense areas
4. **Track repeat customers**: Building loyalty increases predictable income
5. **Monitor burn rate**: Aim to reduce it over time
6. **Review "Other" category**: Categorize these for better insights

### Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Review the ANALYSIS_SUMMARY.md for insights
3. Examine the generated visualizations
4. Check the Excel file for raw data

---

**Note**: This analyzer is customized for HDFC Bank statement format. Other bank formats may require modifications to the parsing logic.
