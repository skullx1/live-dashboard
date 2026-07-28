import anthropic
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

ANTHROPIC_API_KEY = st.secrets.get("ANTHROPIC_API_KEY")


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


def get_ai_single_quote_explanation(quote, symbol, language="English"):
    """Explain the displayed quote with Claude without giving trading advice."""
    if not ANTHROPIC_API_KEY:
        return None, "Claude API key was not found in secrets.toml."

    high_price = quote.get("h", 0)
    low_price = quote.get("l", 0)
    current_price = quote.get("c", 0)

    if high_price > low_price:
        range_position = ((current_price - low_price) / (high_price - low_price)) * 100
    else:
        range_position = 50

    prompt = f"""
Explain the following stock quote in {language}.

Stock symbol: {symbol}
Current price: ${quote.get('c', 0):.2f}
Price change: ${quote.get('d', 0):+.2f}
Percentage change: {quote.get('dp', 0):+.2f}%
Open price: ${quote.get('o', 0):.2f}
Previous close: ${quote.get('pc', 0):.2f}
Day high: ${quote.get('h', 0):.2f}
Day low: ${quote.get('l', 0):.2f}
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

        try:
            message = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=700,
                system=(
                    "You are a careful educational stock-data explainer. "
                    "Be concise, factual, and easy to understand."
                ),
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.NotFoundError:
            message = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=700,
                system=(
                    "You are a careful educational stock-data explainer. "
                    "Be concise, factual, and easy to understand."
                ),
                messages=[{"role": "user", "content": prompt}],
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
    except anthropic.APIError as e:
        status_code = getattr(e, "status_code", "unknown")
        return None, f"Claude API error ({status_code}): {e}"


def get_ai_market_summary(market_rows, language="English"):
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

    advancers = sum(row["percent_change"] > 0 for row in market_rows)
    decliners = sum(row["percent_change"] < 0 for row in market_rows)
    unchanged = len(market_rows) - advancers - decliners
    average_change = (
        sum(row["percent_change"] for row in market_rows) / len(market_rows)
        if market_rows
        else 0
    )
    strongest = max(market_rows, key=lambda row: row["percent_change"])
    weakest = min(market_rows, key=lambda row: row["percent_change"])

    prompt = f"""
Write a concise market snapshot in {language} using only the data below.

Stocks in this dashboard:
{market_lines}

Calculated breadth:
- Advancing stocks: {advancers}
- Declining stocks: {decliners}
- Unchanged stocks: {unchanged}
- Average percentage change: {average_change:+.2f}%
- Strongest daily movement: {strongest['symbol']} ({strongest['percent_change']:+.2f}%)
- Weakest daily movement: {weakest['symbol']} ({weakest['percent_change']:+.2f}%)

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

        try:
            message = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=900,
                system=(
                    "You are a careful educational market-data summarizer. "
                    "Be concise, factual, and easy to understand."
                ),
                messages=[{"role": "user", "content": prompt}],
            )
        except anthropic.NotFoundError:
            message = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=900,
                system=(
                    "You are a careful educational market-data summarizer. "
                    "Be concise, factual, and easy to understand."
                ),
                messages=[{"role": "user", "content": prompt}],
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
    except anthropic.APIError as e:
        status_code = getattr(e, "status_code", "unknown")
        return None, f"Claude API error ({status_code}): {e}"


def show():
    """Streamlit view function called by app.py."""
    st.markdown(
        '<div class="dash-title">🤖 AI <span>Market Insights</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dash-caption">Educational market data explanations generated by Claude.</div>',
        unsafe_allow_html=True,
    )

    if not ANTHROPIC_API_KEY:
        st.error("Claude API key missing in secrets.toml.")
        return

    selected_stock = st.selectbox(
        "Choose stock for single analysis", list(STOCKS.keys())
    )
    sym = STOCKS[selected_stock]

    if st.button("Generate Single Stock Explanation", type="primary"):
        quote, err = fetch_quote(sym)
        if err or not quote:
            st.error(err or "Failed to fetch stock data.")
        else:
            with st.spinner("Generating AI explanation..."):
                exp, exp_err = get_ai_single_quote_explanation(quote, sym)
                if exp_err:
                    st.error(exp_err)
                else:
                    st.markdown(exp)

    st.markdown(
        '<div class="section-label">Full Dashboard Market Snapshot</div>',
        unsafe_allow_html=True,
    )
    if st.button("Generate Overall Market Summary", use_container_width=True):
        market_rows = []
        for name, ticker in STOCKS.items():
            q, _ = fetch_quote(ticker)
            if q and q.get("c"):
                market_rows.append(
                    {
                        "symbol": ticker,
                        "current_price": q["c"],
                        "change": q.get("d", 0),
                        "percent_change": q.get("dp", 0),
                        "open_price": q.get("o", 0),
                        "high_price": q.get("h", 0),
                        "low_price": q.get("l", 0),
                        "previous_close": q.get("pc", 0),
                    }
                )

        if not market_rows:
            st.error("Could not retrieve market data to summarize.")
        else:
            with st.spinner("Claude is analyzing full market snapshot..."):
                sum_text, sum_err = get_ai_market_summary(market_rows)
                if sum_err:
                    st.error(sum_err)
                else:
                    with st.container(border=True):
                        st.markdown(sum_text)