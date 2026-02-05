import PyPDF2
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from collections import defaultdict
import os
from tabulate import tabulate

class AccountStatementAnalyzer:
    def __init__(self, pdf_paths, password):
        """
        Initialize the analyzer with PDF paths and password
        
        Args:
            pdf_paths: List of PDF file paths
            password: Password for the PDFs
        """
        self.pdf_paths = pdf_paths if isinstance(pdf_paths, list) else [pdf_paths]
        self.password = password
        self.transactions = []
        self.df = None
        
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a password-protected PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Decrypt the PDF
                if pdf_reader.is_encrypted:
                    pdf_reader.decrypt(self.password)
                
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                return text
        except Exception as e:
            print(f"Error reading {pdf_path}: {e}")
            return ""
    
    def parse_transactions(self, text):
        """Parse transactions from HDFC bank statement format"""
        lines = text.split('\n')
        transactions = []
        
        # HDFC format: Date Narration Chq/Ref Value_Dt Withdrawal Deposit Closing_Balance
        # Date pattern for dd/mm/yy
        date_pattern = r'^(\d{2}/\d{2}/\d{2})\s+'
        # Amount pattern (handles comma-separated numbers)
        amount_pattern = r'[\d,]+\.\d{2}'
        
        current_transaction = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Skip header lines
            if 'Date' in line and 'Narration' in line and 'Withdrawal' in line:
                continue
            if 'Statement of account' in line or 'Account Branch' in line:
                continue
            if line.startswith('Page No'):
                continue
            
            # Check if line starts with a date
            date_match = re.match(date_pattern, line)
            
            if date_match:
                # Save previous transaction if exists
                if current_transaction:
                    transactions.append(current_transaction)
                
                # Start new transaction
                date_str = date_match.group(1)
                
                try:
                    trans_date = datetime.strptime(date_str, '%d/%m/%y')
                    # Convert to full year format
                    if trans_date.year < 2000:
                        trans_date = trans_date.replace(year=trans_date.year + 100)
                    
                    # Find all amounts in the line
                    amounts = re.findall(amount_pattern, line)
                    
                    if len(amounts) >= 2:
                        # Last amount is always the closing balance
                        balance = float(amounts[-1].replace(',', ''))
                        
                        # Get description (everything between date and amounts)
                        # Remove date
                        desc_line = line[len(date_match.group(0)):].strip()
                        # Remove all amounts from the end
                        for amt in reversed(amounts):
                            last_pos = desc_line.rfind(amt)
                            if last_pos != -1:
                                desc_line = desc_line[:last_pos].strip()
                        
                        description = desc_line
                        
                        # Determine if debit or credit based on number of amounts
                        # If we have 2 amounts: amount and balance
                        # If we have 3 amounts: might be withdrawal, deposit, balance
                        
                        debit = 0
                        credit = 0
                        
                        if len(amounts) == 2:
                            # amount and balance
                            transaction_amt = float(amounts[0].replace(',', ''))
                            # We'll determine debit/credit by comparing with next balance
                            # For now, assume it's the transaction amount
                            current_transaction = {
                                'date': trans_date,
                                'description': description,
                                'debit': 0,
                                'credit': 0,
                                'balance': balance,
                                'transaction_amt': transaction_amt,
                                'raw_line': line
                            }
                        elif len(amounts) >= 3:
                            # withdrawal, deposit, balance format
                            withdrawal = float(amounts[-2].replace(',', ''))
                            deposit = float(amounts[-3].replace(',', '')) if len(amounts) > 2 else 0
                            
                            current_transaction = {
                                'date': trans_date,
                                'description': description,
                                'debit': withdrawal,
                                'credit': deposit,
                                'balance': balance,
                                'raw_line': line
                            }
                    else:
                        # No amounts found, might be continuation of previous description
                        if current_transaction and 'description' in current_transaction:
                            current_transaction['description'] += ' ' + line
                        current_transaction = None
                        
                except Exception as e:
                    current_transaction = None
                    continue
            else:
                # Continuation line - append to current transaction description
                if current_transaction and 'description' in current_transaction:
                    # Check if this line has amounts
                    amounts = re.findall(amount_pattern, line)
                    if amounts and len(amounts) >= 2:
                        # This might have the actual withdrawal/deposit amounts
                        balance = float(amounts[-1].replace(',', ''))
                        current_transaction['balance'] = balance
                        
                        if len(amounts) == 2:
                            transaction_amt = float(amounts[0].replace(',', ''))
                            current_transaction['transaction_amt'] = transaction_amt
                        elif len(amounts) >= 3:
                            withdrawal = float(amounts[-2].replace(',', ''))
                            deposit = float(amounts[-3].replace(',', '')) if len(amounts) > 2 else 0
                            current_transaction['debit'] = withdrawal
                            current_transaction['credit'] = deposit
                    else:
                        # Just description continuation
                        current_transaction['description'] += ' ' + line
        
        # Don't forget the last transaction
        if current_transaction:
            transactions.append(current_transaction)
        
        # Second pass: determine debit/credit based on balance changes
        processed_transactions = []
        prev_balance = None
        
        for trans in transactions:
            if 'transaction_amt' in trans and trans['debit'] == 0 and trans['credit'] == 0:
                # Determine based on balance change
                if prev_balance is not None:
                    balance_change = trans['balance'] - prev_balance
                    if balance_change < 0:
                        # Balance decreased = debit/withdrawal
                        trans['debit'] = abs(balance_change)
                    else:
                        # Balance increased = credit/deposit
                        trans['credit'] = abs(balance_change)
                else:
                    # First transaction - assume based on transaction amount
                    trans['debit'] = trans['transaction_amt']
                
                del trans['transaction_amt']
            
            prev_balance = trans['balance']
            processed_transactions.append(trans)
        
        return processed_transactions
    
    def load_data(self):
        """Load and parse all PDFs"""
        all_transactions = []
        
        for pdf_path in self.pdf_paths:
            print(f"Processing {os.path.basename(pdf_path)}...")
            text = self.extract_text_from_pdf(pdf_path)
            transactions = self.parse_transactions(text)
            all_transactions.extend(transactions)
            print(f"  Found {len(transactions)} transactions")
        
        if not all_transactions:
            print("No transactions found. The PDF format might need custom parsing.")
            print("Please check the raw text output below:")
            print("\n" + "="*80)
            for pdf_path in self.pdf_paths:
                text = self.extract_text_from_pdf(pdf_path)
                print(text[:2000])  # Print first 2000 chars
                print("\n" + "="*80)
            return False
        
        self.df = pd.DataFrame(all_transactions)
        self.df = self.df.sort_values('date').reset_index(drop=True)
        
        # Add month and year columns
        self.df['month'] = self.df['date'].dt.to_period('M')
        self.df['year'] = self.df['date'].dt.year
        self.df['month_name'] = self.df['date'].dt.strftime('%B %Y')
        
        print(f"\nTotal transactions loaded: {len(self.df)}")
        return True
    
    def identify_customers(self):
        """Identify unique customers from credit transactions"""
        # Customers are typically those who make payments (credits)
        credit_transactions = self.df[self.df['credit'] > 0].copy()
        
        if credit_transactions.empty:
            return {}
        
        # Extract potential customer names from descriptions
        customers = defaultdict(lambda: {'count': 0, 'total_amount': 0, 'transactions': []})
        
        for idx, row in credit_transactions.iterrows():
            desc = row['description']
            
            # For UPI transactions, extract the actual name
            # Format: UPI-NAME-phoneorUPI@bank-BANK-refnumber-description
            customer_name = desc
            
            if 'UPI-' in desc:
                # Extract name after UPI-
                match = re.search(r'UPI-([A-Za-z\s]+?)[-\d@]', desc)
                if match:
                    customer_name = match.group(1).strip()
                else:
                    # Try alternate format
                    parts = desc.split('-')
                    if len(parts) > 1:
                        customer_name = parts[1].strip()
            elif 'NEFT' in desc or 'IMPS' in desc or 'RTGS' in desc:
                # Extract name from bank transfer
                match = re.search(r'(?:NEFT|IMPS|RTGS)\s+CR-[A-Z0-9]+-([A-Za-z\s]+)', desc, re.IGNORECASE)
                if match:
                    customer_name = match.group(1).strip()
            else:
                # Try to extract a meaningful name
                # Remove common patterns
                cleaned = re.sub(r'\d{10,}', '', desc)  # Remove long numbers
                cleaned = re.sub(r'[A-Z0-9]{10,}', '', cleaned)  # Remove long alphanumeric codes
                cleaned = re.sub(r'@\w+', '', cleaned)  # Remove email patterns
                customer_name = cleaned.strip()
            
            # Clean up the name
            customer_name = re.sub(r'\s+', ' ', customer_name).strip()
            customer_name = customer_name[:50]  # Limit length
            
            if customer_name and len(customer_name) > 2:
                customers[customer_name]['count'] += 1
                customers[customer_name]['total_amount'] += row['credit']
                customers[customer_name]['transactions'].append(row['date'])
        
        return dict(customers)
    
    def categorize_expenses(self):
        """Categorize expenses into cost heads"""
        # Debit transactions are expenses
        expense_transactions = self.df[self.df['debit'] > 0].copy()
        
        if expense_transactions.empty:
            return {}
        
        # Define category keywords
        categories = {
            'Salary & Wages': ['salary', 'wage', 'payroll', 'employee'],
            'Rent': ['rent', 'lease'],
            'Utilities': ['electric', 'water', 'gas', 'internet', 'phone', 'utility'],
            'Supplies': ['supply', 'supplies', 'stationery', 'office'],
            'Marketing': ['marketing', 'advertising', 'promotion', 'ad'],
            'Transportation': ['fuel', 'petrol', 'diesel', 'transport', 'travel', 'uber', 'ola'],
            'Professional Fees': ['legal', 'consultant', 'professional', 'accounting', 'audit'],
            'Bank Charges': ['charge', 'fee', 'bank'],
            'Insurance': ['insurance', 'premium'],
            'Maintenance': ['maintenance', 'repair', 'service'],
            'Taxes': ['tax', 'gst', 'tds'],
            'Purchases': ['purchase', 'buy', 'vendor', 'supplier'],
        }
        
        cost_heads = defaultdict(lambda: {'amount': 0, 'count': 0, 'transactions': []})
        
        for idx, row in expense_transactions.iterrows():
            desc = row['description'].lower()
            categorized = False
            
            for category, keywords in categories.items():
                if any(keyword in desc for keyword in keywords):
                    cost_heads[category]['amount'] += row['debit']
                    cost_heads[category]['count'] += 1
                    cost_heads[category]['transactions'].append({
                        'date': row['date'],
                        'description': row['description'],
                        'amount': row['debit']
                    })
                    categorized = True
                    break
            
            if not categorized:
                cost_heads['Other']['amount'] += row['debit']
                cost_heads['Other']['count'] += 1
                cost_heads['Other']['transactions'].append({
                    'date': row['date'],
                    'description': row['description'],
                    'amount': row['debit']
                })
        
        return dict(cost_heads)
    
    def generate_monthly_visualization(self):
        """Generate monthly credit and debit visualization"""
        monthly_summary = self.df.groupby('month_name').agg({
            'credit': 'sum',
            'debit': 'sum'
        }).reset_index()
        
        # Create figure with secondary y-axis
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Monthly Credits vs Debits', 'Net Cash Flow'),
            vertical_spacing=0.15
        )
        
        # Add credits and debits
        fig.add_trace(
            go.Bar(name='Credits (Income)', x=monthly_summary['month_name'], 
                   y=monthly_summary['credit'], marker_color='green'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(name='Debits (Expenses)', x=monthly_summary['month_name'], 
                   y=monthly_summary['debit'], marker_color='red'),
            row=1, col=1
        )
        
        # Add net cash flow
        monthly_summary['net'] = monthly_summary['credit'] - monthly_summary['debit']
        colors = ['green' if x >= 0 else 'red' for x in monthly_summary['net']]
        
        fig.add_trace(
            go.Bar(name='Net Cash Flow', x=monthly_summary['month_name'], 
                   y=monthly_summary['net'], marker_color=colors),
            row=2, col=1
        )
        
        fig.update_layout(height=800, showlegend=True, title_text="Account Statement Analysis")
        fig.write_html('monthly_analysis.html')
        print("\n✓ Monthly visualization saved to 'monthly_analysis.html'")
        
        return monthly_summary
    
    def generate_cost_heads_chart(self, cost_heads):
        """Generate pie chart for cost heads"""
        if not cost_heads:
            return
        
        categories = list(cost_heads.keys())
        amounts = [cost_heads[cat]['amount'] for cat in categories]
        
        # Create subplots
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Expense Distribution', 'Transaction Count by Category'),
            specs=[[{"type": "pie"}, {"type": "pie"}]]
        )
        
        fig.add_trace(
            go.Pie(labels=categories, values=amounts, hole=.3, name="Amount"),
            row=1, col=1
        )
        
        counts = [cost_heads[cat]['count'] for cat in categories]
        fig.add_trace(
            go.Pie(labels=categories, values=counts, hole=.3, name="Count"),
            row=1, col=2
        )
        
        fig.update_layout(title_text="Cost Heads Analysis", height=500)
        fig.write_html('cost_heads.html')
        print("✓ Cost heads visualization saved to 'cost_heads.html'")
    
    def generate_customer_analysis(self, customers):
        """Generate customer analysis visualization"""
        if not customers:
            return
        
        # Sort by total amount
        sorted_customers = sorted(customers.items(), key=lambda x: x[1]['total_amount'], reverse=True)
        top_customers = sorted_customers[:20]  # Top 20 customers
        
        names = [c[0][:30] for c in top_customers]  # Truncate long names
        amounts = [c[1]['total_amount'] for c in top_customers]
        counts = [c[1]['count'] for c in top_customers]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Top Customers by Revenue', 'Top Customers by Transaction Count'),
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        fig.add_trace(
            go.Bar(x=amounts, y=names, orientation='h', marker_color='lightblue'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=counts, y=names, orientation='h', marker_color='lightcoral'),
            row=1, col=2
        )
        
        fig.update_layout(height=600, showlegend=False, title_text="Customer Analysis")
        fig.write_html('customer_analysis.html')
        print("✓ Customer analysis saved to 'customer_analysis.html'")
    
    def generate_additional_charts(self):
        """Generate additional analytical charts"""
        # 1. Balance over time chart
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=(
                'Account Balance Over Time',
                'Daily Transaction Volume',
                'Transaction Pattern by Day of Week'
            ),
            vertical_spacing=0.12,
            specs=[[{"type": "scatter"}], [{"type": "bar"}], [{"type": "bar"}]]
        )
        
        # Balance over time
        balance_data = self.df.sort_values('date')
        fig.add_trace(
            go.Scatter(x=balance_data['date'], y=balance_data['balance'], 
                      mode='lines', name='Balance', line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # Daily transaction volume
        daily_data = self.df.groupby(self.df['date'].dt.date).agg({
            'credit': 'sum',
            'debit': 'sum'
        }).reset_index()
        daily_data.columns = ['date', 'credit', 'debit']
        
        fig.add_trace(
            go.Bar(x=daily_data['date'], y=daily_data['credit'], 
                  name='Daily Income', marker_color='green'),
            row=2, col=1
        )
        fig.add_trace(
            go.Bar(x=daily_data['date'], y=daily_data['debit'], 
                  name='Daily Expenses', marker_color='red'),
            row=2, col=1
        )
        
        # Weekday analysis
        self.df['weekday'] = self.df['date'].dt.day_name()
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_data = self.df.groupby('weekday').agg({
            'credit': 'sum',
            'debit': 'sum'
        }).reindex(weekday_order)
        
        fig.add_trace(
            go.Bar(x=weekday_order, y=weekday_data['credit'], 
                  name='Income by Weekday', marker_color='lightgreen'),
            row=3, col=1
        )
        fig.add_trace(
            go.Bar(x=weekday_order, y=weekday_data['debit'], 
                  name='Expenses by Weekday', marker_color='lightcoral'),
            row=3, col=1
        )
        
        fig.update_layout(height=1400, showlegend=True, title_text="Advanced Analytics Dashboard")
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_yaxes(title_text="Balance (₹)", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Amount (₹)", row=2, col=1)
        fig.update_xaxes(title_text="Day of Week", row=3, col=1)
        fig.update_yaxes(title_text="Amount (₹)", row=3, col=1)
        
        fig.write_html('advanced_analytics.html')
        print("✓ Advanced analytics saved to 'advanced_analytics.html'")
    
    def calculate_financial_metrics(self):
        """Calculate key financial metrics"""
        metrics = {}
        
        # Total income and expenses
        metrics['total_income'] = self.df['credit'].sum()
        metrics['total_expenses'] = self.df['debit'].sum()
        metrics['net_profit'] = metrics['total_income'] - metrics['total_expenses']
        
        # Average transaction values
        metrics['avg_income_per_transaction'] = self.df[self.df['credit'] > 0]['credit'].mean()
        metrics['avg_expense_per_transaction'] = self.df[self.df['debit'] > 0]['debit'].mean()
        
        # Monthly averages
        monthly_data = self.df.groupby('month').agg({
            'credit': 'sum',
            'debit': 'sum'
        })
        metrics['avg_monthly_income'] = monthly_data['credit'].mean()
        metrics['avg_monthly_expenses'] = monthly_data['debit'].mean()
        
        # Burn rate (how fast money is spent)
        if metrics['total_income'] > 0:
            metrics['burn_rate'] = (metrics['total_expenses'] / metrics['total_income']) * 100
        
        # Transaction counts
        metrics['total_transactions'] = len(self.df)
        metrics['income_transactions'] = len(self.df[self.df['credit'] > 0])
        metrics['expense_transactions'] = len(self.df[self.df['debit'] > 0])
        
        # Date range
        metrics['start_date'] = self.df['date'].min()
        metrics['end_date'] = self.df['date'].max()
        metrics['period_days'] = (metrics['end_date'] - metrics['start_date']).days
        
        # Largest transactions
        metrics['largest_income'] = self.df[self.df['credit'] > 0]['credit'].max() if metrics['income_transactions'] > 0 else 0
        metrics['largest_expense'] = self.df[self.df['debit'] > 0]['debit'].max() if metrics['expense_transactions'] > 0 else 0
        
        # Smallest transactions
        metrics['smallest_income'] = self.df[self.df['credit'] > 0]['credit'].min() if metrics['income_transactions'] > 0 else 0
        metrics['smallest_expense'] = self.df[self.df['debit'] > 0]['debit'].min() if metrics['expense_transactions'] > 0 else 0
        
        # Median values
        metrics['median_income'] = self.df[self.df['credit'] > 0]['credit'].median() if metrics['income_transactions'] > 0 else 0
        metrics['median_expense'] = self.df[self.df['debit'] > 0]['debit'].median() if metrics['expense_transactions'] > 0 else 0
        
        # Daily averages
        if metrics['period_days'] > 0:
            metrics['avg_daily_income'] = metrics['total_income'] / metrics['period_days']
            metrics['avg_daily_expenses'] = metrics['total_expenses'] / metrics['period_days']
        
        return metrics
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        # Generate all visualizations first
        print("\nGenerating visualizations...")
        monthly_summary = self.generate_monthly_visualization()
        
        customers = self.identify_customers()
        self.generate_customer_analysis(customers)
        
        cost_heads = self.categorize_expenses()
        self.generate_cost_heads_chart(cost_heads)
        
        self.generate_additional_charts()
        
        print("\n" + "="*80)
        print("ACCOUNT STATEMENT ANALYSIS REPORT")
        print("="*80)
        
        # Financial metrics
        metrics = self.calculate_financial_metrics()
        
        print("\n📊 FINANCIAL OVERVIEW")
        print("-" * 80)
        print(f"Analysis Period: {metrics['start_date'].strftime('%d %B %Y')} to {metrics['end_date'].strftime('%d %B %Y')} ({metrics['period_days']} days)")
        print(f"Total Income:    ₹{metrics['total_income']:,.2f}")
        print(f"Total Expenses:  ₹{metrics['total_expenses']:,.2f}")
        print(f"Net Profit:      ₹{metrics['net_profit']:,.2f}")
        print(f"Burn Rate:       {metrics.get('burn_rate', 0):.2f}%")
        
        print(f"\n📈 MONTHLY AVERAGES")
        print("-" * 80)
        print(f"Average Monthly Income:   ₹{metrics['avg_monthly_income']:,.2f}")
        print(f"Average Monthly Expenses: ₹{metrics['avg_monthly_expenses']:,.2f}")
        
        print(f"\n💳 TRANSACTION SUMMARY")
        print("-" * 80)
        print(f"Total Transactions:       {metrics['total_transactions']}")
        print(f"Income Transactions:      {metrics['income_transactions']}")
        print(f"Expense Transactions:     {metrics['expense_transactions']}")
        print(f"Avg Income per Trans:     ₹{metrics['avg_income_per_transaction']:,.2f}")
        print(f"Avg Expense per Trans:    ₹{metrics['avg_expense_per_transaction']:,.2f}")
        
        # Customer analysis
        print(f"\n👥 CUSTOMER ANALYSIS")
        print("-" * 80)
        print(f"Total Unique Customers:   {len(customers)}")
        
        # Identify repeat customers
        repeat_customers = {k: v for k, v in customers.items() if v['count'] > 1}
        print(f"Repeat Customers:         {len(repeat_customers)}")
        print(f"One-time Customers:       {len(customers) - len(repeat_customers)}")
        
        if repeat_customers:
            print(f"\nTop 10 Repeat Customers:")
            sorted_repeat = sorted(repeat_customers.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
            customer_table = []
            for name, data in sorted_repeat:
                customer_table.append([
                    name[:40],
                    data['count'],
                    f"₹{data['total_amount']:,.2f}",
                    f"₹{data['total_amount']/data['count']:,.2f}"
                ])
            print(tabulate(customer_table, 
                          headers=['Customer', 'Transactions', 'Total Amount', 'Avg Amount'],
                          tablefmt='grid'))
        
        # Cost heads analysis
        print(f"\n💰 EXPENSE BREAKDOWN BY COST HEADS")
        print("-" * 80)
        
        cost_table = []
        sorted_costs = sorted(cost_heads.items(), key=lambda x: x[1]['amount'], reverse=True)
        for category, data in sorted_costs:
            percentage = (data['amount'] / metrics['total_expenses']) * 100 if metrics['total_expenses'] > 0 else 0
            cost_table.append([
                category,
                data['count'],
                f"₹{data['amount']:,.2f}",
                f"{percentage:.1f}%"
            ])
        
        print(tabulate(cost_table, 
                      headers=['Category', 'Transactions', 'Total Amount', '% of Total'],
                      tablefmt='grid'))
        
        # Cash flow trends
        print(f"\n📉 CASH FLOW TREND")
        print("-" * 80)
        monthly_summary_data = self.df.groupby('month_name').agg({
            'credit': 'sum',
            'debit': 'sum'
        })
        monthly_summary_data['net'] = monthly_summary_data['credit'] - monthly_summary_data['debit']
        
        trend_table = []
        for month, row in monthly_summary_data.iterrows():
            trend_table.append([
                month,
                f"₹{row['credit']:,.2f}",
                f"₹{row['debit']:,.2f}",
                f"₹{row['net']:,.2f}",
                "✓" if row['net'] >= 0 else "✗"
            ])
        
        print(tabulate(trend_table,
                      headers=['Month', 'Income', 'Expenses', 'Net', 'Profitable'],
                      tablefmt='grid'))
        
        # Top expenses and income
        print(f"\n💸 TOP 10 EXPENSES")
        print("-" * 80)
        top_expenses = self.df[self.df['debit'] > 0].nlargest(10, 'debit')[['date', 'description', 'debit']]
        expense_table = []
        for idx, row in top_expenses.iterrows():
            expense_table.append([
                row['date'].strftime('%d %b %Y'),
                row['description'][:50],
                f"₹{row['debit']:,.2f}"
            ])
        print(tabulate(expense_table, headers=['Date', 'Description', 'Amount'], tablefmt='grid'))
        
        print(f"\n💰 TOP 10 INCOME SOURCES")
        print("-" * 80)
        top_income = self.df[self.df['credit'] > 0].nlargest(10, 'credit')[['date', 'description', 'credit']]
        income_table = []
        for idx, row in top_income.iterrows():
            income_table.append([
                row['date'].strftime('%d %b %Y'),
                row['description'][:50],
                f"₹{row['credit']:,.2f}"
            ])
        print(tabulate(income_table, headers=['Date', 'Description', 'Amount'], tablefmt='grid'))
        
        # Additional insights
        print(f"\n🔍 ADDITIONAL INSIGHTS")
        print("-" * 80)
        print(f"Largest Single Income:    ₹{metrics['largest_income']:,.2f}")
        print(f"Smallest Single Income:   ₹{metrics['smallest_income']:,.2f}")
        print(f"Median Income per Trans:  ₹{metrics['median_income']:,.2f}")
        print(f"")
        print(f"Largest Single Expense:   ₹{metrics['largest_expense']:,.2f}")
        print(f"Smallest Single Expense:  ₹{metrics['smallest_expense']:,.2f}")
        print(f"Median Expense per Trans: ₹{metrics['median_expense']:,.2f}")
        print(f"")
        print(f"Average Daily Income:     ₹{metrics['avg_daily_income']:,.2f}")
        print(f"Average Daily Expenses:   ₹{metrics['avg_daily_expenses']:,.2f}")
        
        # Profitable months count
        profitable_months = len(monthly_summary_data[monthly_summary_data['net'] > 0])
        total_months = len(monthly_summary_data)
        print(f"")
        print(f"Profitable Months:        {profitable_months} out of {total_months}")
        print(f"Profitability Rate:       {(profitable_months/total_months*100):.1f}%")
        
        # Export to Excel
        self.export_to_excel(metrics, customers, cost_heads, monthly_summary_data)
        
        # Weekday analysis
        print(f"\n📅 TRANSACTION PATTERN BY DAY OF WEEK")
        print("-" * 80)
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        if 'weekday' in self.df.columns:
            weekday_summary = self.df.groupby('weekday').agg({
                'credit': 'sum',
                'debit': 'sum',
                'description': 'count'
            }).reindex(weekday_order)
            weekday_summary.columns = ['Income', 'Expenses', 'Transaction Count']
            
            weekday_table = []
            for day, row in weekday_summary.iterrows():
                weekday_table.append([
                    day,
                    row['Transaction Count'],
                    f"₹{row['Income']:,.2f}",
                    f"₹{row['Expenses']:,.2f}",
                    f"₹{row['Income'] - row['Expenses']:,.2f}"
                ])
            print(tabulate(weekday_table, 
                          headers=['Day', 'Transactions', 'Income', 'Expenses', 'Net'],
                          tablefmt='grid'))
        
        print("\n" + "="*80)
        print("✓ Analysis complete! Check the generated files:")
        print("  - monthly_analysis.html (Interactive monthly charts)")
        print("  - cost_heads.html (Expense distribution)")
        print("  - customer_analysis.html (Customer insights)")
        print("  - advanced_analytics.html (Balance, daily trends, weekday patterns)")
        print("  - financial_report.xlsx (Detailed Excel report)")
        print("="*80 + "\n")
    
    def export_to_excel(self, metrics, customers, cost_heads, monthly_summary):
        """Export all data to Excel"""
        with pd.ExcelWriter('financial_report.xlsx', engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                'Metric': list(metrics.keys()),
                'Value': list(metrics.values())
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # All transactions
            self.df.to_excel(writer, sheet_name='All Transactions', index=False)
            
            # Customers
            customer_df = pd.DataFrame([
                {
                    'Customer': name,
                    'Transaction Count': data['count'],
                    'Total Amount': data['total_amount'],
                    'Average Amount': data['total_amount'] / data['count']
                }
                for name, data in customers.items()
            ]).sort_values('Total Amount', ascending=False)
            customer_df.to_excel(writer, sheet_name='Customers', index=False)
            
            # Cost heads
            cost_df = pd.DataFrame([
                {
                    'Category': cat,
                    'Transaction Count': data['count'],
                    'Total Amount': data['amount']
                }
                for cat, data in cost_heads.items()
            ]).sort_values('Total Amount', ascending=False)
            cost_df.to_excel(writer, sheet_name='Cost Heads', index=False)
            
            # Monthly summary
            monthly_summary.to_excel(writer, sheet_name='Monthly Summary')
        
        print("\n✓ Excel report saved to 'financial_report.xlsx'")


def main():
    # Configuration
    PDF_PATHS = [
        "/Users/mayankkaura/Library/Application Support/Cursor/User/workspaceStorage/d11d41837161e58e67c79c1f44c58a19/pdfs/dceaa5e7-fe3d-4dc6-8c79-e17a3c51e4ec/Acct Statement_9808_04022026_10.15.00.pdf",
        "/Users/mayankkaura/Library/Application Support/Cursor/User/workspaceStorage/d11d41837161e58e67c79c1f44c58a19/pdfs/7cff8d70-8cf6-4fc2-b524-ca547f57c549/Acct Statement_9808_04022026_10.16.16.pdf"
    ]
    PASSWORD = "219274449"
    
    # Initialize analyzer
    print("Initializing Account Statement Analyzer...")
    analyzer = AccountStatementAnalyzer(PDF_PATHS, PASSWORD)
    
    # Load data
    if not analyzer.load_data():
        print("\nNote: If no transactions were found, you may need to customize the parser")
        print("for your specific bank statement format.")
        return
    
    # Generate comprehensive report
    print("\nGenerating analysis and visualizations...")
    analyzer.generate_report()


if __name__ == "__main__":
    main()
