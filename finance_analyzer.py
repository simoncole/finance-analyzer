import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import argparse
import os
warnings.filterwarnings('ignore')

def load_venmo_data(start_date=None, end_date=None):
    """Load and integrate Venmo transaction data"""
    venmo_file = "venmo_categorized_transactions.csv"
    
    if not os.path.exists(venmo_file):
        print(f"⚠️ Venmo data file not found: {venmo_file}")
        print("💡 Run 'python3 venmo_categorizer.py' first to categorize Venmo transactions")
        return pd.DataFrame()
    
    print(f"📂 Loading Venmo data from {venmo_file}...")
    venmo_df = pd.read_csv(venmo_file)
    
    # Convert to match Discover format
    venmo_df['Trans. Date'] = pd.to_datetime(venmo_df['Date'])
    venmo_df['Post Date'] = venmo_df['Trans. Date']  # Same as transaction date for Venmo
    venmo_df['Enhanced_Category'] = venmo_df['Category']
    venmo_df['Source'] = 'Venmo'
    
    # CRITICAL FIX: Normalize sign convention to match Discover
    # Discover: Positive = Expense, Negative = Income
    # Venmo: Positive = Income, Negative = Expense  
    # Solution: Flip Venmo signs to match Discover convention
    venmo_df['Amount'] = -venmo_df['Amount']  # Flip signs
    print(f"🔄 Normalized Venmo sign convention to match Discover")
    
    # Apply date filtering if specified
    if start_date or end_date:
        original_count = len(venmo_df)
        if start_date:
            start_date_dt = pd.to_datetime(start_date)
            venmo_df = venmo_df[venmo_df['Trans. Date'] >= start_date_dt]
        if end_date:
            end_date_dt = pd.to_datetime(end_date)
            venmo_df = venmo_df[venmo_df['Trans. Date'] <= end_date_dt]
        
        filtered_count = len(venmo_df)
        print(f"🔍 Venmo: Filtered {original_count} → {filtered_count} transactions")
    
    # Add transaction type classification
    venmo_df['Type'] = venmo_df['Transaction_Type']
    
    # Extract month/year for analysis
    venmo_df['Month'] = venmo_df['Trans. Date'].dt.to_period('M')
    venmo_df['Year'] = venmo_df['Trans. Date'].dt.year
    venmo_df['Month_Name'] = venmo_df['Trans. Date'].dt.strftime('%B')
    venmo_df['Day_of_Week'] = venmo_df['Trans. Date'].dt.day_name()
    
    print(f"✅ Loaded {len(venmo_df)} Venmo transactions")
    return venmo_df

def load_and_clean_data(csv_file, start_date=None, end_date=None, include_venmo=True):
    """Load and clean the Discover CSV data with optional date filtering and Venmo integration"""
    print(f"📂 Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Convert dates
    df['Trans. Date'] = pd.to_datetime(df['Trans. Date'])
    df['Post Date'] = pd.to_datetime(df['Post Date'])
    
    # Apply date filtering if specified
    if start_date or end_date:
        original_count = len(df)
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['Trans. Date'] >= start_date]
            print(f"🔍 Discover: Filtering from {start_date.strftime('%Y-%m-%d')}")
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['Trans. Date'] <= end_date]
            print(f"🔍 Discover: Filtering until {end_date.strftime('%Y-%m-%d')}")
        
        filtered_count = len(df)
        print(f"📊 Discover: Filtered {original_count} → {filtered_count} transactions")
    
    # Clean amounts (ensure numeric)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    # Add expense vs income classification (exclude credit card payments from income)
    def classify_transaction(row):
        if row['Amount'] > 0:
            return 'Expense'
        elif 'INTERNET PAYMENT' in str(row['Description']).upper() or 'PAYMENT - THANK YOU' in str(row['Description']).upper() or 'DIRECTPAY' in str(row['Description']).upper():
            return 'Credit Card Payment'  # Don't count as income
        else:
            return 'Credit/Payment'
    
    df['Type'] = df.apply(classify_transaction, axis=1)
    df['Source'] = 'Discover'
    
    # Extract month/year for analysis
    df['Month'] = df['Trans. Date'].dt.to_period('M')
    df['Year'] = df['Trans. Date'].dt.year
    df['Month_Name'] = df['Trans. Date'].dt.strftime('%B')
    df['Day_of_Week'] = df['Trans. Date'].dt.day_name()
    
    print(f"✅ Loaded {len(df)} Discover transactions")
    
    # Load and integrate Venmo data if requested
    if include_venmo:
        venmo_df = load_venmo_data(start_date, end_date)
        if not venmo_df.empty:
            # Combine datasets
            # Ensure both have the same columns for combination
            common_columns = ['Trans. Date', 'Post Date', 'Description', 'Amount', 'Enhanced_Category', 
                            'Type', 'Month', 'Year', 'Month_Name', 'Day_of_Week', 'Source']
            
            # Prepare Discover data
            df_combined = df.copy()
            df_combined = enhanced_categorization(df_combined)  # Apply categorization first
            
            # Prepare Venmo data for combination
            venmo_combined = venmo_df[['Trans. Date', 'Post Date', 'Description', 'Amount', 'Enhanced_Category', 
                                     'Type', 'Month', 'Year', 'Month_Name', 'Day_of_Week', 'Source']].copy()
            
            # Combine both datasets
            combined_df = pd.concat([df_combined, venmo_combined], ignore_index=True)
            combined_df = combined_df.sort_values('Trans. Date')
            
            # Filter out credit card payments from the final dataset
            credit_card_payments = combined_df[
                (combined_df['Amount'] < 0) & 
                (combined_df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))
            ]
            
            if not credit_card_payments.empty:
                combined_df = combined_df[~(
                    (combined_df['Amount'] < 0) & 
                    (combined_df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))
                )]
                print(f"🚫 Filtered out {len(credit_card_payments)} credit card payment transactions")
            
            print(f"🔗 Combined {len(df)} Discover + {len(venmo_df)} Venmo = {len(combined_df)} total transactions (after filtering)")
            return combined_df
    
    return df

