import streamlit as st

def allProgress_stacked():
    options = ['Android', 'iOS']
    selection = st.pills('', options, selection_mode = 'single', default=options[0], label_visibility = 'hidden')