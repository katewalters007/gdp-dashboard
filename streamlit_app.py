import streamlit as st
import pandas as pd
import yfinance as yf
import feedparser
from datetime import datetime, timedelta

from stock_analysis import build_analysis_snapshot, get_stock_data, get_suggested_stocks, normalize_tickers
from auth_utils import (
    get_user_preferences,
    update_user_theme,
    add_price_alert,
    remove_price_alert,
    get_triggered_alerts,
    send_price_alert_email,
    mark_alert_as_triggered,
    get_smtp_config,
    _load_users,
    _save_users,
    _find_user_index_by_email,
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

            /* Ensure all form labels and input labels are visible */
            [data-testid="stDateInput"] label,
            [data-testid="stNumberInput"] label,
            [data-testid="stTextInput"] label,
            [data-testid="stSelectbox"] label,
            [data-testid="stMultiSelect"] label,
            .stDateInput label,
            .stNumberInput label,
            .stTextInput label,
            .stSelectbox label,
            .stMultiSelect label,
            [data-baseweb="label"] {
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
            .stMarkdownContainer h3 * {
                color: #E8D5B7 !important;
                background-color: transparent !important;
            }

            [data-testid="stAlert"] > div:nth-child(2),
            [data-testid="stAlert"] > div:nth-child(2) * {
                color: var(--dark-text) !important;
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

            /* Ensure chart text is visible */
            .stPlotlyContainer svg text,
            [data-testid="stMetricValue"] {
                color: var(--dark-text) !important;
                fill: var(--dark-text) !important;
            }

            [data-testid="stMetricLabel"],
            [data-testid="stMetricDelta"] {
                color: var(--dark-muted) !important;
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

            /* Explicit styling for subheaders */
            h2, h3, h4, h5, h6 {
                color: #E8D5B7 !important;
            }

            /* Ensure dataframe text is readable */
            [data-testid="dataFrame"] td,
            [data-testid="dataFrame"] th {
                color: var(--dark-text) !important;
                background-color: rgba(30, 45, 56, 0.5) !important;
            }

            [data-testid="dataFrame"] thead th {
                background-color: rgba(45, 106, 159, 0.7) !important;
                color: #FFFFFF !important;
            }

            /* Graph/chart area background */
            .stPlotlyContainer svg rect:first-child {
                fill: rgba(30, 45, 56, 0.5) !important;
            }

            a,
            [data-testid="stSidebar"] a {
                color: #9FD3E6 !important;
            }

            /* Form labels and wrapper text */
            [data-testid="stDateInput"] > div > label,
            [data-testid="stNumberInput"] > div > label,
            [data-testid="stTextInput"] > div > label,
            [data-testid="stSelectbox"] > div > label,
            .stDateInput > label,
            .stNumberInput > label,
            .stTextInput > label,
            .stSelectbox > label {
                color: var(--dark-text) !important;
            }

            /* Wrapper divs for form elements */
            [data-testid="stDateInput"] > div,
            [data-testid="stNumberInput"] > div,
            [data-testid="stTextInput"] > div,
            [data-testid="stSelectbox"] > div {
                color: var(--dark-text) !important;
            }

            /* Ensure button text is visible */
            [data-testid="stButton"] button {
                color: white !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Initialize user preferences
if 'authenticated_user_email' not in st.session_state:
    st.session_state.authenticated_user_email = None

if 'user_preferences' not in st.session_state:
    st.session_state.user_preferences = None

# Load user preferences if authenticated
if st.session_state.authenticated_user_email:
    st.session_state.user_preferences = get_user_preferences(st.session_state.authenticated_user_email)

# Apply theme based on user preference
current_theme = st.session_state.user_preferences.get("theme", "light") if st.session_state.user_preferences else "light"

# Add theme-specific CSS overrides if dark mode
if current_theme == "dark":
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] {
                background: linear-gradient(180deg, #0F1A22 0%, #162631 100%) !important;
            }
        </style>
    """, unsafe_allow_html=True)

# Add sidebar preferences panel for authenticated users
if st.session_state.authenticated_user_email:
    with st.sidebar:
        st.markdown(f"**👤 {st.session_state.authenticated_user_email}**")
        
        if st.button("🚪 Logout", key="logout_btn"):
            st.session_state.authenticated_user_email = None
            st.session_state.user_preferences = None
            st.experimental_rerun()
        
        st.divider()
        st.markdown("### ⚙️ Settings")
        
        # Theme toggle
        new_theme = st.selectbox(
            "Select Theme",
            ["light", "dark"],
            index=0 if current_theme == "light" else 1,
            key="theme_selector"
        )
        
        if new_theme != current_theme:
            success, message = update_user_theme(st.session_state.authenticated_user_email, new_theme)
            if success:
                st.success(message)
                st.session_state.user_preferences["theme"] = new_theme
                st.experimental_rerun()
            else:
                st.error(message)
        
        # Notification toggle
        notifications_enabled = st.session_state.user_preferences.get("enable_notifications", True)
        new_notifications_enabled = st.checkbox(
            "Enable Email Notifications",
            value=notifications_enabled,
            key="notifications_toggle"
        )
        
        # Update notifications preference if changed
        if new_notifications_enabled != notifications_enabled:
            users = _load_users()
            user_index = _find_user_index_by_email(users, st.session_state.authenticated_user_email)
            if user_index is not None:
                users[user_index]["preferences"]["enable_notifications"] = new_notifications_enabled
                _save_users(users)
                st.session_state.user_preferences["enable_notifications"] = new_notifications_enabled
                st.success("Notification settings updated!")
                st.experimental_rerun()
        
        st.divider()
        st.markdown("### 🔔 Price Alerts")
        
        with st.expander("Manage Price Alerts"):
            col1, col2 = st.columns(2)
            
            with col1:
                alert_ticker = st.text_input("Ticker", placeholder="e.g., AAPL").upper()
            
            with col2:
                alert_type = st.selectbox("Alert Type", ["above", "below"])
            
            alert_price = st.number_input("Price ($)", min_value=0.01, step=0.01)
            
            if st.button("Add Alert"):
                if alert_ticker:
                    success, message = add_price_alert(
                        st.session_state.authenticated_user_email,
                        alert_ticker,
                        alert_type,
                        alert_price
                    )
                    if success:
                        st.success(message)
                        st.session_state.user_preferences = get_user_preferences(
                            st.session_state.authenticated_user_email
                        )
                    else:
                        st.error(message)
                else:
                    st.error("Please enter a ticker symbol")
            
            st.markdown("#### Active Alerts")
            price_alerts = st.session_state.user_preferences.get("price_alerts", {})
            
            if price_alerts:
                for alert_key, alert_info in price_alerts.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"**{alert_info['ticker']}** {alert_info['type'].title()} ${alert_info['price']:.2f}")
                    with col2:
                        if st.button("✕", key=f"remove_{alert_key}"):
                            success, message = remove_price_alert(
                                st.session_state.authenticated_user_email,
                                alert_key
                            )
                            if success:
                                st.session_state.user_preferences = get_user_preferences(
                                    st.session_state.authenticated_user_email
                                )
                                st.experimental_rerun()
            else:
                st.caption("No active alerts")

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

# Display price alert notifications if user is authenticated
if st.session_state.authenticated_user_email and st.session_state.user_preferences:
    ticker_data_for_alerts = {}
    
    # We'll check alerts when we have ticker data
    st.session_state.check_alerts = True
else:
    st.session_state.check_alerts = False

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

# Initialize session state for selected tickers
if 'selected_tickers_list' not in st.session_state:
    st.session_state.selected_tickers_list = ['AAPL', 'GOOGL', 'MSFT']

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
        if st.button(ticker, key=f'sugg_{ticker}'):
            if ticker not in st.session_state.selected_tickers_list:
                st.session_state.selected_tickers_list.append(ticker)
            st.experimental_rerun()

if ticker_input:
    selected_tickers = normalize_tickers(ticker_input)
    st.session_state.selected_tickers_list = selected_tickers
else:
    selected_tickers = []

if not len(selected_tickers):
    st.warning("Enter at least one stock ticker")

# Main content area for Stock Analysis
st.markdown("<h2 style='font-family: \"Playfair Display\", serif; letter-spacing: 1px; margin-top: 5px; margin-bottom: 10px;'>Stock Analysis</h2>", unsafe_allow_html=True)

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

# Check for triggered price alerts and send email notifications
if st.session_state.authenticated_user_email and st.session_state.user_preferences and ticker_data:
    current_prices = {ticker: data['Close'].iloc[-1] for ticker, data in ticker_data.items()}
    triggered_alerts = get_triggered_alerts(st.session_state.authenticated_user_email, current_prices)
    
    if triggered_alerts:
        st.divider()
        st.markdown("### 🔔 Price Alert Notifications")
        
        # Send email notifications for triggered alerts
        smtp_config = get_smtp_config()
        notifications_sent = 0
        
        for alert in triggered_alerts:
            st.info(alert["message"])
            
            # Send email notification if notifications are enabled
            if st.session_state.user_preferences.get("enable_notifications", True):
                if smtp_config:
                    success, email_msg = send_price_alert_email(
                        st.session_state.authenticated_user_email,
                        alert,
                        smtp_config
                    )
                    if success:
                        # Mark alert as triggered so we don't send duplicate emails
                        mark_alert_as_triggered(
                            st.session_state.authenticated_user_email,
                            alert["alert_key"]
                        )
                        notifications_sent += 1
        
        if notifications_sent > 0:
            st.success(f"✅ {notifications_sent} email notification(s) sent!")
        
        st.divider()

if not combined_data.empty:
    # Display historical price chart
    st.subheader('Stock Price Over Time')
    st.line_chart(combined_data)
    
    # Display current metrics
    st.subheader('Current Stock Data')
    
    cols = st.columns(min(len(selected_tickers), 4))
    
    for i, ticker in enumerate(selected_tickers):
        col = cols[i % len(cols)]
        
        with col:
            if ticker in ticker_data:
                stock_data = ticker_data[ticker]
                current_price = stock_data['Close'].iloc[-1].item()
                previous_price = stock_data['Close'].iloc[0].item()
                price_change = current_price - previous_price
                percent_change = (price_change / previous_price) * 100
                
                st.metric(
                    label=ticker,
                    value=f'${current_price:.2f}',
                    delta=f'{percent_change:.2f}%',
                    delta_color='normal' if price_change >= 0 else 'inverse'
                )
            else:
                st.warning(f'Could not fetch data for {ticker}')

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
        st.dataframe(stats_df)
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
    
    if st.button('Refresh', key='refresh_news'):
        st.cache_data.clear()
        st.experimental_rerun()
    
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
