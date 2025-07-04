import streamlit as st
import pandas as pd
import numpy as np
import re
from datetime import datetime #
from utils.jira_processed import jiraProgress_proc
from datetime import datetime, timedelta

import altair as alt
import plotly.express as px
import plotly.graph_objects as go

from streamlit_extras.stylable_container import stylable_container
from st_keyup import st_keyup

from utils.gdrive_conn import get_list_files, read_file_from_drive
from utils.jira_processed import jiraProgress_proc
from components.filters import apply_filters, reset_jira_filters
from components.metrics import display_summary_metrics

import json

st.set_page_config(page_title='BSI Testing Insight', layout='wide')

def truncate_feature_name(name, max_words=2):
    """Memotong string menjadi maksimal N kata dan menambahkan '...' jika lebih panjang."""
    words = name.split()
    if len(words) > max_words:
        return ' '.join(words[:max_words]) + ' ...'
    else:
        return name

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

def color_status(status_value):
    """
    Memberikan style CSS berdasarkan nilai status tiket.
    Menggunakan warna yang aman dan teks yang kontras.
    """
    status_lower = str(status_value).lower()

    # Definisikan warna-warna yang bagus
    color_resolved = '#24b24c'
    color_invalid = '#9c9c9c'
    color_open = '#2C497F'

    if status_lower in ['done', 'resolve', 'resolved', 'closed']:
        # Untuk status selesai, background hijau, teks putih
        return f'background-color: {color_resolved}; color: white;'
    elif status_lower == 'invalid':
        # Untuk status invalid, background abu-abu, teks putih
        return f'background-color: {color_invalid}; color: white;'
    else:
        # Untuk status lainnya (Open, In Progress, dll), background merah, teks putih
        return f'background-color: {color_open}; color: white;'
    
def color_severity(severity_value):
    """
    Memberikan style CSS berdasarkan nilai severity.
    """
    severity_lower = str(severity_value).strip().lower()
    
    # Definisikan warna-warna
    color_highest = '#dc3545'  # Merah
    color_medium = '#ffc107'   # Kuning-Amber (lebih baik dari 'yellow')
    color_low = '#0d6efd'      # Biru

    if severity_lower == 'highest':
        # Background merah, teks putih
        return f'background-color: {color_highest}; color: white;'
    elif severity_lower == 'medium':
        # Background kuning, teks HITAM agar mudah dibaca
        return f'background-color: {color_medium}; color: black;'
    elif severity_lower == 'low':
        # Background biru, teks putih
        return f'background-color: {color_low}; color: white;'
    
    # Default, jika tidak ada yang cocok
    return ''

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

def create_feature_squad_status_bubble_chart(df: pd.DataFrame):
    """
    Membuat bubble chart kategorikal untuk menunjukkan distribusi tiket
    berdasarkan Fitur, Status, dan Squad.

    - Sumbu Y: Fitur
    - Sumbu X: Status Tiket
    - Warna: Squad
    - Ukuran Bubble: Jumlah Tiket

    Args:
        df (pd.DataFrame): DataFrame yang sudah difilter.

    Returns:
        go.Figure or None: Objek gambar Plotly atau None jika tidak ada data.
    """
    if df.empty:
        return None

    # Pastikan kolom yang dibutuhkan tidak kosong
    required_cols = ['Feature', 'Squad', 'Status']
    df_chart = df.dropna(subset=required_cols).copy()

    if df_chart.empty:
        return None

    # 1. Agregasi data: Hitung jumlah tiket untuk setiap kombinasi
    bubble_data = df_chart.groupby(['Feature', 'Squad', 'Status']).size().reset_index(name='Jumlah Tiket')
    
    # Tambahkan nama fitur yang dipotong untuk label sumbu Y
    bubble_data['Feature_Display'] = bubble_data['Feature'].apply(lambda name: truncate_feature_name(name, max_words=3))


    # 2. Buat bubble chart menggunakan Plotly Express
    fig = px.scatter(
        bubble_data,
        x='Status',
        y='Feature_Display',
        size='Jumlah Tiket',
        color='Squad',
        size_max=30,  # Ukuran bubble maksimum agar tidak terlalu besar
        labels={
            "Status": "Status Tiket",
            "Feature_Display": "Fitur",
            "Jumlah Tiket": "Jumlah Tiket",
            "Squad": "Squad"
        },
        custom_data=['Feature', 'Squad', 'Jumlah Tiket'] # Data tambahan untuk hover
    )

    # 3. Kustomisasi tampilan (layout & hover)
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=20),
        height=1000 # Beri tinggi yang cukup untuk bubble chart
    )
    
    # Kustomisasi tooltip
    fig.update_traces(
        hovertemplate="<b>Fitur: %{customdata[0]}</b><br><br>" +
                      "Status: %{x}<br>" +
                      "Squad: %{customdata[1]}<br>" +
                      "Jumlah Tiket: %{customdata[2]}<extra></extra>"
    )

    return fig

