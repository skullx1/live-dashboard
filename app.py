from datetime import datetime

import anthropic
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

try:
    ANTHROPIC_API_KEY = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    ANTHROPIC_API_KEY = None


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


def get_ai_explanation(symbol, quote, language):
    """Explain the displayed quote with Claude without giving trading advice."""
    if not ANTHROPIC_API_KEY:
        return None, "Claude API key was not found in secrets.toml."

    high_price = quote["h"]
    low_price = quote["l"]
    current_price = quote["c"]

    if high_price > low_price:
        range_position = ((current_price - low_price) / (high_price - low_price)) * 100
    else:
        range_position = 50

    prompt = f"""
Explain the following stock quote in {language}.

Stock symbol: {symbol}
Current price: ${quote['c']:.2f}
Price change: ${quote['d']:+.2f}
Percentage change: {quote['dp']:+.2f}%
Open price: ${quote['o']:.2f}
Previous close: ${quote['pc']:.2f}
Day high: ${quote['h']:.2f}
Day low: ${quote['l']:.2f}
Current position within today's low-to-high range: {range_position:.1f}%

Use this structure:
1. Momentum: Positive, Neutral, or Negative.
2. What changed today.
3. Position within today's range.
4. Plain-language explanation of the key numbers.
5. A short educational note.

Use only the numbers provided. Do not predict the future. Do not recommend
buying, selling, or holding the stock. Do not provide personalized financial
advice. Clearly state that this is educational analysis of the displayed data.
"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=700,
            system=(
                "You are a careful educational stock-data explainer. "
                "Be concise, factual, and easy to understand."
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        explanation = "\n".join(
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        )

        if not explanation:
            return None, "Claude returned an empty explanation."

        return explanation, None

    except anthropic.AuthenticationError:
        return None, "Claude rejected the API key. Check ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        return None, "Claude rate limit reached. Please try again later."
    except anthropic.APIConnectionError:
        return None, "Unable to connect to Claude right now."
    except anthropic.APIError:
        return None, "Claude could not generate an explanation right now."


def get_ai_market_summary(market_rows, language):
    """Summarize the displayed market snapshot with Claude."""
    if not ANTHROPIC_API_KEY:
        return None, "Claude API key was not found in secrets.toml."

    market_lines = "\n".join(
        (
            f"{row['symbol']}: current ${row['current_price']:.2f}, "
            f"change {row['change']:+.2f}, "
            f"percentage change {row['percent_change']:+.2f}%, "
            f"open ${row['open_price']:.2f}, "
            f"high ${row['high_price']:.2f}, "
            f"low ${row['low_price']:.2f}, "
            f"previous close ${row['previous_close']:.2f}"
        )
        for row in market_rows
    )

    advancers = sum(
        row["percent_change"] > 0
        for row in market_rows
    )
    decliners = sum(
        row["percent_change"] < 0
        for row in market_rows
    )
    unchanged = len(market_rows) - advancers - decliners
    average_change = sum(
        row["percent_change"]
        for row in market_rows
    ) / len(market_rows)
    strongest = max(
        market_rows,
        key=lambda row: row["percent_change"],
    )
    weakest = min(
        market_rows,
        key=lambda row: row["percent_change"],
    )

    prompt = f"""
Write a concise market snapshot in {language} using only the data below.

Stocks in this dashboard:
{market_lines}

Calculated breadth:
- Advancing stocks: {advancers}
- Declining stocks: {decliners}
- Unchanged stocks: {unchanged}
- Average percentage change: {average_change:+.2f}%
- Strongest daily movement: {strongest['symbol']}
  ({strongest['percent_change']:+.2f}%)
- Weakest daily movement: {weakest['symbol']}
  ({weakest['percent_change']:+.2f}%)

Use this structure:
1. Market tone: Positive, Mixed, or Negative.
2. Market breadth.
3. Leaders and laggards.
4. Notable movements in plain language.
5. A short educational takeaway.

