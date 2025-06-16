import streamlit as st
import pandas as pd

def jiraProgress_proc(path):
    """
    Loads JIRA data from a CSV file and performs basic processing.
    """
    try:
        df = pd.read_csv(path)

        # Pastikan kolom-kolom inti ada dan konversi tipe data jika perlu
        if 'Tickets' not in df.columns or 'Title' not in df.columns:
            st.error("Kolom 'Tickets' atau 'Title' tidak ditemukan dalam file CSV. Aplikasi mungkin tidak berfungsi dengan benar.")
            # Kembalikan DataFrame kosong dengan kolom esensial jika kolom inti tidak ada
            return pd.DataFrame(columns=['Tickets', 'Title', 'Status', 'Feature', 'Platform', 'Created', 'Severity', 'Reporter'])

        if 'Created' in df.columns:
            df['Created'] = pd.to_datetime(df['Created'], errors='coerce')
        else:
            st.warning("Kolom 'Created' tidak ditemukan. Filter tanggal mungkin tidak berfungsi.")
            df['Created'] = pd.NaT # Tambahkan kolom kosong jika tidak ada agar filter tidak error

        # Konversi kolom lain ke string untuk konsistensi tampilan jika belum
        for col in ['Tickets', 'Title', 'Status', 'Feature', 'Platform', 'Severity', 'Reporter']:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('N/A') # Isi NaN dengan 'N/A' setelah jadi string
            elif col in ['Tickets', 'Title']: # Kolom wajib
                 st.error(f"Kolom wajib '{col}' tidak ada.")
                 df[col] = 'N/A'


        return df

    except FileNotFoundError:
        st.error(f"ERROR: File data JIRA '{path}' tidak ditemukan. Mohon periksa path file.")
        # Kembalikan DataFrame kosong dengan kolom esensial
        return pd.DataFrame(columns=['Tickets', 'Title', 'Status', 'Feature', 'Platform', 'Created', 'Severity', 'Reporter'])
    except pd.errors.EmptyDataError:
        st.warning(f"PERINGATAN: File data JIRA '{path}' kosong.")
        return pd.DataFrame(columns=['Tickets', 'Title', 'Status', 'Feature', 'Platform', 'Created', 'Severity', 'Reporter'])
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data JIRA dari '{path}': {e}")
        return pd.DataFrame(columns=['Tickets', 'Title', 'Status', 'Feature', 'Platform', 'Created', 'Severity', 'Reporter'])