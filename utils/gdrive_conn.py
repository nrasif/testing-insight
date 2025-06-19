import streamlit as st
import pandas as pd


import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

from secrets_api.googledrive_api import SCOPE_ID, SERVICE_ACC_ID, PARENT_FOLDER

@st.cache_data
def authenticate():
    """Autentikasi ke Google Drive menggunakan Service Account."""
    creds = service_account.Credentials.from_service_account_file(SERVICE_ACC_ID, scopes=SCOPE_ID)
    return creds

@st.cache_data
def get_list_files():
    """Mengambil daftar file dari parent folder yang ditentukan."""
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(
        q=f"'{PARENT_FOLDER}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name, modifiedTime)'
    ).execute()
    items = results.get('files', [])
    return {item['name']: item['id'] for item in items}

@st.cache_data
def read_file_from_drive(file_id):
    """Membaca konten file dari Google Drive berdasarkan ID-nya."""
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    file_data = BytesIO()
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    file_data.seek(0)
    return file_data