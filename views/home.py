import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

STOCKS = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "NVIDIA (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA",
    "Google (GOOGL)": "GOOGL",
}

# Black and purple chart colors
BG = "#000000"
SURFACE = "#0B0014"
BORDER = "#5B21B6"
TEXT_PRIMARY = "#F3E8FF"
TEXT_SECONDARY = "#C4B5FD"
ACCENT = "#8B5CF6"
UP = "#C084FC"
DOWN = "#6D28D9"


@st.cache_data(ttl=60)
def fetch_quote(symbol):
    try:
        token = st.secrets.get("FINNHUB_API_KEY")
        if not token:
            return None, "Finnhub API key missing."

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Market-Dashboard/1.0"
        }

        res = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={token}",
            headers=headers,
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()

        if not data or data.get("c", 0) == 0:
            return None, "No data found."

        return data, None

    except requests.exceptions.Timeout:
        return None, "Finnhub took too long to respond."
    except requests.exceptions.ConnectionError:
        return None, "Internet connection failed."
    except requests.exceptions.RequestException as e:
        return None, f"Finnhub request failed: {e}"


def render_price_bar_chart(quote, symbol):
    """Render a purple bar chart for the selected stock price points."""
    labels = [
        "Previous Close",
        "Open",
        "Day High",
        "Day Low",
        "Current",
    ]
    prices = [
        quote.get("pc", 0),
        quote.get("o", 0),
        quote.get("h", 0),
        quote.get("l", 0),
        quote.get("c", 0),
    ]

    current_color = UP if quote.get("d", 0) >= 0 else DOWN
    colors = [
        TEXT_SECONDARY,
        ACCENT,
        UP,
        DOWN,
        current_color,
    ]

    st.markdown(
        '<div class="section-label">PRICE COMPARISON</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=prices,
            marker_color=colors,
            marker_line=dict(color="#D8B4FE", width=1),
            text=[f"${price:,.2f}" for price in prices],
            textposition="outside",
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Price: $%{y:,.2f}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text=f"{symbol} Price Comparison",
            font=dict(color=TEXT_PRIMARY, size=18),
        ),
        plot_bgcolor=SURFACE,
        paper_bgcolor=BG,
        font=dict(
            color=TEXT_PRIMARY,
            family="JetBrains Mono",
        ),
        margin=dict(t=65, b=20, l=20, r=20),
        yaxis=dict(
            title="Price ($)",
            gridcolor=BORDER,
            zerolinecolor=BORDER,
        ),
        xaxis=dict(gridcolor=BORDER),
        height=370,
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"single_stock_price_chart_{symbol}",
    )


def render_intraday_range_gauge(quote, symbol):
    """Render a gauge indicator showing current position inside today's low-high range."""
    high = quote.get("h", 0)
    low = quote.get("l", 0)
    current = quote.get("c", 0)

    if high > low:
        position_pct = ((current - low) / (high - low)) * 100
    else:
        position_pct = 50.0

    st.markdown(
        '<div class="section-label">INTRADAY RANGE & POSITION INDICATOR</div>',
        unsafe_allow_html=True,
    )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=position_pct,
            number={"suffix": "%", "font": {"color": TEXT_PRIMARY, "size": 28}},
            title={
                "text": f"{symbol} Position within Day High-Low Range",
                "font": {"color": TEXT_SECONDARY, "size": 14},
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": BORDER,
                    "tickfont": {"color": TEXT_SECONDARY},
                },
                "bar": {"color": ACCENT, "thickness": 0.4},
                "bgcolor": SURFACE,
                "borderwidth": 1,
                "bordercolor": BORDER,
                "steps": [
                    {"range": [0, 33.3], "color": "#1F0B38"},
                    {"range": [33.3, 66.6], "color": "#2A1248"},
                    {"range": [66.6, 100], "color": "#38185C"},
                ],
            },
        )
    )

    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT_PRIMARY, family="JetBrains Mono"),
        height=260,
        margin=dict(t=40, b=10, l=30, r=30),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"range_gauge_{symbol}",
    )


def render_analytics_breakdown(quote):
    """Calculates and renders intraday volatility & price performance metrics."""
    high = quote.get("h", 0)
    low = quote.get("l", 0)
    current = quote.get("c", 0)
    prev_close = quote.get("pc", 0)

    trading_spread = high - low
    spread_pct = (trading_spread / prev_close * 100) if prev_close else 0
    from_high_pct = ((current - high) / high * 100) if high else 0
    from_low_pct = ((current - low) / low * 100) if low else 0

    st.markdown(
        '<div class="section-label">KEY INTRADAY METRICS & RATIOS</div>',
        unsafe_allow_html=True,
    )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Trading Spread ($)", f"${trading_spread:.2f}")
    m2.metric("Spread Volatility", f"{spread_pct:.2f}%")
    m3.metric("Offset from Day High", f"{from_high_pct:+.2f}%")
    m4.metric("Lift from Day Low", f"{from_low_pct:+.2f}%")


def render_market_overview_table():
    """Renders a dashboard-wide market table comparing all tickers."""
    st.markdown(
        '<div class="section-label">FULL DASHBOARD MARKET OVERVIEW</div>',
        unsafe_allow_html=True,
    )

    rows = []
    for label, ticker in STOCKS.items():
        q, err = fetch_quote(ticker)
        if q and not err:
            rows.append(
                {
                    "Stock": label,
                    "Ticker": ticker,
                    "Price ($)": f"${q.get('c', 0):.2f}",
                    "Change ($)": f"{q.get('d', 0):+.2f}",
                    "Change (%)": f"{q.get('dp', 0):+.2f}%",
                    "High ($)": f"${q.get('h', 0):.2f}",
                    "Low ($)": f"${q.get('l', 0):.2f}",
                    "Prev. Close ($)": f"${q.get('pc', 0):.2f}",
                }
            )

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Market table unavailable right now.")


def show():
    """Main view renderer called by app.py."""
    st.markdown(
        '<div class="dash-title">🏠 Market <span>Overview</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dash-caption">Real-time stock data analytics & intraday price visualisations.</div>',
        unsafe_allow_html=True,
    )

    selected_stock = st.selectbox(
        "Choose stock to view market overview",
        list(STOCKS.keys()),
        index=0,
        key="single_stock_select",
    )
    symbol = STOCKS[selected_stock]

    quote, err = fetch_quote(symbol)

    if err or not quote:
        st.error(err or f"Could not fetch data for {symbol}.")
        return

    # Top KPI Metrics Cards
    with st.container(border=True):
        st.markdown(f"### {selected_stock}")
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            label="Current Price",
            value=f"${quote['c']:.2f}",
            delta=(
                f"{quote.get('dp', 0):+.2f}% "
                f"(${quote.get('d', 0):+.2f})"
            ),
        )
        c2.metric(
            label="Open Price",
            value=f"${quote.get('o', 0):.2f}",
        )
        c3.metric(
            label="Day High",
            value=f"${quote.get('h', 0):.2f}",
        )
        c4.metric(
            label="Day Low",
            value=f"${quote.get('l', 0):.2f}",
        )

    # 1. Main Price Bar Chart
    render_price_bar_chart(quote, symbol)

    # 2. Intraday Position Meter
    render_intraday_range_gauge(quote, symbol)

    # 3. Key Intraday Ratios Breakdown
    render_analytics_breakdown(quote)

    # 4. Multi-Stock Market Overview Table
    render_market_overview_table()