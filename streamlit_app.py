import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests

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
            color: var(--earth-brown) !important;
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
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Declare some useful functions.

@st.cache_data(ttl='1h')
def get_stock_data(ticker, start_date, end_date):
    """Fetch stock data from yfinance.

    This uses caching with a 1-hour TTL to avoid excessive API calls.
    """
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if stock_data.empty:
            return None
        return stock_data
    except Exception as e:
        return None

@st.cache_data(ttl='1h')
def get_top_performers(tickers_list, lookback_days=365):
    """Find best performing stocks from a list based on price change."""
    performers = {}
    
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        for ticker in tickers_list:
            try:
                stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
                if not stock_data.empty:
                    start_price = stock_data['Close'].iloc[0].item()
                    end_price = stock_data['Close'].iloc[-1].item()
                    percent_change = ((end_price - start_price) / start_price) * 100
                    performers[ticker] = float(percent_change)
            except:
                continue
    except:
        pass
    
    # Return top 5 performers sorted by return
    if performers:
        sorted_performers = sorted(performers.items(), key=lambda x: x[1], reverse=True)
        return [ticker for ticker, _ in sorted_performers[:5]]
    
    # Fallback to default if no data available
    return ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL']

@st.cache_data(ttl='1h')
def get_suggested_stocks():
    """Get list of well-performing tech and finance stocks."""
    default_stocks = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN', 'NFLX', 'SPY', 'QQQ']
    return get_top_performers(default_stocks)

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
    <h1 style='font-family: "Playfair Display", serif; text-align: center; letter-spacing: 2px; font-size: 56px;'>Stock Tracker</h1>
    <p style='text-align: center; color: gray; font-size: 14px;'>Track historical and current stock data. Enter your favorite stock tickers and explore their performance over time.</p>
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
        if st.button(ticker, key=f'sugg_{ticker}', width='stretch'):
            if ticker not in st.session_state.selected_tickers_list:
                st.session_state.selected_tickers_list.append(ticker)
            st.rerun()

if ticker_input:
    selected_tickers = [t.strip().upper() for t in ticker_input.split(',')]
    selected_tickers = [t for t in selected_tickers if t]  # Remove empty strings
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

if not combined_data.empty:
    # Display historical price chart
    st.subheader('Stock Price Over Time')
    st.line_chart(combined_data, use_container_width=True)
    
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
    
    # Display detailed statistics
    st.subheader('Performance Statistics')
    stats_data = []
    for ticker in selected_tickers:
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
else:
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