def enhanced_categorization(df):
    """Enhance Discover's categories with custom logic"""
    df = df.copy()
    
    def categorize_enhanced(row):
        desc = row['Description'].upper()
        original_cat = row['Category']
        
        # Housing (NASA Exchange)
        if 'NASAAMESEXCHANGEL' in desc:
            return 'Housing'
        
        # Coffee shops
        elif any(coffee in desc for coffee in ['COFFEE', 'COPPERLINE', 'STARBUCKS', 'COFFEE VILLAGE', 'SIGHTGLASS']):
            return 'Coffee & Cafes'
        
        # Tech subscriptions & tools
        elif any(tech in desc for tech in ['CURSOR', 'OPENAI', 'CHATGPT', 'APPLE.COM']):
            return 'Tech & Software'
        
        # Transportation
        elif any(transport in desc for transport in ['UBER', 'LYFT', 'CLIPPER', 'ZIPCAR']):
            return 'Transportation'
        
        # Airlines
        elif 'UNITED AIRLINES' in desc:
            return 'Air Travel'
        
        # Restaurants & Fast Food (separate from groceries)
        elif (any(asian in desc for asian in ['THAI NOODLE', 'PHO TO LUV', '5TH ELEMENT INDIA']) or
              any(fast_food in desc for fast_food in ['MCDONALD', 'CHIPOTLE', 'CHICK-FIL-A', 'IN-N-OUT']) or
              original_cat == 'Restaurants'):
            return 'Restaurants & Dining'
        
        # Education/Work (NASA but not exchange, Embry Riddle)
        elif any(edu in desc for edu in ['NASA', 'EMBRY RIDDLE', 'ERAU']) and 'NASAAMESEXCHANGEL' not in desc:
            return 'Education/Work'
        
        # Gas stations
        elif any(gas in desc for gas in ['EXXONMOBIL', 'SHELL', 'CHEVRON', 'WAWA', 'CIRCLE K', 'MARATHON']):
            return 'Gas & Fuel'
        
        # Groceries & Supermarkets (food shopping)
        elif (any(grocery in desc for grocery in ['PUBLIX', 'SAFEWAY', 'TRADER JOE', 'WINN-DIXIE', 'TARGET']) or
              original_cat in ['Groceries', 'Supermarkets']):
            return 'Groceries & Supermarkets'
        
        # Keep original category for others, but clean up some names
        elif original_cat == 'Travel/ Entertainment':
            return 'Travel & Entertainment'
        elif original_cat == 'Awards and Rebate Credits':
            return 'Cashback & Credits'
        elif original_cat == 'Payments and Credits':
            return 'Payments & Credits'
        else:
            return original_cat
    
    df['Enhanced_Category'] = df.apply(categorize_enhanced, axis=1)
    print("🔄 Enhanced categorization complete")
    return df

