import streamlit as st
from components.logo_sidebar import get_logo
from components.card import card_testing
from components.progress_stackedbar import allProgress_stacked
from datetime import datetime

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

get_logo('assets/testinginsight.png')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)
    
date = '28/01/2025'

# Text title
st.markdown(
    f"""
    <p class='card_feature'>
        <span class='green_text'>UAT</span>
        <span class='black_text'>progress {date}</span>
    </p>
    """,
    unsafe_allow_html=True
)


# Card Component
cards = [
    {"text": "Execution", "value": "88%", "delta": "+10%", "help_text": "Test case execution progress", "delta_color": "normal"},
    {"text": "Passed", "value": "53%", "delta": "+11%", "help_text": "Percentage of test cases successfully executed without issues", "delta_color": "normal"},
    {"text": "Failed", "value": "34%", "delta": "+7%", "help_text": "Percentage of test cases that did not meet the expected results", "delta_color": "inverse"},
]

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
    
    allProgress_stacked()
    
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
st.markdown('test')
st.markdown('test')
st.markdown('test')
st.markdown('test')
st.markdown('test')
st.markdown('test')
st.markdown('test')
st.markdown('test')