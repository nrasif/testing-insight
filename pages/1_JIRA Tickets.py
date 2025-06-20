import streamlit as st
import pandas as pd
from utils.jira_processed import jiraProgress_proc
from datetime import datetime, timedelta
import urllib.parse
import json
import plotly.graph_objects as go
import numpy as np # Pastikan numpy diimpor karena digunakan oleh duration_to_hours dan format_hours_to_days_hours

import re
from streamlit_extras.stylable_container import stylable_container
import streamlit_antd_components as sac

from utils.gdrive_conn import get_list_files, read_file_from_drive
from utils.jira_processed import jiraProgress_proc

# --- Import fungsi filter dari modul terpisah ---
from components.filters import apply_filters, reset_jira_filters

# JIRA_PATH = "data/jira_tiket.csv"
CSS_PATH = 'css/style.css'
TICKETS_PER_PAGE = 20

st.set_page_config(
    page_title="IntipinJira",
    page_icon="✅",
    layout='wide'
    )

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
    st.session_state.labels_filter = []
if "stage_filter" not in st.session_state:
    st.session_state.stage_filter = []
if "solved_filter" not in st.session_state:
    st.session_state.solved_filter = None
if "title_filter" not in st.session_state:
    st.session_state.title_filter = ""
    
# Inisialisasi untuk logika pagination dan state management
if 'current_page_col1' not in st.session_state:
    st.session_state.current_page_col1 = 1
if 'selected_ticket_id' not in st.session_state:
    st.session_state.selected_ticket_id = None
if 'selected_ticket_details' not in st.session_state:
    st.session_state.selected_ticket_details = None
if "last_filters" not in st.session_state:
    st.session_state.last_filters = {}
if 'filter_just_changed' not in st.session_state:
    st.session_state.filter_just_changed = False
if 'pagination_key_counter' not in st.session_state:
    st.session_state.pagination_key_counter = 0

# Wrapper function untuk tombol reset
def reset_all_filters_wrapper(df_data: pd.DataFrame):
    """
    Fungsi pembungkus untuk memanggil reset_jira_filters dari modul filters.py.
    """
    reset_jira_filters(df_data)
    st.session_state.current_page_col1 = 1

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


try:
    with open(CSS_PATH) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning(f"CSS file '{CSS_PATH}' not found.")

