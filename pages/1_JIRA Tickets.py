import streamlit as st
import pandas as pd
from utils.jira_processed import jiraProgress_proc
from datetime import datetime, timedelta
import urllib.parse
import json
import plotly.graph_objects as go

JIRA_PATH = "data/jira_tiket.csv"
CSS_PATH = 'css/style.css'
TICKETS_PER_PAGE = 20

st.set_page_config(
    page_title="IntipinJira",
    page_icon="✅",
    layout='wide'
    )

@st.cache_data
def load_data(path):
    return jiraProgress_proc(path)

df_jira_original = load_data(JIRA_PATH)

# Kalkulasi nilai default tanggal sekali saja di awal
min_date_data, max_date_data, default_date_val = (None, None, (datetime.now().date() - timedelta(days=7), datetime.now().date()))
if 'Created' in df_jira_original.columns and not df_jira_original['Created'].dropna().empty:
    if not pd.api.types.is_datetime64_any_dtype(df_jira_original['Created']):
        df_jira_original['Created'] = pd.to_datetime(df_jira_original['Created'], errors='coerce')
    
    if not df_jira_original['Created'].dropna().empty:
        min_date_data = df_jira_original['Created'].dropna().min().date()
        max_date_data = df_jira_original['Created'].dropna().max().date()
        default_date_val = (min_date_data, max_date_data)

# Inisialisasi semua state filter HANYA JIKA belum ada
if "project_filter" not in st.session_state:
    st.session_state.project_filter = []
if "status_filter" not in st.session_state:
    st.session_state.status_filter = []
if "feature_filter" not in st.session_state:
    st.session_state.feature_filter = []
if "platform_filter" not in st.session_state:
    st.session_state.platform_filter = []
if "search_filter" not in st.session_state:
    st.session_state.search_filter = ""
if "date_filter" not in st.session_state:
    st.session_state.date_filter = default_date_val

# Fungsi untuk mereset semua filter
def reset_all_filters():
    # Langsung set ulang nilai di session_state ke kondisi awal
    st.session_state.project_filter = []
    st.session_state.status_filter = []
    st.session_state.feature_filter = []
    st.session_state.platform_filter = []
    st.session_state.search_filter = ""
    st.session_state.date_filter = default_date_val # Gunakan default_date_val yang sudah dihitung
    
    # Reset juga halaman dan tiket yang dipilih
    st.session_state.current_page_col1 = 1
    st.session_state.selected_ticket_id = None
    st.session_state.selected_ticket_details = None
    
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


try:
    with open(CSS_PATH) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning(f"CSS file '{CSS_PATH}' not found.")

st.markdown(
    f"""
    <p style="font-size: 24px; margin-bottom: 20px;">
        <span class='green_text'>JIRA</span>
        <span class='black_text'>Tickets</span>
    </p>
    """,
    unsafe_allow_html=True
)

# Filter Section
with st.expander('Filter', expanded=False):

    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([0.12, 0.22, 0.22, 0.22, 0.22]) # Sesuaikan rasio jika perlu

    with filter_col1:
        if 'Tickets' in df_jira_original.columns:
            df_jira_original['Project_Code'] = df_jira_original['Tickets'].apply(
                lambda x: x.split('-')[0] if isinstance(x, str) and '-' in x else 'None'
            )
            project_opt_dynamic = sorted(df_jira_original['Project_Code'].unique().tolist())

        project_selected = st.multiselect(
            label='Project',
            placeholder='Select Project',
            options=project_opt_dynamic,
            label_visibility="collapsed",
            key='project_filter',
        )

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
        created_date_range = st.date_input(
            "Date Range",
            # value=default_date_val,
            min_value=min_date_data,
            max_value=max_date_data,
            format="DD/MM/YYYY",
            label_visibility="collapsed",
            key='date_filter'
        )

    label_col, stage_col, solved_col, search_col, reset_col = st.columns([0.92, 0.85, 0.85, 4, 1.1]) # Kolom search 4x lebih lebar dari tombol

    with label_col:
        label_opt_dynamic = []
        if "Labels" in df_jira_original and not df_jira_original['Labels'].dropna().empty:
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
        if "Stage" in df_jira_original and not df_jira_original['Stage'].dropna().empty:
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
            placeholder='Solved?',
            options = solved_opt,
            label_visibility='collapsed',
            index=None,
            key='solved_filter'
        )
            
    with search_col:
        ticket_id_search = st.text_input(
            label="Ticket ID Search",
            placeholder="Filter by code project, example: RIB-1006 or 1006",
            label_visibility="collapsed",
            key="search_filter" # <-- TAMBAHKAN KEY DI SINI JUGA
        ).strip()

    with reset_col:
        # Ini tombol resetnya, ditaruh di kolom sebelahnya
        st.button(
            ":material/refresh: Reset Filters", 
            on_click=reset_all_filters, # Panggil fungsi reset saat diklik
            use_container_width=True,
            type="secondary" # Membuat tombol terlihat 'secondary' (biasanya abu-abu)
        )


