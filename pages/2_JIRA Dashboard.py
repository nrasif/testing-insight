import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime #
from utils.jira_processed import jiraProgress_proc
from datetime import datetime, timedelta

import altair as alt
import plotly.express as px
import plotly.graph_objects as go

from streamlit_extras.stylable_container import stylable_container

from config import NAMA_FILE_JIRA, METRIC_CARD_STYLE
from utils.data_loader import load_and_process_jira_data

from components.filters import render_filters, apply_filters
from components.metrics import display_summary_metrics

from components.views import render_ticket_details_dashboard
from components.charts import (
    render_severity_per_feature_chart,
    render_ticket_status_overview_chart,
    render_daily_activity_chart,
    render_cumulative_lifecycle_chart,
    render_ticket_distribution_bubble_chart
)

import json

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
        
        /* Ini adalah font default untuk seluruh aplikasi */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
    </style>
""")

@st.cache_data
def get_data(filename: str):
    """Cached function to load and process data."""
    with st.spinner("Loading and processing data..."):
        df = load_and_process_jira_data(filename)
    return df

# --- Main Data Loading & Filtering ---
df_jira_original = get_data(NAMA_FILE_JIRA)

# Cukup panggil satu fungsi ini untuk mendapatkan data matang
with st.spinner("Sabar yah, lagi ngeload datanya nih hehe..", show_time=True):
    df_jira_original = load_and_process_jira_data(NAMA_FILE_JIRA)



with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

st.html(
    f"""
    <p style="margin-bottom: 20px;">
        <span class='green_text'>JIRA</span>
        <span class='black_text'>Dashboard</span>
    </p>
    """
)

# Filter Section
with st.expander(':material/tune: Filter', expanded=False):
    render_filters(df_jira_original)

df_filtered = apply_filters(df_jira_original)


display_summary_metrics(df_filtered, METRIC_CARD_STYLE)

col1, col2 = st.columns([1.6,2.4])

with col1:
    render_severity_per_feature_chart(df_filtered)
    render_ticket_details_dashboard(df_filtered)
    render_daily_activity_chart(df_filtered)
    render_cumulative_lifecycle_chart(df_filtered)

with col2:
    render_ticket_status_overview_chart(df_filtered)
    render_ticket_distribution_bubble_chart(df_filtered)