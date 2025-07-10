"""
Interactive visualizations for the Personal Finance Analyzer web app
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import calendar

def create_spending_pie_chart(df, title="Spending by Category"):
    """
    Create an interactive pie chart of spending by category
    
    Args:
        df: DataFrame with transaction data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        # Calculate net spending by category (expenses - income within each category)
        category_spending = df.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
        
        # Filter to only positive spending (expenses)
        expense_categories = category_spending[category_spending > 0]
        
        if expense_categories.empty:
            st.warning("No expense categories found for pie chart")
            return None
        
        # Create pie chart
        fig = px.pie(
            values=expense_categories.values,
            names=expense_categories.index,
            title=title,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        # Update layout
        fig.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.2f}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            showlegend=True,
            height=500,
            font=dict(size=12)
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating pie chart: {str(e)}")
        return None

def create_spending_bar_chart(df, title="Spending by Category"):
    """
    Create an interactive bar chart of spending by category
    
    Args:
        df: DataFrame with transaction data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        # Calculate net spending by category
        category_spending = df.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
        
        # Create bar chart
        fig = px.bar(
            x=category_spending.index,
            y=category_spending.values,
            title=title,
            labels={'x': 'Category', 'y': 'Amount ($)'},
            color=category_spending.values,
            color_continuous_scale='RdYlGn_r'
        )
        
        # Update layout
        fig.update_layout(
            xaxis_tickangle=-45,
            height=500,
            showlegend=False,
            xaxis_title="Category",
            yaxis_title="Amount ($)"
        )
        
        # Update hover template
        fig.update_traces(
            hovertemplate='<b>%{x}</b><br>Amount: $%{y:,.2f}<extra></extra>'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating bar chart: {str(e)}")
        return None

def create_monthly_trend_chart(df, title="Monthly Spending Trend"):
    """
    Create a line chart showing spending trends over time
    
    Args:
        df: DataFrame with transaction data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        # Group by month and calculate totals
        df['Month_Year'] = df['Trans. Date'].dt.to_period('M')
        monthly_data = df.groupby('Month_Year').agg({
            'Amount': ['sum', 'count']
        }).round(2)
        
        # Flatten column names
        monthly_data.columns = ['Total_Amount', 'Transaction_Count']
        monthly_data = monthly_data.reset_index()
        monthly_data['Month_Year_Str'] = monthly_data['Month_Year'].astype(str)
        
        # Separate expenses and income
        expenses_monthly = df[df['Amount'] > 0].groupby('Month_Year')['Amount'].sum()
        income_monthly = df[(df['Amount'] < 0) & 
                           (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))].groupby('Month_Year')['Amount'].sum().abs()
        
        # Create subplot with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Add expenses line
        fig.add_trace(
            go.Scatter(
                x=[str(x) for x in expenses_monthly.index],
                y=expenses_monthly.values,
                mode='lines+markers',
                name='Expenses',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False,
        )
        
        # Add income line if we have income data
        if not income_monthly.empty:
            fig.add_trace(
                go.Scatter(
                    x=[str(x) for x in income_monthly.index],
                    y=income_monthly.values,
                    mode='lines+markers',
                    name='Income',
                    line=dict(color='green', width=3),
                    marker=dict(size=8)
                ),
                secondary_y=False,
            )
        
        # Add transaction count on secondary axis
        fig.add_trace(
            go.Scatter(
                x=monthly_data['Month_Year_Str'],
                y=monthly_data['Transaction_Count'],
                mode='lines+markers',
                name='Transaction Count',
                line=dict(color='blue', width=2, dash='dash'),
                marker=dict(size=6),
                opacity=0.7
            ),
            secondary_y=True,
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Month",
            height=500,
            hovermode='x unified'
        )
        
        # Set y-axes titles
        fig.update_yaxes(title_text="Amount ($)", secondary_y=False)
        fig.update_yaxes(title_text="Number of Transactions", secondary_y=True)
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating trend chart: {str(e)}")
        return None

def create_daily_spending_chart(df, title="Daily Spending Pattern"):
    """
    Create a chart showing spending patterns by day of week
    
    Args:
        df: DataFrame with transaction data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        # Group by day of week
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_spending = df[df['Amount'] > 0].groupby('Day_of_Week')['Amount'].agg(['sum', 'mean', 'count'])
        daily_spending = daily_spending.reindex(day_order)
        
        # Create bar chart
        fig = go.Figure()
        
        # Add total spending bars
        fig.add_trace(go.Bar(
            x=daily_spending.index,
            y=daily_spending['sum'],
            name='Total Spending',
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>Total: $%{y:,.2f}<br>Transactions: %{customdata}<extra></extra>',
            customdata=daily_spending['count']
        ))
        
        # Add average spending line
        fig.add_trace(go.Scatter(
            x=daily_spending.index,
            y=daily_spending['mean'],
            mode='lines+markers',
            name='Average per Transaction',
            line=dict(color='red', width=3),
            marker=dict(size=8),
            yaxis='y2',
            hovertemplate='<b>%{x}</b><br>Average: $%{y:.2f}<extra></extra>'
        ))
        
        # Update layout with secondary y-axis
        fig.update_layout(
            title=title,
            xaxis_title="Day of Week",
            yaxis=dict(title="Total Spending ($)", side="left"),
            yaxis2=dict(title="Average per Transaction ($)", side="right", overlaying="y"),
            height=500,
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating daily spending chart: {str(e)}")
        return None

def create_transaction_size_distribution(df, title="Transaction Size Distribution"):
    """
    Create a histogram showing the distribution of transaction sizes
    
    Args:
        df: DataFrame with transaction data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        # Filter to expenses only
        expenses = df[df['Amount'] > 0]['Amount']
        
        if expenses.empty:
            st.warning("No expense transactions found for distribution chart")
            return None
        
        # Create histogram
        fig = px.histogram(
            x=expenses,
            nbins=30,
            title=title,
            labels={'x': 'Transaction Amount ($)', 'y': 'Frequency'},
            color_discrete_sequence=['skyblue']
        )
        
        # Add statistics annotations
        mean_val = expenses.mean()
        median_val = expenses.median()
        
        fig.add_vline(x=mean_val, line_dash="dash", line_color="red", 
                     annotation_text=f"Mean: ${mean_val:.2f}")
        fig.add_vline(x=median_val, line_dash="dash", line_color="green", 
                     annotation_text=f"Median: ${median_val:.2f}")
        
        # Update layout
        fig.update_layout(
            height=400,
            showlegend=False,
            xaxis_title="Transaction Amount ($)",
            yaxis_title="Number of Transactions"
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating distribution chart: {str(e)}")
        return None

def create_category_trend_chart(df, selected_categories=None, title="Category Trends Over Time"):
    """
    Create a line chart showing trends for specific categories over time
    
    Args:
        df: DataFrame with transaction data
        selected_categories: List of categories to include
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        if selected_categories is None:
            # Get top 5 spending categories
            top_categories = df[df['Amount'] > 0].groupby('Enhanced_Category')['Amount'].sum().nlargest(5).index.tolist()
            selected_categories = top_categories
        
        # Group by month and category
        df['Month_Year'] = df['Trans. Date'].dt.to_period('M')
        category_trends = df[df['Enhanced_Category'].isin(selected_categories)].groupby(['Month_Year', 'Enhanced_Category'])['Amount'].sum().unstack(fill_value=0)
        
        # Create line chart
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        for i, category in enumerate(category_trends.columns):
            fig.add_trace(go.Scatter(
                x=[str(x) for x in category_trends.index],
                y=category_trends[category],
                mode='lines+markers',
                name=category,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=6)
            ))
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_title="Month",
            yaxis_title="Amount ($)",
            height=500,
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating category trend chart: {str(e)}")
        return None

def create_income_vs_expenses_chart(df, title="Income vs Expenses Over Time"):
    """
    Create a chart comparing income and expenses over time
    
    Args:
        df: DataFrame with transaction data
        title: Chart title
    
    Returns:
        Plotly figure object
    """
    try:
        # Group by month
        df['Month_Year'] = df['Trans. Date'].dt.to_period('M')
        
        # Calculate monthly expenses and income
        monthly_expenses = df[df['Amount'] > 0].groupby('Month_Year')['Amount'].sum()
        monthly_income = df[(df['Amount'] < 0) & 
                           (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))].groupby('Month_Year')['Amount'].sum().abs()
        
        # Ensure both series have the same index
        all_months = pd.Index(set(monthly_expenses.index) | set(monthly_income.index))
        monthly_expenses = monthly_expenses.reindex(all_months, fill_value=0)
        monthly_income = monthly_income.reindex(all_months, fill_value=0)
        
        # Create bar chart
        fig = go.Figure()
        
        months_str = [str(x) for x in all_months]
        
        fig.add_trace(go.Bar(
            x=months_str,
            y=monthly_expenses,
            name='Expenses',
            marker_color='red',
            opacity=0.8
        ))
        
        fig.add_trace(go.Bar(
            x=months_str,
            y=monthly_income,
            name='Income',
            marker_color='green',
            opacity=0.8
        ))
        
        # Add net spending line
        net_spending = monthly_expenses - monthly_income
        fig.add_trace(go.Scatter(
            x=months_str,
            y=net_spending,
            mode='lines+markers',
            name='Net Spending',
            line=dict(color='blue', width=3),
            marker=dict(size=8),
            yaxis='y2'
        ))
        
        # Update layout with secondary y-axis
        fig.update_layout(
            title=title,
            xaxis_title="Month",
            yaxis=dict(title="Amount ($)", side="left"),
            yaxis2=dict(title="Net Spending ($)", side="right", overlaying="y"),
            height=500,
            barmode='group',
            hovermode='x unified'
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating income vs expenses chart: {str(e)}")
        return None 