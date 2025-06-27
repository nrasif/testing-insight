import pandas as pd
import re
import streamlit as st # Diperlukan untuk reset_jira_filters karena berinteraksi dengan st.session_state


def apply_filters(df_original: pd.DataFrame, 
                  ticket_id_search: str, 
                  status_filter: list, 
                  feature_filter: list, 
                  platform_filter: list, 
                  date_filter: tuple, 
                  labels_filter: list, 
                  stage_filter: list, 
                  solved_filter: str, 
                  title_filter: str,
                  pills_selection: str | None = None) -> pd.DataFrame: # <<< PARAMETER BARU DITAMBAHKAN
    """
    Menerapkan berbagai filter ke DataFrame JIRA.

    Args:
        df_original (pd.DataFrame): DataFrame JIRA asli.
        ticket_id_search (str): ID tiket yang dipisahkan koma untuk pencarian.
        status_filter (list): Daftar status yang dipilih.
        feature_filter (list): Daftar fitur yang dipilih.
        platform_filter (list): Daftar platform yang dipilih.
        date_filter (tuple): Tuple (tanggal_mulai, tanggal_akhir) untuk kolom 'Created'.
        labels_filter (list): Daftar label yang dipilih.
        stage_filter (list): Daftar tahap (stage) yang dipilih.
        solved_filter (str): 'Solved', 'Not Yet', atau None.
        title_filter (str): Kata kunci yang dipisahkan koma untuk pencarian di 'Title'.
        pills_selection (str | None): Opsi yang dipilih dari st.pills. Defaultnya None.
        
    Returns:
        pd.DataFrame: DataFrame yang sudah difilter.
    """
    df_filtered = df_original.copy()

    # <<< BLOK FILTER PILLS DIMULAI >>>
    # Filter berdasarkan pilihan dari st.pills
    if pills_selection:
        if pills_selection == 'PTR 1.1.0':
            df_filtered = df_filtered[df_filtered['Title'].str.contains('PTR 1.1.0', na=False)]
        
        elif pills_selection == "SITBAU 1.1.0 GS 9.10.1":
            df_filtered = df_filtered[
                (df_filtered['Title'].str.contains('GS 9.10.1', na=False)) & 
                (df_filtered['Stage'] == 'Regression')
            ]

        elif pills_selection == "PTR 1.1.0 GS 9.10.1":
            df_filtered = df_filtered[
                (df_filtered['Title'].str.contains('GS 9.10.1', na=False)) & 
                (df_filtered['Stage'] == 'PTR')
            ]
            
        elif pills_selection == "SITBAU Always On 1.1.0":
            df_filtered = df_filtered[
                (df_filtered['Title'].str.contains('Always On', na=False)) & 
                (df_filtered['Stage'] == 'Regression')
            ]

        elif pills_selection == "PTR Always On 1.1.0":
            df_filtered = df_filtered[
                (df_filtered['Title'].str.contains('Always On', na=False)) & 
                (df_filtered['Stage'] == 'PTR')
            ]

    # Filter berdasarkan Ticket ID Search
    if ticket_id_search and 'Tickets' in df_filtered.columns:
        search_terms = [term.strip() for term in ticket_id_search.split(',') if term.strip()]
        if search_terms:
            regex_pattern = '|'.join(map(re.escape, search_terms))
            df_filtered = df_filtered[df_filtered['Tickets'].astype(str).str.contains(regex_pattern, case=False, na=False)]

    # Filter berdasarkan Status
    if status_filter and 'Status' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Status'].isin(status_filter)]

    # Filter berdasarkan Feature
    if feature_filter and 'Feature' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Feature'].isin(feature_filter)]

    # Filter berdasarkan Platform
    if platform_filter and 'Platform' in df_filtered.columns:
        platform_conditions = pd.Series([False] * len(df_filtered), index=df_filtered.index)
        for p_select in platform_filter:
            platform_conditions = platform_conditions | df_filtered['Platform'].astype(str).str.contains(p_select, case=False, na=False)
        df_filtered = df_filtered[platform_conditions]

    # Filter berdasarkan Date Range 'Created'
    if date_filter and len(date_filter) == 2 and 'Created' in df_filtered.columns:
        start_date, end_date = pd.to_datetime(date_filter[0]), pd.to_datetime(date_filter[1])
        if not pd.api.types.is_datetime64_any_dtype(df_filtered['Created']):
            df_filtered['Created'] = pd.to_datetime(df_filtered['Created'], errors='coerce')
        df_filtered = df_filtered[
            (df_filtered['Created'].dt.normalize() >= start_date.normalize()) &
            (df_filtered['Created'].dt.normalize() <= end_date.normalize())
        ]
        
    # Filter berdasarkan Labels
    if labels_filter and 'Labels' in df_filtered.columns:
        if not pd.api.types.is_string_dtype(df_filtered['Labels']):
            df_filtered['Labels'] = df_filtered['Labels'].astype(str)
        regex_pattern = '|'.join(map(re.escape, labels_filter))
        df_filtered = df_filtered[df_filtered['Labels'].str.contains(regex_pattern, na=False)]
        
    # Filter berdasarkan Stage
    if stage_filter and 'Stage' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Stage'].isin(stage_filter)]
        
    # Filter berdasarkan Solved/Not Yet
    if solved_filter == 'Solved':
        df_filtered = df_filtered[df_filtered['Resolved_Time'].notna()]
    elif solved_filter == 'Not Yet':
        if 'Status' in df_filtered.columns:
            df_filtered = df_filtered[~df_filtered['Status'].isin(['RESOLVE', 'Invalid'])]

    # Filter berdasarkan Title Search
    if title_filter and 'Title' in df_filtered.columns:
        title_terms = [term.strip() for term in title_filter.split(',') if term.strip()]
        if title_terms:
            regex_pattern = '|'.join(map(re.escape, title_terms))
            df_filtered = df_filtered[df_filtered['Title'].astype(str).str.contains(regex_pattern, case=False, na=False)]
            
    return df_filtered

def reset_jira_filters(df_data: pd.DataFrame):
    """
    Mereset semua filter Streamlit session state yang berhubungan dengan JIRA ke nilai defaultnya.
    
    Args:
        df_data (pd.DataFrame): DataFrame JIRA asli untuk menentukan tanggal min/max.
    """
    # <<< BARIS BARU DITAMBAHKAN >>>
    st.session_state.pills_selection = None # Reset filter pills, sesuaikan key jika berbeda
    
    st.session_state.status_filter = []
    st.session_state.feature_filter = []
    st.session_state.platform_filter = []
    st.session_state.search_filter = ""
    st.session_state.labels_filter = []
    st.session_state.stage_filter = []
    st.session_state.solved_filter = None
    st.session_state.title_filter = ""
    
    if 'Created' in df_data.columns and not df_data['Created'].dropna().empty:
        min_date = df_data['Created'].dropna().min().date()
        max_date = df_data['Created'].dropna().max().date()
        st.session_state.date_filter = (min_date, max_date)
    else:
        st.session_state.date_filter = (None, None)
    
    st.session_state.current_page_col1 = 1
    st.session_state.selected_ticket_id = None
    st.session_state.selected_ticket_details = None

