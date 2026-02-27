import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import requests

# Set the title and favicon that appear in the Browser's tab bar.
st.set_page_config(
    page_title='Stock Tracker',
    page_icon=':chart_with_upwards_trend:', # This is an emoji shortcode. Could be a URL too.
)

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
def get_stock_info(ticker):
    """Fetch current stock info from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        return stock.info
    except Exception as e:
        return None

@st.cache_data(ttl='5m')
def get_stock_news(ticker):
    """Fetch news articles for a stock ticker from yfinance."""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            return []
        
        formatted_news = []
        for article in news:
            # Handle different possible structures from yfinance
            formatted_article = {
                'title': article.get('title') or article.get('headline') or 'Untitled',
                'link': article.get('link') or article.get('url') or '#',
                'source': article.get('source') or article.get('publisher') or 'Financial News'
            }
            formatted_news.append(formatted_article)
        
        return formatted_news if formatted_news else []
    except Exception as e:
        return []

# -----------------------------------------------------------------------------
# Draw the actual page

# Set the title that appears at the top of the page.
'''
# :chart_with_upwards_trend: Stock Tracker

Track historical and current stock data. Enter your favorite stock tickers and explore their performance over time.
'''

# Add some spacing
''
''

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

''

ticker_input = st.text_input(
    'Enter stock tickers (comma-separated)',
    value='AAPL, GOOGL, MSFT',
    placeholder='e.g., AAPL, GOOGL, MSFT'
)

# Suggested well-performing stocks
st.caption('💡 Suggested well-performing stocks:')
col_sugg1, col_sugg2, col_sugg3, col_sugg4, col_sugg5 = st.columns(5)

suggested_tickers = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft', 
    'NVDA': 'Nvidia',
    'TSLA': 'Tesla',
    'GOOGL': 'Google'
}

with col_sugg1:
    if st.button('AAPL', key='sugg_aapl', use_container_width=True):
        ticker_input = 'AAPL'

with col_sugg2:
    if st.button('MSFT', key='sugg_msft', use_container_width=True):
        ticker_input = 'MSFT'

with col_sugg3:
    if st.button('NVDA', key='sugg_nvda', use_container_width=True):
        ticker_input = 'NVDA'

with col_sugg4:
    if st.button('TSLA', key='sugg_tsla', use_container_width=True):
        ticker_input = 'TSLA'

with col_sugg5:
    if st.button('GOOGL', key='sugg_googl', use_container_width=True):
        ticker_input = 'GOOGL'

if ticker_input:
    selected_tickers = [t.strip().upper() for t in ticker_input.split(',')]
    selected_tickers = [t for t in selected_tickers if t]  # Remove empty strings
else:
    selected_tickers = []

if not len(selected_tickers):
    st.warning("Enter at least one stock ticker")

''
''
''

# Create tabs for different sections
tab1, tab2 = st.tabs(["📊 Stock Analysis", "📰 News & Articles"])

with tab1:
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
        st.header('Stock Price Over Time', divider='gray')
        ''
        st.line_chart(combined_data)
        ''
        ''
        
        # Display current metrics
        st.header('Current Stock Data', divider='gray')
        ''
        
        cols = st.columns(min(len(selected_tickers), 4))
        
        for i, ticker in enumerate(selected_tickers):
            col = cols[i % len(cols)]
            
            with col:
                if ticker in ticker_data:
                    stock_data = ticker_data[ticker]
                    current_price = float(stock_data['Close'].iloc[-1])
                    previous_price = float(stock_data['Close'].iloc[0])
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
        
        ''
        ''
        
        # Display detailed statistics
        st.header('Performance Statistics', divider='gray')
        ''
        
        stats_data = []
        for ticker in selected_tickers:
            if ticker in ticker_data:
                stock_data = ticker_data[ticker]
                current_price = float(stock_data['Close'].iloc[-1])
                high = float(stock_data['High'].max())
                low = float(stock_data['Low'].min())
                avg = float(stock_data['Close'].mean())
                
                stats_data.append({
                    'Ticker': ticker,
                    'Current Price': f'${current_price:.2f}',
                    '52-Week High': f'${high:.2f}',
                    '52-Week Low': f'${low:.2f}',
                    'Average Price': f'${avg:.2f}'
                })
        
        if stats_data:
            stats_df = pd.DataFrame(stats_data)
            st.dataframe(stats_df, use_container_width=True)
    else:
        st.error('Could not fetch data for any of the selected tickers. Please check the ticker symbols.')

with tab2:
    col1, col2 = st.columns([0.85, 0.15])
    with col1:
        st.header('Latest Stock News', divider='gray')
    with col2:
        if st.button('🔄 Refresh', key='refresh_news'):
            st.cache_data.clear()
            st.rerun()
    
    if not selected_tickers:
        st.info('Enter stock tickers in the main section to see related news articles.')
    else:
        all_news = {}
        
        # Fetch news for all selected tickers
        with st.spinner('Fetching latest news...'):
            for ticker in selected_tickers:
                news = get_stock_news(ticker)
                if news:
                    all_news[ticker] = news[:5]  # Get top 5 articles per ticker
        
        if all_news:
            st.success(f'✅ News updated - Showing latest articles for {", ".join(all_news.keys())}')
            ''
            
            for ticker, articles in all_news.items():
                st.subheader(f'📰 {ticker}')
                
                if not articles or len(articles) == 0:
                    st.info(f'No recent articles found for {ticker}. Try refreshing again soon!')
                else:
                    for i, article in enumerate(articles):
                        # Extract article data with proper defaults
                        title = article.get('title', '').strip() if isinstance(article.get('title'), str) else 'Untitled Article'
                        link = article.get('link', '').strip() if isinstance(article.get('link'), str) else '#'
                        source = article.get('source', 'Financial News').strip() if isinstance(article.get('source'), str) else 'Financial News'
                        
                        # Skip if title is completely empty
                        if not title or title == 'Untitled Article':
                            title = f'Article {i+1} from {source}'
                        
                        # Create a clickable article box
                        if link and link != '#':
                            st.markdown(f"**[{title}]({link})**")
                        else:
                            st.markdown(f"**{title}**")
                        
                        st.caption(f"📌 Source: {source}")
                        st.divider()
        else:
            st.warning('No news articles found for the selected tickers. Try clicking Refresh or check back later.')
