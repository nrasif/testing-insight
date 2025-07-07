# components/filters.py
import streamlit as st
import pandas as pd
from datetime import date

# --- Adjust Python Path to import from root ---
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# A dictionary to define all filter keys and their default values.
# This makes initialization and resetting much cleaner.
FILTER_DEFAULTS = {
    "search_filter": "",
    "title_filter": "",
    "status_filter": [],
    "feature_filter": [],
    "platform_filter": [],
    "labels_filter": [],
    "stage_filter": [],
    "solved_filter": None,
    "pills_selection": None,
    "date_filter": (date.today(), date.today()) # Placeholder default
}

def initialize_filter_session_state(df: pd.DataFrame, force_reset=False):
    """
    Initializes or resets all filter-related session states from a single source of truth.
    - df: The original DataFrame, used to set the date range.
    - force_reset: If True, it will overwrite existing values with defaults.
    """
    # Initialize date filter separately as it depends on the data
    if 'date_filter' not in st.session_state or force_reset:
        if 'Created' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Created']) and not df['Created'].dropna().empty:
            valid_dates = df['Created'].dropna()
            st.session_state.date_filter = (valid_dates.min().date(), valid_dates.max().date())
        else:
            # Provide a sensible default if no data is available
            st.session_state.date_filter = (date.today(), date.today())

    # Initialize all other filters from the defaults dictionary
    for key, default_value in FILTER_DEFAULTS.items():
        if key == 'date_filter': continue # Skip date_filter as it's handled above
        if key not in st.session_state or force_reset:
            st.session_state[key] = default_value

    # Reset pagination for the ticket list when filters are reset
    if force_reset:
        if 'current_page' in st.session_state:
            st.session_state.current_page = 1
        if 'pagination_key_counter' in st.session_state:
            st.session_state.pagination_key_counter += 1


def render_filters(df: pd.DataFrame):
    """Renders all filter widgets in the Streamlit expander."""
    initialize_filter_session_state(df) # Ensure state exists before rendering

    # --- Row 1 ---
    search_col, _, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1.5, 0.05, 1, 1.3, 1, 1])

    with search_col:
        st.text_input("Ticket ID Search", placeholder="e.g. 1061, 998", key="search_filter", label_visibility="collapsed")

    with filter_col2:
        status_opts = sorted(df['Status'].astype(str).unique()) if 'Status' in df.columns else []
        st.multiselect("Status", options=status_opts, placeholder="Select Status", key='status_filter', label_visibility="collapsed")

    with filter_col3:
        feature_opts = sorted(df['Feature'].astype(str).unique()) if 'Feature' in df.columns else []
        st.multiselect("Feature", options=feature_opts, placeholder="Select Feature", key='feature_filter', label_visibility="collapsed")

    with filter_col4:
        platform_opts = sorted(df['Platform'].astype(str).unique()) if 'Platform' in df.columns else []
        st.multiselect("Platform", options=platform_opts, placeholder="Select Platform", key='platform_filter', label_visibility="collapsed")

    with filter_col5:
        # --- PERBAIKAN ---
        # Logika di sini diubah agar widget date_input selalu ditampilkan,
        # selama data tanggal yang valid ada di DataFrame.
        if 'Created' in df.columns and pd.api.types.is_datetime64_any_dtype(df['Created']) and not df['Created'].dropna().empty:
            min_date_bound = df['Created'].min().date()
            max_date_bound = df['Created'].max().date()
            
            st.date_input(
                "Date Range",
                min_value=min_date_bound,
                max_value=max_date_bound,
                format="DD/MM/YYYY",
                key='date_filter', # Kunci ini akan membaca dan menulis ke session_state
                label_visibility="collapsed"
            )
        else:
            st.info("Date filter not available.")


    # --- Row 2 ---
    label_col, stage_col, solved_col, title_col, reset_col = st.columns([0.8, 0.76, 1, 2.33, 1])

    with label_col:
        if "Labels" in df.columns and not df['Labels'].dropna().empty:
            labels = sorted(df['Labels'].dropna().str.split(',').explode().str.strip().unique())
            st.multiselect("Labels", options=[l for l in labels if l], placeholder="Select Labels", key='labels_filter', label_visibility="collapsed")

    with stage_col:
        stage_opts = sorted(df['Stage'].astype(str).unique()) if 'Stage' in df.columns else []
        st.multiselect("Stage", options=stage_opts, placeholder="Select Stage", key='stage_filter', label_visibility="collapsed")

    with solved_col:
        st.selectbox("Is it solved?", options=['Solved', 'Not Yet'], index=None, placeholder="Is it solved?", key='solved_filter', label_visibility="collapsed")

    with title_col:
        st.text_input("Title Search", placeholder='Keywords in Title', key='title_filter', label_visibility="collapsed")

    with reset_col:
        st.button(":material/refresh: Reset Filters", on_click=initialize_filter_session_state, args=(df, True), use_container_width=True, type="secondary")


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies all active filters from session_state to the DataFrame.
    This function now reads directly from st.session_state.
    """
    if df.empty:
        return df

    df_filtered = df.copy()

    # Text-based searches
    if st.session_state.get('search_filter'):
        search_terms = [term.strip() for term in st.session_state.search_filter.split(',') if term.strip()]
        if search_terms:
            df_filtered = df_filtered[df_filtered['Tickets'].astype(str).str.contains('|'.join(search_terms), case=False, na=False)]

    if st.session_state.get('title_filter'):
        title_terms = [term.strip() for term in st.session_state.title_filter.split(',') if term.strip()]
        if title_terms:
            df_filtered = df_filtered[df_filtered['Title'].astype(str).str.contains('|'.join(title_terms), case=False, na=False)]

    # Multi-select filters
    for key in ["status_filter", "feature_filter", "platform_filter", "stage_filter"]:
        # Derives the column name (e.g., 'status_filter' -> 'Status')
        column_name = key.replace('_filter', '').capitalize()
        if st.session_state.get(key):
            df_filtered = df_filtered[df_filtered[column_name].isin(st.session_state[key])]

    # Special handler for Labels (AND logic)
    if st.session_state.get('labels_filter'):
        for label in st.session_state.labels_filter:
            df_filtered = df_filtered[df_filtered['Labels'].astype(str).str.contains(label, case=False, na=False)]

    # --- Date Range Filter Logic ---
    date_filter_value = st.session_state.get('date_filter')
    if date_filter_value:
        start_date, end_date = None, None
        # Handle both single date and range selection
        if isinstance(date_filter_value, tuple) and len(date_filter_value) == 1:
            start_date = date_filter_value[0]
            end_date = start_date  # Treat single date as a one-day range
        elif isinstance(date_filter_value, tuple) and len(date_filter_value) == 2:
            start_date, end_date = date_filter_value

        # Apply the filter if the dates are valid
        if start_date and end_date and pd.api.types.is_datetime64_any_dtype(df_filtered['Created']):
             df_filtered = df_filtered[df_filtered['Created'].dt.date.between(start_date, end_date)]

    # Single-select filters
    if st.session_state.get('solved_filter'):
        is_solved = st.session_state.solved_filter == 'Solved'
        if 'Resolved_Time' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['Resolved_Time'].notna() if is_solved else df_filtered['Resolved_Time'].isna()]

    return df_filtered.reset_index(drop=True)
