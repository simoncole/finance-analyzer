"""
Internship budget analysis and tracking for the Personal Finance Analyzer web app
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def calculate_internship_metrics(df, internship_start, internship_end, total_income, daily_rent=50.0):
    """
    Calculate comprehensive internship budget metrics
    
    Args:
        df: DataFrame with transaction data
        internship_start: Start date of internship
        internship_end: End date of internship
        total_income: Total expected income during internship
        daily_rent: Daily rent allocation (default $50/day)
    
    Returns:
        Dictionary containing internship metrics
    """
    try:
        # Filter data to internship period
        internship_df = df[
            (df['Trans. Date'] >= pd.to_datetime(internship_start)) &
            (df['Trans. Date'] <= pd.to_datetime(internship_end))
        ].copy()
        
        if internship_df.empty:
            return None
        
        # Calculate internship duration
        duration_days = (pd.to_datetime(internship_end) - pd.to_datetime(internship_start)).days + 1
        days_elapsed = (datetime.now().date() - pd.to_datetime(internship_start).date()).days + 1
        days_elapsed = max(0, min(days_elapsed, duration_days))  # Clamp to valid range
        
        # Calculate spending metrics (expenses only)
        expenses = internship_df[internship_df['Amount'] > 0].copy()
        
        # Remove rent transactions from analysis (since we're treating it as smooth allocation)
        rent_keywords = ['NASA', 'NASAAMESEXCHANGEL', 'AMES EXCHANGE LODGE']
        rent_mask = expenses['Description'].str.contains('|'.join(rent_keywords), case=False, na=False)
        expenses_no_rent = expenses[~rent_mask].copy()
        
        # Calculate actual spending
        actual_spending = expenses_no_rent['Amount'].sum()
        
        # Add smooth rent allocation
        smooth_rent_total = daily_rent * days_elapsed
        total_actual_spending = actual_spending + smooth_rent_total
        
        # Budget calculations
        remaining_budget = total_income - total_actual_spending
        daily_budget = total_income / duration_days
        actual_daily_rate = total_actual_spending / days_elapsed if days_elapsed > 0 else 0
        
        # Projections
        remaining_days = duration_days - days_elapsed
        if remaining_days > 0:
            projected_total_spending = total_actual_spending + (actual_daily_rate * remaining_days)
            projected_surplus_deficit = total_income - projected_total_spending
        else:
            projected_total_spending = total_actual_spending
            projected_surplus_deficit = remaining_budget
        
        # Category breakdown (excluding rent)
        category_spending = expenses_no_rent.groupby('Enhanced_Category')['Amount'].sum().sort_values(ascending=False)
        
        # Daily spending data for burndown chart
        daily_spending = expenses_no_rent.groupby(expenses_no_rent['Trans. Date'].dt.date)['Amount'].sum()
        
        # Create comprehensive date range data for burndown chart
        internship_start_date = pd.to_datetime(internship_start).date()
        internship_end_date = pd.to_datetime(internship_end).date()
        today = datetime.now().date()
        
        # Full date range for the entire internship period
        full_date_range = pd.date_range(start=internship_start, end=internship_end)
        
        # Actual data range (up to today or end of internship, whichever is earlier)
        actual_end_date = min(today, internship_end_date)
        actual_date_range = pd.date_range(start=internship_start, end=actual_end_date)
        
        cumulative_data = []
        cumulative_actual = 0
        
        # Build data for each day in the full internship period
        for date in full_date_range:
            current_date = date.date()
            days_into_internship = (current_date - internship_start_date).days + 1
            
            # Calculate ideal cumulative spending
            ideal_cumulative = daily_budget * days_into_internship
            
            # Calculate actual cumulative spending (only for dates up to today)
            if current_date <= actual_end_date:
                day_spending = daily_spending.get(current_date, 0)
                cumulative_actual += day_spending + daily_rent
                actual_cumulative = cumulative_actual
                remaining_budget = total_income - cumulative_actual
            else:
                # For future dates, use None so they don't appear on actual spending line
                actual_cumulative = None
                remaining_budget = None
            
            cumulative_data.append({
                'Date': current_date,
                'Actual_Cumulative': actual_cumulative,
                'Ideal_Cumulative': ideal_cumulative,
                'Remaining_Budget': remaining_budget,
                'Is_Future': current_date > actual_end_date
            })
        
        cumulative_df = pd.DataFrame(cumulative_data)
        
        return {
            'duration_days': duration_days,
            'days_elapsed': days_elapsed,
            'remaining_days': remaining_days,
            'total_income': total_income,
            'actual_spending': actual_spending,
            'smooth_rent_total': smooth_rent_total,
            'total_actual_spending': total_actual_spending,
            'remaining_budget': remaining_budget,
            'daily_budget': daily_budget,
            'actual_daily_rate': actual_daily_rate,
            'projected_total_spending': projected_total_spending,
            'projected_surplus_deficit': projected_surplus_deficit,
            'category_spending': category_spending,
            'cumulative_df': cumulative_df,
            'on_budget': projected_surplus_deficit >= 0,
            'budget_variance_pct': (projected_surplus_deficit / total_income) * 100,
            'spending_efficiency': (actual_daily_rate / daily_budget) * 100 if daily_budget > 0 else 0
        }
        
    except Exception as e:
        st.error(f"Error calculating internship metrics: {str(e)}")
        return None

def create_budget_burndown_chart(metrics):
    """Create an interactive budget burndown chart"""
    try:
        df = metrics['cumulative_df']
        
        fig = go.Figure()
        
        # Split data into actual and future portions
        actual_data = df[df['Actual_Cumulative'].notna()].copy()
        future_data = df[df['Is_Future'] == True].copy()
        
        # Ideal spending line (full internship period)
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['Ideal_Cumulative'],
            mode='lines',
            name='Ideal Budget Pace',
            line=dict(color='green', width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>Ideal: $%{y:,.2f}<extra></extra>'
        ))
        
        # Actual spending line (only up to current date)
        if not actual_data.empty:
            fig.add_trace(go.Scatter(
                x=actual_data['Date'],
                y=actual_data['Actual_Cumulative'],
                mode='lines+markers',
                name='Actual Spending',
                line=dict(color='red', width=3),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>Actual: $%{y:,.2f}<extra></extra>'
            ))
        
        # Projected spending line (if internship is ongoing)
        if not future_data.empty and len(actual_data) > 0:
            # Calculate projection based on current spending rate
            last_actual = actual_data['Actual_Cumulative'].iloc[-1]
            last_date = actual_data['Date'].iloc[-1]
            
            # Create projection line
            projection_dates = [last_date] + future_data['Date'].tolist()
            current_daily_rate = metrics['actual_daily_rate']
            
            projection_values = [last_actual]
            for i, future_date in enumerate(future_data['Date']):
                days_ahead = (future_date - last_date).days
                projected_value = last_actual + (current_daily_rate * days_ahead)
                projection_values.append(projected_value)
            
            fig.add_trace(go.Scatter(
                x=projection_dates,
                y=projection_values,
                mode='lines',
                name='Projected Spending',
                line=dict(color='orange', width=2, dash='dot'),
                hovertemplate='<b>%{x}</b><br>Projected: $%{y:,.2f}<extra></extra>'
            ))
        
        # Remaining budget (secondary axis, only for actual dates)
        if not actual_data.empty:
            fig.add_trace(go.Scatter(
                x=actual_data['Date'],
                y=actual_data['Remaining_Budget'],
                mode='lines',
                name='Remaining Budget',
                line=dict(color='blue', width=2),
                yaxis='y2',
                hovertemplate='<b>%{x}</b><br>Remaining: $%{y:,.2f}<extra></extra>'
            ))
        
        # Add budget limit line
        fig.add_hline(
            y=metrics['total_income'], 
            line_dash="dot", 
            line_color="orange",
            annotation_text=f"Total Budget: ${metrics['total_income']:,.2f}"
        )
        
        # Add vertical line for "today" if internship is ongoing
        today = datetime.now().date()
        internship_end = pd.to_datetime(df['Date'].max()).date()
        
        if today < internship_end:
            fig.add_vline(
                x=today,
                line_dash="solid",
                line_color="purple",
                line_width=2,
                annotation_text="Today",
                annotation_position="top"
            )
        
        fig.update_layout(
            title='Internship Budget Burndown Chart',
            xaxis_title='Date',
            yaxis=dict(title='Cumulative Spending ($)', side='left'),
            yaxis2=dict(title='Remaining Budget ($)', side='right', overlaying='y'),
            height=500,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating burndown chart: {str(e)}")
        return None

def create_daily_spending_chart(metrics):
    """Create a daily spending rate chart"""
    try:
        df = metrics['cumulative_df']
        
        # Filter to only actual data (not future dates)
        actual_data = df[df['Actual_Cumulative'].notna()].copy()
        
        if actual_data.empty:
            return None
        
        # Calculate daily rates
        actual_data = actual_data.copy()
        actual_data['Daily_Actual'] = actual_data['Actual_Cumulative'].diff().fillna(actual_data['Actual_Cumulative'].iloc[0])
        
        fig = go.Figure()
        
        # Daily actual spending
        fig.add_trace(go.Bar(
            x=actual_data['Date'],
            y=actual_data['Daily_Actual'],
            name='Daily Spending',
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>Daily: $%{y:.2f}<extra></extra>'
        ))
        
        # Daily budget line
        fig.add_hline(
            y=metrics['daily_budget'],
            line_dash="dash",
            line_color="green",
            annotation_text=f"Daily Budget: ${metrics['daily_budget']:.2f}"
        )
        
        # Average daily rate line
        fig.add_hline(
            y=metrics['actual_daily_rate'],
            line_dash="dot",
            line_color="red",
            annotation_text=f"Current Avg: ${metrics['actual_daily_rate']:.2f}/day"
        )
        
        # Add vertical line for "today" if needed
        today = datetime.now().date()
        internship_end = pd.to_datetime(df['Date'].max()).date()
        
        if today < internship_end and today in actual_data['Date'].values:
            fig.add_vline(
                x=today,
                line_dash="solid",
                line_color="purple",
                line_width=1,
                annotation_text="Today",
                annotation_position="top"
            )
        
        fig.update_layout(
            title='Daily Spending Analysis',
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            height=400,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating daily spending chart: {str(e)}")
        return None

def create_category_budget_chart(metrics):
    """Create a category spending breakdown for internship period"""
    try:
        category_data = metrics['category_spending']
        
        if category_data.empty:
            return None
        
        # Calculate percentages
        total_category_spending = category_data.sum()
        percentages = (category_data / total_category_spending * 100).round(1)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=category_data.index,
            y=category_data.values,
            text=[f"${val:,.0f}<br>({pct}%)" for val, pct in zip(category_data.values, percentages.values)],
            textposition='auto',
            marker_color=px.colors.qualitative.Set3,
            hovertemplate='<b>%{x}</b><br>Amount: $%{y:,.2f}<br>Percentage: %{text}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Spending by Category (Internship Period)',
            xaxis_title='Category',
            yaxis_title='Amount ($)',
            xaxis_tickangle=-45,
            height=500
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating category budget chart: {str(e)}")
        return None

def show_internship_dashboard(df):
    """Main internship analysis dashboard"""
    st.markdown("### 💼 Internship Budget Configuration")
    
    # Configuration inputs
    col1, col2 = st.columns(2)
    
    with col1:
        # Date inputs
        default_start = datetime(2025, 5, 15).date()
        default_end = datetime(2025, 8, 10).date()
        
        internship_start = st.date_input(
            "Internship Start Date",
            value=default_start,
            key="internship_start"
        )
        
        internship_end = st.date_input(
            "Internship End Date", 
            value=default_end,
            key="internship_end"
        )
    
    with col2:
        # Budget inputs
        total_income = st.number_input(
            "Total Expected Income ($)",
            min_value=0.0,
            value=8200.0,
            step=100.0,
            key="total_income"
        )
        
        daily_rent = st.number_input(
            "Daily Rent Allocation ($)",
            min_value=0.0,
            value=50.0,
            step=5.0,
            help="Smooth daily rent allocation (e.g., $3500 total / 70 days = $50/day)",
            key="daily_rent"
        )
    
    # Calculate metrics
    if st.button("🔄 Analyze Internship Budget", type="primary"):
        with st.spinner("Analyzing internship budget..."):
            metrics = calculate_internship_metrics(
                df, internship_start, internship_end, total_income, daily_rent
            )
            
            if metrics is None:
                st.error("Unable to calculate internship metrics. Please check your date range and data.")
                return
            
            # Store metrics in session state
            st.session_state.internship_metrics = metrics
            st.success("✅ Internship analysis complete!")
    
    # Display analysis if metrics are available
    if 'internship_metrics' in st.session_state:
        metrics = st.session_state.internship_metrics
        
        st.markdown("---")
        st.markdown("### 📊 Budget Overview")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Income",
                f"${metrics['total_income']:,.2f}",
                help="Expected total income during internship"
            )
        
        with col2:
            spending_color = "normal" if metrics['on_budget'] else "inverse"
            st.metric(
                "Total Spending",
                f"${metrics['total_actual_spending']:,.2f}",
                delta=f"${metrics['total_actual_spending'] - metrics['total_income']:,.2f}",
                delta_color=spending_color
            )
        
        with col3:
            budget_color = "normal" if metrics['remaining_budget'] > 0 else "inverse"
            st.metric(
                "Remaining Budget",
                f"${metrics['remaining_budget']:,.2f}",
                delta=f"{metrics['budget_variance_pct']:+.1f}%",
                delta_color=budget_color
            )
        
        with col4:
            efficiency_color = "inverse" if metrics['spending_efficiency'] > 100 else "normal"
            st.metric(
                "Spending Efficiency",
                f"{metrics['spending_efficiency']:.1f}%",
                delta="vs ideal budget pace",
                delta_color=efficiency_color
            )
        
        # Progress metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            progress_pct = (metrics['days_elapsed'] / metrics['duration_days']) * 100
            st.metric(
                "Time Progress",
                f"{progress_pct:.1f}%",
                delta=f"{metrics['days_elapsed']}/{metrics['duration_days']} days"
            )
        
        with col2:
            st.metric(
                "Daily Budget",
                f"${metrics['daily_budget']:.2f}",
                delta=f"Actual: ${metrics['actual_daily_rate']:.2f}/day"
            )
        
        with col3:
            projection_color = "normal" if metrics['projected_surplus_deficit'] >= 0 else "inverse"
            st.metric(
                "Projected Result",
                f"${metrics['projected_surplus_deficit']:+,.2f}",
                delta="Surplus/Deficit",
                delta_color=projection_color
            )
        
        # Status indicators
        st.markdown("### 🎯 Budget Status")
        
        if metrics['on_budget']:
            st.success(f"✅ **On Track!** You're projected to finish with a surplus of ${metrics['projected_surplus_deficit']:,.2f}")
        else:
            st.error(f"⚠️ **Over Budget!** You're projected to exceed budget by ${abs(metrics['projected_surplus_deficit']):,.2f}")
        
        # Recommendations
        if metrics['spending_efficiency'] > 110:
            st.warning("💡 **Recommendation:** Your spending rate is significantly above budget. Consider reviewing discretionary expenses.")
        elif metrics['spending_efficiency'] > 100:
            st.info("💡 **Recommendation:** You're slightly over budget pace. Monitor spending closely in remaining days.")
        elif metrics['spending_efficiency'] < 80:
            st.info("💡 **Great job!** You're well under budget. You have flexibility for larger expenses if needed.")
        
        # Charts
        st.markdown("---")
        st.markdown("### 📈 Budget Analysis Charts")
        
        # Burndown chart
        burndown_fig = create_budget_burndown_chart(metrics)
        if burndown_fig:
            st.plotly_chart(burndown_fig, use_container_width=True, key="internship_burndown")
        
        # Daily spending and category breakdown
        col1, col2 = st.columns(2)
        
        with col1:
            daily_fig = create_daily_spending_chart(metrics)
            if daily_fig:
                st.plotly_chart(daily_fig, use_container_width=True, key="internship_daily")
        
        with col2:
            category_fig = create_category_budget_chart(metrics)
            if category_fig:
                st.plotly_chart(category_fig, use_container_width=True, key="internship_categories")
        
        # Detailed breakdown
        st.markdown("### 📋 Detailed Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**💰 Spending Breakdown**")
            st.write(f"• **Non-rent spending:** ${metrics['actual_spending']:,.2f}")
            st.write(f"• **Smooth rent allocation:** ${metrics['smooth_rent_total']:,.2f}")
            st.write(f"• **Total spending:** ${metrics['total_actual_spending']:,.2f}")
            st.write(f"• **Average daily rate:** ${metrics['actual_daily_rate']:.2f}")
            
            st.markdown("**📅 Timeline**")
            st.write(f"• **Days elapsed:** {metrics['days_elapsed']}")
            st.write(f"• **Days remaining:** {metrics['remaining_days']}")
            st.write(f"• **Total duration:** {metrics['duration_days']} days")
        
        with col2:
            st.markdown("**🎯 Projections**")
            st.write(f"• **Projected total spending:** ${metrics['projected_total_spending']:,.2f}")
            st.write(f"• **Expected outcome:** ${metrics['projected_surplus_deficit']:+,.2f}")
            st.write(f"• **Budget variance:** {metrics['budget_variance_pct']:+.1f}%")
            
            if metrics['category_spending'].empty == False:
                st.markdown("**🏷️ Top Categories**")
                top_categories = metrics['category_spending'].head(3)
                for i, (category, amount) in enumerate(top_categories.items(), 1):
                    pct = (amount / metrics['actual_spending']) * 100 if metrics['actual_spending'] > 0 else 0
                    st.write(f"{i}. **{category}:** ${amount:,.2f} ({pct:.1f}%)")

def show_internship_analysis_page(df):
    """Main internship analysis page"""
    st.markdown('<h1 class="main-header">💼 Internship Budget Analysis</h1>', unsafe_allow_html=True)
    
    if not st.session_state.data_loaded:
        st.warning("⚠️ Please upload and process data first!")
        if st.button("📂 Go to Data Upload"):
            st.session_state.current_page = "Upload"
            st.rerun()
        return
    
    # Show internship dashboard
    show_internship_dashboard(df) 