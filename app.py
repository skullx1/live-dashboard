from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

# ----------------------------------------------------------------------------
# Theme tokens — black and purple palette
# ----------------------------------------------------------------------------
BG = "#000000"
SURFACE = "#0B0014"
SURFACE_ALT = "#160026"
BORDER = "#5B21B6"
TEXT_PRIMARY = "#F3E8FF"
TEXT_SECONDARY = "#C4B5FD"
UP = "#C084FC"      # lighter purple for gains
DOWN = "#6D28D9"    # darker purple for losses
ACCENT = "#8B5CF6"  # main purple accent

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

    /* Hide default streamlit chrome */
    #MainMenu, header, footer {{visibility: hidden;}}

    /* ---- Ticker strip ---- */
    .ticker-wrap {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 10px 18px;
        margin-bottom: 22px;
        overflow-x: auto;
        white-space: nowrap;
    }}
    .ticker-item {{
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 14px;
        margin-right: 32px;
        color: {TEXT_PRIMARY};
    }}
    .ticker-item .sym {{
        color: {TEXT_SECONDARY};
        margin-right: 6px;
    }}
    .ticker-up {{ color: {UP}; font-weight: 600; }}
    .ticker-down {{ color: {DOWN}; font-weight: 600; }}

    /* ---- Title ---- */
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

    /* ---- Section headers ---- */
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

    /* ---- Metric cards ---- */
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
    div[data-testid="stMetricDelta"] svg {{
        fill: {UP} !important;
    }}

    /* ---- Inputs ---- */
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

    /* ---- Buttons ---- */
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

    /* ---- Dataframe ---- */
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

# Read the API key safely from .streamlit/secrets.toml
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    st.error("Finnhub API key was not found in secrets.toml.")
    st.stop()


@st.cache_data(ttl=60)
def get_stock_quote(symbol):
    """Get the latest available stock quote from Finnhub."""
    url = "https://finnhub.io/api/v1/quote"
    params = {
        "symbol": symbol,
        "token": API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return None, data["error"]

        if not data or data.get("c", 0) == 0:
            return None, "No data was found. Check the stock symbol."

        return data, None

    except requests.exceptions.Timeout:
        return None, "The API took too long to respond. Please try again."

    except requests.exceptions.ConnectionError:
        return None, "Internet connection failed. Check your connection."

    except requests.exceptions.RequestException:
        return None, "Unable to fetch stock data right now."


stocks = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "NVIDIA (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA",
    "Google (GOOGL)": "GOOGL",
}

# ----------------------------------------------------------------------------
# Header + live ticker strip
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="dash-title">📈 Stock<span>Terminal</span></div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="dash-caption">Latest available stock data pulled from the Finnhub API.</div>',
    unsafe_allow_html=True,
)

ticker_html = '<div class="ticker-wrap">'
for name, sym in stocks.items():
    data, err = get_stock_quote(sym)
    if err or not data:
        ticker_html += f'<span class="ticker-item"><span class="sym">{sym}</span>—</span>'
        continue
    dp = data.get("dp", 0) or 0
    arrow = "▲" if dp >= 0 else "▼"
    css_class = "ticker-up" if dp >= 0 else "ticker-down"
    ticker_html += (
        f'<span class="ticker-item"><span class="sym">{sym}</span>'
        f'${data["c"]:,.2f} <span class="{css_class}">{arrow} {dp:+.2f}%</span></span>'
    )
