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
- **Email Price Alerts**: Get notifications when stocks reach your target prices with an external monitoring script

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run Stock_Tracker.py
   ```

3. Enter stock tickers (e.g., AAPL, GOOGL, MSFT) and adjust the date range to explore stock data
4. Open the advisor page from the Streamlit sidebar to rank a preset or custom watchlist based on historical data

### Setting up Price Alerts (Optional)

To enable the email price alert feature:

1. **Configure SMTP** - Update `.streamlit/secrets.toml` with Gmail credentials:
   ```toml
   [smtp]
   host = "smtp.gmail.com"
   port = 587
   username = "your-email@gmail.com"
   password = "your-app-password"  # Use Gmail App Password
   from_address = "Stock Tracker <your-email@gmail.com>"
   use_ssl = false
   ```

2. **Run the Price Monitor** - Set up the external monitoring script using cron or cloud scheduler:
   ```bash
   # Linux/Mac: Add to crontab (crontab -e)
   */5 * * * * cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py
   ```

3. **Create Alerts** - Use the "Price Alerts" page in the app to set up email notifications

📖 See [PRICE_ALERTS_SETUP.md](PRICE_ALERTS_SETUP.md) for detailed setup instructions.
