#!/usr/bin/env python3

import pandas as pd
import os

def debug_categories():
    """Debug transactions in categories showing unexpected net income"""
    
    print("🔍 DEBUGGING CATEGORY NET INCOME ISSUES")
    print("="*60)
    
    # Load Discover data
    print("\n📂 Loading Discover data...")
    discover_df = pd.read_csv('Discover-Last12Months-20250629.csv')
    discover_df['Source'] = 'Discover'
    
    # Load Venmo data if available
    venmo_df = pd.DataFrame()
    if os.path.exists('venmo_categorized_transactions.csv'):
        print("📂 Loading Venmo data...")
        venmo_df = pd.read_csv('venmo_categorized_transactions.csv')
        venmo_df['Source'] = 'Venmo'
        # Rename columns to match Discover format
        venmo_df = venmo_df.rename(columns={'Date': 'Trans. Date', 'Category': 'Enhanced_Category'})
    
    # Filter for internship period (May 15 - present)
    start_date = '2025-05-15'
    discover_df['Trans. Date'] = pd.to_datetime(discover_df['Trans. Date'])
    discover_filtered = discover_df[discover_df['Trans. Date'] >= start_date].copy()
    
    if not venmo_df.empty:
        venmo_df['Trans. Date'] = pd.to_datetime(venmo_df['Trans. Date'])
        venmo_filtered = venmo_df[venmo_df['Trans. Date'] >= start_date].copy()
    else:
        venmo_filtered = pd.DataFrame()
    
    print(f"📊 Filtered to transactions from {start_date} onward")
    print(f"   Discover: {len(discover_filtered)} transactions")
    print(f"   Venmo: {len(venmo_filtered)} transactions")
    
    # Debug Groceries & Supermarkets
    print("\n" + "="*60)
    print("🛒 DEBUGGING: GROCERIES & SUPERMARKETS")
    print("="*60)
    
    # From Discover (original category or enhanced)
    grocery_discover = discover_filtered[
        (discover_filtered['Category'].isin(['Groceries', 'Supermarkets'])) |
        (discover_filtered['Description'].str.contains('PUBLIX|SAFEWAY|TRADER JOE|WINN-DIXIE|TARGET', case=False, na=False))
    ].copy()
    
    # From Venmo
    grocery_venmo = venmo_filtered[
        venmo_filtered['Enhanced_Category'] == 'Groceries & Supermarkets'
    ].copy() if not venmo_filtered.empty else pd.DataFrame()
    
    print(f"\n📊 DISCOVER GROCERY TRANSACTIONS ({len(grocery_discover)}):")
    if not grocery_discover.empty:
        for _, row in grocery_discover.iterrows():
            amount_type = "EXPENSE" if row['Amount'] > 0 else "INCOME/CREDIT"
            print(f"   {row['Trans. Date'].strftime('%m/%d/%Y')}: ${row['Amount']:8.2f} ({amount_type}) - {row['Description'][:60]}")
        
        grocery_discover_total = grocery_discover['Amount'].sum()
        print(f"\n   💰 Discover Grocery Total: ${grocery_discover_total:.2f}")
    else:
        print("   No Discover grocery transactions found")
    
    print(f"\n📊 VENMO GROCERY TRANSACTIONS ({len(grocery_venmo)}):")
    if not grocery_venmo.empty:
        for _, row in grocery_venmo.iterrows():
            amount_type = "EXPENSE" if row['Amount'] < 0 else "INCOME"
            print(f"   {row['Trans. Date'].strftime('%m/%d/%Y')}: ${row['Amount']:8.2f} ({amount_type}) - {row['Description']} from {row['Other_Party']}")
        
        grocery_venmo_total = grocery_venmo['Amount'].sum()
        print(f"\n   💰 Venmo Grocery Total: ${grocery_venmo_total:.2f}")
    else:
        print("   No Venmo grocery transactions found")
    
    # Calculate net
    discover_total = grocery_discover['Amount'].sum() if not grocery_discover.empty else 0
    venmo_total = grocery_venmo['Amount'].sum() if not grocery_venmo.empty else 0
    grocery_net = discover_total + venmo_total
    
    print(f"\n🧮 GROCERY NET CALCULATION:")
    print(f"   Discover Total: ${discover_total:.2f}")
    print(f"   Venmo Total: ${venmo_total:.2f}")
    print(f"   NET TOTAL: ${grocery_net:.2f}")
    
    if grocery_net < 0:
        print(f"   ✅ Net Income: ${abs(grocery_net):.2f}")
    else:
        print(f"   💸 Net Expense: ${grocery_net:.2f}")
    
    # Debug Payments & Credits
    print("\n" + "="*60)
    print("💳 DEBUGGING: PAYMENTS & CREDITS")
    print("="*60)
    
    payments_discover = discover_filtered[
        discover_filtered['Category'] == 'Payments and Credits'
    ].copy()
    
    print(f"\n📊 DISCOVER PAYMENTS & CREDITS TRANSACTIONS ({len(payments_discover)}):")
    if not payments_discover.empty:
        for _, row in payments_discover.iterrows():
            amount_type = "EXPENSE" if row['Amount'] > 0 else "CREDIT/PAYMENT"
            is_credit_card = "INTERNET PAYMENT" in row['Description'] or "DIRECTPAY" in row['Description']
            payment_type = " [CREDIT CARD PAYMENT]" if is_credit_card else " [OTHER CREDIT]"
            print(f"   {row['Trans. Date'].strftime('%m/%d/%Y')}: ${row['Amount']:8.2f} ({amount_type}) - {row['Description'][:60]}{payment_type}")
        
        payments_total = payments_discover['Amount'].sum()
        print(f"\n   💰 Payments & Credits Total: ${payments_total:.2f}")
        
        # Separate credit card payments from other credits
        credit_card_payments = payments_discover[
            payments_discover['Description'].str.contains('INTERNET PAYMENT|DIRECTPAY', case=False, na=False)
        ]
        other_credits = payments_discover[
            ~payments_discover['Description'].str.contains('INTERNET PAYMENT|DIRECTPAY', case=False, na=False)
        ]
        
        print(f"\n   🔍 BREAKDOWN:")
        print(f"   Credit Card Payments: ${credit_card_payments['Amount'].sum():.2f} (should be filtered out)")
        print(f"   Other Credits: ${other_credits['Amount'].sum():.2f} (legitimate income)")
        
        if not other_credits.empty:
            print(f"\n   📋 OTHER CREDITS DETAILS:")
            for _, row in other_credits.iterrows():
                print(f"      {row['Trans. Date'].strftime('%m/%d/%Y')}: ${row['Amount']:8.2f} - {row['Description']}")
    
    else:
        print("   No Payments & Credits transactions found")
    
    print("\n" + "="*60)
    print("🎯 ISSUES IDENTIFIED:")
    print("="*60)
    
    # Issue 1: Check for miscategorized Venmo transactions
    if not grocery_venmo.empty:
        gas_transactions = grocery_venmo[grocery_venmo['Description'].str.contains('⛽|gas', case=False, na=False)]
        if not gas_transactions.empty:
            print("\n❌ ISSUE 1: Gas transaction miscategorized as Groceries!")
            for _, row in gas_transactions.iterrows():
                print(f"   {row['Trans. Date'].strftime('%m/%d/%Y')}: ${row['Amount']:8.2f} - '{row['Description']}' from {row['Other_Party']}")
                print(f"   💡 SUGGESTION: Should be categorized as 'Gas & Fuel' instead of 'Groceries & Supermarkets'")
    
    # Issue 2: Check credit card payment filtering
    if not payments_discover.empty:
        unfiltered_cc_payments = payments_discover[
            payments_discover['Description'].str.contains('INTERNET PAYMENT|DIRECTPAY', case=False, na=False)
        ]
        if not unfiltered_cc_payments.empty:
            print(f"\n❌ ISSUE 2: Credit card payments not being filtered out!")
            print(f"   Total credit card payments: ${unfiltered_cc_payments['Amount'].sum():.2f}")
            print(f"   💡 SUGGESTION: These should be excluded from financial analysis")

if __name__ == "__main__":
    debug_categories() 