Keep the answer easy to scan. Use only the supplied snapshot. Do not introduce
news, forecasts, company fundamentals, or outside information. Do not recommend
buying, selling, or holding any stock. State that this is an educational summary
of a limited stock list and not a summary of the entire market.
"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=900,
            system=(
                "You are a careful educational market-data summarizer. "
                "Be concise, factual, and easy to understand."
            ),
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        summary = "\n".join(
            block.text
            for block in message.content
            if getattr(block, "type", None) == "text"
        )

        if not summary:
            return None, "Claude returned an empty market summary."

        return summary, None

    except anthropic.AuthenticationError:
        return None, "Claude rejected the API key. Check ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        return None, "Claude rate limit reached. Please try again later."
    except anthropic.APIConnectionError:
        return None, "Unable to connect to Claude right now."
    except anthropic.APIError:
        return None, "Claude could not generate a market summary right now."


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
    symbol = stocks[selected_stock]

ai_col1, ai_col2 = st.columns([1, 1])
with ai_col1:
    generate_ai = st.toggle(
        "Generate AI explanation",
        help="Claude explains the displayed numbers without buy or sell advice.",
    )
with ai_col2:
    ai_language = st.selectbox(
        "AI explanation language",
        ["English", "Arabic"],
        disabled=not generate_ai,
    )

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

        if generate_ai:
            st.markdown(
                '<div class="section-label">AI Stock Explainer</div>',
                unsafe_allow_html=True,
            )

            with st.spinner("Claude is explaining the stock data..."):
                explanation, ai_error = get_ai_explanation(
                    symbol,
                    quote,
                    ai_language,
                )

            if ai_error:
                st.error(ai_error)
            else:
                with st.container(border=True):
                    st.markdown(explanation)
                    st.caption(
                        "Educational data explanation only — not financial advice."
                    )

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

# ----------------------------------------------------------------------------
# Compare two stocks
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="section-label">Compare Two Stocks</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Compare the latest available quote and daily movement for two US stocks."
)

comparison_options = list(stocks.keys())
compare_col1, compare_col2 = st.columns(2)

with compare_col1:
    comparison_name_1 = st.selectbox(
        "First stock",
        comparison_options,
        index=0,
        key="comparison_stock_1",
    )

with compare_col2:
    comparison_name_2 = st.selectbox(
        "Second stock",
        comparison_options,
        index=1,
        key="comparison_stock_2",
    )

compare_clicked = st.button(
    "Compare stocks",
    key="compare_stocks_button",
    use_container_width=True,
)

if compare_clicked:
    comparison_symbol_1 = stocks[comparison_name_1]
    comparison_symbol_2 = stocks[comparison_name_2]

    if comparison_symbol_1 == comparison_symbol_2:
        st.warning("Choose two different stocks to compare.")
    else:
        with st.spinner(
            f"Comparing {comparison_symbol_1} and {comparison_symbol_2}..."
        ):
            comparison_quote_1, comparison_error_1 = get_stock_quote(
                comparison_symbol_1
            )
            comparison_quote_2, comparison_error_2 = get_stock_quote(
                comparison_symbol_2
            )

        if comparison_error_1:
            st.error(
                f"{comparison_symbol_1}: {comparison_error_1}"
            )
        elif comparison_error_2:
            st.error(
                f"{comparison_symbol_2}: {comparison_error_2}"
            )
        else:
            st.session_state["stock_comparison"] = {
                "symbol_1": comparison_symbol_1,
                "symbol_2": comparison_symbol_2,
                "quote_1": comparison_quote_1,
                "quote_2": comparison_quote_2,
            }

comparison_result = st.session_state.get("stock_comparison")

