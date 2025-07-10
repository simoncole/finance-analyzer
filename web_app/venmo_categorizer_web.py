"""
Web-based Venmo transaction categorizer for the Personal Finance Analyzer
"""

import pandas as pd
import streamlit as st
import json
import os
import sys
from datetime import datetime
import io

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Category options (matching the original categorizer)
CATEGORY_OPTIONS = [
    "Groceries & Supermarkets",
    "Restaurants & Dining", 
    "Gas & Fuel",
    "Entertainment",
    "Shopping",
    "Healthcare",
    "Education/Work",
    "Travel",
    "Housing",
    "Transportation",
    "Utilities",
    "Personal Care",
    "Gifts & Donations",
    "Financial Services",
    "Other"
]

def load_venmo_csv(uploaded_file):
    """Load and validate Venmo CSV file"""
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        # Check if this is a raw Venmo file that needs processing
        if 'ID' in df.columns and 'Datetime' in df.columns:
            # This is a raw Venmo export - process it
            df = process_raw_venmo_file(df)
        
        # Validate required columns for categorization
        required_columns = ['Date', 'Description', 'Amount', 'Transaction_Type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            st.info("Expected columns: Date, Description, Amount, Transaction_Type")
            return None
        
        return df
        
    except Exception as e:
        st.error(f"Error loading Venmo file: {str(e)}")
        return None

def process_raw_venmo_file(df):
    """Process raw Venmo export file into standardized format"""
    try:
        # Skip header rows (first 3 rows are typically metadata)
        if len(df) > 3 and df.iloc[0].isna().all():
            df = df.iloc[3:].reset_index(drop=True)
        
        # Rename columns to standard format
        column_mapping = {
            'Datetime': 'Date',
            'Amount (total)': 'Amount',
            'Type': 'Transaction_Type',
            'Note': 'Description'
        }
        
        df = df.rename(columns=column_mapping)
        
        # Clean up the data
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df['Amount'] = pd.to_numeric(df['Amount'].astype(str).str.replace('$', '').str.replace(',', ''), errors='coerce')
        
        # Filter to payments only (exclude charges from friends)
        df = df[df['Transaction_Type'] == 'Payment'].copy()
        
        # Remove any rows with missing data
        df = df.dropna(subset=['Date', 'Amount', 'Description'])
        
        return df
        
    except Exception as e:
        st.error(f"Error processing raw Venmo file: {str(e)}")
        return None

def save_categorization_progress(transactions_data, progress_file='venmo_categorization_progress.json'):
    """Save categorization progress to JSON file"""
    try:
        progress_data = {
            'timestamp': datetime.now().isoformat(),
            'total_transactions': len(transactions_data),
            'categorized_count': sum(1 for t in transactions_data if t.get('category')),
            'transactions': transactions_data
        }
        
        # Convert to JSON string for download
        json_str = json.dumps(progress_data, indent=2, default=str)
        return json_str
        
    except Exception as e:
        st.error(f"Error saving progress: {str(e)}")
        return None

def load_categorization_progress(uploaded_file):
    """Load previously saved categorization progress"""
    try:
        if uploaded_file is None:
            return None
        
        # Read the JSON file
        content = uploaded_file.read()
        progress_data = json.loads(content)
        
        return progress_data.get('transactions', [])
        
    except Exception as e:
        st.error(f"Error loading progress file: {str(e)}")
        return None

def export_categorized_transactions(transactions_data):
    """Export categorized transactions to CSV format"""
    try:
        # Filter only categorized transactions
        categorized = [t for t in transactions_data if t.get('category')]
        
        if not categorized:
            return None
        
        # Create DataFrame
        df = pd.DataFrame(categorized)
        
        # Ensure proper column order
        columns = ['Date', 'Description', 'Amount', 'Category', 'Transaction_Type']
        df = df[columns]
        
        # Convert to CSV string
        csv_string = df.to_csv(index=False)
        return csv_string
        
    except Exception as e:
        st.error(f"Error exporting transactions: {str(e)}")
        return None

def show_venmo_categorizer():
    """Main Venmo categorization interface"""
    st.markdown('<div class="section-header">💸 Venmo Transaction Categorizer</div>', unsafe_allow_html=True)
    
    st.markdown("""
    This tool helps you categorize your Venmo transactions for financial analysis. 
    You can upload raw Venmo exports or continue from previous progress.
    """)
    
    # File upload section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📂 Upload Venmo Data")
        venmo_file = st.file_uploader(
            "Upload Venmo CSV file",
            type=['csv'],
            key="venmo_categorizer_upload",
            help="Upload your Venmo transaction export (CSV format)"
        )
    
    with col2:
        st.markdown("#### 📄 Load Previous Progress")
        progress_file = st.file_uploader(
            "Upload progress file (optional)",
            type=['json'],
            key="progress_upload",
            help="Continue from where you left off"
        )
    
    # Initialize session state
    if 'venmo_transactions' not in st.session_state:
        st.session_state.venmo_transactions = []
    if 'current_transaction_index' not in st.session_state:
        st.session_state.current_transaction_index = 0
    if 'categorization_mode' not in st.session_state:
        st.session_state.categorization_mode = False
    
    # Load data
    if venmo_file is not None:
        df = load_venmo_csv(venmo_file)
        if df is not None:
            # Convert DataFrame to transaction list
            transactions = []
            for _, row in df.iterrows():
                transactions.append({
                    'Date': str(row['Date']),
                    'Description': row['Description'],
                    'Amount': float(row['Amount']),
                    'Transaction_Type': row['Transaction_Type'],
                    'category': None  # To be filled during categorization
                })
            
            # Load previous progress if available
            if progress_file is not None:
                previous_transactions = load_categorization_progress(progress_file)
                if previous_transactions:
                    # Merge with existing categorizations
                    progress_dict = {
                        (t['Date'], t['Description'], t['Amount']): t.get('category')
                        for t in previous_transactions
                        if t.get('category')
                    }
                    
                    for transaction in transactions:
                        key = (transaction['Date'], transaction['Description'], transaction['Amount'])
                        if key in progress_dict:
                            transaction['category'] = progress_dict[key]
                    
                    st.success(f"Loaded progress file with {len([t for t in previous_transactions if t.get('category')])} categorized transactions")
            
            st.session_state.venmo_transactions = transactions
            st.session_state.current_transaction_index = 0
            st.session_state.categorization_mode = True
            
            st.success(f"✅ Loaded {len(transactions)} Venmo transactions")
    
    # Show categorization interface if we have transactions
    if st.session_state.categorization_mode and st.session_state.venmo_transactions:
        show_categorization_interface()

def show_categorization_interface():
    """Show the interactive categorization interface"""
    transactions = st.session_state.venmo_transactions
    current_idx = st.session_state.current_transaction_index
    
    if current_idx >= len(transactions):
        show_completion_interface()
        return
    
    # Progress indicator
    categorized_count = sum(1 for t in transactions if t.get('category'))
    total_count = len(transactions)
    progress = categorized_count / total_count if total_count > 0 else 0
    
    st.markdown("### 🎯 Categorization Progress")
    st.progress(progress)
    st.write(f"**Progress:** {categorized_count} of {total_count} transactions categorized ({progress:.1%})")
    
    # Current transaction
    current_transaction = transactions[current_idx]
    
    st.markdown("---")
    st.markdown("### 💳 Current Transaction")
    
    # Transaction details
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Date", current_transaction['Date'])
    with col2:
        st.metric("Amount", f"${current_transaction['Amount']:.2f}")
    with col3:
        st.metric("Type", current_transaction['Transaction_Type'])
    
    # Description (prominent display)
    st.markdown(f"**Description:** `{current_transaction['Description']}`")
    
    # Current category (if any)
    if current_transaction.get('category'):
        st.info(f"Current category: **{current_transaction['category']}**")
    
    # Category selection
    st.markdown("### 🏷️ Select Category")
    
    # Quick category buttons (most common categories)
    quick_categories = ["Groceries & Supermarkets", "Restaurants & Dining", "Gas & Fuel", "Entertainment", "Shopping", "Other"]
    
    st.markdown("**Quick Categories:**")
    cols = st.columns(3)
    for i, category in enumerate(quick_categories):
        with cols[i % 3]:
            if st.button(f"📌 {category}", key=f"quick_{category}_{current_idx}"):
                assign_category(current_transaction, category)
    
    # Full category dropdown
    selected_category = st.selectbox(
        "Or choose from all categories:",
        [""] + CATEGORY_OPTIONS,
        index=0,
        key=f"category_select_{current_idx}"
    )
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ Assign Category", disabled=not selected_category):
            if selected_category:
                assign_category(current_transaction, selected_category)
    
    with col2:
        if st.button("⏭️ Skip Transaction"):
            next_transaction()
    
    with col3:
        if st.button("⏮️ Previous Transaction", disabled=current_idx == 0):
            previous_transaction()
    
    with col4:
        if st.button("💾 Save Progress"):
            save_progress()
    
    # Navigation
    st.markdown("---")
    st.markdown("### 🧭 Navigation")
    
    # Transaction selector
    transaction_options = [
        f"{i+1}. {t['Date']} - {t['Description'][:50]}{'...' if len(t['Description']) > 50 else ''} - ${t['Amount']:.2f} {'✅' if t.get('category') else '⏳'}"
        for i, t in enumerate(transactions)
    ]
    
    selected_transaction = st.selectbox(
        "Jump to transaction:",
        range(len(transactions)),
        index=current_idx,
        format_func=lambda x: transaction_options[x],
        key="transaction_navigator"
    )
    
    if selected_transaction != current_idx:
        st.session_state.current_transaction_index = selected_transaction
        st.rerun()
    
    # Summary statistics
    show_categorization_summary(transactions)

def assign_category(transaction, category):
    """Assign a category to the current transaction and move to next"""
    transaction['category'] = category
    st.success(f"✅ Assigned '{category}' to transaction")
    
    # Move to next uncategorized transaction
    transactions = st.session_state.venmo_transactions
    current_idx = st.session_state.current_transaction_index
    
    # Find next uncategorized transaction
    for i in range(current_idx + 1, len(transactions)):
        if not transactions[i].get('category'):
            st.session_state.current_transaction_index = i
            st.rerun()
            return
    
    # If no more uncategorized transactions, go to next transaction
    if current_idx + 1 < len(transactions):
        st.session_state.current_transaction_index = current_idx + 1
    
    st.rerun()

def next_transaction():
    """Move to next transaction"""
    current_idx = st.session_state.current_transaction_index
    if current_idx + 1 < len(st.session_state.venmo_transactions):
        st.session_state.current_transaction_index = current_idx + 1
        st.rerun()

def previous_transaction():
    """Move to previous transaction"""
    current_idx = st.session_state.current_transaction_index
    if current_idx > 0:
        st.session_state.current_transaction_index = current_idx - 1
        st.rerun()

def save_progress():
    """Save current categorization progress"""
    transactions = st.session_state.venmo_transactions
    json_str = save_categorization_progress(transactions)
    
    if json_str:
        st.download_button(
            label="📥 Download Progress File",
            data=json_str,
            file_name=f"venmo_categorization_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        st.success("💾 Progress saved! Click the download button above.")

def show_categorization_summary(transactions):
    """Show summary of categorization progress"""
    st.markdown("---")
    st.markdown("### 📊 Categorization Summary")
    
    # Count by category
    category_counts = {}
    category_amounts = {}
    total_amount = 0
    
    for transaction in transactions:
        category = transaction.get('category', 'Uncategorized')
        amount = transaction['Amount']
        
        category_counts[category] = category_counts.get(category, 0) + 1
        category_amounts[category] = category_amounts.get(category, 0) + amount
        
        if category != 'Uncategorized':
            total_amount += amount
    
    # Display summary
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**By Count:**")
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(transactions)) * 100
            st.write(f"• {category}: {count} ({percentage:.1f}%)")
    
    with col2:
        st.markdown("**By Amount:**")
        for category, amount in sorted(category_amounts.items(), key=lambda x: x[1], reverse=True):
            if category != 'Uncategorized':
                percentage = (amount / total_amount) * 100 if total_amount > 0 else 0
                st.write(f"• {category}: ${amount:.2f} ({percentage:.1f}%)")

def show_completion_interface():
    """Show interface when categorization is complete"""
    st.markdown("### 🎉 Categorization Complete!")
    
    transactions = st.session_state.venmo_transactions
    categorized_count = sum(1 for t in transactions if t.get('category'))
    
    st.success(f"You have categorized {categorized_count} out of {len(transactions)} transactions!")
    
    # Final summary
    show_categorization_summary(transactions)
    
    # Export options
    st.markdown("---")
    st.markdown("### 📤 Export Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Export categorized transactions
        csv_string = export_categorized_transactions(transactions)
        if csv_string:
            st.download_button(
                label="📊 Download Categorized Transactions (CSV)",
                data=csv_string,
                file_name=f"venmo_categorized_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Save final progress
        json_str = save_categorization_progress(transactions)
        if json_str:
            st.download_button(
                label="💾 Download Final Progress File (JSON)",
                data=json_str,
                file_name=f"venmo_categorization_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Options to continue
    if st.button("🔄 Start New Categorization"):
        st.session_state.venmo_transactions = []
        st.session_state.current_transaction_index = 0
        st.session_state.categorization_mode = False
        st.rerun()
    
    if st.button("✏️ Review/Edit Categories"):
        st.session_state.current_transaction_index = 0
        st.rerun()
