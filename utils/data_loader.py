# utils/data_loader.py
import pandas as pd
import streamlit as st
from .gdrive_conn import get_list_files, read_file_from_drive
from .jira_processed import jiraProgress_proc

def load_and_process_jira_data(filename: str) -> pd.DataFrame:
    """
    Handles the entire data loading and processing pipeline.
    1. Finds the file on Google Drive.
    2. Reads the file content.
    3. Converts it to a DataFrame.
    4. Processes the DataFrame using jiraProgress_proc.
    5. Returns the cleaned DataFrame.
    """
    try:
        all_files = get_list_files()
        file_id = all_files.get(filename)

        if not file_id:
            st.error(f"File '{filename}' not found in Google Drive.")
            return pd.DataFrame()

        file_content = read_file_from_drive(file_id)
        df_raw = pd.read_csv(file_content)
        df_processed = jiraProgress_proc(df_raw)

        # Ensure 'Created' column is datetime
        if 'Created' in df_processed.columns:
            df_processed['Created'] = pd.to_datetime(df_processed['Created'], errors='coerce')

        # Ensure 'Resolved_Time' column is datetime
        if 'Resolved_Time' in df_processed.columns:
            df_processed['Resolved_Time'] = pd.to_datetime(df_processed['Resolved_Time'], errors='coerce')

        return df_processed

    except ValueError as ve:
        st.error(f"Error during data processing: {ve}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"An unexpected error occurred while loading data: {e}")
        return pd.DataFrame()
