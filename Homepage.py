import streamlit as st
import base64
from pathlib import Path

# --- Fungsi untuk menyisipkan gambar lokal sebagai Base64 ---
def get_image_as_base64(path):
    """Membaca file gambar lokal dan mengubahnya menjadi string Base64."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        st.warning(f"Gambar tidak ditemukan di: {path}. Pastikan path dan nama file benar.")
        # Mengembalikan placeholder abu-abu jika gambar tidak ada
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mN8/x8AAuMB8DtXNJsAAAAASUVORK5CYII="

pages = {
    "JIRA": [
        st.Page("pages/1_JIRA Tickets.py", title="JIRA View"),
        st.Page("pages/2_JIRA Dashboard.py", title="Dashboard")
    ],
    "Knowledge Center": [
        st.Page("pages/3_QAChatbot.py", title="Chatbot"),
        st.Page("pages/4_Knowledge Center.py", title="Documentation")
    ],
}

# Create the navigation object
pg = st.navigation(pages, position='top')

st.set_page_config(
    page_title="IntipinJira",
    page_icon="✅",
    layout="wide"
)

# Run the navigation. This will display the sidebar and the selected page's content.
pg.run()