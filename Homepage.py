import streamlit as st
from components.logo_sidebar import get_logo
from streamlit_extras.stylable_container import stylable_container

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

get_logo('assets/testinginsight.png')

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)

# Create styled cards with a shadow

card_style = """
    {
        
        border: 1px groove #52546a;
        border-radius: 10px;
        padding-left: 25px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
"""

col1, col2 = st.columns([1,1])

with col1:
    with stylable_container("Card1", css_styles=card_style):
        st.metric("Passed", "88%", "5%", help="Test case that passes the test")
        
with col2:
    with stylable_container("Card2", css_styles=card_style):
        st.metric("Failed", "12%", "-1%", help="Test case that fails the test")