def create_feature_squad_status_bubble_chart(df: pd.DataFrame):
    """
    Membuat bubble chart kategorikal untuk menunjukkan distribusi tiket
    berdasarkan Fitur, Status, dan Squad, dengan total per status dan fitur.
    """
    if df.empty:
        return None

    # Salin DataFrame untuk menghindari SettingWithCopyWarning
    df_chart = df.copy()

    # --- PERUBAHAN DIMULAI DI SINI ---
    # Ganti nilai None/NaN di kolom 'Squad' menjadi 'Unclassified'
    df_chart['Squad'] = df_chart['Squad'].fillna('Unclassified')
    # Drop baris hanya jika 'Feature' atau 'Status' yang kosong
    df_chart.dropna(subset=['Feature', 'Status'], inplace=True)
    # --- PERUBAHAN SELESAI DI SINI ---

    if df_chart.empty:
        return None

    bubble_data = df_chart.groupby(['Feature', 'Squad', 'Status']).size().reset_index(name='Total Tickets')
    bubble_data['Feature_Display'] = bubble_data['Feature'].apply(lambda name: truncate_feature_name(name, max_words=3))

    fig = px.scatter(
        bubble_data,
        x='Status',
        y='Feature_Display',
        size='Total Tickets',
        color='Squad',
        size_max=50,
        labels={"Status": "Ticket Status", "Feature_Display": "Features", "Total Tickets": "Total Tickets", "Squad": "Squad"},
        custom_data=['Feature', 'Squad', 'Total Tickets']
    )

    # --- HITUNG DAN TAMBAHKAN TOTAL UNTUK SETIAP STATUS (ATAS) ---
    status_totals = bubble_data.groupby('Status')['Total Tickets'].sum().reset_index()
    for index, row in status_totals.iterrows():
        fig.add_annotation(
            x=row['Status'],
            y=1.05,
            yref="paper",
            text=f"<br> <br> <br><b>{row['Total Tickets']}</b>",
            showarrow=False,
            font=dict(color="#333333", size=14),
            align="center"
        )

    # --- HITUNG DAN TAMBAHKAN TOTAL UNTUK SETIAP FITUR (KANAN) ---
    feature_totals = bubble_data.groupby('Feature_Display')['Total Tickets'].sum().reset_index()
    for index, row in feature_totals.iterrows():
        fig.add_annotation(
            x=1.02, # Posisikan sedikit di kanan area plot
            xref="paper",
            y=row['Feature_Display'],
            text=f"<b>{row['Total Tickets']}</b>",
            showarrow=False,
            xanchor='left',
            font=dict(color="#333333", size=12)
        )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)', categoryorder='total ascending'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=70, b=20), # Beri ruang lebih di atas (t) dan kanan (r)
        height=940
    )
    
    fig.update_traces(
        hovertemplate="<b>Feature: %{customdata[0]}</b><br><br>" +
                      "Status: %{x}<br>" +
                      "Squad: %{customdata[1]}<br>" +
                      "Total Tickets: %{customdata[2]}<extra></extra>"
    )
    return fig


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
    
    options_data = ['PTR 1.1.0', 'SITBAU 1.1.0 GS 9.10.1', 'PTR 1.1.0 GS 9.10.1', 'SITBAU Always On 1.1.0', 'PTR Always On 1.1.0', 'Release 1.1.1 SITBAU']
    st.pills("Quick filter by project:", options_data, selection_mode="single", key="pills_selection")

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
    st.session_state.title_filter,
    st.session_state.pills_selection
)


df_filtered['Resolved_Time'] = pd.to_datetime(df_filtered['Resolved_Time'], errors='coerce')

total_tickets = len(df_filtered.index)

total_open_tickets = (df_filtered['Resolved_Time'].isna() & (df_filtered['Status'] != 'Invalid')).sum()
total_solved_tickets = (df_filtered['Resolved_Time'].notna()).sum()
total_invalid_ticket = (df_filtered['Status'] == 'Invalid').sum()

solved_tickets_df = df_filtered[df_filtered['Resolved_Time'].notna()].copy()
solved_tickets_df['duration_hours'] = solved_tickets_df['Duration_toResolve'].apply(duration_to_hours)
avg_duration_in_hours = solved_tickets_df['duration_hours'].mean()
formatted_avg_duration = format_hours_to_days_hours(avg_duration_in_hours)


