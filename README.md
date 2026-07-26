# Stock Market Dashboard

A live finance dashboard built with Python and Streamlit.  
The application pulls the latest available US stock data from the Finnhub API.

## Features

- Choose from popular US stocks.
- Search using a custom stock symbol.
- Display the current price and percentage change.
- Display open, high, low, and previous close prices.
- Show a price comparison chart.
- Handle connection errors and invalid symbols.
- Keep the API key outside the Python code.

## Technologies

- Python
- Streamlit
- Requests
- Pandas
- Finnhub API

## Setup

Install the required packages:

```bash
pip install -r requirements.txt
```

Create this file:

```text
.streamlit/secrets.toml
```

Add your Finnhub API key:

```toml
FINNHUB_API_KEY = "YOUR_API_KEY"
```

## Run

```bash
python -m streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

## Data Source

Stock market data is retrieved from the Finnhub public API.

## Note

This dashboard is an educational project and displays the latest data available from the API.