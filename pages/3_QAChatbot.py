import streamlit as st

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)


messages = st.container(height=650)
if prompt := st.chat_input("Say something"):
    messages.chat_message("user").write(prompt)