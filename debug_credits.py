#!/usr/bin/env python3
"""
Debug script to analyze credit/payment transactions
"""

import pandas as pd
import os
from datetime import datetime

def load_venmo_data(start_date=None, end_date=None):
    """Load and integrate Venmo transaction data"""
    venmo_file = "venmo_categorized_transactions.csv"
    
    if not os.path.exists(venmo_file):
        print(f"⚠️ Venmo data file not found: {venmo_file}")
        return pd.DataFrame()
    
    print(f"📂 Loading Venmo data from {venmo_file}...")
    venmo_df = pd.read_csv(venmo_file)
    
    # Convert to match Discover format
    venmo_df['Trans. Date'] = pd.to_datetime(venmo_df['Date'])
    venmo_df['Post Date'] = venmo_df['Trans. Date']
    venmo_df['Enhanced_Category'] = venmo_df['Category']
    venmo_df['Source'] = 'Venmo'
    
    # Apply date filtering if specified
    if start_date or end_date:
        if start_date:
            start_date_dt = pd.to_datetime(start_date)
            venmo_df = venmo_df[venmo_df['Trans. Date'] >= start_date_dt]
        if end_date:
            end_date_dt = pd.to_datetime(end_date)
            venmo_df = venmo_df[venmo_df['Trans. Date'] <= end_date_dt]
    
    # Add transaction type classification
    venmo_df['Type'] = venmo_df['Transaction_Type']
    
    return venmo_df

def load_discover_data(csv_file, start_date=None, end_date=None):
    """Load Discover data"""
    print(f"📂 Loading data from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # Convert dates
    df['Trans. Date'] = pd.to_datetime(df['Trans. Date'])
    df['Post Date'] = pd.to_datetime(df['Post Date'])
    
    # Apply date filtering if specified
    if start_date or end_date:
        if start_date:
            start_date = pd.to_datetime(start_date)
            df = df[df['Trans. Date'] >= start_date]
        if end_date:
            end_date = pd.to_datetime(end_date)
            df = df[df['Trans. Date'] <= end_date]
    
    # Clean amounts (ensure numeric)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    
    # Add expense vs income classification
    df['Type'] = df['Amount'].apply(lambda x: 'Expense' if x > 0 else 'Credit/Payment')
    df['Source'] = 'Discover'
    
    return df

def debug_credits_analysis():
    """Debug what's being classified as credits/payments"""
    print("🔍 DEBUGGING CREDITS/PAYMENTS CLASSIFICATION")
    print("="*60)
    
    # Load Discover data
    discover_df = load_discover_data('Discover-Last12Months-20250629.csv', '2025-06-01', '2025-06-29')
    
    # Load Venmo data
    venmo_df = load_venmo_data('2025-06-01', '2025-06-29')
    
    print(f"\n📊 DATA OVERVIEW:")
    print(f"Discover transactions: {len(discover_df)}")
    print(f"Venmo transactions: {len(venmo_df)}")
    
    # Analyze Discover credits (negative amounts)
    discover_credits = discover_df[discover_df['Amount'] < 0].copy()
    discover_expenses = discover_df[discover_df['Amount'] > 0].copy()
    
    print(f"\n💳 DISCOVER CARD ANALYSIS:")
    print(f"📊 Total Discover transactions: {len(discover_df)}")
    print(f"💸 Expenses (positive amounts): {len(discover_expenses)} transactions = ${discover_expenses['Amount'].sum():,.2f}")
    print(f"💰 Credits (negative amounts): {len(discover_credits)} transactions = ${abs(discover_credits['Amount'].sum()):,.2f}")
    
    if not discover_credits.empty:
        print(f"\n🔍 DISCOVER CREDITS BREAKDOWN:")
        print("-" * 40)
        for idx, row in discover_credits.iterrows():
            print(f"Date: {row['Trans. Date'].strftime('%Y-%m-%d')}")
            print(f"Amount: ${abs(row['Amount']):,.2f}")
            print(f"Description: {row['Description']}")
            print(f"Category: {row.get('Category', 'N/A')}")
            print(f"Type: {row['Type']}")
            print("-" * 40)
    
    # Analyze Venmo income
    if not venmo_df.empty:
        venmo_income = venmo_df[venmo_df['Amount'] < 0].copy()  # Negative = income in our system
        venmo_expenses = venmo_df[venmo_df['Amount'] > 0].copy()  # Positive = expenses
        
        print(f"\n💰 VENMO ANALYSIS:")
        print(f"📊 Total Venmo transactions: {len(venmo_df)}")
        print(f"💸 Expenses (positive amounts): {len(venmo_expenses)} transactions = ${venmo_expenses['Amount'].sum():,.2f}")
        print(f"💰 Income (negative amounts): {len(venmo_income)} transactions = ${abs(venmo_income['Amount'].sum()):,.2f}")
        
        if not venmo_income.empty:
            print(f"\n🔍 VENMO INCOME BREAKDOWN:")
            print("-" * 40)
            for idx, row in venmo_income.iterrows():
                print(f"Date: {row['Trans. Date'].strftime('%Y-%m-%d')}")
                print(f"Amount: ${abs(row['Amount']):,.2f}")
                print(f"Description: {row['Description']}")
                print(f"Category: {row.get('Enhanced_Category', 'N/A')}")
                print(f"Other Party: {row.get('Other_Party', 'N/A')}")
                print(f"Type: {row['Type']}")
                print("-" * 40)
    
    # Calculate totals
    total_discover_credits = abs(discover_credits['Amount'].sum()) if not discover_credits.empty else 0
    total_venmo_income = abs(venmo_income['Amount'].sum()) if not venmo_df.empty and not venmo_income.empty else 0
    
    print(f"\n📈 TOTAL CREDITS/INCOME SUMMARY:")
    print(f"💳 Discover Credits: ${total_discover_credits:,.2f}")
    print(f"💰 Venmo Income: ${total_venmo_income:,.2f}")
    print(f"🔢 TOTAL: ${total_discover_credits + total_venmo_income:,.2f}")
    
    # Show which categories are receiving income
    if not venmo_df.empty:
        income_by_category = venmo_df[venmo_df['Amount'] < 0].groupby('Enhanced_Category')['Amount'].sum()
        if not income_by_category.empty:
            print(f"\n📂 INCOME BY CATEGORY (Venmo):")
            print("-" * 30)
            for category, amount in income_by_category.items():
                print(f"{category}: ${abs(amount):,.2f}")

if __name__ == "__main__":
    debug_credits_analysis() 