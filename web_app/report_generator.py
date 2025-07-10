"""
Comprehensive report generation and export functionality for the Personal Finance Analyzer
"""

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
from datetime import datetime, timedelta
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from io import BytesIO
import numpy as np

def generate_financial_summary(df, date_range=None):
    """Generate comprehensive financial summary"""
    try:
        # Filter by date range if provided
        if date_range:
            start_date, end_date = date_range
            df_filtered = df[
                (df['Trans. Date'] >= pd.to_datetime(start_date)) &
                (df['Trans. Date'] <= pd.to_datetime(end_date))
            ].copy()
        else:
            df_filtered = df.copy()
        
        if df_filtered.empty:
            return None
        
        # Basic metrics
        total_transactions = len(df_filtered)
        date_range_actual = (df_filtered['Trans. Date'].min(), df_filtered['Trans. Date'].max())
        
        # Spending analysis (positive amounts are expenses)
        expenses = df_filtered[df_filtered['Amount'] > 0]
        income = df_filtered[df_filtered['Amount'] < 0]
        
        total_expenses = expenses['Amount'].sum()
        total_income = abs(income['Amount'].sum())
        net_spending = total_expenses - total_income
        
        # Category breakdown
        if 'Enhanced_Category' in df_filtered.columns:
            category_summary = df_filtered.groupby('Enhanced_Category').agg({
                'Amount': 'sum',
                'Trans. Date': 'count'
            }).round(2)
            category_summary.columns = ['Total_Amount', 'Transaction_Count']
            category_summary = category_summary.sort_values('Total_Amount', ascending=False)
        else:
            category_summary = pd.DataFrame()
        
        # Daily spending pattern
        daily_spending = expenses.groupby(expenses['Trans. Date'].dt.date)['Amount'].sum()
        avg_daily_spending = daily_spending.mean()
        
        # Monthly trends
        monthly_summary = df_filtered.groupby(df_filtered['Trans. Date'].dt.to_period('M')).agg({
            'Amount': 'sum',
            'Trans. Date': 'count'
        }).round(2)
        monthly_summary.columns = ['Total_Amount', 'Transaction_Count']
        
        # Top merchants/descriptions
        top_merchants = expenses.groupby('Description')['Amount'].sum().sort_values(ascending=False).head(10)
        
        return {
            'period': date_range_actual,
            'total_transactions': total_transactions,
            'total_expenses': total_expenses,
            'total_income': total_income,
            'net_spending': net_spending,
            'avg_daily_spending': avg_daily_spending,
            'category_summary': category_summary,
            'monthly_summary': monthly_summary,
            'top_merchants': top_merchants,
            'daily_spending': daily_spending
        }
        
    except Exception as e:
        st.error(f"Error generating financial summary: {str(e)}")
        return None

