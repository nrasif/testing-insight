# components/views.py
import streamlit as st
import pandas as pd
from streamlit_extras.stylable_container import stylable_container

# --- Adjust Python Path to import from root ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import STATUS_CATEGORIES

# This component is now self-contained and does not require a global CSS file.

def render_ticket_card(row, status_category):
    """Renders a single ticket card using HTML and CSS classes."""
    severity_color_map = {'Highest': 'severity-highest', 'Medium': 'severity-medium', 'Low': 'severity-low'}
    severity = row.get('Severity', 'N/A')
    status_class = f"status-{status_category}"
    severity_class = severity_color_map.get(severity, "")
    
    st.markdown(f"""
        <div class="ticket-card">
            <div class="card-header">
                <span class="ticket-id">{row['Tickets']}</span>
                <span class="status-badge {status_class}">{row['Status']}</span>
            </div>
            <div>
                <span class="{severity_class}">{severity}</span>
                <div class="ticket-info-list">
                    <b>Squad:</b> {row.get('Squad', 'N/A')} <br>
                    <b>Bug Type:</b> {row.get('Bug Type', 'N/A')}
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

def render_ticket_details_dashboard(df: pd.DataFrame):
    """Renders the main ticket details view with expandable sections for each feature."""
    
    # PERUBAHAN: Menggunakan CSS yang Anda berikan.
    css_final_layout = """
    {
        border: 2px solid #e6e6e6;
        border-radius: 16px;
        padding: 20px;
        height: 500px; 
        overflow-y: auto;
        background-color: #F6F6F6;
        scrollbar-width: none; 
        -ms-overflow-style: none;
    }
    &::-webkit-scrollbar {
        display: none;
    }
    .ticket-card {
        background-color: transparent; 
        box-shadow: none;
        border: none;
        border-bottom: 1px solid #e9ecef;
        height: 150px;
        border-left: 2px solid #454444;
        padding: 10px 10px 10px 20px; 
        margin-bottom: 20px;
    }
    .ticket-card:hover {
        background-color: #f0f0f0;
    }
    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0px;
    }
    .ticket-id {
        font-weight: 700;
        font-size: 0.9em; 
        color: #212529;
    }
    .status-badge {
        font-size: 0.6em; 
        font-weight: 500;
        padding: 4px 8px;
        border-radius: 12px;
    }
    .ticket-severity {
        font-size: 0.6em; 
    }
    .ticket-info-list {
        margin-top: 2px;
        font-size: 0.8em !important; 
        color: #495057;
        padding-left: 0;
    }
    .column-header {
        font-size: 1em;
        font-weight: 700;
        color: #343a40;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 20px;
        margin-left: 5px;
    }
    .ticket-count-badge {
        font-size: 0.85em;
        font-weight: 500;
        background-color: #e9ecef;
        color: #495057;
        padding: 2px 9px;
        border-radius: 8px;
    }
    .status-open { background-color: #ffebee; color: #c62828;}
    .status-resolved { background-color: #e8f5e9; color: #2e7d32; }
    .status-invalid { background-color: #f5f5f5; color: #616161; }
    .severity-highest { color: #d32f2f; font-weight: 600; font-size: 0.8em;}
    .severity-medium { color: #f57c00; font-weight: 600; font-size: 0.8em; }
    .severity-low { color: #0277bd; font-weight: 600; font-size: 0.8em; }
    """

    # Menggunakan stylable_container dengan key dan style yang Anda tentukan.
    with stylable_container(key="final_dashboard_container", css_styles=css_final_layout):
        st.markdown(':material/view_quilt: **Ticket Details Dashboard**',
                    help='Click on a feature to see a detailed card-view of tickets, categorized by status.')

        if df.empty:
            st.info("No tickets found for the selected filters.")
            return

        # Define status filters
        is_resolved = df['Status'].isin(STATUS_CATEGORIES['resolved'])
        is_invalid = df['Status'].isin(STATUS_CATEGORIES['invalid'])
        is_open = ~is_resolved & ~is_invalid

        if 'Feature' not in df.columns or df['Feature'].isnull().all():
            st.info("No 'Feature' data available to display.")
            return

        features_sorted = df['Feature'].value_counts().index.tolist()

        if not features_sorted:
            st.info("No tickets with features found for the selected filters.")
            return

        for feature in features_sorted:
            feature_df = df[df['Feature'] == feature]
            open_count = df[is_open & (df['Feature'] == feature)].shape[0]
            total_count = feature_df.shape[0]
            expander_title = f"**{feature}** — ({open_count} Open / {total_count} Total)"

            with st.expander(expander_title):
                col_open, col_resolved, col_invalid = st.columns(3)

                # --- Column 1: OPEN ---
                with col_open:
                    open_df = df[is_open & (df['Feature'] == feature)]
                    st.markdown(f"<div class='column-header'>Open <span class='ticket-count-badge'>{len(open_df)}</span></div>", unsafe_allow_html=True)
                    if not open_df.empty:
                        for _, row in open_df.iterrows():
                            render_ticket_card(row, "open")
                    else:
                        st.caption("No open tickets.")

                # --- Column 2: RESOLVED ---
                with col_resolved:
                    resolved_df = df[is_resolved & (df['Feature'] == feature)]
                    st.markdown(f"<div class='column-header'>Resolved <span class='ticket-count-badge'>{len(resolved_df)}</span></div>", unsafe_allow_html=True)
                    if not resolved_df.empty:
                        for _, row in resolved_df.iterrows():
                            render_ticket_card(row, "resolved")
                    else:
                        st.caption("No resolved tickets.")

                # --- Column 3: INVALID ---
                with col_invalid:
                    invalid_df = df[is_invalid & (df['Feature'] == feature)]
                    st.markdown(f"<div class='column-header'>Invalid <span class='ticket-count-badge'>{len(invalid_df)}</span></div>", unsafe_allow_html=True)
                    if not invalid_df.empty:
                        for _, row in invalid_df.iterrows():
                            render_ticket_card(row, "invalid")
                    else:
                        st.caption("No invalid tickets.")
