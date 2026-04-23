import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests
import feedparser
from analytics_utils import TAX_RATES, build_profit_analytics
from stock_analysis import get_suggested_stocks, normalize_tickers, get_stock_data, build_analysis_snapshot
from user_backend import (
    init_db,
    save_watchlist,
    get_watchlist,
    get_watchlist_entries,
    update_watchlist_entry,
    add_transaction,
    get_transactions,
    update_transaction,
    delete_transaction,
)

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Stock Tracker',
    page_icon='📈',
    layout='wide'
)

# Add custom CSS for professional Playfair Display font and deep forest color scheme
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;600;700&display=swap');
        
        /* Forest Color Palette */
        :root {
            --forest-green: #1B4332;
            --deep-green: #2D6A4F;
            --forest-blue: #4A90A4;
            --light-blue: #6BA3B8;
            --earth-brown: #6B4423;
            --light-brown: #8B5A3C;
            --sage-grey: #8A9B9E;
            --light-grey: #D4DCDE;
            --dark-grey: #3A3A3A;
            --cream: #F5F3F0;
            --blue-wash: #EBF3F7;
            --brown-wash: #F4EDE3;
            --grey-wash: #F0F3F4;
            --beige-text: #2F241A;
        }
        
        /* Main styling */
        body {
            background: linear-gradient(135deg, #F5F3F0 0%, #EBF3F7 100%);
            color: var(--dark-grey);
        }
        
        /* Main Headers - Playfair Display */
        h1, h2 {
            font-family: 'Playfair Display', serif !important;
            letter-spacing: 1.5px;
        }
        
        /* Subheaders - Josefin Sans */
        h3, h4, h5, h6 {
            font-family: 'Josefin Sans', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: 0.8px;
        }
        
        h1 {
            color: var(--forest-green) !important;
            border-bottom: 4px solid var(--earth-brown);
            padding-bottom: 12px;
            margin-bottom: 20px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.05);
        }

        .page-title {
            color: var(--forest-green) !important;
        }

        .page-subtitle {
            color: #5E666B !important;
        }
        
        h2 {
            color: var(--deep-green) !important;
            border-left: 5px solid var(--forest-blue);
            padding-left: 12px;
        }
        
        h3 {
            color: var(--earth-brown) !important;
        }
        
        /* Streamlit containers */
        .main {
            background: linear-gradient(180deg, #F5F3F0 0%, #EBF3F7 100%);
        }
        
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F4EDE3 0%, #F0F3F4 100%);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, var(--deep-green) 0%, var(--forest-green) 100%) !important;
            color: white !important;
            border: 2px solid var(--forest-green) !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(27, 67, 50, 0.15) !important;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, var(--forest-green) 0%, var(--deep-green) 100%) !important;
            box-shadow: 0 6px 20px rgba(27, 67, 50, 0.3) !important;
            transform: translateY(-2px) !important;
        }
        
        /* Input fields */
        input, textarea, [data-testid="stDateInput"] {
            border: 2px solid var(--light-grey) !important;
            border-radius: 6px !important;
            background-color: white !important;
        }
        
        input:focus, textarea:focus {
            border-color: var(--forest-blue) !important;
            box-shadow: 0 0 0 3px rgba(74, 144, 164, 0.15) !important;
        }
        
        /* Dividers */
        hr {
            background: linear-gradient(90deg, var(--earth-brown) 0%, transparent 50%, var(--forest-blue) 100%) !important;
            height: 2px !important;
            opacity: 0.6;
        }
        
        /* Metrics - Alternating colors */
        [data-testid="metric-container"] {
            background: linear-gradient(135deg, #F9F7F5 0%, var(--blue-wash) 100%);
            border-left: 6px solid var(--light-brown);
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 3px 12px rgba(107, 68, 35, 0.1);
        }
        
        [data-testid="metric-container"]:nth-child(even) {
            background: linear-gradient(135deg, var(--grey-wash) 0%, var(--brown-wash) 100%);
            border-left-color: var(--sage-grey);
        }
        
        [data-testid="metric-container"]:nth-child(3n) {
            background: linear-gradient(135deg, var(--blue-wash) 0%, #F0F3F4 100%);
            border-left-color: var(--forest-blue);
        }
        
        /* Dataframe - Multi-color accents */
        [data-testid="dataFrame"] {
            background-color: white !important;
            border: 2px solid var(--light-grey) !important;
            border-radius: 8px !important;
            overflow: hidden !important;
        }
        
        [data-testid="dataFrame"] thead {
            background: linear-gradient(90deg, var(--deep-green) 0%, var(--forest-blue) 100%) !important;
            color: white !important;
        }
        
        /* Chart containers */
        .stPlotlyContainer {
            background: linear-gradient(135deg, rgba(235, 243, 247, 0.5) 0%, rgba(244, 237, 227, 0.5) 100%);
            border: 1px solid var(--light-grey);
            border-radius: 8px;
            padding: 12px;
        }
        
        /* Links */
        a {
            color: var(--forest-blue) !important;
            text-decoration: none !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        a:hover {
            color: var(--earth-brown) !important;
            text-decoration: underline !important;
        }
        
        /* Alert boxes - Color coded */
        .stAlert {
            border-radius: 8px !important;
            border-left: 6px solid var(--forest-blue) !important;
            background: linear-gradient(90deg, rgba(74, 144, 164, 0.1) 0%, rgba(74, 144, 164, 0.05) 100%) !important;
        }
        
        .stAlert > div {
            color: var(--dark-grey) !important;
        }
        
        /* Info alert - Blue theme */
        [data-testid="stAlert"] {
            background: linear-gradient(90deg, var(--blue-wash) 0%, rgba(74, 144, 164, 0.05) 100%) !important;
        }
        
        /* Warning alert - Brown theme */
        [data-testid="stAlert"] > div:nth-child(2) {
            background: linear-gradient(90deg, var(--brown-wash) 0%, rgba(107, 68, 35, 0.05) 100%) !important;
        }
        
        /* Error alert - Grey theme */
        [data-testid="stAlert"] > div:nth-child(3) {
            background: linear-gradient(90deg, var(--grey-wash) 0%, rgba(138, 155, 158, 0.05) 100%) !important;
        }
        
        /* Sidebar specific styling */
        [data-testid="stSidebar"] h2 {
            color: var(--forest-green) !important;
            border-bottom: 3px solid var(--earth-brown);
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        
        [data-testid="stSidebar"] a {
            color: var(--forest-blue) !important;
        }
        
        /* Subheader styling */
        .stMarkdownContainer h3 {
            color: var(--beige-text) !important;
            border-left: 5px solid var(--light-brown);
            padding-left: 12px;
            background-color: rgba(244, 237, 227, 0.3);
            padding: 8px 12px;
            border-radius: 4px;
        }
        
        /* Text styling */
        .caption {
            color: var(--sage-grey) !important;
        }
        
        /* Spinner */
        .stSpinner {
            color: var(--forest-green) !important;
        }
        
        /* Tab styling */
        [data-testid="stTabs"] button {
            color: var(--dark-grey) !important;
        }
        
        [data-testid="stTabs"] button:hover {
            color: var(--forest-green) !important;
            border-bottom-color: var(--forest-blue) !important;
        }
        
        /* Container backgrounds */
        [data-testid="stVerticalBlock"] > div {
            background: linear-gradient(135deg, transparent 0%, rgba(107, 68, 35, 0.02) 100%);
            border-radius: 8px;
            padding: 4px 0;
            margin: 2px 0;
        }
        
        /* Reduce spacing on subheaders */
        h2, h3 {
            margin-top: 6px !important;
            margin-bottom: 8px !important;
        }
        
        /* Tighter spacing on metrics */
        [data-testid="metric-container"] {
            margin: 2px 0 !important;
            padding: 12px 8px !important;
        }
        
        /* Compact spacing overall */
        .stMarkdown {
            margin: 2px 0 !important;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --dark-surface: #142029;
                --dark-panel: #1E2D38;
                --dark-panel-alt: #243845;
                --dark-border: #456173;
                --dark-text: #F3F1EC;
                --dark-muted: #D7E0E3;
            }

            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"] {
                background: linear-gradient(180deg, #0F1A22 0%, #162631 100%) !important;
                color: var(--dark-text) !important;
            }

            p,
            label,
            span,
            div,
            li,
            small,
            .stMarkdown,
            .stMarkdownContainer,
            [data-testid="stMetricLabel"],
            [data-testid="stMetricValue"],
            [data-testid="stMetricDelta"],
            [data-testid="stSidebar"] * {
                color: var(--dark-text) !important;
            }

            h1,
            h2,
            h3,
            h4,
            h5,
            h6 {
                color: #F4E7CE !important;
            }

            .page-title {
                color: #F3F1EC !important;
            }

            .page-subtitle {
                color: #D7E0E3 !important;
            }

            .stMarkdownContainer h3,
            .stMarkdownContainer h3 *,
            [data-testid="stAlert"] > div:nth-child(2),
            [data-testid="stAlert"] > div:nth-child(2) * {
                color: var(--beige-text) !important;
            }

            .main,
            [data-testid="stVerticalBlock"] > div {
                background: linear-gradient(180deg, rgba(20, 32, 41, 0.96) 0%, rgba(30, 45, 56, 0.96) 100%) !important;
            }

            [data-testid="stSidebar"] {
                background: #000000 !important;
            }

            [data-testid="metric-container"],
            [data-testid="dataFrame"],
            .stPlotlyContainer,
            .stAlert {
                background: linear-gradient(135deg, rgba(30, 45, 56, 0.92) 0%, rgba(36, 56, 69, 0.92) 100%) !important;
                border-color: var(--dark-border) !important;
                color: var(--dark-text) !important;
            }

            input,
            textarea,
            [data-testid="stDateInput"],
            [data-baseweb="input"] input {
                background-color: var(--dark-panel) !important;
                color: var(--dark-text) !important;
                border-color: var(--dark-border) !important;
            }

            .caption,
            [data-testid="stCaptionContainer"] {
                color: var(--dark-muted) !important;
            }

            a,
            [data-testid="stSidebar"] a {
                color: #9FD3E6 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data(ttl='5m')
def get_stock_news(ticker):
    """Fetch news articles for a stock ticker from multiple sources."""
    formatted_news = []
    
    # Try yfinance first
    try:
        stock = yf.Ticker(ticker)
        if hasattr(stock, 'news') and stock.news:
            for article in stock.news[:10]:
                try:
                    title = article.get('title') or article.get('headline')
                    link = article.get('link') or article.get('url')
                    source = article.get('source') or 'Financial News'
                    
                    if title and link:
                        formatted_news.append({
                            'title': str(title),
                            'link': str(link),
                            'source': str(source)
                        })
                except:
                    continue
    except Exception as e:
        pass
    
    # If yfinance didn't return articles, try RSS
    if len(formatted_news) < 2:
        try:
            rss_url = f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}'
            feed = feedparser.parse(rss_url)
            
            if hasattr(feed, 'entries') and feed.entries:
                for entry in feed.entries[:5]:
                    try:
                        title = getattr(entry, 'title', '') or getattr(entry, 'summary', '')
                        link = getattr(entry, 'link', '')
                        
                        if title and link:
                            formatted_news.append({
                                'title': str(title)[:100],
                                'link': str(link),
                                'source': 'Yahoo Finance'
                            })
                            if len(formatted_news) >= 5:
                                break
                    except:
                        continue
        except:
            pass
    
    # Return mock data if no real data available (for testing)
    if len(formatted_news) == 0:
        formatted_news = [
            {
                'title': f'{ticker} Market Update',
                'link': f'https://finance.yahoo.com/quote/{ticker}',
                'source': 'Market Data'
            }
        ]
    
    return formatted_news

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
st.markdown("""
    <h1 class='page-title' style='font-family: "Playfair Display", serif; text-align: center; letter-spacing: 2px; font-size: 56px;'>Stock Tracker</h1>
    <p class='page-subtitle' style='text-align: center; font-size: 14px;'>Track historical and current stock data. Enter your favorite stock tickers and explore their performance over time.</p>
""", unsafe_allow_html=True)
st.divider()

# Add some spacing
st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

# Set default date range (last 1 year)
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        'Start date',
        value=start_date,
        max_value=end_date
    )

with col2:
    end_date = st.date_input(
        'End date',
        value=end_date,
        min_value=start_date,
        max_value=datetime.now()
    )

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# Initialize session state
if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

if 'watchlist_loaded_for' not in st.session_state:
    st.session_state.watchlist_loaded_for = None

if 'selected_tickers_list' not in st.session_state:
    st.session_state.selected_tickers_list = ['AAPL', 'GOOGL', 'MSFT']

current_user = st.session_state.auth_user
if current_user and st.session_state.watchlist_loaded_for != current_user['id']:
    saved_watchlist = get_watchlist(current_user['id'])
    if saved_watchlist:
        st.session_state.selected_tickers_list = saved_watchlist
    st.session_state.watchlist_loaded_for = current_user['id']

watchlist_entries_map = {}
if current_user:
    watchlist_entries_map = {
        entry['ticker']: entry
        for entry in get_watchlist_entries(current_user['id'])
    }

ticker_input = st.text_input(
    'Enter stock tickers (comma-separated)',
    value=', '.join(st.session_state.selected_tickers_list),
    placeholder='e.g., AAPL, GOOGL, MSFT'
)

# Get dynamic suggested stocks
suggested_stocks = get_suggested_stocks()

st.caption('Suggested well-performing stocks:')
cols = st.columns(min(len(suggested_stocks), 5))

for i, ticker in enumerate(suggested_stocks[:5]):
    with cols[i % len(cols)]:
        if st.button(ticker, key=f'sugg_{ticker}', width='stretch'):
            if ticker not in st.session_state.selected_tickers_list:
                st.session_state.selected_tickers_list.append(ticker)
            st.rerun()

if ticker_input:
    selected_tickers = normalize_tickers(ticker_input)
    st.session_state.selected_tickers_list = selected_tickers
else:
    selected_tickers = []

if not len(selected_tickers):
    st.warning("Enter at least one stock ticker")

# Main content tabs
stock_tab, watchlist_tab, transaction_tab = st.tabs([
    'Stock Statistics',
    'Watchlist Notes & Alerts',
    'Transaction Tracker',
])

# Fetch and combine data for all selected tickers
combined_data = pd.DataFrame()
ticker_data = {}

for ticker in selected_tickers:
    stock_data = get_stock_data(ticker, start_date, end_date)
    if stock_data is not None:
        ticker_data[ticker] = stock_data
        stock_data_copy = stock_data[['Close']].copy()
        stock_data_copy.columns = [ticker]
        if combined_data.empty:
            combined_data = stock_data_copy
        else:
            combined_data = combined_data.join(stock_data_copy)

st.session_state.analysis_snapshot = build_analysis_snapshot(ticker_data, start_date, end_date, selected_tickers)
analysis_summary = st.session_state.analysis_snapshot['stocks']

if not combined_data.empty:
    # Display historical price chart
    st.subheader('Stock Price Over Time')
    st.line_chart(combined_data, width='stretch')
    
    # Display current metrics
    st.subheader('Current Stock Data')
    
    cols = st.columns(min(len(selected_tickers), 4))
    stats_data = []
    
    for i, ticker in enumerate(selected_tickers):
        col = cols[i % len(cols)]
        
        with col:
            if ticker in ticker_data:
                stock_data = ticker_data[ticker]
                current_price = stock_data['Close'].iloc[-1].item()
                high = stock_data['High'].max().item()
                low = stock_data['Low'].min().item()
                avg = stock_data['Close'].mean().item()

                stats_data.append({
                    'Ticker': ticker,
                    'Current Price': f'${current_price:.2f}',
                    '52-Week High': f'${high:.2f}',
                    '52-Week Low': f'${low:.2f}',
                    'Average Price': f'${avg:.2f}'
                })

    if stats_data:
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, width='stretch')

    if current_user:
            triggered_alerts = []
            for ticker in selected_tickers:
                entry = watchlist_entries_map.get(ticker, {})
                if ticker not in ticker_data:
                    continue

                current_price = float(ticker_data[ticker]['Close'].iloc[-1].item())
                buy_alert = entry.get('buy_alert_price')
                sell_alert = entry.get('sell_alert_price')

                if buy_alert is not None and current_price <= float(buy_alert):
                    triggered_alerts.append(
                        f"{ticker}: current price ${current_price:.2f} is at or below buy alert ${float(buy_alert):.2f}"
                    )
                if sell_alert is not None and current_price >= float(sell_alert):
                    triggered_alerts.append(
                        f"{ticker}: current price ${current_price:.2f} is at or above sell alert ${float(sell_alert):.2f}"
                    )

            if triggered_alerts:
                st.subheader('Triggered Alerts')
                for alert_message in triggered_alerts:
                    st.warning(alert_message)

with watchlist_tab:
    st.subheader('Watchlist Notes & Alerts')

    if not current_user:
        st.info('Log in to save per-ticker notes and price alerts.')
    elif not selected_tickers:
        st.info('Add tickers to your watchlist to manage notes and alerts.')
    else:
        st.caption('Set a note plus optional buy and sell alert prices for each saved ticker.')

        for ticker in selected_tickers:
            entry = watchlist_entries_map.get(ticker, {})
            default_note = entry.get('note', '')
            default_buy = entry.get('buy_alert_price')
            default_sell = entry.get('sell_alert_price')
            current_price = None
            alert_state = 'No alerts configured.'

            if ticker in ticker_data:
                current_price = float(ticker_data[ticker]['Close'].iloc[-1].item())
                alert_messages = []
                if default_buy is not None and current_price <= float(default_buy):
                    alert_messages.append(f'Buy alert triggered at ${current_price:.2f}')
                if default_sell is not None and current_price >= float(default_sell):
                    alert_messages.append(f'Sell alert triggered at ${current_price:.2f}')
                if alert_messages:
                    alert_state = ' | '.join(alert_messages)

            with st.expander(f'{ticker} settings', expanded=False):
                info_col1, info_col2 = st.columns(2)
                with info_col1:
                    if current_price is not None:
                        st.metric('Current Price', f'${current_price:.2f}')
                    else:
                        st.caption('Current price unavailable for this ticker.')
                with info_col2:
                    if 'triggered' in alert_state.lower():
                        st.warning(alert_state)
                    else:
                        st.info(alert_state)

                with st.form(f'watchlist_entry_form_{ticker}'):
                    note_value = st.text_area(
                        'Watchlist note',
                        value=default_note,
                        placeholder='Why are you watching this stock?',
                        key=f'note_{ticker}',
                    )

                    alert_col1, alert_col2 = st.columns(2)
                    with alert_col1:
                        enable_buy_alert = st.checkbox(
                            'Enable buy alert',
                            value=default_buy is not None,
                            key=f'enable_buy_{ticker}',
                        )
                        buy_alert_value = st.number_input(
                            'Buy alert price',
                            min_value=0.0,
                            value=float(default_buy) if default_buy is not None else 0.0,
                            step=0.01,
                            key=f'buy_alert_{ticker}',
                        )
                    with alert_col2:
                        enable_sell_alert = st.checkbox(
                            'Enable sell alert',
                            value=default_sell is not None,
                            key=f'enable_sell_{ticker}',
                        )
                        sell_alert_value = st.number_input(
                            'Sell alert price',
                            min_value=0.0,
                            value=float(default_sell) if default_sell is not None else 0.0,
                            step=0.01,
                            key=f'sell_alert_{ticker}',
                        )

                    save_watch_settings = st.form_submit_button('Save Note & Alerts', width='stretch')

                if save_watch_settings:
                    buy_alert_to_store = buy_alert_value if enable_buy_alert and buy_alert_value > 0 else None
                    sell_alert_to_store = sell_alert_value if enable_sell_alert and sell_alert_value > 0 else None

                    update_watchlist_entry(
                        current_user['id'],
                        ticker,
                        note_value,
                        buy_alert_to_store,
                        sell_alert_to_store,
                    )
                    st.success(f'Saved note and alerts for {ticker}.')
                    st.rerun()

        watchlist_summary_rows = []
        refreshed_entries = {
            entry['ticker']: entry
            for entry in get_watchlist_entries(current_user['id'])
        }
        for ticker in selected_tickers:
            entry = refreshed_entries.get(ticker, {})
            current_price = None
            if ticker in ticker_data:
                current_price = float(ticker_data[ticker]['Close'].iloc[-1].item())

            status = 'Monitoring'
            buy_alert = entry.get('buy_alert_price')
            sell_alert = entry.get('sell_alert_price')
            if current_price is not None:
                if buy_alert is not None and current_price <= float(buy_alert):
                    status = 'Buy alert triggered'
                if sell_alert is not None and current_price >= float(sell_alert):
                    status = 'Sell alert triggered'

            watchlist_summary_rows.append(
                {
                    'Ticker': ticker,
                    'Current Price': f'${current_price:.2f}' if current_price is not None else 'N/A',
                    'Buy Alert': f"${float(buy_alert):.2f}" if buy_alert is not None else 'Not set',
                    'Sell Alert': f"${float(sell_alert):.2f}" if sell_alert is not None else 'Not set',
                    'Note': entry.get('note', ''),
                    'Status': status,
                }
            )

        if watchlist_summary_rows:
            st.markdown('**Watchlist Alert Summary**')
            st.dataframe(pd.DataFrame(watchlist_summary_rows), width='stretch', hide_index=True)

with transaction_tab:
    st.subheader('Transaction Tracker')

    if current_user:
        with st.form('transaction_form'):
            tx_col1, tx_col2, tx_col3, tx_col4 = st.columns(4)
            with tx_col1:
                trade_date = st.date_input('Trade date', value=datetime.now().date(), key='trade_date')
                ticker_tx = st.text_input('Ticker', placeholder='AAPL', key='ticker_tx').strip().upper()
            with tx_col2:
                action = st.selectbox('Action', ['BUY', 'SELL'], key='action_tx')
                quantity = st.number_input('Quantity', min_value=0.0, step=1.0, key='quantity_tx')
            with tx_col3:
                price = st.number_input('Price', min_value=0.0, step=0.01, key='price_tx')
                tax_area_tx = st.selectbox('Tax area', list(TAX_RATES.keys()), key='tax_area_tx')
            with tx_col4:
                tax_rate_tx = st.number_input(
                    'Tax rate (%)',
                    min_value=0.0,
                    max_value=100.0,
                    value=float(TAX_RATES[tax_area_tx] * 100),
                    step=0.1,
                    key='tax_rate_tx',
                )
            
            notes_tx = st.text_area('Notes (optional)', key='notes_tx')
            submitted = st.form_submit_button('Add Transaction', type='primary')
            
            if submitted:
                if not ticker_tx:
                    st.error('Please enter a ticker symbol.')
                elif quantity <= 0:
                    st.error('Quantity must be greater than 0.')
                elif price <= 0:
                    st.error('Price must be greater than 0.')
                else:
                    add_transaction(
                        current_user['id'],
                        str(trade_date),
                        ticker_tx,
                        action,
                        quantity,
                        price,
                        tax_area_tx,
                        tax_rate_tx / 100.0,
                        notes_tx,
                    )
                    st.success('Transaction added successfully!')
                    st.rerun()
    else:
        st.info('Please log in to add transactions.')

    if analysis_summary:
        top_pick = analysis_summary[0]
        st.subheader('AI Snapshot')
        st.success(
            f"Based on recent return, volatility, and drawdown, {top_pick['ticker']} ranks highest in the current selection. "
            f"Open the AI Assistant page for a deeper explanation."
        )
    
        # Display detailed statistics
        st.subheader('Performance Statistics')
        stats_data = []
        for item in analysis_summary:
            stats_data.append({
                'Ticker': item['ticker'],
                'Current Price': f"${item['current_price']:.2f}",
                'Period Return': f"{item['percent_change']:.2f}%",
                'Annualized Volatility': f"{item['volatility_pct']:.2f}%",
                'Drawdown From High': f"{item['drawdown_pct']:.2f}%",
                'Average Price': f"${item['average_price']:.2f}",
                'AI Score': f"{item['score']:.2f}",
            })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, width='stretch')
        else:
            st.session_state.analysis_snapshot = {
                'generated_at': datetime.now().isoformat(),
                'start_date': str(start_date),
                'end_date': str(end_date),
                'selected_tickers': selected_tickers,
                'stocks': [],
                'top_pick': None,
            }
            st.error('Could not fetch data for any of the selected tickers. Please check the ticker symbols.')

# Sidebar for Latest Stock News
with st.sidebar:
    st.markdown("<h2 style='font-family: \"Playfair Display\", serif; letter-spacing: 1px; font-size: 36px;'>Latest News</h2>", unsafe_allow_html=True)
    
    if st.button('Refresh', key='refresh_news', width='stretch'):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    if not selected_tickers:
        st.info('Enter stock tickers in the main section to see related news articles.')
    else:
        all_news = {}
        
        # Fetch news for all selected tickers
        try:
            with st.spinner('Fetching latest news...'):
                for ticker in selected_tickers:
                    news = get_stock_news(ticker)
                    if news:
                        all_news[ticker] = news[:3]  # Get top 3 articles per ticker for sidebar
        except Exception as e:
            st.error(f"Error fetching news: {str(e)}")
        
        if all_news:
            for ticker, articles in all_news.items():
                st.markdown(f"**{ticker}**")
                
                if not articles or len(articles) == 0:
                    st.caption('No articles available')
                else:
                    for i, article in enumerate(articles, 1):
                        try:
                            # Extract article data with proper defaults
                            title = article.get('title', f'Article {i}')
                            if isinstance(title, str):
                                title = title.strip()[:60] + ('...' if len(title) > 60 else '')
                            else:
                                title = f'Article {i}'
                            
                            link = article.get('link', '#')
                            if not isinstance(link, str):
                                link = '#'
                            else:
                                link = link.strip()
                            
                            source = article.get('source', 'Finance')
                            if isinstance(source, str):
                                source = source.strip()[:20]
                            else:
                                source = 'Finance'
                            
                            # Create a clickable article link
                            if link and link != '#':
                                st.markdown(f"[{title}]({link})")
                            else:
                                st.markdown(f"{title}")
                            
                            st.caption(f"{source}")
                        except Exception as e:
                            st.caption(f"Error displaying article: {str(e)}")
                
                st.divider()
        else:
            st.info('No articles found. Try refreshing or check back later.')