def create_spending_charts_for_report(df, summary_data):
    """Create matplotlib charts optimized for PDF reports"""
    charts = {}
    
    try:
        # Set style for clean PDF output
        plt.style.use('default')
        sns.set_palette("husl")
        
        # 1. Category Pie Chart
        if not summary_data['category_summary'].empty:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Filter positive amounts (expenses) for pie chart
            positive_categories = summary_data['category_summary'][
                summary_data['category_summary']['Total_Amount'] > 0
            ].head(8)
            
            if not positive_categories.empty:
                wedges, texts, autotexts = ax.pie(
                    positive_categories['Total_Amount'],
                    labels=positive_categories.index,
                    autopct='%1.1f%%',
                    startangle=90
                )
                ax.set_title('Spending by Category', fontsize=14, fontweight='bold')
                
                # Improve text readability
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                plt.tight_layout()
                
                # Save to bytes
                img_buffer = BytesIO()
                plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
                img_buffer.seek(0)
                charts['category_pie'] = img_buffer
                plt.close()
        
        # 2. Monthly Trend Chart
        if not summary_data['monthly_summary'].empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            monthly_data = summary_data['monthly_summary']
            months = [str(period) for period in monthly_data.index]
            amounts = monthly_data['Total_Amount']
            
            bars = ax.bar(months, amounts, color='skyblue', edgecolor='navy', alpha=0.7)
            ax.set_title('Monthly Spending Trends', fontsize=14, fontweight='bold')
            ax.set_xlabel('Month')
            ax.set_ylabel('Amount ($)')
            ax.tick_params(axis='x', rotation=45)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'${height:,.0f}',
                       ha='center', va='bottom')
            
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            charts['monthly_trend'] = img_buffer
            plt.close()
        
        # 3. Daily Spending Pattern
        if not summary_data['daily_spending'].empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            daily_data = summary_data['daily_spending']
            dates = pd.to_datetime(daily_data.index)
            amounts = daily_data.values
            
            ax.plot(dates, amounts, linewidth=2, color='green', alpha=0.7)
            ax.fill_between(dates, amounts, alpha=0.3, color='green')
            ax.set_title('Daily Spending Pattern', fontsize=14, fontweight='bold')
            ax.set_xlabel('Date')
            ax.set_ylabel('Daily Spending ($)')
            
            # Format x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            plt.xticks(rotation=45)
            
            # Add average line
            avg_spending = amounts.mean()
            ax.axhline(y=avg_spending, color='red', linestyle='--', alpha=0.7, 
                      label=f'Average: ${avg_spending:.2f}')
            ax.legend()
            
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            charts['daily_pattern'] = img_buffer
            plt.close()
        
        # 4. Top Merchants Chart
        if not summary_data['top_merchants'].empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            top_merchants = summary_data['top_merchants'].head(8)
            # Truncate long merchant names
            labels = [name[:30] + '...' if len(name) > 30 else name for name in top_merchants.index]
            
            bars = ax.barh(labels, top_merchants.values, color='coral', edgecolor='darkred', alpha=0.7)
            ax.set_title('Top Merchants by Spending', fontsize=14, fontweight='bold')
            ax.set_xlabel('Amount ($)')
            
            # Add value labels
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height()/2.,
                       f'${width:,.0f}',
                       ha='left', va='center', fontweight='bold')
            
            plt.tight_layout()
            
            img_buffer = BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            charts['top_merchants'] = img_buffer
            plt.close()
        
        return charts
        
    except Exception as e:
        st.error(f"Error creating charts: {str(e)}")
        return {}

