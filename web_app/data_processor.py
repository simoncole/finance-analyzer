"""
Data processing utilities for the Streamlit web app
"""

import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st
import io
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from finance_analyzer import enhanced_categorization

def process_discover_data(data_input, start_date=None, end_date=None):
    """
    Process Discover CSV data
    
    Args:
        data_input: Either DataFrame or Streamlit uploaded file object
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
    
    Returns:
        Processed DataFrame or None if error
    """
    try:
        # Handle both DataFrame and uploaded file inputs
        if isinstance(data_input, pd.DataFrame):
            df = data_input.copy()
        else:
            # It's an uploaded file object
            df = pd.read_csv(data_input)
        
        # Validate required columns
        required_columns = ['Trans. Date', 'Description', 'Amount', 'Category']
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ Missing required columns. Expected: {required_columns}")
            return None
        
        # Convert dates
        df['Trans. Date'] = pd.to_datetime(df['Trans. Date'])
        df['Post Date'] = pd.to_datetime(df.get('Post Date', df['Trans. Date']))
        
        # Apply date filtering if specified
        if start_date:
            df = df[df['Trans. Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Trans. Date'] <= pd.to_datetime(end_date)]
        
        # Clean amounts (ensure numeric)
        df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        
        # Add transaction type classification
        def classify_transaction(row):
            if row['Amount'] > 0:
                return 'Expense'
            elif 'INTERNET PAYMENT' in str(row['Description']).upper() or 'PAYMENT - THANK YOU' in str(row['Description']).upper() or 'DIRECTPAY' in str(row['Description']).upper():
                return 'Credit Card Payment'
            else:
                return 'Credit/Payment'
        
        df['Type'] = df.apply(classify_transaction, axis=1)
        df['Source'] = 'Discover'
        
        # Extract month/year for analysis
        df['Month'] = df['Trans. Date'].dt.to_period('M')
        df['Year'] = df['Trans. Date'].dt.year
        df['Month_Name'] = df['Trans. Date'].dt.strftime('%B')
        df['Day_of_Week'] = df['Trans. Date'].dt.day_name()
        
        # Apply enhanced categorization
        df = enhanced_categorization(df)
        
        # Filter out credit card payments
        credit_card_payments = df[
            (df['Amount'] < 0) & 
            (df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))
        ]
        
        if not credit_card_payments.empty:
            df = df[~(
                (df['Amount'] < 0) & 
                (df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))
            )]
            st.info(f"🚫 Filtered out {len(credit_card_payments)} credit card payment transactions")
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error processing Discover data: {str(e)}")
        return None

def process_venmo_data(data_input, start_date=None, end_date=None):
    """
    Process Venmo CSV data
    
    Args:
        data_input: Either DataFrame or Streamlit uploaded file object
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
    
    Returns:
        Processed DataFrame or None if error
    """
    try:
        # Handle both DataFrame and uploaded file inputs
        if isinstance(data_input, pd.DataFrame):
            df = data_input.copy()
        else:
            # It's an uploaded file object
            df = pd.read_csv(data_input)
        
        # Validate required columns
        required_columns = ['Date', 'Description', 'Amount', 'Category']
        if not all(col in df.columns for col in required_columns):
            st.error(f"❌ Missing required columns. Expected: {required_columns}")
            return None
        
        # Convert to match Discover format
        df['Trans. Date'] = pd.to_datetime(df['Date'])
        df['Post Date'] = df['Trans. Date']
        df['Enhanced_Category'] = df['Category']
        df['Source'] = 'Venmo'
        
        # CRITICAL FIX: Normalize sign convention to match Discover
        # Discover: Positive = Expense, Negative = Income
        # Venmo: Positive = Income, Negative = Expense
        # Solution: Flip Venmo signs to match Discover convention
        df['Amount'] = -df['Amount']
        
        # Apply date filtering if specified
        if start_date:
            df = df[df['Trans. Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Trans. Date'] <= pd.to_datetime(end_date)]
        
        # Add transaction type classification
        df['Type'] = df['Transaction_Type']
        
        # Extract month/year for analysis
        df['Month'] = df['Trans. Date'].dt.to_period('M')
        df['Year'] = df['Trans. Date'].dt.year
        df['Month_Name'] = df['Trans. Date'].dt.strftime('%B')
        df['Day_of_Week'] = df['Trans. Date'].dt.day_name()
        
        return df
        
    except Exception as e:
        st.error(f"❌ Error processing Venmo data: {str(e)}")
        return None

