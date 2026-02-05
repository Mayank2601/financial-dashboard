# Account Statement Analyzer

A comprehensive Python tool to analyze business account statements from password-protected PDFs.

## Features

### 📊 Core Analysis
- **Monthly Credit/Debit Visualization**: Interactive charts showing income vs expenses over time
- **Unique Customer Identification**: Identifies and counts unique customers, including repeat customers
- **Cost Head Analysis**: Automatically categorizes expenses into different cost heads
- **Cash Flow Tracking**: Monitors net cash flow trends over time

### 💡 Additional Insights
- **Financial Metrics Dashboard**: Key metrics including total income, expenses, net profit, and burn rate
- **Customer Analytics**: 
  - Total unique customers
  - Repeat vs one-time customers
  - Top customers by revenue and transaction count
  - Average transaction value per customer
- **Expense Distribution**: 
  - Pie chart showing expense breakdown by category
  - Percentage distribution across cost heads
  - Transaction counts per category
- **Monthly Trends**: Month-by-month income, expenses, and profitability
- **Transaction Insights**: Average income/expense per transaction
- **Excel Export**: Complete data export with multiple sheets for detailed analysis

### 📈 Generated Reports

1. **monthly_analysis.html** - Interactive Plotly charts showing:
   - Monthly credits vs debits comparison
   - Net cash flow visualization
   
2. **cost_heads.html** - Pie chart of expense distribution by category

3. **customer_analysis.html** - Customer insights:
   - Top customers by revenue
   - Top customers by transaction count
   
4. **financial_report.xlsx** - Comprehensive Excel workbook with:
   - Financial summary metrics
   - All transactions data
   - Customer analysis
   - Cost heads breakdown
   - Monthly summary

5. **Console Report** - Detailed text report with tables showing all key metrics

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Update the PDF paths and password in `analyzer.py` if needed (currently set to your files)

2. Run the analyzer:
```bash
python analyzer.py
```

3. View the generated reports:
   - Open HTML files in your browser for interactive charts
   - Open the Excel file for detailed data analysis
   - Check the console output for the summary report

## Supported Cost Heads

The analyzer automatically categorizes expenses into:
- Salary & Wages
- Rent
- Utilities (electricity, water, internet, phone)
- Office Supplies
- Marketing & Advertising
- Transportation (fuel, travel)
- Professional Fees (legal, consulting, accounting)
- Bank Charges & Fees
- Insurance
- Maintenance & Repairs
- Taxes (GST, TDS)
- Purchases (vendor payments)
- Other (uncategorized)

## Customization

### Custom Bank Format
If your bank statement has a different format, you may need to customize the `parse_transactions()` method in `analyzer.py` to match your specific statement structure.

### Additional Categories
To add more expense categories, edit the `categories` dictionary in the `categorize_expenses()` method.

### Date Formats
The analyzer supports multiple date formats. If your format isn't recognized, add it to the `fmt` list in `parse_transactions()`.

## Troubleshooting

If no transactions are detected:
1. Check if the PDF password is correct
2. The parser will display raw text from the PDF - review this to understand the format
3. Customize the `parse_transactions()` method to match your bank's specific format

## Requirements

- Python 3.7+
- See `requirements.txt` for package dependencies

## Notes

- All amounts are assumed to be in INR (₹)
- The analyzer handles multiple PDF files
- Customer identification is based on transaction descriptions
- Repeat customers are those with more than one transaction
