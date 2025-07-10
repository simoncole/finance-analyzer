import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import os
import sys

# Add the parent directory to the path to import our existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our existing functions
from finance_analyzer import (
    load_and_clean_data,
    enhanced_categorization,
    spending_insights,
    create_spending_dashboard,
    internship_analysis
)

# Import our web app specific data processing utilities
from data_processor import (
    process_discover_data,
    process_venmo_data,
    combine_datasets,
    calculate_basic_metrics,
    get_category_summary
)

# Import visualization and analysis modules
from visualizations import (
    create_spending_pie_chart,
    create_spending_bar_chart,
    create_monthly_trend_chart,
    create_daily_spending_chart,
    create_transaction_size_distribution,
    create_category_trend_chart,
    create_income_vs_expenses_chart
)

from insights import show_spending_insights
from category_manager import show_category_manager

# Import Phase 3 advanced features
from internship_analysis import show_internship_analysis_page
from venmo_categorizer_web import show_venmo_categorizer
from report_generator import show_report_generator

# Import Phase 3 advanced features
from internship_analysis import show_internship_analysis_page
from venmo_categorizer_web import show_venmo_categorizer
from report_generator import show_report_generator

# Page configuration
st.set_page_config(
    page_title="Personal Finance Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced styling and UX
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
    }
    
    .section-header {
        font-size: 1.8rem;
        color: #ff7f0e;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
        background: linear-gradient(90deg, #ff7f0e, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Enhanced cards */
    .metric-card {
        background: linear-gradient(145deg, #f0f2f6, #e1e5e9);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Enhanced upload area */
    .upload-box {
        border: 3px dashed #1f77b4;
        border-radius: 15px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
        background: linear-gradient(145deg, #f8f9fa, #e9ecef);
        transition: all 0.3s ease;
    }
    
    .upload-box:hover {
        border-color: #ff7f0e;
        background: linear-gradient(145deg, #fff3cd, #ffeaa7);
    }
    
    /* Status indicators */
    .status-success {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .status-warning {
        background: linear-gradient(90deg, #ffc107, #fd7e14);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .status-info {
        background: linear-gradient(90deg, #17a2b8, #6f42c1);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    /* Navigation improvements */
    .nav-button {
        width: 100%;
        margin: 0.25rem 0;
        border-radius: 10px;
        border: none;
        padding: 0.75rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    /* Loading animations */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        border-top-color: #1f77b4;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Progress bars */
    .progress-container {
        background-color: #e9ecef;
        border-radius: 10px;
        padding: 3px;
        margin: 1rem 0;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        height: 20px;
        border-radius: 8px;
        transition: width 0.5s ease;
    }
    
    /* Enhanced tables */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Responsive design improvements */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
        .section-header {
            font-size: 1.5rem;
        }
        .metric-card {
            padding: 1rem;
        }
    }
    
    /* Accessibility improvements */
    button:focus {
        outline: 3px solid #1f77b4;
        outline-offset: 2px;
    }
    
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    """Initialize session state variables"""
    if 'discover_data' not in st.session_state:
        st.session_state.discover_data = None
    if 'venmo_data' not in st.session_state:
        st.session_state.venmo_data = None
    if 'combined_data' not in st.session_state:
        st.session_state.combined_data = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False

# Navigation sidebar
def create_sidebar():
    """Create the navigation sidebar"""
    st.sidebar.markdown("## 🧭 Navigation")
    
    pages = {
        "🏠 Home": "Home",
        "📂 Data Upload": "Upload", 
        "💸 Venmo Categorizer": "Venmo",
        "📊 Financial Analysis": "Analysis",
        "💼 Internship Analysis": "Internship",
        "📄 Reports": "Reports"
    }
    
    # Create navigation buttons
    for page_name, page_key in pages.items():
        if st.sidebar.button(page_name, key=f"nav_{page_key}"):
            st.session_state.current_page = page_key
    
    # Data status indicator
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 📊 Data Status")
    
    if st.session_state.data_loaded:
        st.sidebar.success("✅ Data Loaded")
        if st.session_state.discover_data is not None:
            discover_count = len(st.session_state.discover_data)
            st.sidebar.info(f"Discover: {discover_count} transactions")
        if st.session_state.venmo_data is not None:
            venmo_count = len(st.session_state.venmo_data)  
            st.sidebar.info(f"Venmo: {venmo_count} transactions")
    else:
        st.sidebar.warning("⚠️ No Data Loaded")
        st.sidebar.info("Upload data files to get started")

# Page functions
def show_home_page():
    """Display the home/dashboard page"""
    st.markdown('<h1 class="main-header">💰 Personal Finance Analyzer</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Welcome to your Personal Finance Dashboard!
    
    This application helps you analyze your spending patterns, track your budget, and gain insights into your financial habits.
    """)
    
    # Quick overview cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📂 Data Sources", "Discover + Venmo")
        st.markdown("Upload your CSV files to get started")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("📊 Analysis Types", "Multiple Views")
        st.markdown("Category breakdown, trends, budgets")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("💼 Special Features", "Internship Tracking")
        st.markdown("Budget burndown and projections")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick stats if data is loaded
    if st.session_state.data_loaded and st.session_state.combined_data is not None:
        st.markdown('<div class="section-header">📈 Quick Stats</div>', unsafe_allow_html=True)
        
        df = st.session_state.combined_data
        
        # Calculate basic metrics
        expenses = df[df['Amount'] > 0]
        income = df[(df['Amount'] < 0) & 
                   (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))]
        
        total_expenses = expenses['Amount'].sum()
        total_income = abs(income['Amount'].sum())
        net_spending = total_expenses - total_income
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Expenses", f"${total_expenses:,.2f}")
        with col2:
            st.metric("Total Income", f"${total_income:,.2f}")
        with col3:
            st.metric("Net Spending", f"${net_spending:,.2f}")
        with col4:
            st.metric("Transactions", len(df))
    
    # Getting started section
    if not st.session_state.data_loaded:
        st.markdown('<div class="section-header">🚀 Getting Started</div>', unsafe_allow_html=True)
        st.markdown("""
        **Phase 3 Features Now Available!** 🎉
        
        1. **📂 Upload Data**: Go to the Data Upload page and upload your Discover and Venmo CSV files
        2. **💸 Categorize Venmo**: Use the interactive Venmo Categorizer to classify your transactions
        3. **📊 Analyze**: View comprehensive spending patterns and AI-powered insights on the Analysis page
        4. **💼 Track Budget**: Use advanced Internship Analysis with burndown charts and projections
        5. **📄 Generate Reports**: Create and download professional PDF reports with charts and insights
        """)
        
        # Feature highlights
        st.markdown("### ✨ New Advanced Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **💸 Smart Venmo Categorizer**
            - Interactive transaction review
            - Progress tracking & saving
            - Bulk categorization options
            - Export ready data
            """)
        
        with col2:
            st.markdown("""
            **💼 Advanced Budget Tracking**
            - Real-time burndown charts
            - Spending projections
            - Daily rate monitoring
            - Surplus/deficit predictions
            """)
        
        with col3:
            st.markdown("""
            **📊 Professional Reports**
            - PDF report generation
            - Custom date ranges
            - AI-powered insights
            - Multiple export formats
            """)
    else:
        # Show feature overview for loaded data
        st.markdown('<div class="section-header">🎯 Available Actions</div>', unsafe_allow_html=True)
        
        # Action cards
        action_cols = st.columns(4)
        
        with action_cols[0]:
            if st.button("💸 Categorize Venmo", key="quick_venmo", help="Interactively categorize Venmo transactions"):
                st.session_state.current_page = "Venmo"
                st.rerun()
        
        with action_cols[1]:
            if st.button("📊 Analyze Data", key="quick_analysis", help="View comprehensive financial analysis"):
                st.session_state.current_page = "Analysis"
                st.rerun()
        
        with action_cols[2]:
            if st.button("💼 Budget Tracker", key="quick_internship", help="Track internship budget with projections"):
                st.session_state.current_page = "Internship"
                st.rerun()
        
        with action_cols[3]:
            if st.button("📄 Generate Report", key="quick_reports", help="Create professional financial reports"):
                st.session_state.current_page = "Reports"
                st.rerun()
        
        if st.button("🚀 Get Started - Upload Data", type="primary"):
            st.session_state.current_page = "Upload"
            st.rerun()

def show_upload_page():
    """Display the data upload page"""
    st.markdown('<h1 class="main-header">📂 Data Upload & Management</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    Upload your financial data files to start analyzing your spending patterns.
    """)
    
    # Discover file upload
    st.markdown('<div class="section-header">💳 Discover Credit Card Data</div>', unsafe_allow_html=True)
    
    discover_file = st.file_uploader(
        "Upload Discover CSV file",
        type=['csv'],
        key="discover_upload",
        help="Download your transaction history from Discover's website"
    )
    
    if discover_file is not None:
        try:
            # Load and validate the Discover data
            df_discover = pd.read_csv(discover_file)
            
            # Validate columns
            required_columns = ['Trans. Date', 'Description', 'Amount', 'Category']
            if all(col in df_discover.columns for col in required_columns):
                st.success(f"✅ Discover file loaded successfully! ({len(df_discover)} transactions)")
                
                # Show preview
                st.markdown("**Preview:**")
                st.dataframe(df_discover.head(), use_container_width=True)
                
                # Store raw data in session state
                st.session_state.discover_data = df_discover
                
            else:
                st.error(f"❌ Invalid file format. Required columns: {required_columns}")
                
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    # Venmo file upload
    st.markdown('<div class="section-header">💸 Venmo Transaction Data</div>', unsafe_allow_html=True)
    
    venmo_file = st.file_uploader(
        "Upload Venmo categorized transactions CSV",
        type=['csv'],
        key="venmo_upload", 
        help="Upload your categorized Venmo transactions file"
    )
    
    if venmo_file is not None:
        try:
            # Load and validate the Venmo data
            df_venmo = pd.read_csv(venmo_file)
            
            # Validate columns
            required_columns = ['Date', 'Description', 'Amount', 'Category']
            if all(col in df_venmo.columns for col in required_columns):
                st.success(f"✅ Venmo file loaded successfully! ({len(df_venmo)} transactions)")
                
                # Show preview
                st.markdown("**Preview:**")
                st.dataframe(df_venmo.head(), use_container_width=True)
                
                # Store in session state
                st.session_state.venmo_data = df_venmo
                
            else:
                st.error(f"❌ Invalid file format. Required columns: {required_columns}")
                
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
    
    # Process data button
    if st.session_state.discover_data is not None:
        st.markdown('<div class="section-header">⚙️ Process Data</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date (optional)", value=None)
        with col2:
            end_date = st.date_input("End Date (optional)", value=None)
        
        if st.button("🔄 Process & Combine Data", type="primary"):
            with st.spinner("Processing data..."):
                try:
                    # Process Discover data
                    processed_discover = process_discover_data(
                        st.session_state.discover_data,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if processed_discover is None:
                        st.error("❌ Failed to process Discover data")
                        return
                    
                    # Process Venmo data if available
                    processed_venmo = None
                    if st.session_state.venmo_data is not None:
                        processed_venmo = process_venmo_data(
                            st.session_state.venmo_data,
                            start_date=start_date,
                            end_date=end_date
                        )
                    
                    # Combine datasets
                    combined_df = combine_datasets(processed_discover, processed_venmo)
                    
                    # Calculate basic metrics
                    metrics = calculate_basic_metrics(combined_df)
                    
                    # Store processed data and metrics
                    st.session_state.combined_data = combined_df
                    st.session_state.metrics = metrics
                    st.session_state.data_loaded = True
                    
                    # Display success message with summary
                    st.success("✅ Data processed successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Transactions", metrics['total_transactions'])
                    with col2:
                        st.metric("Date Range", metrics['date_range'])
                    with col3:
                        st.metric("Net Spending", f"${metrics['net_spending']:,.2f}")
                    
                    st.info("📊 Ready for analysis! Go to the Financial Analysis page.")
                    
                except Exception as e:
                    st.error(f"❌ Error processing data: {str(e)}")
                    st.exception(e)  # Show full traceback for debugging

def show_analysis_page():
    """Display the financial analysis page"""
    st.markdown('<h1 class="main-header">📊 Financial Analysis</h1>', unsafe_allow_html=True)
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload and process data first!")
        if st.button("📂 Go to Data Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    df = st.session_state.combined_data
    
    # Sidebar filters
    st.sidebar.markdown("## 🔍 Filters")
    
    # Date range filter
    min_date = df['Trans. Date'].min().date()
    max_date = df['Trans. Date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Category filter
    all_categories = sorted(df['Enhanced_Category'].unique())
    selected_categories = st.sidebar.multiselect(
        "Categories",
        all_categories,
        default=all_categories
    )
    
    # Amount filter
    min_amount = float(df['Amount'].min())
    max_amount = float(df['Amount'].max())
    amount_range = st.sidebar.slider(
        "Amount Range ($)",
        min_value=min_amount,
        max_value=max_amount,
        value=(min_amount, max_amount)
    )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['Trans. Date'].dt.date >= start_date) &
            (filtered_df['Trans. Date'].dt.date <= end_date)
        ]
    
    # Category filter
    if selected_categories:
        filtered_df = filtered_df[filtered_df['Enhanced_Category'].isin(selected_categories)]
    
    # Amount filter
    filtered_df = filtered_df[
        (filtered_df['Amount'] >= amount_range[0]) &
        (filtered_df['Amount'] <= amount_range[1])
    ]
    
    # Show filtered data info
    if len(filtered_df) != len(df):
        st.info(f"📊 Showing {len(filtered_df)} of {len(df)} transactions after filtering")
    
    # Main analysis tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "📈 Visualizations", 
        "🔍 Insights", 
        "🏷️ Categories", 
        "📋 Transaction Details"
    ])
    
    with tab1:
        show_analysis_overview(filtered_df)
    
    with tab2:
        show_analysis_visualizations(filtered_df)
    
    with tab3:
        show_spending_insights(filtered_df)
    
    with tab4:
        show_category_manager(filtered_df)
    
    with tab5:
        show_transaction_details(filtered_df)

def show_analysis_overview(df):
    """Show overview analytics and key metrics"""
    st.markdown("### 📊 Financial Overview")
    
    # Calculate key metrics
    expenses = df[df['Amount'] > 0]
    income = df[(df['Amount'] < 0) & 
               (~df['Description'].str.contains('INTERNET PAYMENT|PAYMENT - THANK YOU|DIRECTPAY', case=False, na=False))]
    
    total_expenses = expenses['Amount'].sum()
    total_income = abs(income['Amount'].sum())
    net_spending = total_expenses - total_income
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    with col2:
        st.metric("Total Income", f"${total_income:,.2f}")
    with col3:
        st.metric("Net Spending", f"${net_spending:,.2f}")
    with col4:
        st.metric("Transactions", len(df))
    
    # Quick pie chart
    st.markdown("### 🥧 Quick Category Breakdown")
    fig = create_spending_pie_chart(df, "Spending by Category")
    if fig:
        st.plotly_chart(fig, use_container_width=True, key="overview_pie_chart")
    
    # Top transactions
    st.markdown("### 💰 Largest Transactions")
    largest_transactions = expenses.nlargest(10, 'Amount')[['Trans. Date', 'Description', 'Amount', 'Enhanced_Category']]
    st.dataframe(largest_transactions, use_container_width=True)

def show_analysis_visualizations(df):
    """Show all interactive visualizations"""
    st.markdown("### 📈 Interactive Visualizations")
    
    # Visualization selection
    viz_options = [
        "Spending Pie Chart",
        "Category Bar Chart", 
        "Monthly Trends",
        "Daily Spending Patterns",
        "Transaction Size Distribution",
        "Category Trends Over Time",
        "Income vs Expenses"
    ]
    
    selected_viz = st.selectbox("Select Visualization", viz_options)
    
    # Display selected visualization
    if selected_viz == "Spending Pie Chart":
        fig = create_spending_pie_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="viz_pie_chart")
    
    elif selected_viz == "Category Bar Chart":
        fig = create_spending_bar_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="viz_bar_chart")
    
    elif selected_viz == "Monthly Trends":
        fig = create_monthly_trend_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="viz_monthly_trends")
    
    elif selected_viz == "Daily Spending Patterns":
        fig = create_daily_spending_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="viz_daily_patterns")
    
    elif selected_viz == "Transaction Size Distribution":
        fig = create_transaction_size_distribution(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="viz_transaction_distribution")
    
    elif selected_viz == "Category Trends Over Time":
        # Category selection for trends
        all_categories = sorted(df['Enhanced_Category'].unique())
        selected_cats = st.multiselect(
            "Select Categories for Trend Analysis",
            all_categories,
            default=all_categories[:5]  # Default to top 5
        )
        
        if selected_cats:
            fig = create_category_trend_chart(df, selected_cats)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="viz_category_trends")
    
    elif selected_viz == "Income vs Expenses":
        fig = create_income_vs_expenses_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True, key="viz_income_expenses")
    
    # Show all charts option
    if st.checkbox("Show All Charts", key="show_all_charts"):
        st.markdown("---")
        st.markdown("### 📊 All Visualizations")
        
        # Create all charts
        charts = [
            ("Spending by Category", create_spending_pie_chart(df), "all_pie_chart"),
            ("Category Bar Chart", create_spending_bar_chart(df), "all_bar_chart"),
            ("Monthly Trends", create_monthly_trend_chart(df), "all_monthly_trends"),
            ("Daily Patterns", create_daily_spending_chart(df), "all_daily_patterns"),
            ("Transaction Distribution", create_transaction_size_distribution(df), "all_transaction_dist"),
            ("Income vs Expenses", create_income_vs_expenses_chart(df), "all_income_expenses")
        ]
        
        for chart_name, fig, chart_key in charts:
            if fig:
                st.markdown(f"#### {chart_name}")
                st.plotly_chart(fig, use_container_width=True, key=chart_key)

def show_transaction_details(df):
    """Show detailed transaction table with search and filtering"""
    st.markdown("### 📋 Transaction Details")
    
    # Search functionality
    search_term = st.text_input("🔍 Search transactions", placeholder="Enter description, category, or amount...")
    
    # Sort options
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox("Sort by", ["Trans. Date", "Amount", "Enhanced_Category", "Description"])
    with col2:
        sort_order = st.selectbox("Order", ["Descending", "Ascending"])
    
    # Apply search filter
    display_df = df.copy()
    if search_term:
        mask = (
            display_df['Description'].str.contains(search_term, case=False, na=False) |
            display_df['Enhanced_Category'].str.contains(search_term, case=False, na=False) |
            display_df['Amount'].astype(str).str.contains(search_term, na=False)
        )
        display_df = display_df[mask]
    
    # Apply sorting
    ascending = sort_order == "Ascending"
    display_df = display_df.sort_values(sort_by, ascending=ascending)
    
    # Display results
    st.write(f"**{len(display_df)} transactions found**")
    
    # Format the dataframe for display
    display_columns = ['Trans. Date', 'Description', 'Amount', 'Enhanced_Category', 'Source']
    display_df_formatted = display_df[display_columns].copy()
    display_df_formatted['Trans. Date'] = display_df_formatted['Trans. Date'].dt.strftime('%Y-%m-%d')
    display_df_formatted['Amount'] = display_df_formatted['Amount'].apply(lambda x: f"${x:,.2f}")
    
    # Show in batches for performance
    batch_size = 50
    total_rows = len(display_df_formatted)
    
    if total_rows > batch_size:
        page = st.selectbox(
            "Page",
            range(1, (total_rows // batch_size) + 2),
            format_func=lambda x: f"Page {x} ({(x-1)*batch_size + 1}-{min(x*batch_size, total_rows)})"
        )
        
        start_idx = (page - 1) * batch_size
        end_idx = min(page * batch_size, total_rows)
        batch_df = display_df_formatted.iloc[start_idx:end_idx]
    else:
        batch_df = display_df_formatted
    
    # Display the table
    st.dataframe(batch_df, use_container_width=True, hide_index=True)
    
    # Export functionality
    if st.button("📥 Export Filtered Data"):
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"filtered_transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

def show_internship_page():
    """Display the internship analysis page"""
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload and process data first!")
        if st.button("📂 Go to Data Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    # Use the comprehensive internship analysis module
    show_internship_analysis_page(st.session_state.combined_data)

def show_reports_page():
    """Display the reports page"""
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload and process data first!")
        if st.button("📂 Go to Data Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    # Use the comprehensive report generator module
    show_report_generator(st.session_state.combined_data)

def show_venmo_page():
    """Display the Venmo categorization page"""
    st.markdown('<h1 class="main-header">💸 Venmo Transaction Categorizer</h1>', unsafe_allow_html=True)
    
    # Use the web-based Venmo categorizer
    show_venmo_categorizer()

# Main app logic
def main():
    """Main application logic"""
    init_session_state()
    create_sidebar()
    
    # Route to the current page
    if st.session_state.current_page == "Home":
        show_home_page()
    elif st.session_state.current_page == "Upload":
        show_upload_page()
    elif st.session_state.current_page == "Venmo":
        show_venmo_page()
    elif st.session_state.current_page == "Analysis":
        show_analysis_page()
    elif st.session_state.current_page == "Internship":
        show_internship_page()
    elif st.session_state.current_page == "Reports":
        show_reports_page()

if __name__ == "__main__":
    main() 