# Definisikan palet warna tema hijau-mu sekali lagi
THEME_GREEN = "#24b24c"
THEME_GREEN_DARK = "#1A7D36"
BACKGROUD_COLOR = "#f6f6f6"
BORDER_LIGHT = "#e0e0e0"

# Buat satu "Master Style" untuk semua kartu metrik
METRIC_CARD_STYLE = f"""
    /* Gaya untuk font value (angka utama) */
    div[data-testid="stMetricValue"] {{
        font-weight: 600;
    }}

    /* Gaya dasar untuk SEMUA kartu metrik */
    div[data-testid="stMetric"] {{
        background-color: #f6f6f6; /* Pastikan background putih */
        border: 2px solid {BORDER_LIGHT};
        border-radius: 1rem; /* 16px */
        padding: 1rem; /* Beri sedikit padding internal */
        transition: all 0.2s ease-in-out; /* Animasi halus untuk semua perubahan */
    }}

    /* Gaya kartu saat di-hover (meniru style 'selected') */
    div[data-testid="stMetric"]:hover {{
        background-color: {BACKGROUD_COLOR};
        border-color: {THEME_GREEN};
        
        /* Efek 'terangkat' yang lebih modern */
        transform: translateY(-1px);
    }}
    
    /* Ganti warna teks di dalam kartu saat kartu di-hover */
    div[data-testid="stMetric"]:hover p {{
        color: {THEME_GREEN_DARK};
    }}
"""

display_summary_metrics(
    total_tickets=total_tickets,
    total_open_tickets=total_open_tickets,
    total_solved_tickets=total_solved_tickets,
    total_invalid_ticket=total_invalid_ticket,
    formatted_avg_duration=formatted_avg_duration,
    metric_card_style=METRIC_CARD_STYLE
)


col1, col2 = st.columns([1.6,2.4])

with col1:

    valid_status = ['Highest', 'Medium', 'Low']
    df_final = df_filtered[df_filtered['Severity'].isin(valid_status)].copy()

    chart_data = df_final.groupby(['Feature', 'Severity']).size().reset_index(name='Total Tickets') # bikin total tiket
    chart_data['Feature_Display'] = chart_data['Feature'].apply(truncate_feature_name)

    color_scheme = {'Highest': '#E63946', 'Medium': '#FCA311', 'Low': '#147DF5'}
    unique_features = chart_data['Feature'].unique() if not chart_data.empty else []
    plot_height = len(unique_features) * 40
    if plot_height < 400: plot_height = 400

    if not chart_data.empty:
        css_styles = """
            {
                border: 2px solid #e6e6e6;
                border-radius: 10px;
                padding: 20px;
                height: 500px;
                overflow-y: auto;
                background-color: #F6f6f6;
                box-shadow: 0 4px 8px rgba(0,0,0,0.05);
            }
            /* Kustomisasi scrollbar (opsional, tapi keren) */
            &::-webkit-scrollbar { width: 8px; }
            &::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
            &::-webkit-scrollbar-thumb { background: #cccccc; border-radius: 10px; }
            &::-webkit-scrollbar-thumb:hover { background: #aaaaaa; }
        """

        with stylable_container(key="plot_container", css_styles=css_styles):

            st.markdown(':material/device_thermostat: **Severity per Feature**', 
                        help='Shows how many tickets and their severity each feature got — X-axis: ticket count, Y-axis: feature names.')

            fig = px.bar(
                chart_data,
                x='Total Tickets', 
                y='Feature_Display',  # Gunakan kolom yang sudah dipotong untuk sumbu Y
                color='Severity', 
                orientation='h',
                color_discrete_map={'Highest': '#E63946', 'Medium': '#FCA311', 'Low': '#147DF5'}, 
                height=plot_height,
                labels={'Feature_Display': 'Fitur'}, # Label sumbu Y
                custom_data=['Feature'] # Simpan nama asli fitur untuk tooltip
            )

            # Kustomisasi layout dan tooltip
            fig.update_layout(
                yaxis={'categoryorder':'total ascending', 'title':{'standoff':10}},
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                legend_title_text='Severity',
                xaxis=dict(
                    showgrid=True,
                ),
                margin=dict(l=10, r=10, t=0, b=10)
            )

            # Kustomisasi tooltip untuk menampilkan nama fitur yang asli (full)
            fig.update_traces(
                hovertemplate="<b>Feature: %{customdata[0]}</b><br>" +
                            "Severity: %{fullData.name}<br>" +
                            "Total Tickets: %{x}<extra></extra>"
            )

            fig.layout.xaxis.fixedrange = True
            fig.layout.yaxis.fixedrange = True

            config = {'displayModeBar': False}

            st.plotly_chart(fig, config=config, use_container_width=True)
    else:
        st.warning(f"No tickets found with features matching the filter")