def spending_insights(df):
    """Generate comprehensive spending insights and patterns with revenue tracking"""
    # Separate expenses and income (excluding credit card payments)
    expenses = df[df['Amount'] > 0].copy()
    
    # Only count actual income, not credit card payments
    income = df[(df['Amount'] < 0) & 
                (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))].copy()
    
    # Calculate traditional metrics
    total_spent = expenses['Amount'].sum()
    total_credits = abs(income['Amount'].sum())
    net_spending = total_spent - total_credits
    
    # NEW: Net category analysis (expenses minus income within each category)
    category_net = df.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
    category_expenses = expenses.groupby('Enhanced_Category')['Amount'].sum()
    category_income = income.groupby('Enhanced_Category')['Amount'].sum()
    
    # Separate revenue-generating categories from expense categories
    revenue_categories = category_net[category_net < 0]  # Negative = net income
    expense_categories = category_net[category_net > 0]   # Positive = net expense
    
    # Merchant analysis (traditional)
    merchant_spending = expenses.groupby('Description')['Amount'].sum().sort_values(ascending=False)
    
    # Monthly analysis (net spending)
    monthly_net = df.groupby('Month')['Amount'].sum()
    
    # Day of week analysis (net spending)
    dow_net = df.groupby('Day_of_Week')['Amount'].sum().reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    ])
    
    # Source analysis
    source_breakdown = df.groupby(['Source', 'Enhanced_Category'])['Amount'].sum().unstack(fill_value=0)
    
    insights = {
        'total_transactions': len(df),
        'total_spent': total_spent,
        'total_credits': total_credits,
        'net_spending': net_spending,
        'average_transaction': df['Amount'].mean(),  # Average of all transactions including income
        'largest_expense': expenses.loc[expenses['Amount'].idxmax()] if not expenses.empty else None,
        'largest_income': income.loc[income['Amount'].idxmin()] if not income.empty else None,  # Most negative = largest income
        'most_frequent_merchant': expenses['Description'].value_counts().index[0] if not expenses.empty else 'None',
        'top_expense_category': expense_categories.index[0] if not expense_categories.empty else 'None',
        'top_revenue_category': revenue_categories.index[0] if not revenue_categories.empty else 'None',
        'highest_net_spending_month': monthly_net.idxmax() if not monthly_net.empty else None,
        'highest_net_spending_day': dow_net.idxmax() if not dow_net.empty else None,
        'coffee_net': category_net.get('Coffee & Cafes', 0),
        'restaurant_net': category_net.get('Restaurants & Dining', 0),
        'tech_net': category_net.get('Tech & Software', 0),
        'travel_net': sum([category_net.get(cat, 0) for cat in category_net.index if 'Travel' in cat or 'Air Travel' in cat]),
        'housing_net': category_net.get('Housing', 0),
        'revenue_categories': revenue_categories,
        'expense_categories': expense_categories,
        'category_net': category_net,
        'source_breakdown': source_breakdown,
    }
    
    print("\n" + "="*50)
    print("📊 COMPREHENSIVE FINANCIAL INSIGHTS (WITH REVENUE TRACKING)")
    print("="*50)
    print(f"💳 Total Transactions: {insights['total_transactions']}")
    print(f"💰 Total Spent: ${insights['total_spent']:,.2f}")
    print(f"💸 Total Income/Credits: ${insights['total_credits']:,.2f}")
    print(f"📈 Net Spending: ${insights['net_spending']:,.2f}")
    print(f"📊 Average Transaction: ${insights['average_transaction']:.2f}")
    
    if insights['largest_expense'] is not None:
        print(f"🔥 Largest Expense: ${insights['largest_expense']['Amount']:.2f} at {insights['largest_expense']['Description']}")
    if insights['largest_income'] is not None:
        print(f"💰 Largest Income: ${abs(insights['largest_income']['Amount']):.2f} from {insights['largest_income']['Description']}")
    
    print(f"🏪 Most Frequent Merchant: {insights['most_frequent_merchant']}")
    print(f"📂 Top Net Expense Category: {insights['top_expense_category']}")
    if insights['top_revenue_category'] != 'None':
        print(f"💰 Top Revenue Category: {insights['top_revenue_category']}")
    
    print(f"📅 Highest Net Spending Month: {insights['highest_net_spending_month']}")
    print(f"📆 Highest Net Spending Day: {insights['highest_net_spending_day']}")
    
    print("\n💡 NET CATEGORY ANALYSIS (Expenses - Income):")
    print("-" * 30)
    print(f"☕ Coffee & Cafes: ${insights['coffee_net']:.2f}")
    print(f"🍽️ Restaurants & Dining: ${insights['restaurant_net']:.2f}")
    print(f"💻 Tech & Software: ${insights['tech_net']:.2f}")
    print(f"✈️ Travel: ${insights['travel_net']:,.2f}")
    print(f"🏠 Housing: ${insights['housing_net']:,.2f}")
    
    # Show revenue categories if any exist
    if not revenue_categories.empty:
        print("\n💰 REVENUE-GENERATING CATEGORIES:")
        print("-" * 35)
        for category, net_amount in revenue_categories.items():
            print(f"   {category}: ${abs(net_amount):.2f} net income")
    
    # Show data source breakdown
    print(f"\n📊 DATA SOURCES:")
    print("-" * 20)
    source_totals = df.groupby('Source')['Amount'].sum()
    for source, amount in source_totals.items():
        net_indicator = "income" if amount < 0 else "expense"
        print(f"   {source}: ${abs(amount):.2f} net {net_indicator}")
    
    return insights

