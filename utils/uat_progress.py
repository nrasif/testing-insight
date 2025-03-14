import streamlit as st
import pandas as pd

@st.cache_data
def uatProgress_proc(path):
    df_uat = pd.read_excel(path)
    df_uat.ffill(inplace=True)
    df_uat[['Target Execution', 'Execution', 'Passed', 'Failed']] = df_uat[['Target Execution', 'Execution', 'Passed', 'Failed']].mul(100).astype(float)
    df_uat["Tanggal"] = pd.to_datetime(df_uat["Tanggal"], format="%m/%d/%Y", errors='coerce')
    return df_uat

def card_data(df):
    # data of the card component
    
    
    
    cards = [
        {"text": "Execution", "value": df['Execution'].iloc[0].round(2), "delta": "+10%", "help_text": "Test case execution progress", "delta_color": "normal"},
        {"text": "Passed", "value": "53%", "delta": "+11%", "help_text": "Percentage of test cases successfully executed without issues", "delta_color": "normal"},
        {"text": "Failed", "value": "34%", "delta": "+7%", "help_text": "Percentage of test cases that did not meet the expected results", "delta_color": "inverse"},
    ]
    
    return cards