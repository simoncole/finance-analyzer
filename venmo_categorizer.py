#!/usr/bin/env python3
"""
Interactive Venmo Transaction Categorizer
Allows manual categorization of Venmo transactions for financial analysis
"""

import pandas as pd
import json
import os
from datetime import datetime
import sys

# Define category options (matching the finance analyzer categories)
CATEGORIES = [
    "Housing",
    "Restaurants & Food", 
    "Coffee & Cafes",
    "Groceries & Supermarkets",
    "Transportation",
    "Gas & Fuel",
    "Travel & Entertainment",
    "Air Travel",
    "Tech & Software",
    "Education/Work",
    "Shopping/Merchandise",
    "Services",
    "Health & Medical",
    "Personal Care",
    "Gifts & Donations",
    "Utilities",
    "Insurance",
    "Banking & Fees",
    "Investment",
    "Income/Reimbursement",
    "Other"
]

class VenmoCategorizer:
    def __init__(self):
        self.categorized_data = {}
        self.progress_file = "venmo_categorization_progress.json"
        self.final_output_file = "venmo_categorized_transactions.csv"
        self.load_progress()
    
    def load_progress(self):
        """Load previously saved categorization progress"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r') as f:
                    self.categorized_data = json.load(f)
                print(f"📂 Loaded previous progress: {len(self.categorized_data)} transactions categorized")
            except Exception as e:
                print(f"⚠️ Error loading progress: {e}")
                self.categorized_data = {}
        else:
            print("🆕 Starting fresh categorization")
    
    def save_progress(self):
        """Save current categorization progress"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(self.categorized_data, f, indent=2)
            print(f"💾 Progress saved ({len(self.categorized_data)} transactions)")
        except Exception as e:
            print(f"❌ Error saving progress: {e}")
    
    def load_venmo_data(self, file_paths):
        """Load and clean Venmo CSV data from multiple files"""
        all_transactions = []
        
        for file_path in file_paths:
            print(f"📂 Loading {file_path}...")
            try:
                # Read CSV, skip the header rows that aren't data
                df = pd.read_csv(file_path, skiprows=2)
                
                # Clean up the data - remove empty rows and transfers
                df = df.dropna(subset=['ID'])
                df = df[df['Type'] == 'Payment']  # Only categorize payments, not transfers
                df = df[df['Status'] == 'Complete']  # Only completed transactions
                
                print(f"✅ Found {len(df)} payment transactions in {file_path}")
                all_transactions.append(df)
                
            except Exception as e:
                print(f"❌ Error loading {file_path}: {e}")
                continue
        
        if not all_transactions:
            print("❌ No valid transaction data found!")
            return pd.DataFrame()
        
        # Combine all transactions
        combined_df = pd.concat(all_transactions, ignore_index=True)
        
        # Convert datetime and sort
        combined_df['Datetime'] = pd.to_datetime(combined_df['Datetime'])
        combined_df = combined_df.sort_values('Datetime')
        
        # Clean amount column (remove $ and convert to float)
        combined_df['Amount_Clean'] = combined_df['Amount (total)'].str.replace('$', '').str.replace('+', '').str.replace(' ', '').astype(float)
        
        print(f"📊 Total transactions to categorize: {len(combined_df)}")
        return combined_df
    
    def display_transaction(self, transaction):
        """Display transaction details in a clear format"""
        print("\n" + "="*60)
        print("💳 TRANSACTION DETAILS")
        print("="*60)
        
        # Parse transaction details
        date = pd.to_datetime(transaction['Datetime']).strftime('%Y-%m-%d %H:%M')
        amount = transaction['Amount_Clean']
        note = transaction['Note'] if pd.notna(transaction['Note']) else "No note"
        from_person = transaction['From'] if pd.notna(transaction['From']) else "Unknown"
        to_person = transaction['To'] if pd.notna(transaction['To']) else "Unknown"
        
        # Determine if this is income or expense for Simon
        if to_person == "Simon Cole":
            direction = "💰 INCOMING"
            other_party = from_person
            amount_display = f"+${abs(amount):.2f}"
        else:
            direction = "💸 OUTGOING"  
            other_party = to_person
            amount_display = f"-${abs(amount):.2f}"
        
        print(f"📅 Date: {date}")
        print(f"💵 Amount: {amount_display}")
        print(f"📝 Note: {note}")
        print(f"👤 {direction} - Other party: {other_party}")
        print(f"🆔 Transaction ID: {transaction['ID']}")
    
    def display_categories(self):
        """Display category options"""
        print("\n" + "📂 CATEGORY OPTIONS")
        print("-" * 40)
        
        # Display in two columns for better readability
        for i, category in enumerate(CATEGORIES, 1):
            if i <= len(CATEGORIES)//2:
                left_category = f"{i:2d}. {category}"
                right_index = i + len(CATEGORIES)//2
                if right_index <= len(CATEGORIES):
                    right_category = f"{right_index:2d}. {CATEGORIES[right_index-1]}"
                    print(f"{left_category:<35} {right_category}")
                else:
                    print(left_category)
    
    def get_user_choice(self, transaction):
        """Get user's category choice for a transaction"""
        while True:
            self.display_categories()
            print(f"\n📌 Special options:")
            print(f"{len(CATEGORIES)+1:2d}. Skip this transaction")
            print(f"{len(CATEGORIES)+2:2d}. Save progress and exit")
            print(f"{len(CATEGORIES)+3:2d}. Show transaction details again")
            
            try:
                choice = input(f"\n👉 Enter category number (1-{len(CATEGORIES)+3}): ").strip()
                
                if not choice:
                    print("⚠️ Please enter a number")
                    continue
                
                choice_num = int(choice)
                
                if 1 <= choice_num <= len(CATEGORIES):
                    selected_category = CATEGORIES[choice_num - 1]
                    confirm = input(f"✅ Confirm categorization as '{selected_category}'? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return selected_category
                    else:
                        print("🔄 Let's try again...")
                        continue
                
                elif choice_num == len(CATEGORIES) + 1:  # Skip
                    return "SKIP"
                
                elif choice_num == len(CATEGORIES) + 2:  # Save and exit
                    return "EXIT"
                
                elif choice_num == len(CATEGORIES) + 3:  # Show details again
                    self.display_transaction(transaction)
                    continue
                
                else:
                    print(f"⚠️ Please enter a number between 1 and {len(CATEGORIES)+3}")
                    
            except ValueError:
                print("⚠️ Please enter a valid number")
            except KeyboardInterrupt:
                print("\n\n🛑 Interrupted by user")
                return "EXIT"
    
    def categorize_transactions(self, df):
        """Main categorization loop"""
        if df.empty:
            print("❌ No transactions to categorize!")
            return
        
        total_transactions = len(df)
        already_categorized = len(self.categorized_data)
        
        print(f"\n🚀 STARTING CATEGORIZATION")
        print(f"📊 Total transactions: {total_transactions}")
        print(f"✅ Already categorized: {already_categorized}")
        print(f"🎯 Remaining: {total_transactions - already_categorized}")
        print(f"\n💡 Tips:")
        print(f"   - Use the transaction note and other party to determine category")
        print(f"   - You can skip transactions and come back to them later")
        print(f"   - Progress is automatically saved")
        
        skipped_count = 0
        
        for index, transaction in df.iterrows():
            transaction_id = str(transaction['ID'])
            
            # Skip if already categorized
            if transaction_id in self.categorized_data:
                continue
            
            # Display progress
            current_position = len(self.categorized_data) + skipped_count + 1
            print(f"\n🔢 Transaction {current_position} of {total_transactions}")
            
            # Show transaction details
            self.display_transaction(transaction)
            
            # Get user choice
            category = self.get_user_choice(transaction)
            
            if category == "EXIT":
                print("\n💾 Saving progress and exiting...")
                self.save_progress()
                return
            
            elif category == "SKIP":
                print("⏭️ Skipping transaction")
                skipped_count += 1
                continue
            
            else:
                # Save categorization
                self.categorized_data[transaction_id] = {
                    'category': category,
                    'date': transaction['Datetime'].isoformat() if pd.notna(transaction['Datetime']) else '',
                    'amount': transaction['Amount_Clean'],
                    'note': transaction['Note'] if pd.notna(transaction['Note']) else '',
                    'from': transaction['From'] if pd.notna(transaction['From']) else '',
                    'to': transaction['To'] if pd.notna(transaction['To']) else '',
                    'categorized_at': datetime.now().isoformat()
                }
                
                print(f"✅ Categorized as: {category}")
                
                # Auto-save progress every 5 transactions
                if len(self.categorized_data) % 5 == 0:
                    self.save_progress()
        
        print(f"\n🎉 Categorization complete!")
        print(f"📊 Total categorized: {len(self.categorized_data)}")
        if skipped_count > 0:
            print(f"⏭️ Skipped: {skipped_count}")
        
        self.save_progress()
        self.export_final_data(df)
    
    def export_final_data(self, original_df):
        """Export categorized data to CSV"""
        print(f"\n📁 Exporting categorized data...")
        
        # Create a list to store the final data
        final_data = []
        
        for index, transaction in original_df.iterrows():
            transaction_id = str(transaction['ID'])
            
            # Get category if it exists
            if transaction_id in self.categorized_data:
                category = self.categorized_data[transaction_id]['category']
            else:
                category = "Uncategorized"
            
            # Determine transaction type for Simon
            if transaction['To'] == "Simon Cole":
                transaction_type = "Income"
                amount = abs(transaction['Amount_Clean'])
                other_party = transaction['From']
            else:
                transaction_type = "Expense"
                amount = -abs(transaction['Amount_Clean'])  # Negative for expenses
                other_party = transaction['To']
            
            final_data.append({
                'Date': pd.to_datetime(transaction['Datetime']).strftime('%Y-%m-%d'),
                'Description': transaction['Note'] if pd.notna(transaction['Note']) else f"Venmo - {other_party}",
                'Amount': amount,
                'Category': category,
                'Other_Party': other_party,
                'Transaction_Type': transaction_type,
                'Source': 'Venmo',
                'Original_ID': transaction['ID']
            })
        
        # Create DataFrame and save
        final_df = pd.DataFrame(final_data)
        final_df.to_csv(self.final_output_file, index=False)
        
        print(f"✅ Exported {len(final_df)} transactions to {self.final_output_file}")
        
        # Show summary stats
        categorized_count = len([t for t in final_data if t['Category'] != 'Uncategorized'])
        expense_total = sum([t['Amount'] for t in final_data if t['Transaction_Type'] == 'Expense'])
        income_total = sum([t['Amount'] for t in final_data if t['Transaction_Type'] == 'Income'])
        
        print(f"\n📊 SUMMARY:")
        print(f"✅ Categorized: {categorized_count}/{len(final_df)} transactions")
        print(f"💸 Total Expenses: ${abs(expense_total):.2f}")
        print(f"💰 Total Income: ${income_total:.2f}")
        print(f"📈 Net: ${income_total + expense_total:.2f}")


def main():
    """Main function"""
    print("🚀 VENMO TRANSACTION CATEGORIZER")
    print("="*50)
    
    # File paths
    venmo_files = [
        "VenmoStatement_May_2025.csv",
        "VenmoStatement_Jun_2025.csv"
    ]
    
    # Check if files exist
    missing_files = [f for f in venmo_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        print("📁 Please ensure all Venmo CSV files are in the current directory")
        return
    
    # Initialize categorizer
    categorizer = VenmoCategorizer()
    
    # Load data
    df = categorizer.load_venmo_data(venmo_files)
    if df.empty:
        return
    
    # Start categorization
    categorizer.categorize_transactions(df)
    
    print(f"\n✨ Categorization session complete!")
    print(f"📁 Files created:")
    print(f"   - {categorizer.progress_file} (progress backup)")
    print(f"   - {categorizer.final_output_file} (final categorized data)")


if __name__ == "__main__":
    main() 