def create_spending_dashboard(df, show_all_charts=False):
    """Create financial analysis dashboard with optional additional charts"""
    print("\n🎨 Creating interactive dashboards...")
    
    # Net spending by category (expenses minus income within each category)
    category_net = df.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
    
    # Only show categories with positive net spending for the pie chart
    positive_categories = category_net[category_net > 0]
    
    if not positive_categories.empty:
        fig_pie = px.pie(values=positive_categories.values, 
                         names=positive_categories.index,
                         title='🥧 Net Spending by Category (Expenses - Income)',
                         hole=0.3)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.show()
    else:
        print("📊 No net expenses found - all categories are revenue-positive!")
        return []
    
    charts = [fig_pie]
    
    if show_all_charts:
        print("📊 Generating additional charts...")
        
        # 1. Monthly spending trend
        monthly_spending = expenses.groupby('Month')['Amount'].sum().reset_index()
        monthly_spending['Month_str'] = monthly_spending['Month'].astype(str)
        
        fig1 = px.line(monthly_spending, x='Month_str', y='Amount', 
                       title='📈 Monthly Spending Trend',
                       labels={'Amount': 'Total Spent ($)', 'Month_str': 'Month'},
                       markers=True)
        fig1.update_layout(title_font_size=16, showlegend=False)
        fig1.show()
        
        # 2. Top merchants
        merchant_spending = expenses.groupby('Description')['Amount'].sum().sort_values(ascending=False).head(10)
        
        fig2 = px.bar(x=merchant_spending.values, y=merchant_spending.index,
                      title='🏪 Top 10 Merchants by Spending',
                      labels={'x': 'Total Spent ($)', 'y': 'Merchant'},
                      orientation='h',
                      color=merchant_spending.values,
                      color_continuous_scale='viridis')
        fig2.update_layout(height=500, showlegend=False)
        fig2.show()
        
        # 3. Day of week analysis
        dow_spending = expenses.groupby('Day_of_Week')['Amount'].sum().reindex([
            'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
        ])
        
        fig3 = px.bar(x=dow_spending.index, y=dow_spending.values,
                      title='📅 Spending by Day of Week',
                      labels={'x': 'Day of Week', 'y': 'Total Spent ($)'},
                      color=dow_spending.values,
                      color_continuous_scale='blues')
        fig3.show()
        
        # 4. Transaction amount distribution
        fig4 = px.histogram(expenses, x='Amount', nbins=30,
                           title='💰 Transaction Amount Distribution',
                           labels={'Amount': 'Transaction Amount ($)', 'count': 'Number of Transactions'})
        fig4.show()
        
        charts.extend([fig1, fig2, fig3, fig4])
        print("✅ All dashboards created!")
    else:
        print("✅ Pie chart created! (Use --all-charts to see additional visualizations)")
    
    return charts

def monthly_budget_analysis(df, budget_limits=None):
    """Analyze spending against budget limits"""
    if budget_limits is None:
        # Default budget suggestions based on observed spending
        expenses = df[df['Amount'] > 0]
        category_avg = expenses.groupby('Enhanced_Category')['Amount'].sum() / 12  # Average per month
        
        budget_limits = {
            'Restaurants & Dining': 300,
            'Coffee & Cafes': 50,
            'Groceries & Supermarkets': 200,
            'Gas & Fuel': 150,
            'Tech & Software': 50,
            'Travel & Entertainment': 400,
            'Transportation': 100,
        }
    
    print("\n💰 BUDGET ANALYSIS")
    print("="*30)
    
    expenses = df[df['Amount'] > 0]
    monthly_category_spending = expenses.groupby(['Month', 'Enhanced_Category'])['Amount'].sum().unstack(fill_value=0)
    
    for category, limit in budget_limits.items():
        if category in monthly_category_spending.columns:
            monthly_spent = monthly_category_spending[category]
            avg_monthly = monthly_spent.mean()
            over_budget_months = (monthly_spent > limit).sum()
            
            status = "✅ Within budget" if avg_monthly <= limit else "⚠️ Over budget"
            print(f"{category}: ${avg_monthly:.2f}/month (Budget: ${limit}) {status}")
            if over_budget_months > 0:
                print(f"   📊 Over budget in {over_budget_months} months")
    
    return monthly_category_spending

