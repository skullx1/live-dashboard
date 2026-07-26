from datetime import datetime

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide",
)

# Read the API key safely from .streamlit/secrets.toml
try:
    API_KEY = st.secrets["FINNHUB_API_KEY"]
except Exception:
    st.error("Finnhub API key was not found in secrets.toml.")
    st.stop()


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


st.title("📈 Stock Market Dashboard")
st.caption("Latest available stock data pulled from the Finnhub API.")

stocks = {
    "Apple (AAPL)": "AAPL",
    "Microsoft (MSFT)": "MSFT",
    "Amazon (AMZN)": "AMZN",
    "NVIDIA (NVDA)": "NVDA",
    "Tesla (TSLA)": "TSLA",
    "Google (GOOGL)": "GOOGL",
}

selected_stock = st.selectbox("Choose a stock", list(stocks.keys()))

custom_symbol = st.text_input(
    "Or enter another US stock symbol",
    placeholder="Example: META",
)

if custom_symbol.strip():
    symbol = custom_symbol.strip().upper()
else:
    symbol = stocks[selected_stock]

if st.button("Get stock data", type="primary"):
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

        st.subheader(f"{symbol} — Latest Quote")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Current price",
            f"${current_price:,.2f}",
            f"{change:+.2f}",
        )

        col2.metric(
            "Percentage change",
            f"{percent_change:.2f}%",
        )

        col3.metric(
            "Previous close",
            f"${previous_close:,.2f}",
        )

        st.divider()

        col4, col5, col6 = st.columns(3)
        col4.metric("Open", f"${open_price:,.2f}")
        col5.metric("Day high", f"${high_price:,.2f}")
        col6.metric("Day low", f"${low_price:,.2f}")

        chart_data = pd.DataFrame({
            "Price point": [
                "Previous close",
                "Open",
                "Day high",
                "Day low",
                "Current",
            ],
            "Price": [
                previous_close,
                open_price,
                high_price,
                low_price,
                current_price,
            ],
        })

        st.subheader("Price comparison")
        st.bar_chart(chart_data, x="Price point", y="Price")

        if quote.get("t"):
            update_time = datetime.fromtimestamp(quote["t"])
            st.caption(
                f"Last market update: "
                f"{update_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

st.info(
    "This dashboard is for learning and displays the latest data "
    "available from the API."
)