if comparison_result:
    comparison_symbol_1 = comparison_result["symbol_1"]
    comparison_symbol_2 = comparison_result["symbol_2"]
    comparison_quote_1 = comparison_result["quote_1"]
    comparison_quote_2 = comparison_result["quote_2"]

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        with st.container(border=True):
            st.subheader(comparison_symbol_1)
            st.metric(
                "Current price",
                f"${comparison_quote_1['c']:,.2f}",
                f"{comparison_quote_1['d']:+.2f}",
            )
            metric_left, metric_right = st.columns(2)
            metric_left.metric(
                "Daily change",
                f"{comparison_quote_1['dp']:+.2f}%",
            )
            metric_right.metric(
                "Day range",
                f"${comparison_quote_1['l']:,.2f} – "
                f"${comparison_quote_1['h']:,.2f}",
            )

    with result_col2:
        with st.container(border=True):
            st.subheader(comparison_symbol_2)
            st.metric(
                "Current price",
                f"${comparison_quote_2['c']:,.2f}",
                f"{comparison_quote_2['d']:+.2f}",
            )
            metric_left, metric_right = st.columns(2)
            metric_left.metric(
                "Daily change",
                f"{comparison_quote_2['dp']:+.2f}%",
            )
            metric_right.metric(
                "Day range",
                f"${comparison_quote_2['l']:,.2f} – "
                f"${comparison_quote_2['h']:,.2f}",
            )

    comparison_chart_col1, comparison_chart_col2 = st.columns(2)

    with comparison_chart_col1:
        st.markdown("**Daily Percentage Change**")
        comparison_changes = [
            comparison_quote_1["dp"],
            comparison_quote_2["dp"],
        ]
        comparison_change_fig = go.Figure(
            go.Bar(
                x=[comparison_symbol_1, comparison_symbol_2],
                y=comparison_changes,
                marker_color=[
                    UP if value >= 0 else DOWN
                    for value in comparison_changes
                ],
                text=[
                    f"{value:+.2f}%"
                    for value in comparison_changes
                ],
                textposition="outside",
            )
        )
        comparison_change_fig.update_layout(
            plot_bgcolor=SURFACE,
            paper_bgcolor=BG,
            font=dict(color=TEXT_PRIMARY, family="JetBrains Mono"),
            margin=dict(t=20, b=10, l=10, r=10),
            yaxis=dict(
                title="Change (%)",
                gridcolor=BORDER,
                zerolinecolor=TEXT_SECONDARY,
            ),
            xaxis=dict(gridcolor=BORDER),
            height=340,
        )
        st.plotly_chart(
            comparison_change_fig,
            use_container_width=True,
        )

    with comparison_chart_col2:
        st.markdown("**Latest Price Points**")
        price_point_labels = [
            "Previous close",
            "Open",
            "Day high",
            "Day low",
            "Current",
        ]
        quote_keys = ["pc", "o", "h", "l", "c"]
        comparison_prices_fig = go.Figure()
        comparison_prices_fig.add_trace(
            go.Bar(
                name=comparison_symbol_1,
                x=price_point_labels,
                y=[
                    comparison_quote_1[key]
                    for key in quote_keys
                ],
                marker_color=ACCENT,
            )
        )
        comparison_prices_fig.add_trace(
            go.Bar(
                name=comparison_symbol_2,
                x=price_point_labels,
                y=[
                    comparison_quote_2[key]
                    for key in quote_keys
                ],
                marker_color=UP,
            )
        )
        comparison_prices_fig.update_layout(
            barmode="group",
            plot_bgcolor=SURFACE,
            paper_bgcolor=BG,
            font=dict(color=TEXT_PRIMARY, family="JetBrains Mono"),
            margin=dict(t=20, b=10, l=10, r=10),
            yaxis=dict(
                title="Price ($)",
                gridcolor=BORDER,
                zerolinecolor=BORDER,
            ),
            xaxis=dict(gridcolor=BORDER),
            legend=dict(orientation="h", y=1.12, x=0),
            height=340,
        )
        st.plotly_chart(
            comparison_prices_fig,
            use_container_width=True,
        )

    comparison_table = pd.DataFrame(
        [
            {
                "Stock": comparison_symbol_1,
                "Current Price": comparison_quote_1["c"],
                "Daily Change": comparison_quote_1["d"],
                "Percentage Change": comparison_quote_1["dp"],
                "Open": comparison_quote_1["o"],
                "Day High": comparison_quote_1["h"],
                "Day Low": comparison_quote_1["l"],
                "Previous Close": comparison_quote_1["pc"],
            },
            {
                "Stock": comparison_symbol_2,
                "Current Price": comparison_quote_2["c"],
                "Daily Change": comparison_quote_2["d"],
                "Percentage Change": comparison_quote_2["dp"],
                "Open": comparison_quote_2["o"],
                "Day High": comparison_quote_2["h"],
                "Day Low": comparison_quote_2["l"],
                "Previous Close": comparison_quote_2["pc"],
            },
        ]
    )

    st.markdown("**Comparison Data Table**")
    st.dataframe(
        comparison_table.style.format(
            {
                "Current Price": "${:,.2f}",
                "Daily Change": "{:+.2f}",
                "Percentage Change": "{:+.2f}%",
                "Open": "${:,.2f}",
                "Day High": "${:,.2f}",
                "Day Low": "${:,.2f}",
                "Previous Close": "${:,.2f}",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

# ----------------------------------------------------------------------------
# AI market summary
# ----------------------------------------------------------------------------
st.markdown(
    '<div class="section-label">AI Market Summary</div>',
    unsafe_allow_html=True,
)
st.caption(
    "Claude summarizes the latest snapshot for the six stocks in this "
    "dashboard. This is educational analysis, not financial advice."
)

summary_control_col1, summary_control_col2 = st.columns([1, 2])

with summary_control_col1:
    market_summary_language = st.selectbox(
        "Summary language",
        ["Arabic", "English"],
        key="market_summary_language",
    )

with summary_control_col2:
    st.write("")
    st.write("")
    generate_market_summary = st.button(
        "Generate AI market summary",
        key="generate_market_summary_button",
        use_container_width=True,
    )

if generate_market_summary:
    market_summary_rows = []
    unavailable_symbols = []

    with st.spinner("Claude is preparing the market summary..."):
        for market_symbol in stocks.values():
            market_quote, market_error = get_stock_quote(
                market_symbol
            )

            if market_error:
                unavailable_symbols.append(market_symbol)
                continue

            market_summary_rows.append(
                {
                    "symbol": market_symbol,
                    "current_price": market_quote["c"],
                    "change": market_quote["d"],
                    "percent_change": market_quote["dp"],
                    "open_price": market_quote["o"],
                    "high_price": market_quote["h"],
                    "low_price": market_quote["l"],
                    "previous_close": market_quote["pc"],
                }
            )

        if len(market_summary_rows) < 2:
            market_summary_text = None
            market_summary_error = (
                "Not enough stock data was available to create a summary."
            )
        else:
            market_summary_text, market_summary_error = (
                get_ai_market_summary(
                    market_summary_rows,
                    market_summary_language,
                )
            )

    if market_summary_error:
        st.error(market_summary_error)
    else:
        st.session_state["ai_market_summary_result"] = {
            "summary": market_summary_text,
            "rows": market_summary_rows,
            "language": market_summary_language,
            "unavailable_symbols": unavailable_symbols,
            "generated_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

market_summary_result = st.session_state.get(
    "ai_market_summary_result"
)

if market_summary_result:
    summary_rows = market_summary_result["rows"]
    summary_advancers = sum(
        row["percent_change"] > 0
        for row in summary_rows
    )
    summary_decliners = sum(
        row["percent_change"] < 0
        for row in summary_rows
    )
    summary_average = sum(
        row["percent_change"]
        for row in summary_rows
    ) / len(summary_rows)

    summary_metric_col1, summary_metric_col2, summary_metric_col3 = (
        st.columns(3)
    )
    summary_metric_col1.metric(
        "Advancing stocks",
        summary_advancers,
    )
    summary_metric_col2.metric(
        "Declining stocks",
        summary_decliners,
    )
    summary_metric_col3.metric(
        "Average change",
        f"{summary_average:+.2f}%",
    )

    with st.container(border=True):
        st.markdown(market_summary_result["summary"])
        st.caption(
            "Generated "
            f"{market_summary_result['generated_at']} • "
            "Educational summary of this dashboard's limited stock list "
            "only — not financial advice."
        )

    if market_summary_result["unavailable_symbols"]:
        st.warning(
            "Data was unavailable for: "
            + ", ".join(
                market_summary_result["unavailable_symbols"]
            )
        )

st.markdown(
    f'<div style="margin-top:30px; padding:14px 18px; background:{SURFACE_ALT}; '
    f'border:1px solid {BORDER}; border-radius:10px; color:{TEXT_SECONDARY}; font-size:13px;">'
    f"ℹ️ This dashboard is for learning and displays the latest data available from the API."
    f"</div>",
    unsafe_allow_html=True,
)