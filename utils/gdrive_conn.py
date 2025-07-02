

import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

@st.cache_data
def authenticate():
    """
    Autentikasi ke Google Drive menggunakan credentials dari st.secrets.
    """

    creds_dict = st.secrets["gcp_service_account"]

    scope = st.secrets["gdrive_config"]["SCOPE_ID"]

    creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scope)
    return creds

@st.cache_data
def get_list_files():
    """
    Mengambil daftar file dari parent folder yang ditentukan di st.secrets.
    """
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    parent_folder = st.secrets["gdrive_config"]["PARENT_FOLDER"]
    
    results = service.files().list(
        q=f"'{parent_folder}' in parents and trashed=false",
        spaces='drive',
        fields='files(id, name, modifiedTime)'
    ).execute()
    
    items = results.get('files', [])
    return {item['name']: item['id'] for item in items}

@st.cache_data
def read_file_from_drive(file_id):
    """
    Membaca konten file dari Google Drive berdasarkan ID-nya.
    Fungsi ini tidak perlu diubah karena sudah memanggil authenticate() yang baru.
    """
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