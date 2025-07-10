"""
Spending insights and analytics for the Personal Finance Analyzer web app
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import calendar
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def calculate_spending_insights(df):
    """
    Calculate comprehensive spending insights from transaction data
    
    Args:
        df: DataFrame with transaction data
    
    Returns:
        Dictionary containing various insights
    """
    try:
        insights = {}
        
        # Basic metrics
        expenses = df[df['Amount'] > 0].copy()
        income = df[(df['Amount'] < 0) & 
                   (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))].copy()
        
        insights['total_expenses'] = expenses['Amount'].sum()
        insights['total_income'] = abs(income['Amount'].sum())
        insights['net_spending'] = insights['total_expenses'] - insights['total_income']
        insights['total_transactions'] = len(df)
        
        # Date range
        insights['date_range'] = {
            'start': df['Trans. Date'].min(),
            'end': df['Trans. Date'].max(),
            'days': (df['Trans. Date'].max() - df['Trans. Date'].min()).days + 1
        }
        
        # Spending frequency
        insights['avg_daily_spending'] = insights['total_expenses'] / insights['date_range']['days']
        insights['avg_transaction_size'] = expenses['Amount'].mean()
        insights['median_transaction_size'] = expenses['Amount'].median()
        
        # Category insights
        category_spending = expenses.groupby('Enhanced_Category')['Amount'].agg(['sum', 'count', 'mean']).round(2)
        category_spending.columns = ['total', 'count', 'average']
        category_spending = category_spending.sort_values('total', ascending=False)
        insights['category_breakdown'] = category_spending
        
        # Top categories
        insights['top_category'] = category_spending.index[0] if len(category_spending) > 0 else 'None'
        insights['top_category_amount'] = category_spending.iloc[0]['total'] if len(category_spending) > 0 else 0
        insights['top_category_percentage'] = (insights['top_category_amount'] / insights['total_expenses'] * 100) if insights['total_expenses'] > 0 else 0
        
        # Monthly patterns
        expenses['Month'] = expenses['Trans. Date'].dt.to_period('M')
        monthly_spending = expenses.groupby('Month')['Amount'].sum()
        insights['monthly_spending'] = monthly_spending
        insights['highest_spending_month'] = monthly_spending.idxmax() if len(monthly_spending) > 0 else None
        insights['lowest_spending_month'] = monthly_spending.idxmin() if len(monthly_spending) > 0 else None
        insights['avg_monthly_spending'] = monthly_spending.mean()
        
        # Weekly patterns
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_spending = expenses.groupby('Day_of_Week')['Amount'].sum().reindex(day_order, fill_value=0)
        insights['daily_patterns'] = daily_spending
        insights['highest_spending_day'] = daily_spending.idxmax()
        insights['lowest_spending_day'] = daily_spending.idxmin()
        
        # Transaction size distribution
        insights['large_transactions'] = len(expenses[expenses['Amount'] > insights['avg_transaction_size'] * 2])
        insights['small_transactions'] = len(expenses[expenses['Amount'] < insights['avg_transaction_size'] * 0.5])
        
        # Spending volatility
        insights['spending_std'] = expenses['Amount'].std()
        insights['spending_cv'] = insights['spending_std'] / insights['avg_transaction_size'] if insights['avg_transaction_size'] > 0 else 0
        
        # Income insights (if available)
        if not income.empty:
            insights['income_sources'] = income.groupby('Enhanced_Category')['Amount'].sum().abs().sort_values(ascending=False)
            insights['largest_income_source'] = insights['income_sources'].index[0] if len(insights['income_sources']) > 0 else 'None'
        
        return insights
        
    except Exception as e:
        st.error(f"Error calculating insights: {str(e)}")
        return None

def show_key_metrics(insights):
    """Display key financial metrics in a dashboard format"""
    st.markdown("### 📊 Key Financial Metrics")
    
    # Main metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Expenses",
            f"${insights['total_expenses']:,.2f}",
            delta=f"${insights['avg_daily_spending']:.2f}/day"
        )
    
    with col2:
        st.metric(
            "Total Income",
            f"${insights['total_income']:,.2f}",
            delta="Income sources" if insights['total_income'] > 0 else None
        )
    
    with col3:
        net_spending = insights['net_spending']
        delta_color = "inverse" if net_spending > 0 else "normal"
        st.metric(
            "Net Spending",
            f"${net_spending:,.2f}",
            delta="Expenses - Income",
            delta_color=delta_color
        )
    
    with col4:
        st.metric(
            "Transactions",
            f"{insights['total_transactions']:,}",
            delta=f"Avg: ${insights['avg_transaction_size']:.2f}"
        )
    
    # Secondary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Date Range",
            f"{insights['date_range']['days']} days",
            delta=f"{insights['date_range']['start'].strftime('%Y-%m-%d')} to {insights['date_range']['end'].strftime('%Y-%m-%d')}"
        )
    
    with col2:
        st.metric(
            "Top Category",
            insights['top_category'],
            delta=f"{insights['top_category_percentage']:.1f}% of spending"
        )
    
    with col3:
        st.metric(
            "Avg Monthly",
            f"${insights['avg_monthly_spending']:,.2f}",
            delta="Monthly spending"
        )

def show_spending_patterns(insights):
    """Display spending pattern insights"""
    st.markdown("### 📈 Spending Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📅 Monthly Patterns**")
        if not insights['monthly_spending'].empty:
            highest_month = insights['highest_spending_month']
            lowest_month = insights['lowest_spending_month']
            
            st.write(f"• **Highest spending:** {highest_month} (${insights['monthly_spending'][highest_month]:,.2f})")
            st.write(f"• **Lowest spending:** {lowest_month} (${insights['monthly_spending'][lowest_month]:,.2f})")
            
            # Monthly variation
            monthly_std = insights['monthly_spending'].std()
            monthly_cv = monthly_std / insights['avg_monthly_spending'] if insights['avg_monthly_spending'] > 0 else 0
            st.write(f"• **Monthly variation:** {monthly_cv:.1%} (coefficient of variation)")
        
        st.markdown("**📊 Transaction Size Analysis**")
        st.write(f"• **Average transaction:** ${insights['avg_transaction_size']:.2f}")
        st.write(f"• **Median transaction:** ${insights['median_transaction_size']:.2f}")
        st.write(f"• **Large transactions (>2x avg):** {insights['large_transactions']}")
        st.write(f"• **Small transactions (<0.5x avg):** {insights['small_transactions']}")
    
    with col2:
        st.markdown("**📆 Weekly Patterns**")
        highest_day = insights['highest_spending_day']
        lowest_day = insights['lowest_spending_day']
        
        st.write(f"• **Highest spending day:** {highest_day} (${insights['daily_patterns'][highest_day]:,.2f})")
        st.write(f"• **Lowest spending day:** {lowest_day} (${insights['daily_patterns'][lowest_day]:,.2f})")
        
        # Weekend vs weekday analysis
        weekend_spending = insights['daily_patterns'][['Saturday', 'Sunday']].sum()
        weekday_spending = insights['daily_patterns'][['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']].sum()
        weekend_pct = weekend_spending / (weekend_spending + weekday_spending) * 100
        
        st.write(f"• **Weekend spending:** {weekend_pct:.1f}% of total")
        st.write(f"• **Weekday spending:** {100-weekend_pct:.1f}% of total")
        
        st.markdown("**🎯 Spending Consistency**")
        volatility_level = "High" if insights['spending_cv'] > 1 else "Medium" if insights['spending_cv'] > 0.5 else "Low"
        st.write(f"• **Spending volatility:** {volatility_level} ({insights['spending_cv']:.2f})")
        st.write(f"• **Standard deviation:** ${insights['spending_std']:.2f}")

def show_category_insights(insights):
    """Display category-based insights"""
    st.markdown("### 🏷️ Category Insights")
    
    category_breakdown = insights['category_breakdown']
    
    if category_breakdown.empty:
        st.warning("No category data available")
        return
    
    # Top categories
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔝 Top Spending Categories**")
        top_5 = category_breakdown.head(5)
        
        for i, (category, row) in enumerate(top_5.iterrows(), 1):
            percentage = (row['total'] / insights['total_expenses']) * 100
            st.write(f"{i}. **{category}**: ${row['total']:,.2f} ({percentage:.1f}%)")
            st.write(f"   - {row['count']} transactions, avg ${row['average']:.2f}")
    
    with col2:
        st.markdown("**📊 Category Statistics**")
        
        # Category diversity
        significant_categories = len(category_breakdown[category_breakdown['total'] > insights['total_expenses'] * 0.05])
        st.write(f"• **Significant categories (>5% of spending):** {significant_categories}")
        
        # Largest single category impact
        top_category_impact = insights['top_category_percentage']
        if top_category_impact > 50:
            concentration = "Very High"
        elif top_category_impact > 30:
            concentration = "High"
        elif top_category_impact > 20:
            concentration = "Medium"
        else:
            concentration = "Low"
        
        st.write(f"• **Spending concentration:** {concentration}")
        st.write(f"  (Top category: {top_category_impact:.1f}%)")
        
        # Average spending per category
        avg_per_category = category_breakdown['total'].mean()
        st.write(f"• **Average per category:** ${avg_per_category:,.2f}")
        
        # Most frequent category
        most_frequent_cat = category_breakdown['count'].idxmax()
        st.write(f"• **Most frequent category:** {most_frequent_cat}")
        st.write(f"  ({category_breakdown.loc[most_frequent_cat, 'count']} transactions)")

def show_income_insights(insights):
    """Display income-related insights if available"""
    if 'income_sources' not in insights or insights['total_income'] == 0:
        return
    
    st.markdown("### 💰 Income Insights")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💵 Income Sources**")
        
        income_sources = insights['income_sources'].head(5)
        for i, (category, amount) in enumerate(income_sources.items(), 1):
            percentage = (amount / insights['total_income']) * 100
            st.write(f"{i}. **{category}**: ${amount:,.2f} ({percentage:.1f}%)")
    
    with col2:
        st.markdown("**📊 Income vs Expenses**")
        
        income_to_expense_ratio = insights['total_income'] / insights['total_expenses'] if insights['total_expenses'] > 0 else 0
        
        if income_to_expense_ratio >= 1:
            status = "✅ Positive"
            message = "Income covers expenses"
        elif income_to_expense_ratio >= 0.8:
            status = "⚠️ Close"
            message = "Income nearly covers expenses"
        else:
            status = "❌ Deficit"
            message = "Expenses exceed income"
        
        st.write(f"• **Cash flow status:** {status}")
        st.write(f"  {message}")
        st.write(f"• **Income/Expense ratio:** {income_to_expense_ratio:.2f}")
        
        savings_rate = (insights['total_income'] - insights['total_expenses']) / insights['total_income'] * 100 if insights['total_income'] > 0 else 0
        st.write(f"• **Savings rate:** {savings_rate:.1f}%")

def show_recommendations(insights):
    """Display personalized recommendations based on spending patterns"""
    st.markdown("### 💡 Personalized Recommendations")
    
    recommendations = []
    
    # High spending category recommendation
    if insights['top_category_percentage'] > 40:
        recommendations.append({
            'type': '🎯 Focus Area',
            'title': 'High Category Concentration',
            'message': f"Your top category ({insights['top_category']}) accounts for {insights['top_category_percentage']:.1f}% of spending. Consider reviewing transactions in this category for potential savings.",
            'priority': 'high'
        })
    
    # Transaction size recommendations
    if insights['large_transactions'] > insights['total_transactions'] * 0.1:  # More than 10% large transactions
        recommendations.append({
            'type': '💳 Spending Habits',
            'title': 'Large Transaction Alert',
            'message': f"You have {insights['large_transactions']} large transactions (>2x average). Review these for potential budget impact.",
            'priority': 'medium'
        })
    
    # Spending volatility
    if insights['spending_cv'] > 1:
        recommendations.append({
            'type': '📊 Consistency',
            'title': 'High Spending Variability',
            'message': "Your spending varies significantly between transactions. Consider setting category budgets for more consistent spending.",
            'priority': 'medium'
        })
    
    # Cash flow recommendations
    if 'total_income' in insights and insights['total_income'] > 0:
        savings_rate = (insights['total_income'] - insights['total_expenses']) / insights['total_income']
        if savings_rate < 0.1:  # Less than 10% savings rate
            recommendations.append({
                'type': '💰 Savings',
                'title': 'Low Savings Rate',
                'message': f"Your current savings rate is {savings_rate:.1%}. Consider the 50/30/20 rule: 50% needs, 30% wants, 20% savings.",
                'priority': 'high'
            })
    
    # Daily spending recommendation
    if insights['avg_daily_spending'] > 100:  # Arbitrary threshold
        recommendations.append({
            'type': '📅 Daily Habits',
            'title': 'High Daily Spending',
            'message': f"Your average daily spending is ${insights['avg_daily_spending']:.2f}. Setting a daily spending limit might help with budgeting.",
            'priority': 'medium'
        })
    
    # Weekend spending pattern
    weekend_spending = insights['daily_patterns'][['Saturday', 'Sunday']].sum()
    total_weekly_spending = insights['daily_patterns'].sum()
    weekend_pct = weekend_spending / total_weekly_spending * 100 if total_weekly_spending > 0 else 0
    
    if weekend_pct > 40:  # More than 40% on weekends
        recommendations.append({
            'type': '📆 Weekend Spending',
            'title': 'High Weekend Spending',
            'message': f"{weekend_pct:.1f}% of your spending occurs on weekends. Consider planning weekend activities with set budgets.",
            'priority': 'low'
        })
    
    # Display recommendations
    if recommendations:
        # Sort by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        recommendations.sort(key=lambda x: priority_order[x['priority']])
        
        for rec in recommendations:
            if rec['priority'] == 'high':
                st.error(f"**{rec['type']}: {rec['title']}**\n\n{rec['message']}")
            elif rec['priority'] == 'medium':
                st.warning(f"**{rec['type']}: {rec['title']}**\n\n{rec['message']}")
            else:
                st.info(f"**{rec['type']}: {rec['title']}**\n\n{rec['message']}")
    else:
        st.success("🎉 **Great job!** Your spending patterns look healthy. Keep up the good financial habits!")

def show_spending_insights(df):
    """Main function to display all spending insights"""
    st.markdown('<div class="section-header">🔍 Spending Insights</div>', unsafe_allow_html=True)
    
    # Calculate insights
    with st.spinner("Analyzing your spending patterns..."):
        insights = calculate_spending_insights(df)
    
    if insights is None:
        st.error("Failed to calculate insights")
        return
    
    # Display insights in sections
    show_key_metrics(insights)
    st.markdown("---")
    
    show_spending_patterns(insights)
    st.markdown("---")
    
    show_category_insights(insights)
    st.markdown("---")
    
    show_income_insights(insights)
    st.markdown("---")
    
    show_recommendations(insights) 