import pandas as pd
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


def fetch_quote(symbol):
    try:
        token = st.secrets.get("FINNHUB_API_KEY")
        if not token:
            return None, "Finnhub API key missing."
        res = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={token}",
            timeout=10,
        )
        data = res.json()
        if not data or data.get("c", 0) == 0:
            return None, "No data found."
        return data, None
    except Exception as e:
        return None, str(e)


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

    # Single stock overview card with standard metrics
    with st.container(border=True):
        st.markdown(f"### {selected_stock}")
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            label="Current Price",
            value=f"${quote['c']:.2f}",
            delta=f"{quote.get('dp', 0):+.2f}% (${quote.get('d', 0):+.2f})",
        )
        c2.metric(label="Open Price", value=f"${quote.get('o', 0):.2f}")
        c3.metric(label="Day High", value=f"${quote.get('h', 0):.2f}")
        c4.metric(label="Day Low", value=f"${quote.get('l', 0):.2f}")


def render_comparison_section():
    st.markdown("---")
    st.markdown(
        '<div class="section-label">COMPARE TWO STOCKS</div>',
        unsafe_allow_html=True,
    )

    col_select1, col_select2 = st.columns(2)
    with col_select1:
        stock1 = st.selectbox(
            "First stock", list(STOCKS.keys()), index=0, key="comp1"
        )
    with col_select2:
        stock2 = st.selectbox(
            "Second stock", list(STOCKS.keys()), index=1, key="comp2"
        )

    sym1 = STOCKS[stock1]
    sym2 = STOCKS[stock2]

    q1, err1 = fetch_quote(sym1)
    q2, err2 = fetch_quote(sym2)

    if err1 or err2 or not q1 or not q2:
        st.error("Could not fetch comparison data from API.")
        return

    # Side-by-Side Cards
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            st.markdown(f"### {sym1}")
            st.metric(
                label="Current Price",
                value=f"${q1['c']:.2f}",
                delta=f"{q1.get('dp', 0):+.2f}% (${q1.get('d', 0):+.2f})",
            )

    with c2:
        with st.container(border=True):
            st.markdown(f"### {sym2}")
            st.metric(
                label="Current Price",
                value=f"${q2['c']:.2f}",
                delta=f"{q2.get('dp', 0):+.2f}% (${q2.get('d', 0):+.2f})",
            )

    # Performance Leader Callout
    dp1 = q1.get("dp", 0)
    dp2 = q2.get("dp", 0)
    diff = dp1 - dp2

    if diff > 0:
        st.info(
            f"⚡ **{sym1}** is outperforming **{sym2}** by **+{abs(diff):.2f}%** today."
        )
    elif diff < 0:
        st.info(
            f"⚡ **{sym2}** is outperforming **{sym1}** by **+{abs(diff):.2f}%** today."
        )
    else:
        st.info(f"⚖️ **{sym1}** and **{sym2}** are performing identically today.")

    # Side-by-Side Breakdown Table
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
    st.dataframe(metrics_df, hide_index=True, use_container_width=True)


def show():
    st.markdown(
        '<div class="dash-title">📊 Market <span>Overview</span></div>',
        unsafe_allow_html=True,
    )

    # 1. Single stock overview dropdown and metrics
    render_single_stock_overview()

    # 2. Side-by-side stock comparison feature
    render_comparison_section()