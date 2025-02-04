import streamlit as st
from components.logo_sidebar import get_logo
from components.card import card_testing
from components.progress_stackedbar import allProgress_stacked

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

get_logo('assets/testinginsight.png')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)




