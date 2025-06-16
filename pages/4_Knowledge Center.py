import streamlit as st

st.set_page_config(page_title='IntipinJira', layout='wide')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)