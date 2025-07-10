"""
Category management utilities for the Personal Finance Analyzer web app
"""

import pandas as pd
import streamlit as st
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_all_categories(df):
    """Get all unique categories from the dataset"""
    return sorted(df['Enhanced_Category'].unique().tolist())

def get_category_summary(df):
    """Get summary statistics for each category"""
    try:
        summary = df.groupby('Enhanced_Category').agg({
            'Amount': ['sum', 'count', 'mean'],
            'Description': lambda x: list(x.unique())[:5]  # Sample descriptions
        }).round(2)
        
        # Flatten column names
        summary.columns = ['Total_Amount', 'Transaction_Count', 'Avg_Amount', 'Sample_Descriptions']
        summary = summary.sort_values('Total_Amount', ascending=False)
        
        return summary
    except Exception as e:
        st.error(f"Error creating category summary: {str(e)}")
        return None

def show_category_overview(df):
    """Display an overview of all categories with key statistics"""
    st.markdown("### 📊 Category Overview")
    
    summary = get_category_summary(df)
    if summary is None:
        return
    
    # Display as an interactive table
    st.dataframe(
        summary.style.format({
            'Total_Amount': '${:,.2f}',
            'Avg_Amount': '${:,.2f}',
            'Transaction_Count': '{:,}'
        }),
        use_container_width=True,
        height=400
    )
    
    # Category insights
    col1, col2, col3 = st.columns(3)
    
    with col1:
        top_category = summary.index[0]
        top_amount = summary.loc[top_category, 'Total_Amount']
        st.metric("Top Spending Category", top_category, f"${top_amount:,.2f}")
    
    with col2:
        total_categories = len(summary)
        positive_spending = len(summary[summary['Total_Amount'] > 0])
        st.metric("Total Categories", total_categories, f"{positive_spending} with expenses")
    
    with col3:
        avg_per_category = summary['Total_Amount'].mean()
        st.metric("Average per Category", f"${avg_per_category:,.2f}")

def show_transaction_editor(df):
    """Show interface for editing individual transaction categories"""
    st.markdown("### ✏️ Edit Transaction Categories")
    
    # Filters for finding transactions
    col1, col2 = st.columns(2)
    
    with col1:
        # Category filter
        current_categories = get_all_categories(df)
        selected_category = st.selectbox(
            "Filter by Current Category",
            ["All Categories"] + current_categories,
            key="category_filter"
        )
    
    with col2:
        # Amount range filter
        min_amount = float(df['Amount'].min())
        max_amount = float(df['Amount'].max())
        amount_range = st.slider(
            "Amount Range",
            min_value=min_amount,
            max_value=max_amount,
            value=(min_amount, max_amount),
            key="amount_filter"
        )
    
    # Text search
    search_text = st.text_input(
        "Search Descriptions",
        placeholder="Enter keywords to search transaction descriptions...",
        key="description_search"
    )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_category != "All Categories":
        filtered_df = filtered_df[filtered_df['Enhanced_Category'] == selected_category]
    
    filtered_df = filtered_df[
        (filtered_df['Amount'] >= amount_range[0]) & 
        (filtered_df['Amount'] <= amount_range[1])
    ]
    
    if search_text:
        filtered_df = filtered_df[
            filtered_df['Description'].str.contains(search_text, case=False, na=False)
        ]
    
    st.write(f"**{len(filtered_df)} transactions found**")
    
    if len(filtered_df) > 0:
        # Show transactions in batches
        batch_size = 10
        total_batches = (len(filtered_df) - 1) // batch_size + 1
        
        if total_batches > 1:
            batch_num = st.selectbox(
                "Select Batch",
                range(1, total_batches + 1),
                format_func=lambda x: f"Batch {x} (rows {(x-1)*batch_size + 1}-{min(x*batch_size, len(filtered_df))})"
            )
            start_idx = (batch_num - 1) * batch_size
            end_idx = min(batch_num * batch_size, len(filtered_df))
            batch_df = filtered_df.iloc[start_idx:end_idx]
        else:
            batch_df = filtered_df
        
        # Display transactions for editing
        for idx, row in batch_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{row['Trans. Date'].strftime('%Y-%m-%d')}**")
                    st.write(f"${row['Amount']:.2f}")
                
                with col2:
                    st.write(f"**Description:**")
                    st.write(row['Description'])
                
                with col3:
                    st.write(f"**Current Category:**")
                    st.write(row['Enhanced_Category'])
                    
                    # Category selector for this transaction
                    new_category = st.selectbox(
                        "New Category",
                        current_categories,
                        index=current_categories.index(row['Enhanced_Category']),
                        key=f"category_select_{idx}"
                    )
                
                with col4:
                    if st.button("Update", key=f"update_{idx}"):
                        # Update the category in session state
                        if 'combined_data' in st.session_state:
                            st.session_state.combined_data.loc[idx, 'Enhanced_Category'] = new_category
                            st.success(f"Updated to {new_category}")
                            st.rerun()
                
                st.markdown("---")