st.markdown("<div style='margin-top:10px;'> </div>", unsafe_allow_html=True)

# Applying Filters
df_filtered = df_jira_original.copy()

# PERTAMA: Terapkan filter Kode Tiket jika ada input
if ticket_id_search and 'Tickets' in df_filtered.columns:
    # Membuat pencarian case-insensitive dan memastikan 'Tickets' adalah string
    df_filtered = df_filtered[df_filtered['Tickets'].astype(str).str.contains(ticket_id_search, case=False, na=False)]

# KEDUA: Terapkan filter-filter lainnya ke df_filtered yang MUNGKIN sudah tersaring oleh pencarian ID tiket
if project_selected: 
    if 'Project_Code' in df_filtered.columns: # Ganti 'Project_Derived' jadi 'Project_Code' sesuai kode filter_col1
        df_filtered = df_filtered[df_filtered['Project_Code'].isin(project_selected)]

if status_selected and 'Status' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Status'].isin(status_selected)]

if feature_selected and 'Feature' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Feature'].isin(feature_selected)]

if platform_selected and 'Platform' in df_filtered.columns:
    platform_conditions = pd.Series([False] * len(df_filtered), index=df_filtered.index) # bikin dulu kondisi awal False dgn panjang index series sama dengan df_filtered
    for p_select in platform_selected:
    # pake simbol | untuk atau, jadi platform_condition | hasil contain -> kalo hasilnya ada, berarti ambil True, karena False | True = True
    # kenapa kita pake cara ini, karena untuk menghindari looping yang setelah kefilter, difilter lagi kalo misal selected platformnya lebih dari satu
    # misal user pilih "android", data nampilin android, tp ketika user pilih lagi 'iOS', data yang tadi udah nampil android, jadi kita filter lagi buat iOS. hasilnya kosong
    # makanya pake metode OR atau | buat nandain misal user milih "android" ya berarti True, tp kalo user pilih "iOS" juga, True yg tadi ga keubah krn ["android", "iOS"] ngubah 22nya True
        platform_conditions = platform_conditions | df_filtered['Platform'].str.contains(p_select, case=False, na=False)
    df_filtered = df_filtered[platform_conditions] # since platform_condition kita bikin indexnya sama dengan df_filtered, jadi bisa langsung filter df_filtered
    # istilahnya nih df_filtered['Platform'].str.contains(p_select, case=False, na=False) buat yang True

if created_date_range and len(created_date_range) == 2 and 'Created' in df_filtered.columns:
    start_date, end_date = pd.to_datetime(created_date_range[0]), pd.to_datetime(created_date_range[1])
    df_filtered['Created'] = pd.to_datetime(df_filtered['Created'], errors='coerce') # Pastikan datetime
    df_filtered = df_filtered[
        (df_filtered['Created'].dt.normalize() >= start_date.normalize()) &
        (df_filtered['Created'].dt.normalize() <= end_date.normalize())
    ]
    
if label_selected and 'Labels' in df_filtered.columns:
    regex_pattern = '|'.join(label_selected) # tambahin atau as dia bisa contain lebih dari 1
    df_filtered = df_filtered[df_filtered['Labels'].str.contains(regex_pattern, na=False)] # na = False, biar ga error ketika filternya NaN
    
if stage_selected and 'Stage' in df_filtered.columns:
    df_filtered = df_filtered[df_filtered['Stage'].isin(stage_selected)]
    
if solved_selected == 'Solved':
    df_filtered = df_filtered[df_filtered['Resolved_Time'].notna()]

elif solved_selected == 'Not Yet':
    df_filtered = df_filtered[df_filtered['Resolved_Time'].isna()]
    
    

# Session State
if 'current_page_col1' not in st.session_state: # ini page si user disimpen ke dalem session_state, kalo misal baru, halaman 1
    st.session_state.current_page_col1 = 1
if 'selected_ticket_id' not in st.session_state: # ini buat nampung id tiket yang dipilih sama user, kalo ga ada, None
    st.session_state.selected_ticket_id = None
if 'selected_ticket_details' not in st.session_state: # ini buat nampung detail tiket yang abis dipilih user, kalo ga ada, None
    st.session_state.selected_ticket_details = None


main_col1, main_col2, main_col3 = st.columns([0.1, 0.4, 0.2])

