import streamlit as st
import pandas as pd
import re
from datetime import datetime #
from utils.jira_processed import jiraProgress_proc
from datetime import datetime, timedelta

from utils.gdrive_conn import get_list_files, read_file_from_drive
from utils.jira_processed import jiraProgress_proc
from components.filters import apply_filters, reset_jira_filters

st.set_page_config(page_title='BSI Testing Insight', layout='wide')
st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
        
        /* Ini adalah font default untuk seluruh aplikasi */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
    </style>
""")

@st.cache_data
def load_and_process_jira_data(filename: str) -> pd.DataFrame:
    """
    Fungsi ini melakukan seluruh proses:
    1. Mencari file di Google Drive.
    2. Membaca konten file.
    3. Mengubahnya menjadi DataFrame.
    4. Memproses DataFrame.
    5. Mengembalikan DataFrame yang sudah bersih.
    
    Decorator @st.cache_data di sini sangat efisien karena akan men-cache
    hasil akhir (DataFrame yang sudah diproses), sehingga seluruh proses
    di atas hanya berjalan sekali.
    """
    try:
        all_files = get_list_files()
        file_id = all_files.get(filename)
        
        if not file_id:
            st.error(f"File '{filename}' tidak ditemukan di Google Drive.")
            return pd.DataFrame()

        file_content = read_file_from_drive(file_id)
        df_raw = pd.read_csv(file_content)
        df_processed = jiraProgress_proc(df_raw)
        
        return df_processed

    except ValueError as ve:
        st.error(f"Error saat memproses data: {ve}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Terjadi kesalahan yang tidak terduga: {e}")
        return pd.DataFrame()

# Nama file yang ingin kita proses
NAMA_FILE_JIRA = 'jira_tiket.csv' 

# Cukup panggil satu fungsi ini untuk mendapatkan data matang
with st.spinner("Sabar yah, lagi ngeload datanya nih hehe..", show_time=True):
    df_jira_original = load_and_process_jira_data(NAMA_FILE_JIRA)


# 1. Validasi kolom 'Created' dan siapkan filter tanggal
if 'Created' not in df_jira_original.columns or df_jira_original['Created'].dropna().empty:
    st.warning("Kolom 'Created' tidak ada atau kosong. Filter tanggal tidak dapat digunakan.")
    min_date_data = None
    max_date_data = None
else:
    # 2. Jika kolom tanggal ada dan valid, lanjutkan proses
    
    # Konversi tipe data jika perlu
    if not pd.api.types.is_datetime64_any_dtype(df_jira_original['Created']):
        df_jira_original['Created'] = pd.to_datetime(df_jira_original['Created'], errors='coerce')

    # 3. Dapatkan rentang tanggal AKTUAL dari data
    valid_dates = df_jira_original['Created'].dropna()
    min_date_data = valid_dates.min().date()
    max_date_data = valid_dates.max().date()

    # 4. Inisialisasi session_state HANYA jika belum ada
    if 'date_filter' not in st.session_state:
        st.session_state.date_filter = (min_date_data, max_date_data)

# Inisialisasi semua state filter HANYA JIKA belum ada
if "status_filter" not in st.session_state:
    st.session_state.status_filter = []
if "feature_filter" not in st.session_state:
    st.session_state.feature_filter = []
if "platform_filter" not in st.session_state:
    st.session_state.platform_filter = []
if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""
if "labels_filter" not in st.session_state:
    st.session_state.label_filter = []
if "stage_filter" not in st.session_state:
    st.session_state.stage_filter = []
if "solved_filter" not in st.session_state:
    st.session_state.solved_filter = None
if "title_filter" not in st.session_state:
    st.session_state.title_filter = ""

# Wrapper function untuk tombol reset
def reset_all_filters_wrapper(df_data: pd.DataFrame):
    """
    Fungsi pembungkus untuk memanggil reset_jira_filters dari modul filters.py.
    """
    reset_jira_filters(df_data)

def svg_to_img(icon_svg):
    """
    Membuat string HTML untuk placeholder yang bisa dipakai ulang.
    Input:
    - icon_svg (string): Kode mentah SVG untuk ikon.
    """
    # "Bungkus" SVG menjadi format Data URI yang bisa dibaca tag <img>
    encoded_svg = urllib.parse.quote("".join(line.strip() for line in icon_svg.split("\n")))
    data_uri = f"data:image/svg+xml;charset=utf-8,{encoded_svg}"
    
    return data_uri

def duration_to_hours(duration_str):
    if not isinstance(duration_str, str) or duration_str.strip() == '':
        return np.nan
    total_hours = 0
    hari_match = re.search(r'(\d+)\s*hari', duration_str)
    if hari_match:
        total_hours += int(hari_match.group(1)) * 24
    jam_match = re.search(r'(\d+)\s*jam', duration_str)
    if jam_match:
        total_hours += int(jam_match.group(1))
    menit_match = re.search(r'(\d+)\s*menit', duration_str)
    if menit_match:
        total_hours += int(menit_match.group(1)) / 60
    return total_hours if total_hours > 0 else np.nan

def format_hours_to_days_hours(total_hours):
    if pd.isna(total_hours) or total_hours < 0:
        return "N/A"
    if total_hours < 1:
        minutes = round(total_hours * 60)
        if minutes == 0 and total_hours > 0:
            return "Kurang dari 1 menit"
        return f"{minutes} menit"
    days = int(total_hours // 24)
    remaining_hours = int(total_hours % 24)
    parts = []
    if days > 0:
        parts.append(f"{days} hari")
    if remaining_hours > 0:
        parts.append(f"{remaining_hours} jam")
    return " ".join(parts) if parts else f"{days} hari"

with open('css/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html = True)
    
st.html(
    f"""
    <p style="margin-bottom: 20px;">
        <span class='green_text'>JIRA</span>
        <span class='black_text'>Dashboard</span>
    </p>
    """
)

# Filter Section
with st.expander(':material/tune: Filter', expanded=False):

    search_col, or_col, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([1.5, 0.05, 1, 1.3, 1, 1]) # Sesuaikan rasio jika perlu

    with search_col:
        ticket_id_search = st.text_input(
            label="Ticket ID Search",
            placeholder="Ticket Code (can be multiple  e.g. 1061, 998)",
            label_visibility="collapsed",
            key="search_filter"
        )
        
    with or_col:
        st.markdown("""
                    <style>
                    .separator-line {
                        /* Gaya default (desktop) adalah garis vertikal */
                        border-left: 2px solid #e0e0e0;
                        height: 40px;
                        margin: 0 auto;
                    }

                    /* Di HP, kita ubah total gayanya */
                    @media (max-width: 768px) {
                    .separator-line {
                        border-left: none; /* Hapus garis kiri */
                        border-top: 1px solid #e0e0e0; /* Ganti dengan garis atas (jadi horizontal) */
                        height: 0; /* Tinggi direset */
                        width: 80%; /* Lebar garis horizontalnya 80% dari kolom */
                        margin: 15px auto; /* Beri jarak atas dan bawah */
                    }
                    }
                    </style>
                    <div class="separator-line"></div>
                """, unsafe_allow_html=True)

    with filter_col2:
        status_opt_dynamic = []
        if 'Status' in df_jira_original.columns and not df_jira_original.empty:
            status_opt_dynamic = sorted(df_jira_original['Status'].astype(str).unique().tolist())
        
        status_selected = st.multiselect(
            label='Status',
            placeholder='Select Status',
            options=status_opt_dynamic,
            label_visibility="collapsed",
            key='status_filter',
        )

    with filter_col3:
        feature_opt_dynamic = []
        if 'Feature' in df_jira_original.columns and not df_jira_original.empty:
            feature_opt_dynamic = sorted(df_jira_original['Feature'].astype(str).unique().tolist())

        feature_selected = st.multiselect(
            label='Feature',
            placeholder='Select Feature',
            options=feature_opt_dynamic,
            label_visibility="collapsed",
            key='feature_filter',
        )

    with filter_col4:
        platform_opt_dynamic = []
        if 'Platform' in df_jira_original.columns and not df_jira_original.empty:
            # Ambil semua platform unik dulu
            unique_platforms = df_jira_original['Platform'].astype(str).unique().tolist()
            
            undesired_options = ["android & ios", "android&ios", "ios & android", "ios&android"]
            platform_opt_dynamic = sorted([
                p for p in unique_platforms 
                if p.lower().replace(" ", "") not in undesired_options
            ])
            
        platform_selected = st.multiselect(
            label='Platform',
            placeholder='Select Platform',
            options=platform_opt_dynamic,
            label_visibility="collapsed",
            key='platform_filter',
        )

    with filter_col5:
        # Pastikan min_value dan max_value tidak None jika df_jira_original kosong
        if min_date_data is not None and max_date_data is not None:
            created_date_range = st.date_input(
                "Date Range",
                min_value=min_date_data,
                max_value=max_date_data,
                format="DD/MM/YYYY",
                label_visibility="collapsed",
                key='date_filter'
            )
        else:
            st.warning("Tanggal tidak tersedia untuk filter. Pastikan kolom 'Created' ada dan berisi data.")
            created_date_range = None # Atau set ke nilai default lain yang sesuai


    label_col, stage_col, solved_col, title_col, reset_col = st.columns([0.8, 0.76, 1, 2.33, 1]) # Kolom search 4x lebih lebar dari tombol

    with label_col:
        label_opt_dynamic = []
        if "Labels" in df_jira_original.columns and not df_jira_original['Labels'].dropna().empty:
            exploded_labels = df_jira_original['Labels'].dropna().str.split(',').explode()
            unique_labels = sorted(exploded_labels.str.strip().unique())
            
            label_opt_dynamic = [label for label in unique_labels if label]
        
        # Kode multiselect lo tetap sama
        label_selected = st.multiselect(
            label='Labels',
            placeholder='Select Labels',
            options=label_opt_dynamic,
            label_visibility="collapsed",
            key='labels_filter',
        )
        
    with stage_col:
        stage_opt_dynamic = []
        if "Stage" in df_jira_original.columns and not df_jira_original['Stage'].dropna().empty:
            stage_opt_dynamic = sorted(df_jira_original['Stage'].astype(str).unique().tolist())
            
            stage_selected = st.multiselect(
            label='Stage',
            placeholder='Select Stage',
            options=stage_opt_dynamic,
            label_visibility="collapsed",
            key='stage_filter',
            )
    
    with solved_col:
        solved_opt = ['Solved', 'Not Yet']
        
        solved_selected = st.selectbox(
            label = 'Solved',
            placeholder='Is it solved?',
            options = solved_opt,
            label_visibility='collapsed',
            index=None,
            key='solved_filter'
        )
    
    with title_col:
        title_search = st.text_input(
            label="Title Search",
            placeholder='Keywords in Title (can be multiple e.g. card, liabilities)',
            label_visibility='collapsed',
            key='title_filter'
        )

    with reset_col:
        # Ini tombol resetnya, ditaruh di kolom sebelahnya
        st.button(
            ":material/refresh: Reset Filters", 
            on_click=reset_all_filters_wrapper, # Panggil fungsi reset_all_filters_wrapper
            args=(df_jira_original,),
            use_container_width=True,
            type="secondary" # Membuat tombol terlihat 'secondary' (biasanya abu-abu)
        )
        
df_filtered = apply_filters(
    df_jira_original,
    st.session_state.search_filter,
    st.session_state.status_filter,
    st.session_state.feature_filter,
    st.session_state.platform_filter,
    st.session_state.date_filter,
    st.session_state.labels_filter,
    st.session_state.stage_filter,
    st.session_state.solved_filter,
    st.session_state.title_filter
)


df_filtered['Resolved_Time'] = pd.to_datetime(df_filtered['Resolved_Time'], errors='coerce')

total_open_tickets = (df_filtered['Resolved_Time'].isna() & (df_filtered['Status'] != 'Invalid')).sum()
total_solved_tickets = (df_filtered['Resolved_Time'].notna()).sum()
total_invalid_ticket = (df_filtered['Status'] == 'Invalid').sum()

solved_tickets_df = df_filtered[df_filtered['Resolved_Time'].notna()].copy()
solved_tickets_df['duration_hours'] = solved_tickets_df['Duration_toResolve'].apply(duration_to_hours)
avg_duration_in_hours = solved_tickets_df['duration_hours'].mean()
formatted_avg_duration = format_hours_to_days_hours(avg_duration_in_hours)