def show_bulk_category_editor(df):
    """Show interface for bulk category editing"""
    st.markdown("### 🔄 Bulk Category Changes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Find and Replace Categories**")
        
        current_categories = get_all_categories(df)
        from_category = st.selectbox("From Category", current_categories, key="bulk_from")
        to_category = st.selectbox("To Category", current_categories, key="bulk_to")
        
        # Preview how many transactions would be affected
        affected_count = len(df[df['Enhanced_Category'] == from_category])
        st.info(f"This will affect {affected_count} transactions")
        
        if st.button("Apply Bulk Change", type="primary"):
            if from_category != to_category:
                # Apply the change
                if 'combined_data' in st.session_state:
                    st.session_state.combined_data.loc[
                        st.session_state.combined_data['Enhanced_Category'] == from_category, 
                        'Enhanced_Category'
                    ] = to_category
                    st.success(f"Changed {affected_count} transactions from '{from_category}' to '{to_category}'")
                    st.rerun()
            else:
                st.warning("Please select different categories")
    
    with col2:
        st.markdown("**Category Merging**")
        
        # Multi-select for categories to merge
        categories_to_merge = st.multiselect(
            "Select Categories to Merge",
            current_categories,
            key="merge_categories"
        )
        
        if len(categories_to_merge) > 1:
            merge_into = st.selectbox(
                "Merge Into Category",
                categories_to_merge,
                key="merge_target"
            )
            
            # Preview
            total_affected = len(df[df['Enhanced_Category'].isin(categories_to_merge)])
            st.info(f"This will merge {len(categories_to_merge)} categories affecting {total_affected} transactions")
            
            if st.button("Merge Categories", type="primary"):
                # Apply the merge
                if 'combined_data' in st.session_state:
                    for cat in categories_to_merge:
                        if cat != merge_into:
                            st.session_state.combined_data.loc[
                                st.session_state.combined_data['Enhanced_Category'] == cat,
                                'Enhanced_Category'
                            ] = merge_into
                    st.success(f"Merged categories into '{merge_into}'")
                    st.rerun()

def create_new_category_rule(df):
    """Create new categorization rules based on description patterns"""
    st.markdown("### 🆕 Create New Category Rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Pattern-Based Categorization**")
        
        # Pattern input
        description_pattern = st.text_input(
            "Description Pattern",
            placeholder="e.g., STARBUCKS, AMAZON, UBER",
            help="Enter keywords or patterns to match in transaction descriptions"
        )
        
        # Category selection
        current_categories = get_all_categories(df)
        target_category = st.selectbox("Assign to Category", current_categories)
        
        # Case sensitivity option
        case_sensitive = st.checkbox("Case Sensitive", value=False)
        
        if description_pattern:
            # Preview matches
            if case_sensitive:
                matches = df[df['Description'].str.contains(description_pattern, na=False)]
            else:
                matches = df[df['Description'].str.contains(description_pattern, case=False, na=False)]
            
            st.info(f"This pattern would match {len(matches)} transactions")
            
            if len(matches) > 0:
                st.markdown("**Preview of matches:**")
                preview_df = matches[['Trans. Date', 'Description', 'Amount', 'Enhanced_Category']].head(5)
                st.dataframe(preview_df, use_container_width=True)
        
        if st.button("Apply Rule", type="primary") and description_pattern:
            # Apply the rule
            if 'combined_data' in st.session_state:
                if case_sensitive:
                    mask = st.session_state.combined_data['Description'].str.contains(description_pattern, na=False)
                else:
                    mask = st.session_state.combined_data['Description'].str.contains(description_pattern, case=False, na=False)
                
                affected_count = mask.sum()
                st.session_state.combined_data.loc[mask, 'Enhanced_Category'] = target_category
                st.success(f"Applied rule to {affected_count} transactions")
                st.rerun()
    
    with col2:
        st.markdown("**Quick Category Assignment**")
        
        # Show uncategorized or miscategorized transactions
        uncategorized_df = df[df['Enhanced_Category'].isin(['Other', 'Miscellaneous', 'Unknown'])]
        
        if len(uncategorized_df) > 0:
            st.info(f"Found {len(uncategorized_df)} transactions that might need better categories")
            
            # Show a sample
            sample_transaction = uncategorized_df.iloc[0] if len(uncategorized_df) > 0 else None
            
            if sample_transaction is not None:
                st.markdown("**Sample uncategorized transaction:**")
                st.write(f"**Date:** {sample_transaction['Trans. Date'].strftime('%Y-%m-%d')}")
                st.write(f"**Description:** {sample_transaction['Description']}")
                st.write(f"**Amount:** ${sample_transaction['Amount']:.2f}")
                st.write(f"**Current Category:** {sample_transaction['Enhanced_Category']}")
                
                # Quick category assignment
                new_cat = st.selectbox("Quick Assign Category", current_categories, key="quick_assign")
                
                if st.button("Assign Category", key="quick_assign_btn"):
                    idx = sample_transaction.name
                    if 'combined_data' in st.session_state:
                        st.session_state.combined_data.loc[idx, 'Enhanced_Category'] = new_cat
                        st.success(f"Assigned to {new_cat}")
                        st.rerun()

def export_category_mapping(df):
    """Export current category mapping for backup/reference"""
    st.markdown("### 💾 Export Category Mapping")
    
    # Create category mapping summary
    category_map = df.groupby(['Description', 'Enhanced_Category']).size().reset_index(name='Count')
    category_map = category_map.sort_values(['Enhanced_Category', 'Count'], ascending=[True, False])
    
    # Convert to CSV string
    csv_string = category_map.to_csv(index=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Download button
        st.download_button(
            label="📥 Download Category Mapping",
            data=csv_string,
            file_name=f"category_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            help="Download a CSV file with current category assignments"
        )
    
    with col2:
        # Show preview
        st.markdown("**Preview:**")
        st.dataframe(category_map.head(10), use_container_width=True)

def show_category_manager(df):
    """Main category management interface"""
    st.markdown('<div class="section-header">🏷️ Category Management</div>', unsafe_allow_html=True)
    
    # Create tabs for different category management functions
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "✏️ Edit Individual", 
        "🔄 Bulk Changes", 
        "🆕 New Rules", 
        "💾 Export"
    ])
    
    with tab1:
        show_category_overview(df)
    
    with tab2:
        show_transaction_editor(df)
    
    with tab3:
        show_bulk_category_editor(df)
    
    with tab4:
        create_new_category_rule(df)
    
    with tab5:
        export_category_mapping(df) 