def combine_datasets(discover_df, venmo_df=None):
    """
    Combine Discover and Venmo datasets
    
    Args:
        discover_df: Processed Discover DataFrame
        venmo_df: Optional processed Venmo DataFrame
    
    Returns:
        Combined DataFrame
    """
    try:
        if venmo_df is None or venmo_df.empty:
            return discover_df
        
        # Ensure both have the same columns for combination
        common_columns = ['Trans. Date', 'Post Date', 'Description', 'Amount', 'Enhanced_Category', 
                         'Type', 'Month', 'Year', 'Month_Name', 'Day_of_Week', 'Source']
        
        # Select common columns from both datasets
        discover_combined = discover_df[common_columns].copy()
        venmo_combined = venmo_df[common_columns].copy()
        
        # Combine both datasets
        combined_df = pd.concat([discover_combined, venmo_combined], ignore_index=True)
        combined_df = combined_df.sort_values('Trans. Date')
        
        return combined_df
        
    except Exception as e:
        st.error(f"❌ Error combining datasets: {str(e)}")
        return discover_df

def calculate_basic_metrics(df):
    """
    Calculate basic financial metrics from the combined dataset
    
    Args:
        df: Combined DataFrame
    
    Returns:
        Dictionary of basic metrics
    """
    try:
        # Separate expenses and income (excluding credit card payments)
        expenses = df[df['Amount'] > 0].copy()
        income = df[(df['Amount'] < 0) & 
                   (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))].copy()
        
        # Calculate metrics
        total_expenses = expenses['Amount'].sum()
        total_income = abs(income['Amount'].sum())
        net_spending = total_expenses - total_income
        avg_transaction = df['Amount'].mean()
        
        # Category breakdown
        category_net = df.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
        top_expense_category = category_net[category_net > 0].index[0] if len(category_net[category_net > 0]) > 0 else 'None'
        
        # Date range
        date_range = f"{df['Trans. Date'].min().strftime('%Y-%m-%d')} to {df['Trans. Date'].max().strftime('%Y-%m-%d')}"
        
        return {
            'total_transactions': len(df),
            'total_expenses': total_expenses,
            'total_income': total_income,
            'net_spending': net_spending,
            'avg_transaction': avg_transaction,
            'top_expense_category': top_expense_category,
            'date_range': date_range,
            'category_breakdown': category_net
        }
        
    except Exception as e:
        st.error(f"❌ Error calculating metrics: {str(e)}")
        return None

def validate_file_format(df, file_type="discover"):
    """
    Validate that uploaded file has the correct format
    
    Args:
        df: DataFrame to validate
        file_type: 'discover' or 'venmo'
    
    Returns:
        Boolean indicating if file is valid
    """
    if file_type == "discover":
        required_columns = ['Trans. Date', 'Description', 'Amount', 'Category']
    elif file_type == "venmo":
        required_columns = ['Date', 'Description', 'Amount', 'Category']
    else:
        return False
    
    return all(col in df.columns for col in required_columns)

def get_category_summary(df):
    """
    Get a summary of spending by category
    
    Args:
        df: Combined DataFrame
    
    Returns:
        DataFrame with category summaries
    """
    try:
        category_summary = df.groupby('Enhanced_Category').agg({
            'Amount': ['sum', 'count', 'mean'],
            'Description': 'first'  # Just to have something to group by
        }).round(2)
        
        # Flatten column names
        category_summary.columns = ['Total_Amount', 'Transaction_Count', 'Avg_Amount', 'Sample_Description']
        category_summary = category_summary.sort_values('Total_Amount', ascending=False)
        
        return category_summary
        
    except Exception as e:
        st.error(f"❌ Error generating category summary: {str(e)}")
        return None 