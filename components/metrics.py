# components/metrics.py
import streamlit as st
import pandas as pd
from utils.helpers import duration_to_hours, format_hours_to_days_hours
from config import STATUS_CATEGORIES

def display_summary_metrics(df: pd.DataFrame, metric_card_style: str):
    """Calculates and displays the main summary metrics in styled cards."""
    
    st.markdown(f"<style>{metric_card_style}</style>", unsafe_allow_html=True)
    
    if df.empty:
        st.info("No data available for the selected filters to display metrics.")
        return

    total_tickets = len(df.index)
    
    is_invalid = df['Status'].isin(STATUS_CATEGORIES['invalid'])
    is_resolved = df['Status'].isin(STATUS_CATEGORIES['resolved'])
    
    total_open_tickets = len(df[~is_invalid & ~is_resolved])
    total_solved_tickets = df[is_resolved].shape[0]
    total_invalid_ticket = df[is_invalid].shape[0]

    # Calculate average resolution time
    solved_tickets_df = df[df['Resolved_Time'].notna()].copy()
    if not solved_tickets_df.empty and 'Duration_toResolve' in solved_tickets_df.columns:
        solved_tickets_df['duration_hours'] = solved_tickets_df['Duration_toResolve'].apply(duration_to_hours)
        avg_duration_in_hours = solved_tickets_df['duration_hours'].mean()
        formatted_avg_duration = format_hours_to_days_hours(avg_duration_in_hours)
    else:
        formatted_avg_duration = "N/A"

    # Display metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(label="Total Tickets", value=total_tickets)
    m2.metric(label="Open Tickets", value=total_open_tickets)
    m3.metric(label="Solved Tickets", value=total_solved_tickets)
    m4.metric(label="Invalid Tickets", value=total_invalid_ticket)
    m5.metric(label="Avg. Resolution Time", value=formatted_avg_duration)