# --- 1. Definisikan CSS dengan tinggi tetap dan font lebih kecil ---
    css_final_layout = """
    {
        border: 2px solid #e6e6e6;
        border-radius: 16px;
        padding: 20px;
        height: 500px; 
        overflow-y: auto;
        background-color: #F6F6F6;
        scrollbar-width: none; 
        -ms-overflow-style: none;
    }
    &::-webkit-scrollbar {
        display: none;
    }
        
        .ticket-card {
            background-color: transparent; 
            box-shadow: none;
            border: none;
            border-bottom: 1px solid #e9ecef;
            height: 150px;         
            border-left: 2px solid #454444;
            padding: 10px 10px 10px 20px; 
            margin-bottom: 20px;
        }
        
        .ticket-card:hover {
            background-color: #f0f0f0; /* Ganti dengan highlight background subtil saat di-hover */
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0px;
        }
        
        .ticket-id {
            font-weight: 700;
            font-size: 0.9em; 
            color: #212529;
        }
        
        .status-badge {
            font-size: 0.6em; 
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 12px;
        }
        
        .ticket-severity {
            font-size: 0.6em; 
        }
        .ticket-info-list {
            margin-top: 2px;
            font-size: 0.8em !important; 
            color: #495057;
            padding-left: 0;
        }
        
        .column-header {
            font-size: 1em;
            font-weight: 700;
            color: #343a40;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 20px;
            margin-left: 5px;
        }
        .ticket-count-badge {
            font-size: 0.85em;
            font-weight: 500;
            background-color: #e9ecef;
            color: #495057;
            padding: 2px 9px;
            border-radius: 8px;
        }
        
        .status-open { background-color: #ffebee; color: #c62828;}
        .status-resolved { background-color: #e8f5e9; color: #2e7d32; }
        .status-invalid { background-color: #f5f5f5; color: #616161; }
        .severity-highest { color: #d32f2f; font-weight: 600; font-size: 0.8em;}
        .severity-medium { color: #f57c00; font-weight: 600; font-size: 0.8em; }
        .severity-low { color: #0277bd; font-weight: 600; font-size: 0.8em; }
    """

    # --- 2. Gunakan SATU stylable_container untuk membungkus semuanya ---
    with stylable_container(key="final_dashboard_container", css_styles=css_final_layout):

        st.markdown(':material/view_quilt: **Ticket Details Dashboard**', 
                    help='Click on a feature to see a detailed card-view of tickets, categorized by status.')

        if 'df_filtered' in locals() and not df_filtered.empty:
            
            # --- KUNCI 2: Logika Status yang Lebih Tegas ---
            resolved_statuses = ['Done', 'RESOLVE', 'Resolve', 'Done.', 'DONE', 'Closed']
            invalid_statuses = ['Invalid']

            # Buat filter boolean untuk setiap kategori
            is_resolved = df_filtered['Status'].isin(resolved_statuses)
            is_invalid = df_filtered['Status'].isin(invalid_statuses)
            # Tiket 'Open' adalah semua tiket yang BUKAN resolved DAN BUKAN invalid
            is_open = ~is_resolved & ~is_invalid

            # Mapping untuk kelas CSS
            severity_color_map = {'Highest': 'severity-highest', 'Medium': 'severity-medium', 'Low': 'severity-low'}
            
            features_sorted = df_filtered['Feature'].value_counts().index.tolist()

            if not features_sorted:
                st.info("No tickets with features found for the selected filters.")
            else:
                for feature in features_sorted:
                    feature_df = df_filtered[df_filtered['Feature'] == feature]
                    
                    open_tickets_count = df_filtered[is_open & (df_filtered['Feature'] == feature)].shape[0]
                    total_tickets_count = feature_df.shape[0]

                    expander_title = f"**{feature}** — ({open_tickets_count} Open / {total_tickets_count} Total)"
                    
                    # Ganti blok 3 kolom Anda dengan ini
                    with st.expander(expander_title):
                        
                        # Buat 3 Kolom
                        col_open, col_resolved, col_invalid = st.columns(3)

                        # --- Fungsi Bantuan untuk Render Kartu (tetap sama) ---
                        def render_ticket_card(row, status_category):
                            # ... (isi fungsi render_ticket_card tidak perlu diubah) ...
                            severity = row.get('Severity', 'N/A')
                            status_class = f"status-{status_category}"
                            severity_class = severity_color_map.get(severity, "")
                            
                            st.markdown(f"""
                                <div class="ticket-card">
                                    <div class="card-header">
                                        <span class="ticket-id">{row['Tickets']}</span>
                                        <span class="status-badge {status_class}">{row['Status']}</span>
                                    </div>
                                    <div>
                                        <span class="{severity_class}">{severity}</span>
                                        <div class="ticket-info-list">
                                            <b>Squad:</b> {row.get('Squad', 'N/A')} <br>
                                            <b>Bug Type:</b> {row.get('Bug Type', 'N/A')}
                                        </div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                        # --- Kolom 1: OPEN ---
                        with col_open:
                            # Gabungkan filter fitur dan filter status dalam satu baris
                            open_tickets_df = df_filtered[is_open & (df_filtered['Feature'] == feature)]
                            
                            count = len(open_tickets_df.index)
                            st.markdown(f"<div class='column-header'> Open <span class='ticket-count-badge'>{count}</span></div>", unsafe_allow_html=True)
                            
                            if not open_tickets_df.empty:
                                for _, row in open_tickets_df.iterrows():
                                    render_ticket_card(row, "open")
                            else: 
                                st.caption("No open tickets.")
                        
                        # --- Kolom 2: RESOLVED ---
                        with col_resolved:
                            resolved_tickets_df = df_filtered[is_resolved & (df_filtered['Feature'] == feature)]
                            # Hitung jumlah tiket di kolom ini
                            count = len(resolved_tickets_df.index)
                            # Tampilkan header kustom
                            st.markdown(f"<div class='column-header'> Resolved <span class='ticket-count-badge'>{count}</span></div>", unsafe_allow_html=True)
                            
                            if not resolved_tickets_df.empty:
                                for _, row in resolved_tickets_df.iterrows():
                                    render_ticket_card(row, "resolved")
                            else: 
                                st.caption("No resolved tickets.")
                        
                        # --- Kolom 3: INVALID ---
                        with col_invalid:
                            invalid_tickets_df = df_filtered[is_invalid & (df_filtered['Feature'] == feature)]
                            # Hitung jumlah tiket di kolom ini
                            count = len(invalid_tickets_df.index)
                            # Tampilkan header kustom
                            st.markdown(f"<div class='column-header'> Invalid <span class='ticket-count-badge'>{count}</span></div>", unsafe_allow_html=True)
                            
                            if not invalid_tickets_df.empty:
                                for _, row in invalid_tickets_df.iterrows():
                                    render_ticket_card(row, "invalid")
                            else: 
                                st.caption("No invalid tickets.")

        
    with stylable_container(key="daily ticket", css_styles=css_styles):
        st.markdown("**:material/sports_martial_arts: Daily Ticket Activity**", 
                    help="This chart shows the daily number of tickets opened/reopened/ versus tickets solved and invalidated.")

        # FUNGSI DIPERBARUI: Menghitung data harian, bukan kumulatif
        @st.cache_data
        def prepare_daily_activity_data(df):
            """
            Memproses seluruh DataFrame untuk mengekstrak event 'open' dan 'solved'
            dan menghitung jumlahnya per hari.
            """
            all_events = []
            
            solved_states = ['Done', 'RESOLVE', 'Resolve', 'Done.', 'DONE', 'Closed']
            reopen_states = ['Reopened', 'REOPEN']
            invalid_states = ['Invalid']

            for index, row in df.iterrows():
                history_json_str = row.get('Status_History_JSON')
                if not history_json_str or not isinstance(history_json_str, str):
                    continue

                try:
                    history_data = json.loads(history_json_str)
                    if not isinstance(history_data, list): continue

                    for event in history_data:
                        timestamp = pd.to_datetime(event.get('timestamp'))
                        status_to = event.get('status_to')
                        status_from = event.get('status_from')

                        if status_from is None:
                            all_events.append({'date': timestamp.date(), 'type': 'open'})
                        elif status_to in reopen_states:
                            all_events.append({'date': timestamp.date(), 'type': 'open'})
                        elif status_to in solved_states:
                            all_events.append({'date': timestamp.date(), 'type': 'solved'})
                        elif status_to in invalid_states:
                            all_events.append({'date': timestamp.date(), 'type': 'invalid'})
                except (json.JSONDecodeError, TypeError):
                    continue
                    
            if not all_events:
                return pd.DataFrame()

            events_df = pd.DataFrame(all_events)
            daily_counts = events_df.groupby(['date', 'type']).size().unstack(fill_value=0)

            # Pastikan kedua kolom ada
            if 'open' not in daily_counts:
                daily_counts['open'] = 0
            if 'solved' not in daily_counts:
                daily_counts['solved'] = 0
            if 'invalid' not in daily_counts:
                daily_counts['invalid'] = 0
            
            # KUNCI PERUBAHAN: .cumsum() DIHAPUS untuk mendapatkan data harian
            # Kita juga reindex untuk memastikan semua hari ada dalam rentang waktu
            full_date_range = pd.date_range(start=daily_counts.index.min(), end=daily_counts.index.max(), freq='D')
            daily_counts = daily_counts.reindex(full_date_range, fill_value=0)
            
            return daily_counts

        # Pastikan df_filtered ada sebelum menjalankan proses
        if 'df_filtered' in locals() and not df_filtered.empty:
            with st.spinner('Analyzing daily ticket activity...'):
                # Fungsi prepare_daily_activity_data tidak perlu diubah, tetap sama
                daily_df = prepare_daily_activity_data(df_filtered)

            if not daily_df.empty:
                # --- Membuat Plot Line Chart Estetik dengan Plotly Graph Objects ---
                fig_activity = go.Figure()
                
                # Definisikan warna untuk konsistensi
                colors = {
                    'open': "#E24F4F",   # Biru Tua
                    'solved': '#24b24c', # Hijau
                    'invalid': '#636363' # Abu-abu
                }

                # --- Trace untuk Opened / Reopened ---
                fig_activity.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=daily_df['open'],
                    name='Opened / Reopened',
                    mode='lines',
                    line=dict(width=3, color=colors['open'], shape='spline'), # Garis melengkung (spline)
                    fill='tozeroy', # Area di bawah garis
                    fillcolor='rgba(101, 0, 26, 0.1)', # Warna area transparan
                    hovertemplate='<b>Opened/Reopened: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
                ))

                # --- Trace untuk Solved ---
                fig_activity.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=daily_df['solved'],
                    name='Solved',
                    mode='lines',
                    line=dict(width=3, color=colors['solved'], shape='spline'),
                    fill='tozeroy',
                    fillcolor='rgba(36, 178, 76, 0.2)',
                    hovertemplate='<b>Solved: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
                ))

                # --- Trace untuk Invalid ---
                fig_activity.add_trace(go.Scatter(
                    x=daily_df.index,
                    y=daily_df['invalid'],
                    name='Invalid',
                    mode='lines',
                    line=dict(width=3, color=colors['invalid'], shape='spline', dash='dot'), # Garis putus-putus
                    hovertemplate='<b>Invalid: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
                ))

                # --- SENTUHAN ADVANCED: Anotasi untuk Puncak Tiket Open ---
                # if not daily_df['open'].empty and daily_df['open'].max() > 0:
                #     peak_day = daily_df['open'].idxmax()
                #     peak_value = daily_df['open'].max()
                #     fig_activity.add_annotation(
                #         x=peak_day, y=peak_value,
                #         text=f"Peak Open: {int(peak_value)}",
                #         showarrow=True, arrowhead=2, arrowcolor="#2C497F",
                #         font=dict(size=12, color="white"),
                #         align="center",
                #         bgcolor="#2C497F", bordercolor="#2C497F", borderwidth=2,
                #         ax=0, ay=-60 # Posisi panah
                #     )

                # --- Poles Tampilan (Aesthetic Layout) ---
                fig_activity.update_layout(
                    template='plotly_white',
                    hovermode='x unified',
                    xaxis=dict(
                        rangeslider=dict(visible=True, thickness=0.1),
                        showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'
                    ),
                    yaxis=dict(
                        title='Daily Ticket Count',
                        side='right',
                        showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'
                    ),
                    legend=dict(
                        orientation="h", yanchor="bottom", y=1.02,
                        xanchor="right", x=1
                    ),
                    margin=dict(l=20, r=20, t=70, b=0),
                    height=400,
                )
                st.plotly_chart(fig_activity, use_container_width=True)
            else:
                st.info("No valid ticket history data found in the filtered dataset to generate an activity plot.")
        else:
            st.warning("Please filter the data first to see the daily activity.")

    with stylable_container(key="cummulative ticket", css_styles=css_styles):
        st.markdown("**:material/sports_martial_arts: Cumulative Opened Ticket vs Closed Ticket**", 
                    help="This chart shows the cumulative count of unique tickets opened (including reopened) versus unique tickets finally closed (including Invalidated).")


        # --- FUNGSI BARU DENGAN LOGIKA PER TIKET (YANG BENAR) ---
        @st.cache_data
        def prepare_ticket_lifecycle_data(df):
            """
            Menganalisis riwayat setiap tiket untuk menemukan tanggal pembukaan pertamanya
            dan tanggal penutupan terakhirnya, lalu menghitung jumlah kumulatif.
            """
            opened_dates = []
            closed_dates = []

            solved_states = ['Done', 'RESOLVE', 'Resolve', 'Done.', 'DONE', 'Closed']
            invalid_states = ['Invalid']
            final_closed_states = solved_states + invalid_states

            for index, row in df.iterrows():
                history_json_str = row.get('Status_History_JSON')
                if not history_json_str or not isinstance(history_json_str, str):
                    continue
                
                try:
                    history_data = json.loads(history_json_str)
                    if not isinstance(history_data, list) or not history_data:
                        continue

                    # PENTING: Urutkan riwayat berdasarkan timestamp untuk menemukan event pertama dan terakhir
                    history_data.sort(key=lambda x: pd.to_datetime(x.get('timestamp')))

                    # 1. Tentukan tanggal tiket DIBUAT (hanya event pertama)
                    first_event = history_data[0]
                    if first_event.get('status_from') is None:
                        opened_dates.append(pd.to_datetime(first_event['timestamp']).date())
                    
                    # 2. Tentukan tanggal tiket FINAL DITUTUP (hanya event terakhir)
                    last_event = history_data[-1]
                    if last_event.get('status_to') in final_closed_states:
                        closed_dates.append(pd.to_datetime(last_event['timestamp']).date())

                except (json.JSONDecodeError, TypeError, KeyError):
                    continue

            if not opened_dates:
                return pd.DataFrame()

            # Hitung jumlah tiket unik yang dibuka/ditutup per hari
            opened_daily = pd.Series(opened_dates).value_counts()
            closed_daily = pd.Series(closed_dates).value_counts()

            # Gabungkan menjadi satu DataFrame harian
            daily_df = pd.DataFrame({'open': opened_daily, 'closed': closed_daily}).fillna(0)
            
            # Reindex untuk memastikan semua hari ada, lalu hitung kumulatif
            full_date_range = pd.date_range(start=daily_df.index.min(), end=daily_df.index.max(), freq='D')
            daily_df = daily_df.reindex(full_date_range, fill_value=0)
            
            cumulative_df = daily_df.cumsum()
            cumulative_df.rename(columns={'open': 'opened_cumulative', 'closed': 'closed_cumulative'}, inplace=True)
            
            return cumulative_df

        # Jalankan proses dengan fungsi baru
        if 'df_filtered' in locals() and not df_filtered.empty:
            with st.spinner('Analyzing ticket lifecycle...'):
                lifecycle_df = prepare_ticket_lifecycle_data(df_filtered)

            if not lifecycle_df.empty:
                # Bagian plotting ini sama, hanya sumber datanya yang berbeda
                fig_lifecycle = go.Figure()
                
                colors = {"opened": "#E24F4F", "closed": '#24b24c'}

                fig_lifecycle.add_trace(go.Scatter(
                    x=lifecycle_df.index, y=lifecycle_df['opened_cumulative'],
                    name='Opened (Cumulative)', mode='lines',
                    line=dict(width=3.5, color=colors['opened'], shape='spline'),
                    fill='tozeroy', fillcolor='rgba(226, 79, 79, 0.1)',
                    hovertemplate='<b>Total Opened: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
                ))

                fig_lifecycle.add_trace(go.Scatter(
                    x=lifecycle_df.index, y=lifecycle_df['closed_cumulative'],
                    name='Closed (Cumulative)', mode='lines',
                    line=dict(width=3.5, color=colors['closed'], shape='spline'),
                    fill='tozeroy', fillcolor='rgba(36, 178, 76, 0.2)',
                    hovertemplate='<b>Total Closed: %{y}</b><br>Date: %{x|%d %b %Y}<extra></extra>'
                ))
                
                fig_lifecycle.update_layout(
                    template='plotly_white', hovermode='x unified',
                    xaxis=dict(rangeslider=dict(visible=True, thickness=0.08), showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
                    yaxis=dict(title='Cumulative Unique Tickets', side='right', showgrid=True, gridcolor='rgba(220, 220, 220, 0.5)'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=20, r=20, t=70, b=0), height=400,
                )
                st.plotly_chart(fig_lifecycle, use_container_width=True)
            else:
                st.info("No valid ticket history data found for lifecycle analysis.")
        else:
            st.warning("Please filter the data first to see the ticket lifecycle.")



with col2:

    css_styles = """
    {
        border: 2px solid #e6e6e6;
        border-radius: 10px;
        padding: 20px;
        background-color: #F6f6f6;
        height: 500px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
    }
    """
    
    # Gunakan styleable_container untuk membungkus plot
    with stylable_container(key="overview", css_styles=css_styles):
        st.markdown(':material/confirmation_number: **Ticket Status Overview (Open, Closed, Invalid)**', 
                    help='Shows the composition of open, closed, and invalid tickets for each feature. X-axis: feature names, Y-axis: ticket count.')

        if not df_filtered.empty:
            df_plot2 = df_filtered.copy()
            
            # Persiapan Data (Sama seperti sebelumnya)
            solved_states = ['Done', 'RESOLVE', 'Resolve', 'Done.', 'DONE']
            invalid_states = ['Invalid']

            def categorize_ticket_state(status):
                if status in solved_states: return 'Closed'
                elif status in invalid_states: return 'Invalid'
                else: return 'Open'
            
            df_plot2['Ticket_State'] = df_plot2['Status'].apply(categorize_ticket_state)
            
            feature_order = df_plot2['Feature'].value_counts().index
            
            chart_data2 = df_plot2.groupby(['Feature', 'Ticket_State']).size().reset_index(name='Jumlah Tiket')
            pivot_df = chart_data2.pivot(index='Feature', columns='Ticket_State', values='Jumlah Tiket').fillna(0)
            pivot_df = pivot_df.reindex(feature_order)
            
            
            truncated_labels = pivot_df.index.map(lambda name: truncate_feature_name(name, max_words=2))
            

            fig2 = go.Figure()

            status_order = ['Closed', 'Invalid', 'Open']
            colors = {'Open': '#2C497F', 'Closed': '#24b24c', 'Invalid': "#9C9C9C"}

            for i, status in enumerate(status_order):
                if status not in pivot_df.columns:
                    continue

                is_top_layer = (i == len(status_order) - 1)
                radius = 10 if is_top_layer else 0

                fig2.add_trace(go.Bar(
                    name=status,
                    x=truncated_labels, # <- label yang udah dipotong
                    y=pivot_df[status],
                    hovertext=pivot_df.index, # <- Simpan nama lengkap untuk hover
                    marker=dict(
                        color=colors[status],
                        cornerradius=radius,
                        # line=dict(width=2, color='rgba(246, 246, 246, 1)')
                    ),
                    text=pivot_df[status].apply(lambda x: int(x) if x > 0 else ''),
                    textposition='inside',
                    textfont=dict(color='white'),
                    # Kustomisasi hover untuk menampilkan nama lengkap
                    hovertemplate='<b>%{hovertext}</b><br>' + f'{status}: %{{y}}<extra></extra>'
                ))

            # Poles Tampilan (Aesthetic)
            fig2.update_layout(
                barmode='stack',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    showgrid=False,
                    tickfont=dict(size=12, family='sans-serif'),
                    categoryorder='array',
                    categoryarray=truncated_labels # <-- Gunakan label terpotong untuk pengurutan
                ),
                yaxis=dict(
                    showgrid=True,
                    visible=True
                ),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1,
                    title_text="",
                    font=dict(family="sans-serif", size=12)
                ),
                height=400,
                margin=dict(l=10, r=10, t=80, b=0),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="sans-serif"
                )
            )
            
            st.plotly_chart(fig2, use_container_width=True)

        else:
            st.info("No ticket data found for the selected filters. Please adjust the filters and try again")            

    # Gunakan style container yang sama dengan chart lainnya untuk konsistensi
    css_styles_full_width = """
        {
            border: 2px solid #e6e6e6;
            border-radius: 10px;
            padding: 20px;
            background-color: #F6f6f6;
            height: 1015px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
    """

    with stylable_container(key="bubble_chart_container", css_styles=css_styles_full_width):
        st.markdown(':material/bubble_chart: **Ticket Distribution by Feature, Status, and Squad**',
                    help='This is a visualization of ticket density. The Y-axis represents features, the X-axis shows ticket statuses, color indicates the squad, and the bubble size reflects the number of ticket')

        # Panggil fungsi yang baru dibuat dengan data yang sudah difilter
        bubble_chart_fig = create_feature_squad_status_bubble_chart(df_filtered)

        # Tampilkan chart jika berhasil dibuat, atau tampilkan pesan jika tidak ada data
        if bubble_chart_fig:
            st.plotly_chart(bubble_chart_fig, use_container_width=True)
        else:
            st.info("There is not enough data to display the bubble chart based on the selected filters. Please ensure that the tickets contain 'Feature', 'Squad', and 'Status' information.")