st.markdown(
    f"""
    <p style="font-size: 24px; margin-bottom: 20px;">
        <span class='green_text'>JIRA</span>
        <span class='black_text'>View</span>
    </p>
    """,
    unsafe_allow_html=True
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
current_filters = {
    "search": st.session_state.search_filter,
    "status": st.session_state.status_filter,
    "feature": st.session_state.feature_filter,
    "platform": st.session_state.platform_filter,
    "date": st.session_state.date_filter,
    "labels": st.session_state.labels_filter,
    "stage": st.session_state.stage_filter,
    "solved": st.session_state.solved_filter,
    "title": st.session_state.title_filter
}

if st.session_state.get('last_filters', {}) != current_filters:
    st.session_state.filter_just_changed = True
    st.session_state.current_page_col1 = 1
    st.session_state.last_filters = current_filters
    
    # TAMBAHKAN INI: NAIKKAN COUNTER UNTUK MERESET VISUAL PAGINATION
    st.session_state.pagination_key_counter += 1
else:
    st.session_state.filter_just_changed = False

# --- Menerapkan Filter menggunakan fungsi dari filters.py ---
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



# 1. Konversi kolom waktu
df_filtered['Resolved_Time'] = pd.to_datetime(df_filtered['Resolved_Time'], errors='coerce')

# 2. Hitung tiket open & solved
total_open_tickets = (df_filtered['Resolved_Time'].isna() & (df_filtered['Status'] != 'Invalid')).sum()
total_solved_tickets = (df_filtered['Resolved_Time'].notna()).sum()
total_invalid_ticket = (df_filtered['Status'] == 'Invalid').sum()


# 3. Hitung rata-rata waktu penyelesaian
solved_tickets_df = df_filtered[df_filtered['Resolved_Time'].notna()].copy()
solved_tickets_df['duration_hours'] = solved_tickets_df['Duration_toResolve'].apply(duration_to_hours)
avg_duration_in_hours = solved_tickets_df['duration_hours'].mean()
formatted_avg_duration = format_hours_to_days_hours(avg_duration_in_hours)


# 4. Tampilkan metrik
col1, col2, col3, col4 = st.columns(4)

with col1:
    with stylable_container(
        key="open_tickets_metric",
        css_styles="""
            div[data-testid="stMetricValue"] {
                font-weight: 600;
            }
            
            div[data-testid="stMetric"] {
                
                border: 2px solid #dee2e6;
                border-radius: 1rem;
                transition: all 0.2s ease-in-out;
            }

            div[data-testid="stMetric"]:hover {
                
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                transform: scale(1.01);
                z-index: 10;
            }
            """
    ):
        st.metric("Total Open Tickets", f"{total_open_tickets}", border=True, help='Ticket that is not solved with status include everything except "Resolve" and "Invalid"' )

with col2:
    with stylable_container(
        key="solved_tickets_metric",
        css_styles="""
            div[data-testid="stMetricValue"] {
                font-weight: 600;
            }
        
            div[data-testid="stMetric"] {
                
                border: 2px solid #dee2e6;
                border-radius: 1rem;
                transition: all 0.2s ease-in-out;
            }

            div[data-testid="stMetric"]:hover {
                
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                transform: scale(1.01);
                z-index: 10;
            }
            """
    ):
        st.metric("Solved Tickets", f"{total_solved_tickets}", border=True, help='Ticket that is solved')
        
with col3:
    with stylable_container(
        key="invalid_tickets_metric",
        css_styles="""
        
            div[data-testid="stMetricValue"] {
                font-weight: 600;
            }
            
            div[data-testid="stMetric"] {
                
                border: 2px solid #dee2e6;
                border-radius: 1rem;
                transition: all 0.2s ease-in-out;
            }

            div[data-testid="stMetric"]:hover {
                
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                transform: scale(1.01);
                z-index: 10;
            }
            """
    ):
        st.metric("Invalid Ticket", f"{total_invalid_ticket}", border=True, help='Ticket that is Invalid')

with col4:
    with stylable_container(
        key="average_tickets_metric",
        css_styles="""
            div[data-testid="stMetricValue"] {
                font-weight: 600;
            }
        
            div[data-testid="stMetric"] {
                
                border: 2px solid #dee2e6;
                border-radius: 1rem;
                transition: all 0.2s ease-in-out;
            }

            div[data-testid="stMetric"]:hover {
                
                box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                transform: scale(1.01);
                z-index: 10;
            }
            """
    ):
        st.metric("Average Time to Solved", formatted_avg_duration, border=True, help='Average time for ticket to solved or closed')
        
st.markdown("<div style='margin-top:20px;'> </div>", unsafe_allow_html=True)

# Session State
if 'current_page_col1' not in st.session_state: # ini page si user disimpen ke dalem session_state, kalo misal baru, halaman 1
    st.session_state.current_page_col1 = 1
if 'selected_ticket_id' not in st.session_state: # ini buat nampung id tiket yang dipilih sama user, kalo ga ada, None
    st.session_state.selected_ticket_id = None
if 'selected_ticket_details' not in st.session_state: # ini buat nampung detail tiket yang abis dipilih user, kalo ga ada, None
    st.session_state.selected_ticket_details = None

if "title_filter" not in st.session_state:
    st.session_state.title_filter = ""
if "last_filters" not in st.session_state:
    st.session_state.last_filters = {}
if 'filter_just_changed' not in st.session_state:
    st.session_state.filter_just_changed = False
if 'reset_counter' in st.session_state:
    del st.session_state['reset_counter']
if 'pagination_key_counter' not in st.session_state:
    st.session_state.pagination_key_counter = 0


main_col1, main_col2, main_col3 = st.columns([0.1, 0.4, 0.2])

with main_col1:

    if df_filtered.empty or not ('Tickets' in df_filtered.columns and 'Title' in df_filtered.columns):
        st.info("Sorry! There are no tickets matching the selected filters")
    else:
        
        hot_opt = ["Recent", "Hot"]
        # Saran: Tambahkan key di sini dan masukkan ke 'current_filters' agar lebih konsisten
        hot_selection = st.pills(" ", hot_opt, label_visibility='collapsed', key="hot_filter")
        
        df_for_display = df_filtered.copy()
        if hot_selection == "Hot":
            if 'Count_Comments' in df_for_display.columns:
                df_for_display = df_for_display[df_for_display['Count_Comments'] > 3].reset_index(drop=True)
        elif hot_selection == "Recent":
            if 'Created' in df_for_display.columns:
                df_for_display['Created'] = pd.to_datetime(df_for_display['Created'])
                df_for_display = df_for_display.sort_values(by='Created', ascending=False).reset_index(drop=True)
                
        total_tickets = len(df_for_display)
        total_pages = (total_tickets - 1) // TICKETS_PER_PAGE + 1 if total_tickets > 0 else 1

        # Logika validasi out-of-bounds ini tetap penting
        if st.session_state.current_page_col1 > total_pages:
            st.session_state.current_page_col1 = 1
        
        current_page = st.session_state.get('current_page_col1', 1)
        
        start_idx = (current_page - 1) * TICKETS_PER_PAGE
        end_idx = min(start_idx + TICKETS_PER_PAGE, total_tickets)
        
        tickets_to_display = df_for_display.iloc[start_idx:end_idx]
        
        ticket_list_container = st.container(height=1190, border=False)
        with ticket_list_container:
            if tickets_to_display.empty:
                st.write("There are no tickets to display on this page.")
            else:
                for index, row in tickets_to_display.iterrows():
                    # ... (kode looping tombol tiketmu tetap sama)
                    ticket_id = str(row['Tickets'])
                    ticket_title = str(row['Title'])
                    comment_count = row.get('Count_Comments', 0)
                    shortened_title = ticket_title
                    try:
                        title_parts = ticket_title.split(' - ')
                        shortened_title = title_parts[2].strip() if len(title_parts) > 2 else title_parts[-1].strip()
                    except Exception:
                        shortened_title = ticket_title
                    button_key = f"select_{ticket_id}"
                    indicator = "🔥 " if comment_count > 3 else ""
                    button_label = f"{indicator}**{ticket_id}**: {shortened_title}"
                    if st.button(button_label, key=button_key, use_container_width=True):
                        st.session_state.selected_ticket_id = ticket_id
                        st.session_state.selected_ticket_details = row.to_dict()
                        
        if total_pages > 1:
            st.markdown("<div style='margin-top:20px;'> </div>", unsafe_allow_html=True)
            new_page = sac.pagination(
                total=total_tickets,
                page_size=TICKETS_PER_PAGE,
                align='start',
                variant='light',
                size='md',
                color='green',
                show_total=False,
                simple=True,
                key=f"sac_pagination_col1_{st.session_state.pagination_key_counter}"
            )
            
            # Logika di bawah ini tetap sama dan sudah benar
            if not st.session_state.filter_just_changed and new_page != current_page:
                st.session_state.current_page_col1 = new_page
                st.rerun()
                
with main_col2:
    
    details_container = st.container(height=1300, key='main_col2', border=True) 
    
    if st.session_state.selected_ticket_details:
        ticket = st.session_state.selected_ticket_details

        # --- Mulai Bangun SATU String HTML untuk Seluruh Konten ---
        details_html = "<div style='padding: 0px 20px;'>" 

        # Ambil kode tiket untuk membuat URL
        ticket_code = ticket.get('Tickets', 'N/A')
        ticket_url = f"https://itproject.bankbsi.co.id/browse/{ticket_code}"

        # -- Bagian 1: Judul Utama dengan Tombol Link Beranimasi --
        details_html += f"""
        
        <style>
        .jira-button {{
            display: inline-block;
            padding: 2px 10px;
            font-size: 0.85em;
            font-weight: 600;
            color: white;
            background-color: #EAEAEA; /* Warna biru primer */
            border: none;
            border-radius: 5px;
            text-decoration: none;
            text-align: center;
            cursor: pointer;
            margin-bottom: 2px;
            transition: all 0.2s ease-in-out; /* INI KUNCI ANIMASI HALUS */
        }}

        /* Efek saat kursor mouse di atas tombol */
        .jira-button:hover {{
            transform: translateY(-2px); /* Tombol sedikit terangkat */
        }}

        /* Efek saat tombol DITEKAN (diklik) */
        .jira-button:active {{
            transform: translateY(1px); /* Tombol terlihat seperti ditekan ke dalam */
        }}
        </style>
        
        <div style="padding-top: 20px; margin-bottom: 20px;">
            
            <div style="display: flex; align-items: center; margin-bottom: 2px;">
            
                <p style="font-size: 0.9em; color: #6c757d; font-weight: 400; margin: 0;">
                    {ticket_code}
                </p>
                
                <a href="{ticket_url}" target="_blank" class="jira-button" style="margin-left: 12px; color: #495057;">
                    Open in JIRA
                </a>

            </div>

            <h2 style="font-size: 1.8em; font-weight: 600; color: #212529; margin-top: 0px; margin-bottom: 0px; line-height: 1.3;">
                {ticket.get('Title', 'N/A')}
            </h2>
        </div>
        """

        
        # -- Helper function untuk render item metadata --
        def render_meta_item_html(label, value, default_val="–"):
            display_value = value if pd.notna(value) and str(value).strip() and str(value).lower() not in ['nan', 'nat', 'none', ''] else default_val
            return f"""
            <div style="margin-bottom: 18px;"> 
                <p style="font-size: 0.7em; color: #6c757d; margin-bottom: 2px; text-transform: uppercase; font-weight: 500; letter-spacing: 0.5px;">{label}</p>
                <p style="font-size: 0.9em; color: #212529; margin-bottom: 0px; line-height: 1.3;">{display_value}</p>
            </div>
            """
        
        # --- Baris 1: Layout Utama (2 Kolom: Info Kiri & Rincian Waktu Kanan) ---
        details_html += "<div style='display: grid; grid-template-columns: 1fr 1fr; grid-gap: 35px; align-items: start;'>"

        # -- KONTEN KOLOM KIRI: SEMUA METADATA UTAMA --
        col1_content = "<div>" # Pembungkus untuk semua konten di kolom kiri
        
        status_val = ticket.get('Status', 'N/A')
        status_bg_color = "#e9ecef"; status_text_color = "#495057"
        s_clean = str(status_val).lower()
        if any(term in s_clean for term in ["done", "passed", "closed", "resolve"]):
            status_bg_color = "rgba(40, 167, 69, 0.1)"; status_text_color = "#198754";
        elif any(term in s_clean for term in ["progress", "checking", "development"]):
            status_bg_color = "rgba(13, 110, 253, 0.1)"; status_text_color = "#0a58ca";
        elif any(term in s_clean for term in ["to do", "open", "regression"]):
            status_bg_color = "rgba(255, 193, 7, 0.15)"; status_text_color = "#B28400";
        elif any(term in s_clean for term in ["blocked", "failed"]):
            status_bg_color = "rgba(220, 53, 69, 0.1)"; status_text_color = "#dc3545";
        
        col1_content += f"""
        <div style="margin-bottom: 18px;">
            <p style="font-size: 0.7em; color: #6c757d; margin-bottom: 4px; text-transform: uppercase; font-weight: 500; letter-spacing: 0.5px;">Status</p>
            <span style="background-color: {status_bg_color}; color: {status_text_color}; padding: 5px 10px; border-radius: 5px; font-size: 0.85em; font-weight: 500; display: inline-block;">
                {status_val}
            </span>
        </div>
        """
        severity_val = str(ticket.get('Severity', 'N/A')).upper()
        severity_text_color = "#212529"
        if severity_val in ["HIGHEST", "CRITICAL", "BLOCKER"]: severity_text_color = "#D63329";
        elif severity_val in ["HIGH", "MAJOR"]: severity_text_color = "#E57300";
        elif severity_val in ["MEDIUM", "NORMAL"]: severity_text_color = "#B28400";
        elif severity_val in ["LOW", "LOWEST", "MINOR"]: severity_text_color = "#0D6EFD";
        severity_html_part = render_meta_item_html("Severity", severity_val)
        col1_content += severity_html_part.replace(f">{severity_val}<", f"><span style='color: {severity_text_color}; font-weight: 600;'>{severity_val}</span><")
        
        col1_content += render_meta_item_html("Feature", ticket.get('Feature'))
        col1_content += render_meta_item_html("Platform", ticket.get('Platform'))
        bug_type_val = ticket.get('Bug Type') or "UNCLASSIFIED"
        col1_content += render_meta_item_html("Bug Type", bug_type_val)
        col1_content += render_meta_item_html("Labels", ticket.get('Labels'))
        col1_content += render_meta_item_html("Fix Versions", ticket.get('Fix_Versions'))
        col1_content += render_meta_item_html("Stage", ticket.get('Stage'))
        col1_content += render_meta_item_html("Device", ticket.get('Device'))

        col1_content += "</div>"
        details_html += col1_content

        col2_content = "<div style='background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; height: 100%;'>"
        col2_content += "<p style='font-size: 0.8em; color: #495057; margin-top: 0; margin-bottom: 20px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;'>Additional Information</p>"
        
        readable_date_format = '%d %B %Y, %H:%M'

        # Helper function baru untuk memformat tanggal dengan aman
        def format_date_safe(date_string):
            if pd.notna(date_string) and str(date_string).strip() and str(date_string) != '–':
                try:
                    # Coba parse dan format tanggalnya
                    return pd.to_datetime(date_string).strftime(readable_date_format) + " WIB"
                except (ValueError, TypeError, pd.errors.ParserError):
                    # Jika gagal, kembalikan string aslinya
                    return str(date_string)
            return "–"
        
        created_str = format_date_safe(ticket.get('Created'))
        resolved_str = format_date_safe(ticket.get('Resolved_Time'))
        tested_str = format_date_safe(ticket.get('Testing_Time'))
        last_update_val = ticket.get('Time_Since_Last_Status_Update') # Ini durasi, bukan tanggal
        duration_val = ticket.get('Duration_toResolve') # Ini durasi, bukan tanggal
        
        
        col2_content += render_meta_item_html("Reporter", ticket.get('Reporter'))
        col2_content += render_meta_item_html("Assignee", ticket.get('Assignee'))
        col2_content += render_meta_item_html("Squad", ticket.get('Squad'))
        col2_content += render_meta_item_html("Testing At", tested_str)
        col2_content += render_meta_item_html("Created At", created_str)
        col2_content += render_meta_item_html("Latest Status Update", last_update_val)
        col2_content += render_meta_item_html("Solved At", resolved_str)
        col2_content += render_meta_item_html("Solved Duration", duration_val, default_val="Not Yet")
        
        col2_content += "</div>"
        details_html += col2_content

        details_html += "</div>" # Penutup grid utama

        # --- BAGIAN BARU: Menampilkan Deskripsi ---
        details_html += "<hr style='border: none; border-top: 1px solid #e9ecef; margin: 25px 0px 15px 0px;'>"
        details_html += "<p style='font-size: 0.8em; color: #495057; margin-bottom: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>Description</p>"
        
        # Ambil deskripsi yang sudah bersih dari dictionary 'ticket'.
        # 'Description' adalah nama kolom baru yang kita buat di ipynb.
        description_text = ticket.get('Description', '<i>Oops! No description available.</i>')
        
        # Kita bungkus deskripsinya dalam div dengan style dasar.
        # Karena isinya sudah HTML (<table>, dll), dia akan dirender dengan benar.
        details_html += f"<div class='jira-description-content' style='font-size: 0.9em; line-height: 1.6;'>{description_text}</div>"
        
        # --- Akhiri Pembungkus Global ---
        details_html += "<div style='height: 20px;'></div></div>" 

        # --- Render Seluruh HTML ---
        details_container.html(details_html)

    else:
        
        svg_select_ticket = """
        <svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-click"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M3 12l3 0" /><path d="M12 3l0 3" /><path d="M7.8 7.8l-2.2 -2.2" /><path d="M16.2 7.8l2.2 -2.2" /><path d="M7.8 16.2l-2.2 2.2" /><path d="M12 12l9 3l-4 2l-2 4l-3 -9" /></svg>
        """
        icon_select = svg_to_img(svg_select_ticket)

        placeholder_html = f"""
        <div style="
            display: flex; 
            flex-direction: column;
            justify-content: center; 
            align-items: center; 
            background-color: #F6F6F6;
            border-radius: 8px; 
            height: 770px;
            text-align: center;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        ">
            <img src="{icon_select}" alt="Select Icon" style="width: 60px; height: 60px; margin-bottom: 0px;">

            <div style="margin-top: 0px;">
                <h3 style="color: #495057; font-weight: 500; font-size: 1.2em; margin-bottom: 5px;">
                    Pick a Ticket to See the Details!
                </h3>
                <p style="color: #6c757d; font-size: 0.9em; margin: 0;">
                    The details of your selected ticket will be displayed here.
                </p>
            </div>
        </div>
        """
        details_container.html(placeholder_html)

with main_col3:
    
    if st.session_state.selected_ticket_details:
        ticket = st.session_state.selected_ticket_details
        
        tab1, tab2 = st.tabs([":material/forum: Comments", ":material/history: History"])

        with tab1:
            # st.markdown("<p style='font-size: 1.2em; font-weight: 600; color: #212529; margin-top:10px;'></p>", unsafe_allow_html=True)
            comments_html_string = ticket.get('Comments_HTML', '')
            comment_scroll_container = st.container(height=1240)
            if pd.notna(comments_html_string) and comments_html_string.strip():
                comment_scroll_container.html(f"<div style='padding-right:10px;'>{comments_html_string}</div>")
            else:
                svg_no_comment = """
                <svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-mood-edit"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M20.955 11.104a9 9 0 1 0 -9.895 9.847" /><path d="M9 10h.01" /><path d="M15 10h.01" /><path d="M9.5 15c.658 .672 1.56 1 2.5 1c.126 0 .251 -.006 .376 -.018" /><path d="M18.42 15.61a2.1 2.1 0 0 1 2.97 2.97l-3.39 3.42h-3v-3l3.42 -3.39z" /></svg>
                """
                icon_no_comment = svg_to_img(svg_no_comment)
                
                placeholder_no_comment = f"""
                <div style="
                    display: flex; 
                    flex-direction: column;
                    justify-content: center; 
                    align-items: center; 
                    background-color: #F6F6F6;
                    border-radius: 8px; 
                    height: 660px;
                    text-align: center;
                    padding: 20px;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                ">
                    <img src="{icon_no_comment}" alt="Select Icon" style="width: 60px; height: 60px; margin-bottom: 0px;">

                    <div style="margin-top: 0px;">
                        <h3 style="color: #495057; font-weight: 500; font-size: 1.2em; margin-bottom: 5px;">
                            No Comment Yet
                        </h3>
                        <p style="color: #6c757d; font-size: 0.9em; margin: 0;">
                            Be the first one to add a comment on this ticket!
                        </p>
                    </div>
                </div>
                """
                
                comment_scroll_container.html(placeholder_no_comment)

        with tab2:
            # st.markdown("<p style='font-size: 1.2em; font-weight: 600; color: #212529; margin-top:10px;'>Riwayat Status</p>", unsafe_allow_html=True)
            
            history_json_str = ticket.get('Status_History_JSON', '[]')
            
            try:
                history_list = json.loads(history_json_str)
            except json.JSONDecodeError:
                history_list = []

            if history_list:
                df_history = pd.DataFrame(history_list)
                df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
                df_history = df_history.sort_values(by='timestamp').reset_index(drop=True)
                
                def format_timedelta_short(td):
                    if pd.isna(td): return ""
                    total_seconds = td.total_seconds()
                    days, rem = divmod(total_seconds, 86400)
                    hours, rem = divmod(rem, 3600)
                    minutes, _ = divmod(rem, 60)
                    parts = []
                    if days > 0: parts.append(f"{int(days)}h")
                    if hours > 0: parts.append(f"{int(hours)}j")
                    if minutes > 0: parts.append(f"{int(minutes)}m")
                    if not parts: return f"{int(total_seconds)}d"
                    return " ".join(parts)

                # --- LOGIKA BARU: KOMPRESI URUTAN CEPAT (STATE-AWARE COMPRESSION) ---
                TRANSITIONAL_THRESHOLD = timedelta(minutes=5) # Anggap status transisi jika di bawah 5 menit
                
                compressed_history = []
                i = 0
                while i < len(df_history):
                    current_event = df_history.iloc[i]
                    
                    # Cek apakah ada sequence cepat setelah event ini
                    j = i + 1
                    while j < len(df_history) and \
                          (df_history.loc[j, 'timestamp'] - df_history.loc[j-1, 'timestamp']) < TRANSITIONAL_THRESHOLD:
                        j += 1
                    
                    if j > i + 1: # Jika ada sequence transisi (lebih dari 1 event cepat)
                        start_event = current_event
                        end_event = df_history.iloc[j-1]
                        
                        # Gabungkan menjadi satu event "lompatan"
                        compressed_event = {
                            'timestamp': start_event['timestamp'],
                            'status_from': start_event['status_from'],
                            'status_to': end_event['status_to'],
                            'author': end_event['author']
                        }
                        compressed_history.append(compressed_event)
                        i = j # Lompati semua event transisi
                    else: # Jika ini event tunggal yang signifikan
                        compressed_history.append(current_event.to_dict())
                        i += 1
                
                df_history_clean = pd.DataFrame(compressed_history)
                df_history_clean['timestamp'] = pd.to_datetime(df_history_clean['timestamp'])

                # ... (kode dari jawaban sebelumnya untuk y_positions, tick_values, tick_texts tetap sama, 
                #       tapi sekarang menggunakan df_history_clean sebagai input) ...

                TIME_JUMP_THRESHOLD = timedelta(hours=6)
                VISUAL_JUMP_SIZE = 10.0
                TIME_SCALE_PER_HOUR = 2.0

                y_positions = []
                tick_values = []
                tick_texts = []
                last_time = None
                last_date = None
                current_y = 0.0

                for index, row in df_history_clean.iterrows():
                    current_time = row['timestamp']
                    current_date = current_time.date()
                    
                    # Y-position logic
                    if last_time:
                        delta = current_time - last_time
                        if delta > TIME_JUMP_THRESHOLD:
                            current_y += VISUAL_JUMP_SIZE
                        else:
                            hours_passed = delta.total_seconds() / 3600
                            current_y += (hours_passed * TIME_SCALE_PER_HOUR) + 1.0  # Tambah jarak biar ga mepet

                    y_positions.append(current_y)
                    tick_values.append(current_y)
                    
                    # Smart tick label logic
                    if current_date != last_date:
                        tick_texts.append(current_time.strftime('%d %b %Y'))  # Full date
                        last_date = current_date
                    else:
                        tick_texts.append("   " + current_time.strftime('%H:%M'))  # Only time, indented
                    
                    last_time = current_time

                df_history_clean['y_pos'] = y_positions
                
                annotations_y = []
                annotations_text = []
                for i in range(1, len(df_history_clean)):
                    prev_y = df_history_clean.loc[i-1, 'y_pos']
                    curr_y = df_history_clean.loc[i, 'y_pos']
                    
                    # Hitung durasi antara titik-titik yang ditampilkan
                    duration = df_history_clean.loc[i, 'timestamp'] - df_history_clean.loc[i-1, 'timestamp']

                    # Hanya tampilkan durasi jika lebih dari threshold kompresi
                    if duration > TRANSITIONAL_THRESHOLD:
                        annotations_y.append((prev_y + curr_y) / 2) # Posisi Y di tengah garis
                        annotations_text.append(format_timedelta_short(duration))

                # Pewarnaan marker
                colors = []
                for index, row in df_history_clean.iterrows():
                    status_clean = str(row['status_to']).lower()
                    if any(term in status_clean for term in ["to do", "reopen"]):
                        colors.append('#dc3545')
                    elif any(term in status_clean for term in ["done", "passed", "closed", "resolve"]):
                        colors.append('#198754')  # Hijau
                    elif any(term in status_clean for term in ["invalid"]):
                        colors.append('#616569')
                    else:
                        colors.append('#0d6efd')  # Biru

                # Plotting
                if not df_history_clean.empty:
                    fig = go.Figure()
                    config = {'displayModeBar': False}

                    # Garis vertikal utama
                    fig.add_trace(go.Scatter(x=[0] * len(df_history_clean), y=df_history_clean['y_pos'], mode='lines', line=dict(color='#ced4da', width=6), hoverinfo='none'))
                    
                    # Titik-titik status
                    fig.add_trace(go.Scatter(
                        x=[0] * len(df_history_clean), y=df_history_clean['y_pos'], mode='markers+text',
                        marker=dict(size=22, color=colors, symbol='circle', line=dict(width=4, color='white')),
                        text="<b>" + df_history_clean['status_to'] + "</b>", textfont=dict(size=16, color='#212529'),
                        textposition="middle right", hoverinfo='text',
                        hovertext=df_history_clean.apply(lambda r: f"<b>{r['status_to']}</b><br>{r['author']}<br>{r['timestamp'].strftime('%d %b %Y, %H:%M WIB')}", axis=1),
                        hoverlabel=dict(bgcolor='white', bordercolor='lightgray', font=dict(color='black', size=14))
                    ))
                    
                    # --- TRACE DURASI YANG DISEMPURNAKAN ---
                    fig.add_trace(go.Scatter(
                        x=[0.01] * len(annotations_y), # Pindahkan ke kanan & lebih dekat
                        y=annotations_y,
                        mode='text',
                        text=annotations_text,
                        textposition='middle left', # Ratakan kiri teksnya
                        textfont=dict(size=16, color='#6c757d'), # Font sedikit lebih besar
                        hoverinfo='none'
                    ))

                    # Kustomisasi Layout Plot
                    fig.update_layout(
                        showlegend=False, xaxis=dict(visible=False),
                        yaxis=dict(title="", autorange="reversed", showgrid=False, zeroline=False, tickvals=tick_values, ticktext=tick_texts, tickfont=dict(size=13, color='#6c757d')),
                        margin=dict(l=20, r=20, t=0, b=30), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        height=1000
                    )
                    fig.layout.xaxis.fixedrange = True
                    fig.layout.yaxis.fixedrange = True
                    
                    plot_scroll_container = st.container(height=1240)
                    plot_scroll_container.plotly_chart(fig, config=config, use_container_width=True)

                else:
                    st.info("Tidak ada riwayat status yang signifikan untuk ditampilkan.")
            else:
                st.info("Tidak ada riwayat status untuk ditampilkan.")
                
    else:
        svg_comment = """
        <svg  xmlns="http://www.w3.org/2000/svg"  width="24"  height="24"  viewBox="0 0 24 24"  fill="none"  stroke="currentColor"  stroke-width="2"  stroke-linecap="round"  stroke-linejoin="round"  class="icon icon-tabler icons-tabler-outline icon-tabler-messages"><path stroke="none" d="M0 0h24v24H0z" fill="none"/><path d="M21 14l-3 -3h-7a1 1 0 0 1 -1 -1v-6a1 1 0 0 1 1 -1h9a1 1 0 0 1 1 1v10" /><path d="M14 15v2a1 1 0 0 1 -1 1h-7l-3 3v-10a1 1 0 0 1 1 -1h2" /></svg>
        """
        
        icon_comment = svg_to_img(svg_comment)
        
        comment_placeholder = f"""
        <div style="
            display: flex; 
            flex-direction: column;
            justify-content: center; 
            align-items: center; 
            background-color: #F6F6F6;
            border-radius: 8px; 
            height: 770px;
            text-align: center;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        ">
            <img src="{icon_comment}" alt="Select Icon" style="width: 60px; height: 60px; margin-bottom: 0px;">

            <div style="margin-top: 0px;">
                <h3 style="color: #495057; font-weight: 500; font-size: 1.2em; margin-bottom: 5px;">
                    Comment not available
                </h3>
                <p style="color: #6c757d; font-size: 0.9em; margin: 0;">
                    Pick the ticket first to be able to see the comment!
                </p>
            </div>
        </div>
        """
        comment_scroll_placeholder = st.container(height=1300) 
        comment_scroll_placeholder.html(comment_placeholder)
