# 🚀 Quick Start - Interactive Dashboard

## Launch in 3 Easy Steps

### Option 1: Double-Click (Easiest!)
1. Find `launch_dashboard.sh` in this folder
2. Double-click it
3. Dashboard opens automatically in your browser!

### Option 2: Terminal Command
```bash
cd "/Users/mayankkaura/Account_statement analyzer"
python3 -m streamlit run dashboard.py
```

*(Use `python3 -m streamlit` — the plain `streamlit` command may not be on your PATH if you installed with pip --user.)*

### Option 3: Launcher Script
```bash
./launch_dashboard.sh
```

---

## What You Get

### 🎯 Interactive Features
- ✅ **Real-time Filtering**: Date range, amount range, transaction type
- ✅ **6 Analysis Tabs**: Overview, Income, Expenses, Customers, Trends, Raw Data
- ✅ **Interactive Charts**: Hover, zoom, click to explore
- ✅ **Customer Segmentation**: Filter by repeat vs one-time customers
- ✅ **Search & Export**: Find transactions and download as CSV
- ✅ **Dynamic Updates**: Change filters, see instant results

### 📊 Available Views

1. **Overview Tab**
   - Monthly income vs expenses comparison
   - Net cash flow visualization
   - Transaction distribution histograms

2. **Income Analysis Tab**
   - Top income sources (adjustable: show 5-50)
   - Day-of-week patterns
   - Daily income trends

3. **Expense Analysis Tab**
   - Category breakdown (pie charts)
   - Top expenses (adjustable: show 5-50)
   - Weekday spending patterns

4. **Customer Analysis Tab**
   - 256 unique customers
   - Filter: All / Repeat / One-time
   - Sort: By revenue / frequency / name
   - Visual comparison charts

5. **Trends & Patterns Tab**
   - Account balance timeline
   - Cumulative cash flow
   - Transaction volume over time
   - Heatmap: Week vs Day patterns

6. **Raw Data Tab**
   - Search transactions
   - Select columns
   - Download filtered data as CSV

---

## 🔍 Common Use Cases

### "Show me expenses over ₹50,000"
1. Sidebar → Amount Range → Set min to 50,000
2. Go to Expense Analysis tab
3. Review top expenses

### "Who are my best customers?"
1. Go to Customer Analysis tab
2. Filter: "Repeat Customers Only"
3. Sort by: "Total Revenue"
4. Adjust slider to show top 10-20

### "What happened in December?"
1. Sidebar → Date Range → Select Dec 1 to Dec 31
2. Check Overview tab for summary
3. Explore other tabs for details

### "Find all bank charge transactions"
1. Go to Raw Data tab
2. Search box: Type "bank" or "charge"
3. Download results as CSV

### "Compare weekdays vs weekends"
1. Overview tab → Check day-of-week charts
2. Or Trends tab → View heatmap

---

## 💡 Key Insights Available

From your data (full year):
- **Financial Health**: ₹21K profit on ₹83L revenue (0.26% margin)
- **Customer Base**: 256 unique, 95 repeat (37% retention)
- **Top Category**: Utilities at 54.1% of expenses
- **Warning**: Bank charges are 17% of expenses (₹14.1L annually!)
- **Best Month**: December (+₹31K profit)
- **Best Day**: Wednesday (+₹4.28L average)

---

## 🎨 Filter Combinations

### Example 1: Focus on Large Transactions
- Date Range: Full year
- Amount: ₹10,000 - ₹100,000
- Type: Both
- **Result**: See major revenue and expense sources

### Example 2: Analyze Specific Customer Segment
- Date Range: Q4 2025
- Customer Tab: Repeat Customers Only
- Sort: Transaction Count
- **Result**: Identify most loyal customers in recent quarter

### Example 3: Track Monthly Expenses
- Date Range: One month at a time
- Expense Tab: Review category breakdown
- **Result**: Month-over-month comparison

---

## 📱 Access from Other Devices

### Same Computer
- Open browser: `http://localhost:8501`

### Other Devices (Phone/Tablet)
1. Find your computer's IP address:
   ```bash
   # Mac/Linux
   ifconfig | grep "inet "
   ```
2. On other device, browser: `http://[YOUR-IP]:8501`

---

## 🛠️ Troubleshooting

### Dashboard won't start
```bash
# Reinstall dependencies
python3 -m pip install --user -r requirements.txt

# Try again
streamlit run dashboard.py
```

### Port already in use
```bash
# Use different port
streamlit run dashboard.py --server.port=8502
```

### Slow performance
- Filter to smaller date ranges
- Reduce number of displayed items with sliders
- Close other applications

### Data not loading
- Check PDF files are in correct location
- Verify password in dashboard.py (line 39)
- Check analyzer.py is working: `python3 analyzer.py`

---

## 🔄 Updating Data

If you have new statements:

1. Stop the dashboard (Ctrl+C in terminal)
2. Update PDF paths in `dashboard.py` (lines 36-40)
3. Restart dashboard
4. Or click "Clear Cache" in app menu (top-right ⋮)

---

## 💾 Saving Your Analysis

### Screenshots
- Mac: Cmd + Shift + 4
- Windows: Snipping Tool

### Export Data
- Go to Raw Data tab
- Apply filters
- Click "Download as CSV"

### Browser Print
- File → Print → Save as PDF

---

## 🎯 Pro Tips

1. **Multi-tab Comparison**: Open dashboard in 2+ browser tabs with different filters
2. **Bookmark Views**: Set filters → Bookmark page → Quick access later
3. **Excel Integration**: Export CSV → Open in Excel → Create pivot tables
4. **Regular Reviews**: Run weekly to spot trends early
5. **Mobile Access**: Check on-the-go from phone/tablet

---

## 📚 Learn More

- **DASHBOARD_GUIDE.md** - Complete feature documentation
- **ANALYSIS_SUMMARY.md** - Pre-generated insights
- **KEY_FINDINGS.txt** - Quick financial summary
- **QUICK_START.md** - Analyzer usage guide

---

## ⚡ Quick Commands Reference

```bash
# Start dashboard
streamlit run dashboard.py

# Start on different port
streamlit run dashboard.py --server.port=8502

# Start without auto-opening browser
streamlit run dashboard.py --server.headless=true

# Check if working
python3 -c "import streamlit; print('OK')"
```

---

## 🎊 You're All Set!

**Just run:** `streamlit run dashboard.py`

Or double-click: `launch_dashboard.sh`

The dashboard will open at `http://localhost:8501`

**Happy analyzing! 📊**
