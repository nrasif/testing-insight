import pandas as pd
import streamlit as st

def jiraProgress_proc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs basic processing on a JIRA DataFrame.
    """
    # Tidak perlu lagi pd.read_csv(path) di sini.
    
    if 'Tickets' not in df.columns or 'Title' not in df.columns:
        # Daripada st.error, lebih baik raise Exception agar bisa ditangani di pemanggil
        raise ValueError("Kolom 'Tickets' atau 'Title' tidak ditemukan dalam data.")

    if 'Created' in df.columns:
        df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
    else:
        st.warning('Kolom "Created" tidak ditemukan, akan diisi dengan nilai kosong.')
        df['Created'] = pd.NaT


    return df