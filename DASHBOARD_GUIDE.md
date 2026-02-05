# 📊 Interactive Dashboard Guide

## What is This?

An interactive web-based dashboard that lets you **slice, dice, filter, and explore** your financial data in real-time. No coding required!

## 🚀 How to Launch

### Option 1: Simple Command
```bash
cd "/Users/mayankkaura/Account_statement analyzer"
streamlit run dashboard.py
```

### Option 2: If streamlit command not found
```bash
cd "/Users/mayankkaura/Account_statement analyzer"
python3 -m streamlit run dashboard.py
```

The dashboard will automatically open in your default web browser at `http://localhost:8501`

---

## 🎯 Features Overview

### 1. **Dynamic Filters** (Sidebar)
Filter your data in real-time:
- **Date Range Picker**: Select any date range to focus on specific periods
- **Transaction Type**: View only income, only expenses, or both
- **Amount Range Slider**: Filter transactions by amount (e.g., show only large transactions)

### 2. **Six Interactive Tabs**

#### Tab 1: 📈 Overview
- **Top Metrics**: Total income, expenses, profit/loss, burn rate
- **Monthly Comparison**: Side-by-side bar charts of income vs expenses
- **Net Cash Flow**: Visual representation of profitable/unprofitable months
- **Transaction Distribution**: Histograms showing how income and expenses are distributed

#### Tab 2: 💰 Income Analysis
- **Income Statistics**: Transaction count, average, median
- **Top Income Sources**: Slider to show top 5-50 transactions
- **Day of Week Analysis**: Which days bring in most income
- **Daily Income Trend**: Line chart showing income over time
- **Searchable data table**

#### Tab 3: 💸 Expense Analysis
- **Expense Statistics**: Transaction count, average, median
- **Category Breakdown**: Interactive pie chart and bar chart
- **Top Expenses**: View largest expenditures with slider control
- **Weekday Patterns**: See which days have highest expenses
- **Daily Expense Trend**: Track spending over time

#### Tab 4: 👥 Customer Analysis
- **Customer Metrics**: Total, repeat, and one-time customers
- **Filter Options**:
  - All Customers
  - Repeat Customers Only
  - One-time Customers Only
- **Sorting Options**:
  - By Total Revenue
  - By Transaction Count
  - By Name (alphabetical)
- **Dual Charts**: Revenue vs frequency comparison
- **Customer Details Table**: Complete breakdown with averages

#### Tab 5: 📅 Trends & Patterns
- **Balance Timeline**: Track account balance over time
- **Cumulative Flow**: See cumulative income vs expenses
- **Transaction Volume**: Daily transaction count over time
- **Heatmap**: Week vs Day of Week transaction patterns
- **Pattern Recognition**: Identify busy periods visually

#### Tab 6: 📊 Raw Data
- **Search Functionality**: Search transactions by description
- **Column Selector**: Choose which columns to display
- **Sortable Tables**: Click headers to sort
- **CSV Export**: Download filtered data for Excel/other tools
- **Real-time Filtering**: Search results update instantly

---

## 🎨 How to Use - Common Tasks

### Task 1: Analyze Last Month Only
1. Open dashboard
2. In sidebar, click "Select Date Range"
3. Choose start date and end date for last month
4. All tabs update automatically!

### Task 2: Find Largest Expenses in December
1. Set date range to December 2025
2. Go to "Expense Analysis" tab
3. Use slider to show top 20 expenses
4. Review the table

### Task 3: Identify Best Customers
1. Go to "Customer Analysis" tab
2. Select "Repeat Customers Only"
3. Sort by "Total Revenue"
4. Adjust slider to show top 10-20
5. Review both revenue and frequency charts

### Task 4: Check Weekend vs Weekday Performance
1. Go to "Trends & Patterns" tab
2. View "Transaction Heatmap"
3. Or check "Overview" tab for day-of-week bars

### Task 5: Find All Transactions Above ₹50,000
1. In sidebar, use "Amount Range" slider
2. Set minimum to 50,000
3. Go to "Raw Data" tab
4. Click "Download as CSV" to export

### Task 6: Track Specific Category Expenses
1. Go to "Expense Analysis" tab
2. View pie chart - click on category
3. Use search in "Raw Data" tab (e.g., search "bank" for bank charges)

### Task 7: Compare Two Time Periods
1. First, note down metrics for Period 1 (e.g., Jan-Mar)
2. Change date range to Period 2 (e.g., Apr-Jun)
3. Compare the top metrics and charts
4. Screenshots can help with side-by-side comparison

---

## 🔍 Interactive Features

### Hovering
- **Hover over charts** to see exact values
- **Bar charts**: Shows amount and category
- **Line charts**: Shows date and value
- **Pie charts**: Shows category and percentage

### Clicking
- Some charts are zoomable - click and drag to zoom
- Double-click to reset zoom
- Click legend items to hide/show data series

### Filtering Chain
Filters work together:
1. Set date range → filters data
2. Set amount range → filters further
3. All tabs show only matching data

### Real-time Updates
- Every filter change updates ALL tabs instantly
- Top metrics recalculate automatically
- Charts redraw with new data

---

## 💡 Pro Tips

### 1. Multiple Browser Tabs
Open the dashboard URL in multiple browser tabs to compare different filters side-by-side.

### 2. Bookmark Useful Views
After setting filters, bookmark the page to return to that view later.

### 3. Export Data for Excel
Use "Raw Data" tab → Download CSV → Open in Excel for pivot tables and advanced analysis.