def export_analysis_report(df, insights, filename='spending_report.txt', date_range_str=""):
    """Export a detailed analysis report"""
    expenses = df[df['Amount'] > 0]
    
    with open(filename, 'w') as f:
        f.write("PERSONAL FINANCE ANALYSIS REPORT\n")
        f.write("="*50 + "\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if date_range_str:
            f.write(f"Analysis Period: {date_range_str}\n")
        f.write("\n")
        
        f.write("SUMMARY STATISTICS\n")
        f.write("-"*20 + "\n")
        f.write(f"Total Transactions: {insights['total_transactions']}\n")
        f.write(f"Total Spent: ${insights['total_spent']:,.2f}\n")
        f.write(f"Total Credits: ${insights['total_credits']:,.2f}\n")
        f.write(f"Net Spending: ${insights['net_spending']:,.2f}\n")
        f.write(f"Average Transaction: ${insights['average_transaction']:.2f}\n\n")
        
        f.write("TOP SPENDING CATEGORIES\n")
        f.write("-"*25 + "\n")
        category_spending = expenses.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
        for i, (category, amount) in enumerate(category_spending.head(10).items(), 1):
            f.write(f"{i:2d}. {category}: ${amount:,.2f}\n")
        
        f.write("\nTOP MERCHANTS\n")
        f.write("-"*15 + "\n")
        merchant_spending = expenses.groupby('Description')['Amount'].sum().sort_values(ascending=False)
        for i, (merchant, amount) in enumerate(merchant_spending.head(10).items(), 1):
            f.write(f"{i:2d}. {merchant}: ${amount:.2f}\n")
    
    print(f"📄 Report exported to {filename}")

def main(start_date=None, end_date=None, show_all_charts=False):
    """Main execution function with optional date filtering"""
    print("🚀 PERSONAL FINANCE ANALYZER")
    print("="*40)
    
    # Create date range string for reporting
    date_range_str = ""
    if start_date and end_date:
        date_range_str = f"{start_date} to {end_date}"
        print(f"📅 Analyzing period: {date_range_str}")
    elif start_date:
        date_range_str = f"From {start_date}"
        print(f"📅 Analyzing from: {start_date}")
    elif end_date:
        date_range_str = f"Until {end_date}"
        print(f"📅 Analyzing until: {end_date}")
    else:
        print("📅 Analyzing all available data")
    
    # Load and process data (includes Venmo integration)
    df = load_and_clean_data('Discover-Last12Months-20250629.csv', start_date, end_date, include_venmo=True)
    
    if len(df) == 0:
        print("❌ No transactions found in the specified date range!")
        return
    
    # Apply enhanced categorization if not already done
    if 'Enhanced_Category' not in df.columns:
        df = enhanced_categorization(df)
    
    # Generate insights
    insights = spending_insights(df)
    
    # Create visualizations (pie chart always shown by default)
    create_spending_dashboard(df, show_all_charts)
    
    # Budget analysis (adjust budget proportionally for shorter periods)
    if start_date and end_date:
        # Calculate the number of days in the analysis period
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        days_in_period = (end_dt - start_dt).days + 1
        period_fraction = days_in_period / 30  # Assume 30 days per month for budget scaling
        
        # Scale budgets for the analysis period - updated categories
        scaled_budgets = {
            'Restaurants & Dining': 300 * period_fraction,
            'Coffee & Cafes': 50 * period_fraction,
            'Groceries & Supermarkets': 200 * period_fraction,
            'Gas & Fuel': 150 * period_fraction,
            'Tech & Software': 50 * period_fraction,
            'Travel & Entertainment': 400 * period_fraction,
            'Transportation': 100 * period_fraction,
            'Housing': 1000 * period_fraction,  # Add housing budget
        }
        print(f"\n💰 SCALED BUDGET ANALYSIS ({days_in_period} days)")
        print("="*40)
        monthly_budget_analysis(df, scaled_budgets)
    else:
        # Updated budget categories for full analysis
        default_budgets = {
            'Restaurants & Dining': 300,
            'Coffee & Cafes': 50,
            'Groceries & Supermarkets': 200,
            'Gas & Fuel': 150,
            'Tech & Software': 50,
            'Travel & Entertainment': 400,
            'Transportation': 100,
            'Housing': 1000,
        }
        monthly_budget_analysis(df, default_budgets)
    
    # Generate filename based on date range
    if start_date and end_date:
        filename = f"spending_report_{start_date.replace('-', '')}_{end_date.replace('-', '')}.txt"
    elif start_date:
        filename = f"spending_report_from_{start_date.replace('-', '')}.txt"
    elif end_date:
        filename = f"spending_report_until_{end_date.replace('-', '')}.txt"
    else:
        filename = "spending_report.txt"
    
    # Export report
    export_analysis_report(df, insights, filename, date_range_str)
    
    print(f"\n🎉 Analysis complete! Check the generated visualizations and {filename}")
    print("\n💡 RECOMMENDATIONS:")
    print("1. Track your housing costs - often the largest expense category")
    print("2. Monitor dining and grocery spending separately")
    print("3. Track your coffee spending - small amounts add up quickly")
    print("4. Review tech subscriptions for unused services")

def analyze_date_range(start_date, end_date):
    """Convenience function to analyze a specific date range"""
    main(start_date, end_date)

def internship_analysis(csv_file, spending_start_date, income_start_date, income_end_date, 
                       gross_income, total_rent=3500):
    """Analyze internship income vs spending with burndown chart"""
    print("💼 SUMMER INTERNSHIP FINANCIAL ANALYSIS")
    print("="*50)
    
    # Use gross income directly (no tax deduction)
    net_income = gross_income
    print(f"💰 Income Budget: ${net_income:,.2f}")
    print(f"🏠 Total Rent (Smooth): ${total_rent:,.2f}")
    print(f"📅 Income Period: {income_start_date} to {income_end_date}")
    print(f"📊 Spending Tracked From: {spending_start_date}")
    
    # Load and filter data for spending period (includes Venmo)
    print(f"\n📂 Loading financial data from {spending_start_date}...")
    df = load_and_clean_data(csv_file, spending_start_date, None, include_venmo=True)
    if 'Enhanced_Category' not in df.columns:
        df = enhanced_categorization(df)
    
    # Calculate net spending with smooth rent allocation
    today = datetime.now().date()
    income_start_dt = pd.to_datetime(income_start_date).date()
    income_end_dt = pd.to_datetime(income_end_date).date()
    spending_start_dt = pd.to_datetime(spending_start_date).date()
    
    # Separate rent from other expenses
    expenses = df[df['Amount'] > 0].copy()
    rent_payments = expenses[expenses['Description'].str.contains('NASAAMESEXCHANGEL', case=False, na=False)].copy()
    non_rent_expenses = expenses[~expenses['Description'].str.contains('NASAAMESEXCHANGEL', case=False, na=False)].copy()
    
    # Only count actual income, not credit card payments
    income = df[(df['Amount'] < 0) & 
                (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))].copy()
    
    # Calculate smooth rent allocation
    total_internship_days = (income_end_dt - income_start_dt).days + 1
    days_so_far = (today - income_start_dt).days + 1 if today >= income_start_dt else 0
    daily_rent = total_rent / total_internship_days
    allocated_rent_so_far = daily_rent * max(0, days_so_far)
    
    # Calculate totals
    actual_rent_paid = rent_payments['Amount'].sum()
    non_rent_spent = non_rent_expenses['Amount'].sum()
    total_income_received = abs(income['Amount'].sum())
    
    # Net spending = Non-rent expenses + Allocated rent - Income received
    net_spent = non_rent_spent + allocated_rent_so_far - total_income_received
    remaining_budget = net_income - net_spent
    
    print(f"\n🏠 RENT ANALYSIS:")
    print("-" * 20)
    print(f"💰 Actual Rent Paid: ${actual_rent_paid:,.2f}")
    print(f"📊 Allocated Rent (Smooth): ${allocated_rent_so_far:,.2f}")
    print(f"📅 Daily Rent Rate: ${daily_rent:.2f}")
    print(f"🎯 Total Rent Budget: ${total_rent:,.2f}")
    
    print(f"\n📊 CURRENT FINANCIAL STATUS")
    print("-" * 30)
    print(f"💰 Income Budget: ${net_income:,.2f}")
    print(f"💸 Non-Rent Expenses: ${non_rent_spent:,.2f}")
    print(f"🏠 Allocated Rent: ${allocated_rent_so_far:,.2f}")
    print(f"💰 Income Received: ${total_income_received:,.2f}")
    print(f"📈 Net Spent: ${net_spent:,.2f}")
    print(f"💵 Remaining Budget: ${remaining_budget:,.2f}")
    
    if remaining_budget >= 0:
        print(f"✅ Status: Within budget (${remaining_budget:,.2f} remaining)")
    else:
        print(f"⚠️ Status: Over budget by ${abs(remaining_budget):,.2f}")
    
    # Days calculations
    total_days_spending = (today - spending_start_dt).days + 1
    total_days_internship = (income_end_dt - income_start_dt).days + 1
    days_remaining = (income_end_dt - today).days
    
    # Calculate projections (excluding rent since it's already allocated smoothly)
    non_rent_days = max(1, total_days_spending)
    daily_non_rent_rate = (non_rent_spent - total_income_received) / non_rent_days if non_rent_days > 0 else 0
    projected_non_rent_spending = daily_non_rent_rate * (income_end_dt - spending_start_dt).days
    projected_total_net_spending = projected_non_rent_spending + total_rent  # Add full rent allocation
    
    print(f"\n📈 SPENDING ANALYSIS")
    print("-" * 20)
    print(f"📅 Days tracking spending: {total_days_spending}")
    print(f"📅 Days remaining in internship: {days_remaining}")
    print(f"💰 Daily non-rent rate: ${daily_non_rent_rate:.2f}")
    print(f"🏠 Daily rent allocation: ${daily_rent:.2f}")
    print(f"🎯 Projected total net spending: ${projected_total_net_spending:,.2f}")
    
    if projected_total_net_spending <= net_income:
        surplus = net_income - projected_total_net_spending
        print(f"✅ Projected surplus: ${surplus:,.2f}")
    else:
        deficit = projected_total_net_spending - net_income
        print(f"⚠️ Projected deficit: ${deficit:,.2f}")
    
    # Create burndown chart with smooth rent allocation
    create_burndown_chart_with_rent(df, spending_start_date, income_start_date, income_end_date, net_income, total_rent)
    
    # Create pie chart visualization
    print(f"\n🎨 Creating spending visualization...")
    create_spending_dashboard(df, show_all_charts=False)
    
    # Category breakdown for internship period (with smooth rent allocation)
    print(f"\n📂 NET SPENDING BREAKDOWN BY CATEGORY (SMOOTH RENT)")
    print("-" * 50)
    
    # Calculate category spending excluding actual rent payments
    df_no_actual_rent = df[~((df['Amount'] > 0) & 
                            (df['Description'].str.contains('NASAAMESEXCHANGEL', case=False, na=False)))].copy()
    category_net = df_no_actual_rent.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
    
    # Add smooth rent allocation to housing category
    if 'Housing' in category_net.index:
        category_net['Housing'] += allocated_rent_so_far
    else:
        category_net['Housing'] = allocated_rent_so_far
    
    # Re-sort after adding smooth rent
    category_net = category_net.sort_values(ascending=False)
    
    for i, (category, net_amount) in enumerate(category_net.items(), 1):
        percentage = (net_amount / net_spent) * 100 if net_spent > 0 else 0
        if net_amount > 0:
            if category == 'Housing':
                print(f"{i:2d}. {category}: ${net_amount:,.2f} ({percentage:.1f}%) [Smooth Rent Allocation]")
            else:
                print(f"{i:2d}. {category}: ${net_amount:,.2f} ({percentage:.1f}%)")
        else:
            print(f"{i:2d}. {category}: ${abs(net_amount):,.2f} net income")
    
    # Weekly net spending analysis (with smooth rent allocation)
    df_no_actual_rent['Week'] = df_no_actual_rent['Trans. Date'].dt.to_period('W')
    weekly_non_rent = df_no_actual_rent.groupby('Week')['Amount'].sum()
    
    print(f"\n📅 WEEKLY NET SPENDING TREND (SMOOTH RENT)")
    print("-" * 45)
    for week, net_amount in weekly_non_rent.items():
        # Add smooth rent allocation for weeks within internship period
        week_start = week.start_time.date()
        week_end = week.end_time.date()
        
        # Calculate how many days of this week fall within internship period
        week_income_start = max(week_start, income_start_dt)
        week_income_end = min(week_end, income_end_dt)
        
        if week_income_start <= week_income_end:
            days_in_period = (week_income_end - week_income_start).days + 1
            week_rent_allocation = daily_rent * days_in_period
        else:
            week_rent_allocation = 0
        
        total_week_spending = net_amount + week_rent_allocation
        
        if total_week_spending > 0:
            print(f"Week of {week.start_time.strftime('%m/%d')}: ${total_week_spending:,.2f} net spent")
            if week_rent_allocation > 0:
                print(f"   (${net_amount:,.2f} non-rent + ${week_rent_allocation:,.2f} smooth rent)")
        else:
            print(f"Week of {week.start_time.strftime('%m/%d')}: ${abs(total_week_spending):,.2f} net income")
    
    # Generate recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 20)
    
    if remaining_budget < 0:
        print("🚨 You're currently over budget!")
        print(f"   Consider reducing net spending by ${abs(remaining_budget/days_remaining):.2f}/day")
    elif days_remaining > 0:
        daily_budget_remaining = remaining_budget / days_remaining
        print(f"💰 Daily budget remaining: ${daily_budget_remaining:.2f}")
        if daily_budget_remaining < daily_non_rent_rate:
            print(f"⚠️ Current net spending (${daily_non_rent_rate:.2f}/day) exceeds remaining budget")
            print(f"   Reduce to ${daily_budget_remaining:.2f}/day to stay on track")
        else:
            print(f"✅ You're on track! Keep net spending under ${daily_budget_remaining:.2f}/day")
    
    # Top net expense categories to monitor
    top_net_expenses = category_net[category_net > 0].head(3)
    print(f"\n🎯 TOP NET EXPENSE CATEGORIES TO MONITOR:")
    for i, (category, net_amount) in enumerate(top_net_expenses.items(), 1):
        percentage = (net_amount / net_spent) * 100 if net_spent > 0 else 0
        print(f"{i}. {category}: ${net_amount:,.2f} ({percentage:.1f}% of net spending)")
    
    # Show revenue categories if any
    revenue_cats = category_net[category_net < 0]
    if not revenue_cats.empty:
        print(f"\n💰 REVENUE-GENERATING CATEGORIES:")
        for category, net_income in revenue_cats.items():
            print(f"   {category}: ${abs(net_income):,.2f} net income")
    
    return {
        'net_income': net_income,
        'non_rent_spent': non_rent_spent,
        'allocated_rent': allocated_rent_so_far,
        'actual_rent_paid': actual_rent_paid,
        'total_income_received': total_income_received,
        'net_spent': net_spent,
        'remaining_budget': remaining_budget,
        'daily_non_rent_rate': daily_non_rent_rate,
        'daily_rent': daily_rent,
        'projected_total_net_spending': projected_total_net_spending,
        'days_remaining': days_remaining
    }