with main_col1:

    if df_filtered.empty or not ('Tickets' in df_filtered.columns and 'Title' in df_filtered.columns):
        st.info("Sorry! There are no tickets matching the selected filters")
    else:
        
        hot_opt = ["Recent", "Hot"]
        hot_selection = st.pills(" ", hot_opt, label_visibility='collapsed', default='Recent')
        
        
        df_for_display = df_filtered.copy()
        if hot_selection == "Hot":
            if 'Count_Comments' in df_for_display.columns:
                df_for_display = df_for_display[df_for_display['Count_Comments'] > 3]
        elif hot_selection == "Recent":
            if 'Created' in df_for_display.columns:
                df_for_display['Created'] = pd.to_datetime(df_for_display['Created'])
                df_for_display = df_for_display.sort_values(by='Created', ascending=False)
                
        total_tickets = len(df_for_display)
        # bikin total page dibagi sisa (//) dengan 20, misal 141 dibagi 20 sisa 7 sebelum ke koma, karena untuk mencakup sisa tiket, ditambah 1
        total_pages = (total_tickets - 1) // TICKETS_PER_PAGE + 1 if total_tickets > 0 else 1

        if st.session_state.current_page_col1 > total_pages:
            st.session_state.current_page_col1 = max(1, total_pages) # ngecegah misal kalo user lagi di halaman 8, trus user make filter jadi total halaman 2, maka user akan direset ke halaman terakhir yang valid
            # nah kenapa max(1, total_pages), karena max harus ada pembanding buat ngambil yang maksimal

        # ini buat dapet index awal dari tiket df, jadi kalo user emang lagi di halaman 1, maka dikurang 1 (0) * 20 = 0 <- index awal
        # kalo misal start_idx = user lagi di halaman 2, maka 2-1 * 20 = 20 <- ini yg jadi index awal
        start_idx = (st.session_state.current_page_col1 - 1) * TICKETS_PER_PAGE
        end_idx = min(start_idx + TICKETS_PER_PAGE, total_tickets)
        
        tickets_to_display = df_for_display.iloc[start_idx:end_idx]
        
        ticket_list_container = st.container(height=1330, border=False)
        with ticket_list_container:
            if tickets_to_display.empty:
                st.write("There are no tickets to display on this page.")
            else:
                for index, row in tickets_to_display.iterrows():
                    ticket_id = str(row['Tickets'])
                    ticket_title = str(row['Title'])
                    # Ambil jumlah komen dari kolom 'Count_Comments'
                    # Pakai .get() lebih aman, kalau kolomnya nggak ada, dia nggak error
                    comment_count = row.get('Count_Comments', 0) 
                    
                    # Logika pemotongan judul tetap dipertahankan
                    shortened_title = ticket_title 
                    try:
                        title_parts = ticket_title.split(' - ')
                        if len(title_parts) > 2:
                            shortened_title = title_parts[2].strip()
                        else:
                            shortened_title = title_parts[-1].strip()
                    except Exception:
                        shortened_title = ticket_title
                    
                    button_key = f"select_{ticket_id}_{start_idx + index}_{st.session_state.current_page_col1}" # Button key lebih unik lagi
                    
                        
                    indicator = "🔥 " if comment_count > 3 else ""
            
                    # 2. Gabungkan indicator ke dalam label tombol
                    button_label = f"{indicator}**{ticket_id}**: {shortened_title}"
                    
                    # 3. Gunakan label baru ini di tombol lo
                    if st.button(button_label, key=button_key, use_container_width=True):
                        st.session_state.selected_ticket_id = ticket_id
                        st.session_state.selected_ticket_details = row.to_dict()

        if total_pages > 1:
            st.markdown("---")
            nav_cols = st.columns([1, 1, 2, 1, 1])
            with nav_cols[0]:
                if st.button(":material/first_page:", key="pg_first_col1", disabled=(st.session_state.current_page_col1 == 1), use_container_width=True):
                    st.session_state.current_page_col1 = 1
                    st.rerun()
            with nav_cols[1]:
                if st.button(":material/chevron_left:", key="pg_prev_col1", disabled=(st.session_state.current_page_col1 == 1), use_container_width=True):
                    st.session_state.current_page_col1 -= 1
                    st.rerun()
            with nav_cols[2]:
                st.write(f"<div style='text-align: center; margin-top: 0.5em;'> {st.session_state.current_page_col1} / {total_pages}</div>", unsafe_allow_html=True)
            with nav_cols[3]:
                if st.button(":material/chevron_right:", key="pg_next_col1", disabled=(st.session_state.current_page_col1 == total_pages), use_container_width=True):
                    st.session_state.current_page_col1 += 1
                    st.rerun()
            with nav_cols[4]:
                if st.button(":material/last_page:", key="pg_last_col1", disabled=(st.session_state.current_page_col1 == total_pages), use_container_width=True):
                    st.session_state.current_page_col1 = total_pages
                    st.rerun()

with main_col2:
    
    details_container = st.container(height=1500) 
    
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
            # Jika datanya kosong atau "–", kembalikan "–"
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
        col2_content += render_meta_item_html("Solved At", resolved_str, default_val="Belum Selesai")
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
            comment_scroll_container = st.container(height=1440)
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
                    while j < len(df_history) and (df_history.loc[j, 'timestamp'] - df_history.loc[j-1, 'timestamp']) < TRANSITIONAL_THRESHOLD:
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
                #      tapi sekarang menggunakan df_history_clean sebagai input) ...

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
                    # if row['status_from'] is None:  # Titik awal
                    #     colors.append('#dc3545')  # Merah
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
                    
                    plot_scroll_container = st.container(height=1440)
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
        comment_scroll_placeholder = st.container(height=1500) 
        comment_scroll_placeholder.html(comment_placeholder)
