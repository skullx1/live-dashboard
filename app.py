import streamlit as st
from views import home, ai_summary, chatbot

st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

# ----------------------------------------------------------------------------
# Theme tokens & CSS Injection
# ----------------------------------------------------------------------------
BG = "#000000"
SURFACE = "#0B0014"
SURFACE_ALT = "#160026"
BORDER = "#5B21B6"
TEXT_PRIMARY = "#F3E8FF"
TEXT_SECONDARY = "#C4B5FD"
UP = "#C084FC"
DOWN = "#6D28D9"
ACCENT = "#8B5CF6"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background:
            radial-gradient(circle at top right, #160026 0%, transparent 35%),
            linear-gradient(135deg, #000000 0%, #08000F 55%, #120020 100%);
        color: {TEXT_PRIMARY};
    }}

    #MainMenu, footer {{visibility: hidden;}}

    .dash-title {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 34px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: {TEXT_PRIMARY};
        margin-bottom: 0px;
    }}
    .dash-title span {{ color: {ACCENT}; }}
    .dash-caption {{
        color: {TEXT_SECONDARY};
        font-size: 14px;
        margin-bottom: 24px;
    }}

    .section-label {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        color: {ACCENT};
        border-bottom: 1px solid {BORDER};
        padding-bottom: 8px;
        margin: 28px 0 16px 0;
    }}

    div[data-testid="stMetric"] {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 0 18px rgba(139, 92, 246, 0.16);
    }}
    div[data-testid="stMetricLabel"] {{
        color: {TEXT_SECONDARY} !important;
        font-family: 'Inter', sans-serif;
        font-size: 13px !important;
    }}
    div[data-testid="stMetricValue"] {{
        color: {TEXT_PRIMARY} !important;
        font-family: 'JetBrains Mono', monospace;
    }}
    div[data-testid="stMetricDelta"] {{
        color: {UP} !important;
    }}

    .stSelectbox label, .stTextInput label {{
        color: {TEXT_SECONDARY} !important;
        font-size: 13px;
    }}
    div[data-baseweb="select"] > div, .stTextInput input {{
        background-color: {SURFACE} !important;
        border: 1px solid {BORDER} !important;
        color: {TEXT_PRIMARY} !important;
        font-family: 'JetBrains Mono', monospace;
    }}

    .stButton > button {{
        background-color: {ACCENT};
        color: {TEXT_PRIMARY};
        border: 1px solid #A855F7;
        border-radius: 10px;
        font-weight: 700;
        padding: 8px 22px;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 0 16px rgba(139, 92, 246, 0.24);
    }}
    .stButton > button:hover {{
        background-color: #C084FC;
        color: #160026;
        border-color: #D8B4FE;
    }}

    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 10px;
        overflow: hidden;
    }}

    hr {{ border-color: {BORDER} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Session & Page State Initialization
# ----------------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "main"

st.sidebar.title("📌 Navigation")

if st.sidebar.button("🏠 Market Overview", use_container_width=True):
    st.session_state.page = "main"

if st.sidebar.button("🤖 AI Market Insights", use_container_width=True):
    st.session_state.page = "ai_summary"

if st.sidebar.button("💬 Stock Chatbot", use_container_width=True):
    st.session_state.page = "chatbot"

# Render target view
if st.session_state.page == "main":
    home.show()
elif st.session_state.page == "ai_summary":
    ai_summary.show()
elif st.session_state.page == "chatbot":
    chatbot.show()