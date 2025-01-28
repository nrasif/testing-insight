import streamlit as st
from components.logo_sidebar import get_logo
from components.card import card_testing

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

get_logo('assets/testinginsight.png')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

date = '28/01/2025'

# Text title
st.markdown(
    f"""
    <p class='uat_line'>
        <span class='uat_text'>UAT</span>
        <span class='card_title'>Progress {date}</span>
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