ticker_html += "</div>"
st.markdown(ticker_html, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Symbol picker
# ----------------------------------------------------------------------------
col_a, col_b = st.columns([2, 2])
with col_a:
    selected_stock = st.selectbox("Choose a stock", list(stocks.keys()))
with col_b:
    custom_symbol = st.text_input(
        "Or enter another US stock symbol",
        placeholder="Example: META",
    )

if custom_symbol.strip():
    symbol = custom_symbol.strip().upper()
else:
    symbol = stocks[selected_stock]

get_data = st.button("Get stock data", type="primary")

if get_data:
    with st.spinner(f"Fetching {symbol} data..."):
        quote, error = get_stock_quote(symbol)

    if error:
        st.error(error)

    else:
        current_price = quote["c"]
        change = quote["d"]
        percent_change = quote["dp"]
        high_price = quote["h"]
        low_price = quote["l"]
        open_price = quote["o"]
        previous_close = quote["pc"]

        move_color = UP if change >= 0 else DOWN

        st.markdown(f'<div class="section-label">{symbol} — Latest Quote</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        col1.metric("Current price", f"${current_price:,.2f}", f"{change:+.2f}")
        col2.metric("Percentage change", f"{percent_change:.2f}%")
        col3.metric("Previous close", f"${previous_close:,.2f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Open", f"${open_price:,.2f}")
        col5.metric("Day high", f"${high_price:,.2f}")
        col6.metric("Day low", f"${low_price:,.2f}")

        chart_data = pd.DataFrame({
            "Price point": ["Previous close", "Open", "Day high", "Day low", "Current"],
            "Price": [previous_close, open_price, high_price, low_price, current_price],
        })

        st.markdown('<div class="section-label">Price Comparison</div>', unsafe_allow_html=True)

        fig = go.Figure(
            go.Bar(
                x=chart_data["Price point"],
                y=chart_data["Price"],
                marker_color=[TEXT_SECONDARY, ACCENT, UP, DOWN, move_color],
                text=[f"${v:,.2f}" for v in chart_data["Price"]],
                textposition="outside",
            )
        )
        fig.update_layout(
            plot_bgcolor=SURFACE,
            paper_bgcolor=BG,
            font=dict(color=TEXT_PRIMARY, family="JetBrains Mono"),
            margin=dict(t=10, b=10, l=10, r=10),
            yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
            xaxis=dict(gridcolor=BORDER),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)

        if quote.get("t"):
            update_time = datetime.fromtimestamp(quote["t"])
            st.caption(f"Last market update: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")

        st.markdown('<div class="section-label">Market Overview</div>', unsafe_allow_html=True)

        overview_rows = []
        for stock_name, stock_symbol in stocks.items():
            stock_data, stock_error = get_stock_quote(stock_symbol)
            if not stock_error:
                overview_rows.append({
                    "Stock": stock_symbol,
                    "Current Price": stock_data["c"],
                    "Percentage Change": stock_data["dp"],
                })

        if overview_rows:
            overview = pd.DataFrame(overview_rows)

            overview_col1, overview_col2 = st.columns(2)

            with overview_col1:
                st.markdown("**Current Price Comparison**")
                fig_price = go.Figure(
                    go.Bar(
                        x=overview["Stock"],
                        y=overview["Current Price"],
                        marker_color=ACCENT,
                        text=[f"${v:,.2f}" for v in overview["Current Price"]],
                        textposition="outside",
                    )
                )
                fig_price.update_layout(
                    plot_bgcolor=SURFACE,
                    paper_bgcolor=BG,
                    font=dict(color=TEXT_PRIMARY, family="JetBrains Mono"),
                    margin=dict(t=10, b=10, l=10, r=10),
                    yaxis=dict(gridcolor=BORDER),
                    xaxis=dict(gridcolor=BORDER),
                    height=340,
                )
                st.plotly_chart(fig_price, use_container_width=True)

            with overview_col2:
                st.markdown("**Percentage Change Comparison**")
                colors = [UP if v >= 0 else DOWN for v in overview["Percentage Change"]]
                fig_pct = go.Figure(
                    go.Bar(
                        x=overview["Stock"],
                        y=overview["Percentage Change"],
                        marker_color=colors,
                        text=[f"{v:+.2f}%" for v in overview["Percentage Change"]],
                        textposition="outside",
                    )
                )
                fig_pct.update_layout(
                    plot_bgcolor=SURFACE,
                    paper_bgcolor=BG,
                    font=dict(color=TEXT_PRIMARY, family="JetBrains Mono"),
                    margin=dict(t=10, b=10, l=10, r=10),
                    yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER),
                    xaxis=dict(gridcolor=BORDER),
                    height=340,
                )
                st.plotly_chart(fig_pct, use_container_width=True)

            st.markdown("**Market Data Table**")
            st.dataframe(overview, hide_index=True, use_container_width=True)

st.markdown(
    f'<div style="margin-top:30px; padding:14px 18px; background:{SURFACE_ALT}; '
    f'border:1px solid {BORDER}; border-radius:10px; color:{TEXT_SECONDARY}; font-size:13px;">'
    f"ℹ️ This dashboard is for learning and displays the latest data available from the API."
    f"</div>",
    unsafe_allow_html=True,
)