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

        res = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={token}",
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
        height=390,
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=f"single_stock_price_chart_{symbol}",
    )


def render_single_stock_overview():
    st.markdown(
        '<div class="section-label">SINGLE STOCK OVERVIEW</div>',
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

    render_price_bar_chart(quote, symbol)


def render_comparison_section():
    st.markdown("---")
    st.markdown(
        '<div class="section-label">COMPARE TWO STOCKS</div>',
        unsafe_allow_html=True,
    )

    col_select1, col_select2 = st.columns(2)
    with col_select1:
        stock1 = st.selectbox(
            "First stock",
            list(STOCKS.keys()),
            index=0,
            key="comp1",
        )
    with col_select2:
        stock2 = st.selectbox(
            "Second stock",
            list(STOCKS.keys()),
            index=1,
            key="comp2",
        )

    sym1 = STOCKS[stock1]
    sym2 = STOCKS[stock2]

    if sym1 == sym2:
        st.warning("Choose two different stocks to compare.")
        return

    q1, err1 = fetch_quote(sym1)
    q2, err2 = fetch_quote(sym2)

    if err1 or err2 or not q1 or not q2:
        st.error("Could not fetch comparison data from API.")
        return

    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown(f"### {sym1}")
            st.metric(
                label="Current Price",
                value=f"${q1['c']:.2f}",
                delta=(
                    f"{q1.get('dp', 0):+.2f}% "
                    f"(${q1.get('d', 0):+.2f})"
                ),
            )

    with c2:
        with st.container(border=True):
            st.markdown(f"### {sym2}")
            st.metric(
                label="Current Price",
                value=f"${q2['c']:.2f}",
                delta=(
                    f"{q2.get('dp', 0):+.2f}% "
                    f"(${q2.get('d', 0):+.2f})"
                ),
            )

    dp1 = q1.get("dp", 0)
    dp2 = q2.get("dp", 0)
    diff = dp1 - dp2

    if diff > 0:
        st.info(
            f"⚡ **{sym1}** is outperforming **{sym2}** "
            f"by **+{abs(diff):.2f}%** today."
        )
    elif diff < 0:
        st.info(
            f"⚡ **{sym2}** is outperforming **{sym1}** "
            f"by **+{abs(diff):.2f}%** today."
        )
    else:
        st.info(
            f"⚖️ **{sym1}** and **{sym2}** "
            "are performing identically today."
        )

    st.markdown("#### Detailed Metric Comparison")
    metrics_df = pd.DataFrame(
        {
            "Metric": [
                "Open Price",
                "High Price",
                "Low Price",
                "Previous Close",
            ],
            f"{sym1}": [
                f"${q1.get('o', 0):.2f}",
                f"${q1.get('h', 0):.2f}",
                f"${q1.get('l', 0):.2f}",
                f"${q1.get('pc', 0):.2f}",
            ],
            f"{sym2}": [
                f"${q2.get('o', 0):.2f}",
                f"${q2.get('h', 0):.2f}",
                f"${q2.get('l', 0):.2f}",
                f"${q2.get('pc', 0):.2f}",
            ],
        }
    )
    st.dataframe(
        metrics_df,
        hide_index=True,
        use_container_width=True,
    )


def show():
    st.markdown(
        '<div class="dash-title">📊 Market <span>Overview</span></div>',
        unsafe_allow_html=True,
    )

    render_single_stock_overview()
    render_comparison_section()