def generate_pdf_report(df, report_config):
    """Generate comprehensive PDF financial report"""
    try:
        # Generate summary data
        summary_data = generate_financial_summary(df, report_config.get('date_range'))
        if not summary_data:
            return None
        
        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Get styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.navy
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Build report content
        story = []
        
        # Title
        title = report_config.get('title', 'Personal Finance Report')
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Report period
        start_date, end_date = summary_data['period']
        period_text = f"Report Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}"
        story.append(Paragraph(period_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", heading_style))
        
        summary_items = [
            f"• Total Transactions: {summary_data['total_transactions']:,}",
            f"• Total Expenses: ${summary_data['total_expenses']:,.2f}",
            f"• Total Income: ${summary_data['total_income']:,.2f}",
            f"• Net Spending: ${summary_data['net_spending']:,.2f}",
            f"• Average Daily Spending: ${summary_data['avg_daily_spending']:.2f}"
        ]
        
        for item in summary_items:
            story.append(Paragraph(item, styles['Normal']))
        
        story.append(Spacer(1, 20))
        
        # Category Breakdown
        if not summary_data['category_summary'].empty:
            story.append(Paragraph("Spending by Category", heading_style))
            
            # Create table data
            table_data = [['Category', 'Amount', '# Transactions', '% of Total']]
            total_expenses = summary_data['total_expenses']
            
            for category, row in summary_data['category_summary'].head(10).iterrows():
                amount = row['Total_Amount']
                count = int(row['Transaction_Count'])
                percentage = (amount / total_expenses * 100) if total_expenses > 0 and amount > 0 else 0
                table_data.append([
                    category,
                    f"${amount:,.2f}",
                    str(count),
                    f"{percentage:.1f}%"
                ])
            
            # Create table
            table = Table(table_data, colWidths=[2.5*inch, 1.2*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Top Merchants
        if not summary_data['top_merchants'].empty:
            story.append(Paragraph("Top Merchants", heading_style))
            
            table_data = [['Merchant', 'Total Spent']]
            for merchant, amount in summary_data['top_merchants'].head(8).items():
                # Truncate long merchant names
                merchant_name = merchant[:40] + '...' if len(merchant) > 40 else merchant
                table_data.append([merchant_name, f"${amount:,.2f}"])
            
            table = Table(table_data, colWidths=[4*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
        
        # Monthly Summary
        if not summary_data['monthly_summary'].empty:
            story.append(PageBreak())
            story.append(Paragraph("Monthly Analysis", heading_style))
            
            table_data = [['Month', 'Total Amount', '# Transactions', 'Avg per Transaction']]
            for period, row in summary_data['monthly_summary'].iterrows():
                amount = row['Total_Amount']
                count = int(row['Transaction_Count'])
                avg_per_transaction = amount / count if count > 0 else 0
                table_data.append([
                    str(period),
                    f"${amount:,.2f}",
                    str(count),
                    f"${avg_per_transaction:.2f}"
                ])
            
            table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lavender),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(table)
        
        # Generate insights
        story.append(Spacer(1, 30))
        story.append(Paragraph("Key Insights", heading_style))
        
        insights = generate_insights(summary_data)
        for insight in insights:
            story.append(Paragraph(f"• {insight}", styles['Normal']))
            story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        st.error(f"Error generating PDF report: {str(e)}")
        return None

def generate_insights(summary_data):
    """Generate intelligent insights from financial data"""
    insights = []
    
    try:
        # Spending insights
        if summary_data['avg_daily_spending'] > 100:
            insights.append(f"Your daily spending average of ${summary_data['avg_daily_spending']:.2f} is relatively high. Consider reviewing discretionary expenses.")
        elif summary_data['avg_daily_spending'] < 30:
            insights.append(f"Your daily spending average of ${summary_data['avg_daily_spending']:.2f} shows good spending discipline.")
        
        # Category insights
        if not summary_data['category_summary'].empty:
            top_category = summary_data['category_summary'].index[0]
            top_amount = summary_data['category_summary'].iloc[0]['Total_Amount']
            total_expenses = summary_data['total_expenses']
            
            if total_expenses > 0:
                percentage = (top_amount / total_expenses) * 100
                insights.append(f"'{top_category}' represents {percentage:.1f}% of your total spending (${top_amount:,.2f}).")
                
                if percentage > 40:
                    insights.append(f"Consider if your spending in '{top_category}' aligns with your financial goals.")
        
        # Net spending insight
        net_spending = summary_data['net_spending']
        if net_spending > 0:
            insights.append(f"You spent ${net_spending:,.2f} more than you earned during this period.")
        else:
            insights.append(f"Great job! You saved ${abs(net_spending):,.2f} during this period.")
        
        # Transaction frequency insight
        total_transactions = summary_data['total_transactions']
        period_days = (summary_data['period'][1] - summary_data['period'][0]).days + 1
        avg_transactions_per_day = total_transactions / period_days
        
        if avg_transactions_per_day > 3:
            insights.append(f"You average {avg_transactions_per_day:.1f} transactions per day. Consider consolidating purchases to reduce fees.")
        
        return insights
        
    except Exception as e:
        return ["Unable to generate insights due to data processing error."]

def show_report_generator(df):
    """Main report generation interface"""
    st.markdown('<div class="section-header">📊 Financial Report Generator</div>', unsafe_allow_html=True)
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload and process data first!")
        return
    
    st.markdown("""
    Generate comprehensive financial reports with customizable date ranges, 
    visualizations, and detailed analytics. Export as PDF or CSV formats.
    """)
    
    # Report configuration
    st.markdown("### ⚙️ Report Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Date range selection
        st.markdown("**📅 Date Range**")
        
        # Get data date range
        min_date = df['Trans. Date'].min().date()
        max_date = df['Trans. Date'].max().date()
        
        date_option = st.radio(
            "Select period:",
            ["All Time", "Last 30 Days", "Last 90 Days", "Custom Range"],
            key="report_date_option"
        )
        
        if date_option == "Custom Range":
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
            date_range = (start_date, end_date)
        elif date_option == "Last 30 Days":
            end_date = max_date
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)
        elif date_option == "Last 90 Days":
            end_date = max_date
            start_date = end_date - timedelta(days=90)
            date_range = (start_date, end_date)
        else:
            date_range = None
    
    with col2:
        # Report options
        st.markdown("**📋 Report Options**")
        
        report_title = st.text_input(
            "Report Title",
            value="Personal Finance Report",
            key="report_title"
        )
        
        include_charts = st.checkbox("Include Visualizations", value=True)
        include_insights = st.checkbox("Include AI Insights", value=True)
        include_transactions = st.checkbox("Include Transaction Details", value=False)
    
    # Generate report preview
    if st.button("📊 Generate Report Preview", type="primary"):
        with st.spinner("Generating report preview..."):
            summary_data = generate_financial_summary(df, date_range)
            
            if summary_data:
                st.session_state.report_summary = summary_data
                st.session_state.report_config = {
                    'title': report_title,
                    'date_range': date_range,
                    'include_charts': include_charts,
                    'include_insights': include_insights,
                    'include_transactions': include_transactions
                }
                st.success("✅ Report preview generated!")
            else:
                st.error("Unable to generate report. Please check your data and date range.")
    
    # Show report preview
    if 'report_summary' in st.session_state:
        show_report_preview(df, st.session_state.report_summary, st.session_state.report_config)

def show_report_preview(df, summary_data, config):
    """Display report preview and export options"""
    st.markdown("---")
    st.markdown("### 📄 Report Preview")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Transactions", f"{summary_data['total_transactions']:,}")
    with col2:
        st.metric("Total Expenses", f"${summary_data['total_expenses']:,.2f}")
    with col3:
        st.metric("Total Income", f"${summary_data['total_income']:,.2f}")
    with col4:
        net_color = "normal" if summary_data['net_spending'] <= 0 else "inverse"
        st.metric("Net Spending", f"${summary_data['net_spending']:,.2f}", delta_color=net_color)
    
    # Period info
    start_date, end_date = summary_data['period']
    st.info(f"📅 **Report Period:** {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")
    
    # Category breakdown preview
    if not summary_data['category_summary'].empty:
        st.markdown("#### 🏷️ Top Categories")
        top_categories = summary_data['category_summary'].head(5)
        
        for category, row in top_categories.iterrows():
            amount = row['Total_Amount']
            count = int(row['Transaction_Count'])
            percentage = (amount / summary_data['total_expenses'] * 100) if summary_data['total_expenses'] > 0 and amount > 0 else 0
            
            st.write(f"**{category}:** ${amount:,.2f} ({count} transactions, {percentage:.1f}%)")
    
    # Insights preview
    if config.get('include_insights', True):
        st.markdown("#### 💡 Key Insights")
        insights = generate_insights(summary_data)
        for insight in insights[:3]:  # Show first 3 insights
            st.write(f"• {insight}")
    
    # Export options
    st.markdown("---")
    st.markdown("### 📤 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # PDF Export
        if st.button("📄 Generate PDF Report"):
            with st.spinner("Generating PDF report..."):
                pdf_buffer = generate_pdf_report(df, config)
                if pdf_buffer:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_buffer.getvalue(),
                        file_name=f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("✅ PDF report generated!")
    
    with col2:
        # CSV Export
        if st.button("📊 Export Raw Data (CSV)"):
            # Filter data by date range if specified
            if config.get('date_range'):
                start_date, end_date = config['date_range']
                filtered_df = df[
                    (df['Trans. Date'] >= pd.to_datetime(start_date)) &
                    (df['Trans. Date'] <= pd.to_datetime(end_date))
                ]
            else:
                filtered_df = df
            
            csv_string = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV Data",
                data=csv_string,
                file_name=f"financial_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col3:
        # Summary JSON Export
        if st.button("📋 Export Summary (JSON)"):
            import json
            
            # Prepare summary for JSON export
            json_summary = {
                'report_title': config.get('title', 'Financial Report'),
                'period': {
                    'start': summary_data['period'][0].isoformat(),
                    'end': summary_data['period'][1].isoformat()
                },
                'metrics': {
                    'total_transactions': summary_data['total_transactions'],
                    'total_expenses': float(summary_data['total_expenses']),
                    'total_income': float(summary_data['total_income']),
                    'net_spending': float(summary_data['net_spending']),
                    'avg_daily_spending': float(summary_data['avg_daily_spending'])
                },
                'top_categories': {
                    str(k): float(v['Total_Amount']) 
                    for k, v in summary_data['category_summary'].head(10).iterrows()
                },
                'insights': generate_insights(summary_data),
                'generated_at': datetime.now().isoformat()
            }
            
            json_string = json.dumps(json_summary, indent=2)
            st.download_button(
                label="📥 Download JSON Summary",
                data=json_string,
                file_name=f"financial_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            ) 