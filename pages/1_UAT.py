import streamlit as st
from components.logo_sidebar import get_logo
from components.card import card_testing
from components.progress_stackedbar import uatProgress_stacked
from utils.uat_progress import uatProgress_proc, card_data
from datetime import datetime

# Constants
UAT_PATH = "data/uat_progress.xlsx"
DATE = '28/01/2025'
LOGO_PATH = 'assets/testinginsight.png'
CSS_PATH = 'css/style.css'

# Page configuration
st.set_page_config(page_title='BSI Testing Insight', layout='wide')

# Load data
df_uat = uatProgress_proc(UAT_PATH)
cards = card_data(df_uat)

# Display logo
get_logo(LOGO_PATH)

# Load CSS
with open(CSS_PATH) as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Layout
col1, col2 = st.columns([1, 3.5])

with col1:
    st.markdown(
        f"""
        <p class='card_feature'>
            <span class='green_text'>UAT</span>
            <span class='black_text'>progress {DATE}</span>
        </p>
        """,
        unsafe_allow_html=True
    )

with col2:
    options = ['Android', 'iOS']
    selected_os = st.pills(
        'Select OS',
        options,
        selection_mode='single',
        default=options[0],
        label_visibility='hidden'
    )

# Card component with data from utils
card_testing(cards, num_columns=3)

col1, col2 = st.columns([1, 0.7])

with col1:
    st.markdown(
        f"""
        <p class='chart_feature'>
            <span class='green_text'>Regression</span>
            <span class='black_text'>Progress</span>
        </p>
        """,
        unsafe_allow_html=True
    )

    # Pass the selected OS directly to the function
    @st.fragment
    def chart_fragment(selected_os):
        if isinstance(selected_os, list):
            selected_os = selected_os[0] if selected_os else options[0]
        uatProgress_stacked(df_uat, selected_os)

    # Call the fragment with the current OS selection
    chart_fragment(selected_os)

with col2:
    st.markdown(
        f"""
        <p class='chart_feature'>
            <span class='green_text'>Testing</span>
            <span class='black_text'>Activity</span>
        </p>
        """,
        unsafe_allow_html=True
    )

st.markdown('test')
