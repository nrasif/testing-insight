import streamlit as st
from components.logo_sidebar import get_logo
from components.card import card_testing

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

get_logo('assets/testinginsight.png')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)


cards = [
    {"text": "Execution", "value": "88%", "delta": "+10%", "help_text": "Test case execution progress"},
    {"text": "Passed", "value": "53%", "delta": "+11%", "help_text": "Percentage of test cases successfully executed without issues"},
    {"text": "Failed", "value": "34%", "delta": "-7%", "help_text": "Percentage of test cases that did not meet the expected results"},
]

card_testing(cards, num_columns=3)