### 4. Find Outliers
Use amount slider to focus on either:
- Very small transactions (might be errors)
- Very large transactions (need verification)

### 5. Seasonal Analysis
Compare same periods across months:
- Set date to first week of each month
- Note patterns
- Adjust business strategies accordingly

### 6. Customer Segmentation
In Customer Analysis:
- Filter repeat customers
- Sort by revenue
- Identify top 20% (Pareto principle)
- Focus retention efforts here

### 7. Expense Control
In Expense Analysis:
- Check category breakdown
- Focus on largest categories
- Use filters to drill down
- Find optimization opportunities

---

## 🎯 Power User Techniques

### Technique 1: Cohort Analysis
1. Filter by date range (e.g., Q1)
2. Note customer count in Customer Analysis
3. Change to Q2, Q3, Q4
4. Track how many customers remain active

### Technique 2: Margin Analysis
1. Set date range to one month
2. Note income and expenses
3. Calculate: (Income - Expenses) / Income = Margin
4. Repeat for each month
5. Identify best/worst performing months

### Technique 3: Category Deep Dive
1. Go to Expense Analysis
2. Note "Other" category percentage
3. Go to Raw Data tab
4. Search for common terms in "Other" transactions
5. Identify patterns to create new categories

### Technique 4: Customer Lifetime Value
1. Go to Customer Analysis
2. Filter "Repeat Customers Only"
3. Sort by "Transaction Count"
4. Check "Total Amount" for each
5. Calculate: CLV = Total / Transaction Count

### Technique 5: Cash Flow Forecasting
1. Go to Trends & Patterns
2. Check daily income trend
3. Check daily expense trend
4. Identify patterns (weekly/monthly cycles)
5. Extrapolate for future planning

---

## 📊 Dashboard Metrics Explained

### Burn Rate
- **What**: Percentage of income spent on expenses
- **Formula**: (Total Expenses / Total Income) × 100
- **Good**: <85% (15%+ profit margin)
- **Okay**: 85-95% (5-15% profit)
- **Warning**: 95-100% (0-5% profit)
- **Critical**: >100% (losing money)

### Profit Margin
- **What**: Percentage of income remaining after expenses
- **Formula**: ((Income - Expenses) / Income) × 100
- **Target**: 15%+ is healthy for most businesses

### Transaction Volume
- **What**: Number of transactions in a period
- **Use**: Track business activity level
- **Compare**: Higher volume usually means more activity

---

## 🚨 Troubleshooting

### Dashboard won't load
```bash
# Check if streamlit is installed
python3 -m pip show streamlit

# Reinstall if needed
python3 -m pip install --user streamlit
```

### "Module not found" error
```bash
# Install all dependencies
cd "/Users/mayankkaura/Account_statement analyzer"
python3 -m pip install --user -r requirements.txt
```

### Dashboard is slow
- Try filtering to a smaller date range
- Reduce number of displayed items using sliders
- Close other heavy applications

### Charts not displaying
- Check internet connection (charts use web fonts)
- Try refreshing the browser (Cmd+R or Ctrl+R)
- Clear browser cache

### Data doesn't match PDF
- Verify PDF password is correct
- Check if PDFs contain full year data
- Review parser logic in analyzer.py

---

## 🔄 Refreshing Data

The dashboard caches data for speed. If you:
- Update the PDF files
- Change analyzer.py
- Want fresh calculations

**Click "Clear Cache" in top-right menu → "Clear cache" → Reload**

Or restart the dashboard:
1. Press Ctrl+C in terminal to stop
2. Run `streamlit run dashboard.py` again

---

## 📱 Mobile Access

Access the dashboard from your phone/tablet:
1. Find your computer's IP address
2. On mobile browser, go to: `http://[YOUR-IP]:8501`
3. Use same filtering and viewing features

---

## 💾 Saving Your Analysis

### Method 1: Screenshots
- Use your OS screenshot tool (Cmd+Shift+4 on Mac)
- Capture charts and metrics

### Method 2: CSV Export
- Go to Raw Data tab
- Set desired filters
- Click "Download as CSV"
- Open in Excel/Numbers

### Method 3: Browser Print
- File → Print
- Save as PDF
- Includes all visible content

---

## 🎓 Learning Resources

### Understanding Your Business Better
1. **Start with Overview tab** - Get the big picture
2. **Move to Expenses** - Where is money going?
3. **Check Customers** - Who's bringing in revenue?
4. **Analyze Trends** - When are you busiest?
5. **Drill into Raw Data** - Specific transactions

### Questions to Ask
- Which month was most profitable? (Overview)
- What's my biggest expense category? (Expense Analysis)
- Who are my top 10 customers? (Customer Analysis)
- Are weekends profitable? (Trends)
- Which transactions were over ₹50k? (Raw Data with filter)

---

## 🚀 Next Steps

After mastering the dashboard:
1. **Regular Reviews**: Check weekly for trends
2. **Share Insights**: Export data for stakeholders
3. **Track Changes**: Compare month-over-month
4. **Set Goals**: Use data to set improvement targets
5. **Automate**: Schedule regular analysis runs

---

## ⚡ Keyboard Shortcuts

- **R**: Rerun the app
- **Cmd/Ctrl + R**: Reload page
- **Cmd/Ctrl + F**: Search on page
- **Tab**: Navigate between filters
- **Cmd/Ctrl + Plus/Minus**: Zoom in/out

---

**Enjoy exploring your financial data! 📊**

*For questions or issues, refer to README.md or analyzer documentation.*
