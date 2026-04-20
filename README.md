# :chart_with_upwards_trend: Stock Tracker

A simple Streamlit app for tracking historical and current stock prices, plus a historical advisor that ranks stocks using past performance data.

### Features

- **Real-time Stock Data**: Fetch current and historical stock prices using yfinance
- **Interactive Charts**: Visualize stock price trends over your chosen time period
- **Multiple Tickers**: Track multiple stocks simultaneously for easy comparison
- **Performance Metrics**: View current prices, price changes, highs, lows, and averages
- **Customizable Date Range**: Select any date range to analyze stock performance
- **Historical Stock Advisor**: Rank a watchlist by past return, volatility, drawdown, and price trend to surface buy candidates
- **Standalone Advisor Page**: Analyze preset universes or custom tickers without depending on an external AI API

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

3. Enter stock tickers (e.g., AAPL, GOOGL, MSFT) and adjust the date range to explore stock data
4. Open the advisor page from the Streamlit sidebar to rank a preset or custom watchlist based on historical data
