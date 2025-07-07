# --- File Configuration ---
NAMA_FILE_JIRA = 'jira_tiket.csv'
TICKETS_PER_PAGE = 20 # Add this for the ticket list page

# --- Status Definitions ---
STATUS_CATEGORIES = {
    "resolved": ['Done', 'RESOLVE', 'Resolve', 'Done.', 'DONE', 'Closed'],
    "invalid": ['Invalid'],
    "reopen": ['Reopened', 'REOPEN']
}
STATUS_CATEGORIES["final_closed"] = STATUS_CATEGORIES["resolved"] + STATUS_CATEGORIES["invalid"]

# --- Color Palettes ---
SEVERITY_COLORS = {'Highest': '#E63946', 'Medium': '#FCA311', 'Low': '#147DF5'}
TICKET_STATE_COLORS = {'Open': '#2C497F', 'Closed': '#24b24c', 'Invalid': "#9C9C9C"}
ACTIVITY_CHART_COLORS = {
    'open': "#E24F4F",
    'solved': '#24b24c',
    'invalid': '#636363'
}
LIFECYCLE_CHART_COLORS = {"opened": "#E24F4F", "closed": '#24b24c'}

# --- Styling for Containers ---
PLOT_CONTAINER_STYLE = """
{
    border: 2px solid #e6e6e6;
    border-radius: 10px;
    padding: 20px;
    height: 500px;
    overflow-y: auto;
    background-color: #F6f6f6;
    box-shadow: 0 4px 8px rgba(0,0,0,0.05);
}
&::-webkit-scrollbar { width: 8px; }
&::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
&::-webkit-scrollbar-thumb { background: #cccccc; border-radius: 10px; }
&::-webkit-scrollbar-thumb:hover { background: #aaaaaa; }
"""

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