def create_burndown_chart_with_rent(df, spending_start_date, income_start_date, income_end_date, net_income, total_rent):
    """Create a burndown chart with smooth rent allocation"""
    print(f"\n📊 Creating burndown chart with smooth rent allocation...")
    
    # Create date range
    start_date = pd.to_datetime(spending_start_date).date()
    income_start = pd.to_datetime(income_start_date).date()
    end_date = pd.to_datetime(income_end_date).date()
    today = datetime.now().date()
    
    # Calculate daily rent rate
    total_internship_days = (end_date - income_start).days + 1
    daily_rent = total_rent / total_internship_days
    
    # Filter out credit card payments and separate rent from other expenses
    df_filtered = df[~((df['Amount'] < 0) & 
                      (df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False)))].copy()
    
    # Remove actual rent payments from spending (we'll use smooth allocation instead)
    df_no_rent = df_filtered[~((df_filtered['Amount'] > 0) & 
                              (df_filtered['Description'].str.contains('NASAAMESEXCHANGEL', case=False, na=False)))].copy()
    
    df_no_rent['Date'] = df_no_rent['Trans. Date'].dt.date
    daily_non_rent_spending = df_no_rent.groupby('Date')['Amount'].sum()
    
    # Calculate cumulative spending with smooth rent allocation
    cumulative_spending_with_rent = {}
    running_total = 0
    
    for single_date in pd.date_range(start_date, today, freq='D'):
        date_obj = single_date.date()
        
        # Add non-rent spending for this day
        day_non_rent_spending = daily_non_rent_spending.get(date_obj, 0)
        running_total += day_non_rent_spending
        
        # Add daily rent allocation if we're in the internship period
        if date_obj >= income_start:
            running_total += daily_rent
        
        cumulative_spending_with_rent[date_obj] = running_total
    
    # Create ideal spending line (linear from income start to end)
    ideal_daily_burn = net_income / total_internship_days
    
    # Create date series for plotting
    dates = pd.date_range(start_date, end_date, freq='D')
    
    # Ideal remaining budget line
    ideal_remaining = []
    actual_remaining = []
    
    for date in dates:
        date_obj = date.date()
        
        # Ideal: start burning from income_start
        if date_obj < income_start:
            ideal_remaining.append(net_income)  # Haven't started earning yet
        else:
            days_since_income_start = (date_obj - income_start).days
            ideal_spent = ideal_daily_burn * days_since_income_start
            ideal_remaining.append(max(0, net_income - ideal_spent))
        
        # Actual spending with smooth rent
        if date_obj <= today:
            spent_so_far = cumulative_spending_with_rent.get(date_obj, 0)
            actual_remaining.append(net_income - spent_so_far)
        else:
            actual_remaining.append(None)  # Future dates
    
    # Create the plot
    fig = go.Figure()
    
    # Ideal burndown line
    fig.add_trace(go.Scatter(
        x=dates,
        y=ideal_remaining,
        mode='lines',
        name='Ideal Budget Remaining',
        line=dict(color='green', dash='dash'),
        hovertemplate='%{x}<br>Ideal Remaining: $%{y:,.2f}<extra></extra>'
    ))
    
    # Actual burndown line
    actual_dates = [d for d, val in zip(dates, actual_remaining) if val is not None]
    actual_values = [val for val in actual_remaining if val is not None]
    
    fig.add_trace(go.Scatter(
        x=actual_dates,
        y=actual_values,
        mode='lines+markers',
        name='Actual Budget Remaining (Smooth Rent)',
        line=dict(color='blue', width=3),
        hovertemplate='%{x}<br>Actual Remaining: $%{y:,.2f}<extra></extra>'
    ))
    
    # Add annotations for key dates
    fig.add_annotation(
        x=pd.to_datetime(income_start),
        y=max(ideal_remaining) * 0.9,
        text="Income & Rent Start",
        showarrow=True,
        arrowhead=2,
        arrowcolor="orange",
        bgcolor="orange",
        bordercolor="orange",
        font=dict(color="white")
    )
    
    fig.add_annotation(
        x=pd.to_datetime(today),
        y=max([v for v in actual_values if v is not None]) * 0.8,
        text="Today",
        showarrow=True,
        arrowhead=2,
        arrowcolor="red",
        bgcolor="red",
        bordercolor="red",
        font=dict(color="white")
    )
    
    fig.update_layout(
        title='💼 Summer Internship Budget Burndown Chart (Smooth Rent Allocation)',
        xaxis_title='Date',
        yaxis_title='Budget Remaining ($)',
        hovermode='x unified',
        height=500
    )
    
    fig.show()
    
    print("✅ Burndown chart with smooth rent allocation created!")
    return fig

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Personal Finance Analyzer')
    parser.add_argument('--start-date', help='Start date for analysis (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date for analysis (YYYY-MM-DD)')
    parser.add_argument('--all-charts', action='store_true', 
                       help='Show all charts (default: only pie chart)')
    parser.add_argument('--internship', action='store_true',
                       help='Run summer internship analysis (income vs spending)')
    
    args = parser.parse_args()
    
    if args.internship:
        # Summer internship analysis
        print("🚀 Running Summer Internship Analysis...")
        internship_analysis(
            csv_file='Discover-Last12Months-20250629.csv',
            spending_start_date='2025-05-15',  # Start tracking from May 15th
            income_start_date='2025-06-02',    # Income starts June 2nd
            income_end_date='2025-08-10',      # Income ends August 10th
            gross_income=8200,                 # $8200 income budget
            total_rent=3500                    # $3500 total rent (smooth allocation)
        )
    elif not any([args.start_date, args.end_date, args.all_charts]):
        # Default June analysis if no arguments provided
        main('2025-06-01', '2025-06-29')
    else:
        # Use provided arguments for regular analysis
        main(args.start_date, args.end_date, args.all_charts)
    
    # Examples of how to use:
    # python3 finance_analyzer.py  # Default: June 1-29, 2025
    # python3 finance_analyzer.py --internship  # Summer internship analysis
    # python3 finance_analyzer.py --all-charts  # June with all charts
    # python3 finance_analyzer.py --start-date 2025-05-01 --end-date 2025-05-31  # May 2025
    # python3 finance_analyzer.py --start-date 2025-01-01 --end-date 2025-03-31 --all-charts  # Q1 with all charts
