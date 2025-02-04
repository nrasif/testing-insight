import streamlit as st
from components.logo_sidebar import get_logo
from components.card import card_testing
from components.progress_stackedbar import uatProgress_stacked
from utils.uat_progress import uatProgress_proc, card_data
from datetime import datetime

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

uat_path = "data/uat_progress.xlsx"
df_uat = uatProgress_proc(uat_path)
cards = card_data() # kalo misal butuh df_uat, define as parameter di dalam kurung
date = '28/01/2025'


get_logo('assets/testinginsight.png')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)
    
col1, col2 = st.columns([1,3.5])

with col1:
    # Card Text title
    st.markdown(
        f"""
        <p class='card_feature'>
            <span class='green_text'>UAT</span>
            <span class='black_text'>progress {date}</span>
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
    
# card component with data from utils
card_testing(cards, num_columns=3)


col1, col2 = st.columns([1,0.7])

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
