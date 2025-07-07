# pages/JIRA Tickets.py
import streamlit as st
import pandas as pd
import os
import sys
import streamlit_antd_components as sac
from streamlit_extras.stylable_container import stylable_container

# --- Adjust Python Path to import from root ---
# This ensures you can import from your components, utils, etc.
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(script_dir, '..')
sys.path.append(project_root)

# --- Local Imports from your project structure ---
from config import NAMA_FILE_JIRA, METRIC_CARD_STYLE
from utils.data_loader import load_and_process_jira_data
from components.filters import render_filters, apply_filters
from components.metrics import display_summary_metrics

from utils.helpers import svg_to_img
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go


# JIRA_PATH = "data/jira_tiket.csv"
CSS_PATH = 'css/style.css'
TICKETS_PER_PAGE = 20

st.set_page_config(
    page_title="IntipinJira",
    page_icon="✅",
    layout='wide'
    )

st.html("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap');
        
        /* Ini adalah font default untuk seluruh aplikasi */
        html, body, [class*="css"] {
            font-family: 'Poppins', sans-serif;
        }
    </style>
""")

try:
    with open(CSS_PATH) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except FileNotFoundError:
    st.warning(f"CSS file '{CSS_PATH}' not found.")

@st.cache_data
def get_data(filename: str):
    """Cached function to load and process data."""
    with st.spinner("Loading and processing data..."):
        df = load_and_process_jira_data(filename)
    return df

# --- Main Data Loading & Filtering ---
df_jira_original = get_data(NAMA_FILE_JIRA)

# Cukup panggil satu fungsi ini untuk mendapatkan data matang
with st.spinner("Sabar yah, lagi ngeload datanya nih hehe..", show_time=True):
    df_jira_original = load_and_process_jira_data(NAMA_FILE_JIRA)
    
    
st.html(
    f"""
    <p style="margin-bottom: 20px;">
        <span class='green_text'>JIRA</span>
        <span class='black_text'>View</span>
    </p>
    """
)

with st.expander(':material/tune: Filter', expanded=True): # Expanded by default for testing
    render_filters(df_jira_original)
    
df_filtered = apply_filters(df_jira_original)


display_summary_metrics(df_filtered, METRIC_CARD_STYLE)


st.html('<div style="margin-bottom: 20px;"></div>')

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
        hot_selection = st.pills(" ", hot_opt, default='Recent', label_visibility='collapsed', key="hot_filter")
        
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
                    
                    if len(button_label) > 50:
                        button_label = button_label[:47] + "..."
                    
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
        details_html = "<div style='padding: 20px 40px;'>" 

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
            background-color: #EAEAEA;
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

            <h2 style="font-size: 1.8em; font-weight: 600; color: #212529; margin-top: 10px; margin-bottom: 50px; line-height: 1.3;">
                {ticket.get('Title', 'N/A')}
            </h2>
        </div>
        """

        
        # -- Helper function untuk render item metadata --
        def render_meta_item_html(label, value, default_val="–"):
            display_value = value if pd.notna(value) and str(value).strip() and str(value).lower() not in ['nan', 'nat', 'none', ''] else default_val
            return f"""
            <div style="margin-bottom: 18px;"> 
                <p style="font-size: 0.7em; color: #6c757d; margin-bottom: 0px; text-transform: uppercase; font-weight: 500; letter-spacing: 0.5px;">{label}</p>
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

        col2_content = "<div class='desc-hover'>"
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
        details_html += "<hr style='border: none; border-top: 2px solid #e9ecef; margin: 30px 0px 30px 0px;'>"
        details_html += "<p style='font-size: 0.8em; color: #495057; margin-bottom: 30px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>Description</p>"
        
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
