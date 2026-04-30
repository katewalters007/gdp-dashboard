import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from stock_analysis import (
    DEFAULT_STOCK_UNIVERSES,
    build_analysis_snapshot,
    get_bulk_stock_data,
    normalize_tickers,
)
from user_backend import get_watchlist

st.set_page_config(
    page_title='AI Stock Assistant',
    page_icon='🤖',
    layout='wide'
)

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

        [data-testid="stChatMessage"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.88) 0%, rgba(235, 243, 247, 0.9) 100%);
            border: 1px solid var(--light-grey);
            border-radius: 14px;
            padding: 0.75rem;
            color: var(--beige-text) !important;
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

            .stMarkdownContainer h3,
            .stMarkdownContainer h3 *,
            [data-testid="stChatMessage"],
            [data-testid="stChatMessage"] *,
            [data-testid="stAlert"] > div:nth-child(2),
            [data-testid="stAlert"] > div:nth-child(2) * {
                color: var(--beige-text) !important;
            }

            .main,
            [data-testid="stSidebar"],
            [data-testid="stVerticalBlock"] > div {
                background: linear-gradient(180deg, rgba(20, 32, 41, 0.96) 0%, rgba(30, 45, 56, 0.96) 100%) !important;
                color: var(--dark-text) !important;
            }

            [data-testid="stChatMessage"] {
                background: linear-gradient(135deg, rgba(245, 243, 240, 0.94) 0%, rgba(235, 243, 247, 0.94) 100%) !important;
                border-color: rgba(107, 68, 35, 0.18) !important;
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

def format_currency(value):
    return f"${value:.2f}"


def format_percent(value):
    return f"{value:.2f}%"


def get_snapshot():
    return st.session_state.get(
        'advisor_snapshot',
        {
            'generated_at': datetime.now().isoformat(),
            'start_date': None,
            'end_date': None,
            'selected_tickers': [],
            'stocks': [],
            'top_pick': None,
            'history': {},
        },
    )


def describe_stock(stock):
    return (
        f"{stock['ticker']} is up {format_percent(stock['percent_change'])} over the selected period, "
        f"with annualized volatility near {format_percent(stock['volatility_pct'])} and a drawdown of "
        f"{format_percent(stock['drawdown_pct'])} from its peak. The current price is {format_currency(stock['current_price'])}, "
        f"versus an average price of {format_currency(stock['average_price'])}."
    )


def rank_table(snapshot):
    rows = []
    for position, stock in enumerate(snapshot['stocks'], start=1):
        rows.append({
            'Rank': position,
            'Ticker': stock['ticker'],
            'AI Score': round(stock['score'], 2),
            'Return %': round(stock['percent_change'], 2),
            'Volatility %': round(stock['volatility_pct'], 2),
            'Drawdown %': round(stock['drawdown_pct'], 2),
        })
    return rows


def get_ticker_mentions(prompt, stocks):
    prompt_upper = prompt.upper()
    return [stock for stock in stocks if stock['ticker'] in prompt_upper]


def build_recommendation(snapshot):
    """Build a recommendation for the best stock from the snapshot."""
    if not snapshot or not snapshot.get('stocks'):
        return 'I do not have valid stock data yet. Run the advisor to load historical prices first.'

    try:
        stocks = snapshot['stocks']
        top_stock = stocks[0]
        runner_up = stocks[1] if len(stocks) > 1 else None
        
        response = [
            f"Based on the selected historical window, {top_stock['ticker']} is the strongest purchase candidate from this list.",
            describe_stock(top_stock),
        ]

        if runner_up:
            score_gap = top_stock['score'] - runner_up['score']
            response.append(
                f"It ranks ahead of {runner_up['ticker']} by {score_gap:.2f} points because it combines stronger momentum with a better risk-adjusted profile in this time window."
            )

        response.append(
            "This assistant is educational only. It ranks the displayed stocks from recent price behavior, not full valuation, earnings quality, or macro risk."
        )
        return "\n\n".join(response)
    except Exception as e:
        return f"Unable to build recommendation: {str(e)}"


def build_comparison_response(stocks):
    """Compare multiple stocks mentioned in the prompt."""
    try:
        if not stocks:
            return "No stocks were mentioned in your question. Please specify ticker symbols to compare."
        
        sorted_stocks = sorted(stocks, key=lambda item: item['score'], reverse=True)
        lines = [f"Among the stocks mentioned, {sorted_stocks[0]['ticker']} looks strongest right now."]
        
        for stock in sorted_stocks:
            lines.append(
                f"{stock['ticker']}: score {stock['score']:.2f}, return {format_percent(stock['percent_change'])}, volatility {format_percent(stock['volatility_pct'])}, drawdown {format_percent(stock['drawdown_pct'])}."
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"Unable to compare stocks: {str(e)}"


def build_risk_response(snapshot):
    """Analyze risk profile of stocks in snapshot."""
    try:
        if not snapshot or not snapshot.get('stocks'):
            return "I do not have enough data to rank risk yet."

        stocks = snapshot['stocks']
        if not stocks:
            return "No stocks available for risk analysis."
        
        riskiest = max(stocks, key=lambda item: item['volatility_pct'])
        steadiest = min(stocks, key=lambda item: item['volatility_pct'])
        
        return (
            f"The highest-volatility name is {riskiest['ticker']} at about {format_percent(riskiest['volatility_pct'])}, so it has shown the largest price swings. "
            f"The steadiest name is {steadiest['ticker']} at about {format_percent(steadiest['volatility_pct'])}."
        )
    except Exception as e:
        return f"Unable to analyze risk: {str(e)}"


def build_drawdown_response(snapshot):
    """Analyze drawdown profiles of stocks in snapshot."""
    try:
        if not snapshot or not snapshot.get('stocks'):
            return "I do not have enough data to compare pullbacks yet."

        stocks = snapshot['stocks']
        if not stocks:
            return "No stocks available for drawdown analysis."
        
        closest_to_high = max(stocks, key=lambda item: item['drawdown_pct'])
        deepest_pullback = min(stocks, key=lambda item: item['drawdown_pct'])
        
        return (
            f"{closest_to_high['ticker']} is closest to its period high with a drawdown of {format_percent(closest_to_high['drawdown_pct'])}. "
            f"{deepest_pullback['ticker']} has the deepest pullback at {format_percent(deepest_pullback['drawdown_pct'])}."
        )
    except Exception as e:
        return f"Unable to analyze drawdowns: {str(e)}"


def get_stock_history(ticker, snapshot):
    history = snapshot.get('history', {})
    stock_history = history.get(ticker)
    if isinstance(stock_history, pd.DataFrame) and 'Close' in stock_history.columns:
        close_prices = stock_history['Close'].dropna()
        return close_prices if not close_prices.empty else None
    return None


def compute_period_return(close_prices, lookback_days):
    if close_prices is None or len(close_prices) <= lookback_days:
        return None
    earlier_price = float(close_prices.iloc[-(lookback_days + 1)])
    latest_price = float(close_prices.iloc[-1])
    if earlier_price == 0:
        return None
    return ((latest_price - earlier_price) / earlier_price) * 100


def build_general_response(prompt, snapshot):
    stocks = snapshot.get('stocks', [])
    if not stocks:
        return 'I do not have enough loaded data to answer that yet. Run the advisor first.'

    top = stocks[0]
    bottom = stocks[-1]
    tickers = ', '.join(stock['ticker'] for stock in stocks[:8])
    if len(stocks) > 8:
        tickers += ', ...'

    # Add some variety to responses to avoid repetition
    response_variations = [
        f"I am answering from the historical snapshot loaded for {len(stocks)} tickers from {snapshot.get('start_date')} to {snapshot.get('end_date')}. The top-ranked name is {top['ticker']} with a score of {top['score']:.2f}, return {format_percent(top['percent_change'])}, and volatility {format_percent(top['volatility_pct'])}. The lowest-ranked name is {bottom['ticker']} with return {format_percent(bottom['percent_change'])}. Currently analyzed tickers include: {tickers}. Ask about a specific ticker, comparison, volatility, drawdown, or overall ranking.",
        f"Based on the loaded analysis covering {len(stocks)} stocks from {snapshot.get('start_date')} to {snapshot.get('end_date')}, {top['ticker']} leads with a {top['score']:.2f} score and {format_percent(top['percent_change'])} return. At the bottom is {bottom['ticker']} with {format_percent(bottom['percent_change'])} performance. The full list includes: {tickers}. Try asking about specific stocks or comparisons.",
        f"From the {len(stocks)} stocks analyzed between {snapshot.get('start_date')} and {snapshot.get('end_date')}, {top['ticker']} ranks highest with {format_percent(top['percent_change'])} return and {format_percent(top['volatility_pct'])} volatility. {bottom['ticker']} shows the lowest return at {format_percent(bottom['percent_change'])}. Available stocks: {tickers}. What would you like to know about these stocks?"
    ]
    
    # Use a simple hash of the prompt to select different response variations
    import hashlib
    variation_index = int(hashlib.md5(prompt.encode()).hexdigest(), 16) % len(response_variations)
    return response_variations[variation_index]


def build_stock_response(stock, prompt, snapshot):
    prompt_lower = prompt.lower()
    history = get_stock_history(stock['ticker'], snapshot)
    latest = stock.get('current_price')
    rank = snapshot['stocks'].index(stock) + 1 if stock in snapshot['stocks'] else None
    performance = format_percent(stock['percent_change'])
    volatility = format_percent(stock['volatility_pct'])
    drawdown = format_percent(stock['drawdown_pct'])
    average = format_currency(stock['average_price'])

    if 'rank' in prompt_lower or 'score' in prompt_lower:
        return (
            f"{stock['ticker']} ranks #{rank} in the current analysis with a score of {stock['score']:.2f}. "
            f"It has returned {performance} over the selected period."
        )

    if any(keyword in prompt_lower for keyword in ['current price', 'price', 'last close', 'close']):
        response = f"{stock['ticker']} most recently closed at {format_currency(latest)}. "
        if history is not None:
            weekly = compute_period_return(history, 5)
            if weekly is not None:
                response += f"That is about {format_percent(weekly)} over the last 5 trading days. "
        return response + f"Overall, it has returned {performance} in the loaded window."

    if any(keyword in prompt_lower for keyword in ['return', 'performance', 'gain', 'loss']):
        response = (
            f"{stock['ticker']} returned {performance} in the historical window loaded. "
            f"Its average price was {average}, and it has {volatility} annualized volatility."
        )
        if history is not None:
            month = compute_period_return(history, 21)
            if month is not None:
                response += f" Over the last month in this dataset it changed by {format_percent(month)}."
        return response

    if any(keyword in prompt_lower for keyword in ['risk', 'volatile', 'volatility', 'risky']):
        return (
            f"{stock['ticker']} has an annualized volatility of {volatility}, which is its primary risk signal in the loaded snapshot. "
            f"Its drawdown from the high is {drawdown}."
        )

    if any(keyword in prompt_lower for keyword in ['drawdown', 'pullback', 'near high', 'below high', 'peak', 'low']):
        return (
            f"{stock['ticker']}'s drawdown from its period high is {drawdown}. "
            f"Its average price over the period was {average}, and it currently trades at {format_currency(latest)}."
        )

    if any(keyword in prompt_lower for keyword in ['trend', 'momentum', 'better than', 'stronger than', 'compare']):
        return (
            f"{stock['ticker']} is currently ranked #{rank} in the analysis and has returned {performance} while showing {volatility} volatility. "
            f"Compared to its own average price, it is {format_percent(stock['trend_vs_average_pct'])} "
            f"{'above' if stock['trend_vs_average_pct'] >= 0 else 'below'} the period average."
        )

    return (
        f"{describe_stock(stock)} "
        f"It ranks #{rank} in the current watchlist and shows {drawdown} drawdown with {volatility} volatility."
    )


def answer_prompt(prompt, snapshot):
    """Generate AI response to user prompt based on loaded stock snapshot."""
    try:
        if not prompt or not isinstance(prompt, str):
            return "Please enter a valid question."

        prompt_lower = prompt.lower().strip()

        if not snapshot or not snapshot.get('stocks'):
            return (
                'Run the historical advisor first so I have a ranked watchlist to analyze. '
                'I score stocks from past price behavior instead of using an external AI API.'
            )

        try:
            mentioned_stocks = get_ticker_mentions(prompt, snapshot['stocks'])
        except Exception:
            mentioned_stocks = []

        if any(keyword in prompt_lower for keyword in ['compare', 'vs', 'versus']) and len(mentioned_stocks) >= 2:
            return build_comparison_response(mentioned_stocks)

        if any(keyword in prompt_lower for keyword in ['which stock', 'what should i buy', 'purchase', 'buy', 'best stock', 'recommend']):
            return build_recommendation(snapshot)

        if any(keyword in prompt_lower for keyword in ['risk', 'risky', 'volatile', 'volatility']):
            return build_risk_response(snapshot)

        if any(keyword in prompt_lower for keyword in ['drawdown', 'pullback', 'near high', 'below high', 'peak']):
            return build_drawdown_response(snapshot)

        if len(mentioned_stocks) == 1:
            return build_stock_response(mentioned_stocks[0], prompt, snapshot)

        if len(mentioned_stocks) > 1:
            return build_comparison_response(mentioned_stocks)

        if any(keyword in prompt_lower for keyword in ['how many', 'how much', 'number of', 'total']):
            return f"I currently have {len(snapshot['stocks'])} stocks loaded in the snapshot covering {snapshot.get('start_date')} through {snapshot.get('end_date')} ."

        return build_general_response(prompt, snapshot)
    except Exception as e:
        return f"I encountered an issue responding to your question: {str(e)}"


snapshot = get_snapshot()

def build_watchlist_input(selection):
    if selection == 'Custom':
        default_tickers = st.session_state.get('advisor_custom_tickers', ['AAPL', 'MSFT', 'NVDA', 'TSLA'])
    elif selection == 'My Watchlist':
        current_user = st.session_state.get('auth_user')
        if current_user:
            watchlist = get_watchlist(current_user['id'])
            if watchlist:
                default_tickers = watchlist
            else:
                default_tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA']  # fallback if watchlist empty
        else:
            default_tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA']  # fallback
    else:
        default_tickers = DEFAULT_STOCK_UNIVERSES[selection]
    return ', '.join(default_tickers)


def build_rank_table(snapshot):
    return pd.DataFrame(rank_table(snapshot))


def build_normalized_chart_data(snapshot):
    """Build normalized price chart data indexed to 100 at start date."""
    series_map = {}
    
    try:
        history = snapshot.get('history', {})
        if not history:
            return pd.DataFrame()
        
        for stock in snapshot['stocks'][:3]:
            ticker = stock['ticker']
            
            try:
                if ticker not in history:
                    continue
                    
                stock_history = history[ticker]
                if stock_history is None or stock_history.empty:
                    continue
                
                # Extract close prices and handle different data formats
                if isinstance(stock_history, pd.DataFrame):
                    if 'Close' not in stock_history.columns:
                        continue
                    close_prices = stock_history['Close'].copy()
                else:
                    continue
                
                # Remove NaN values
                close_prices = close_prices.dropna()
                if close_prices.empty:
                    continue
                
                # Get base price (first valid close price)
                base_price = float(close_prices.iloc[0])
                if base_price <= 0:
                    continue
                
                # Normalize to base 100
                normalized = (close_prices / base_price) * 100
                series_map[ticker] = normalized
                
            except (KeyError, ValueError, TypeError, AttributeError):
                continue
        
        if not series_map:
            return pd.DataFrame()
        
        # Create DataFrame from series, aligning by date
        return pd.DataFrame(series_map)
    
    except Exception:
        return pd.DataFrame()


st.title('Historical Stock Advisor')
st.markdown('This advisor reviews past price action, ranks a stock list by return, volatility, drawdown, and trend strength, and then explains which names look strongest. It is educational only and not financial advice.')

with st.container(border=True):
    st.subheader('Advisor Inputs')
    control_col1, control_col2, control_col3 = st.columns([1.2, 1, 1])

    with control_col1:
        current_user = st.session_state.get('auth_user')
        universe_options = list(DEFAULT_STOCK_UNIVERSES.keys()) + ['Custom']
        if current_user:
            universe_options.insert(0, 'My Watchlist')
        watchlist_choice = st.selectbox(
            'Stock universe',
            options=universe_options,
            index=0,
        )
        tickers_value = st.text_input(
            'Tickers to rank',
            value=build_watchlist_input(watchlist_choice),
            placeholder='e.g., AAPL, MSFT, NVDA, TSLA',
            disabled=(watchlist_choice == 'My Watchlist'),
        )
        st.session_state.advisor_custom_tickers = normalize_tickers(tickers_value)

    with control_col2:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)
        start_date = st.date_input('Start date', value=start_date, max_value=end_date, key='advisor_start_date')
        lookback_note = (pd.Timestamp(st.session_state.advisor_end_date) - pd.Timestamp(start_date)).days if 'advisor_end_date' in st.session_state else 365
        st.caption(f'Current lookback: about {max(lookback_note, 1)} days')

    with control_col3:
        end_date = st.date_input('End date', value=end_date, min_value=start_date, max_value=datetime.now().date(), key='advisor_end_date')
        top_pick_count = st.slider('How many buy ideas to show', min_value=1, max_value=5, value=3)
        analyze_clicked = st.button('Run advisor', width='stretch')
        if st.button('Clear Analysis Cache', width='stretch', help='Clear cached results and force fresh analysis'):
            st.session_state.pop('advisor_snapshot', None)
            st.session_state.pop('analysis_snapshot', None)
            st.session_state.pop('offline_ai_messages', None)
            st.success('Cache cleared! Run the advisor again for fresh analysis.')
            st.rerun()

if analyze_clicked or not snapshot['stocks']:
    advisor_tickers = normalize_tickers(tickers_value)
    ticker_data = get_bulk_stock_data(advisor_tickers, start_date, end_date)
    snapshot = build_analysis_snapshot(ticker_data, start_date, end_date, advisor_tickers)
    snapshot['history'] = ticker_data
    st.session_state.advisor_snapshot = snapshot
    st.session_state.analysis_snapshot = snapshot
    # Clear any existing AI messages to force fresh responses
    st.session_state.offline_ai_messages = [
        {'role': 'assistant', 'content': build_recommendation(snapshot)}
        if snapshot['stocks']
        else {'role': 'assistant', 'content': 'Run the advisor with at least one valid ticker to generate a ranking.'}
    ]

snapshot = get_snapshot()

if snapshot['stocks']:
    top_pick = snapshot['stocks'][0]
    average_score = sum(stock['score'] for stock in snapshot['stocks']) / len(snapshot['stocks'])
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric('Top historical candidate', top_pick['ticker'], f"{top_pick['percent_change']:.2f}% return")
    with metric_col2:
        st.metric('Best AI score', f"{top_pick['score']:.2f}", f"{top_pick['volatility_pct']:.2f}% volatility")
    with metric_col3:
        st.metric('Average score', f"{average_score:.2f}", f"{len(snapshot['stocks'])} valid tickers")

    st.success(build_recommendation(snapshot))
else:
    st.warning('No valid stock analysis is loaded yet. Choose a universe or enter custom tickers, then run the advisor.')

quick_col1, quick_col2, quick_col3 = st.columns(3)
with quick_col1:
    if st.button('Which stock should I purchase?', width='stretch'):
        st.session_state.ai_quick_prompt = 'Which stock should I purchase right now?'
with quick_col2:
    if st.button('Which stock is the least risky?', width='stretch'):
        st.session_state.ai_quick_prompt = 'Which stock is the least risky?'
with quick_col3:
    if st.button('Compare the top two stocks', width='stretch'):
        if len(snapshot['stocks']) >= 2:
            first = snapshot['stocks'][0]['ticker']
            second = snapshot['stocks'][1]['ticker']
            st.session_state.ai_quick_prompt = f'Compare {first} and {second}'
        else:
            st.session_state.ai_quick_prompt = 'Which stock should I purchase right now?'

st.subheader('Current Ranking')
if snapshot['stocks']:
    # Show debug info about loaded stocks
    with st.expander("📊 Analysis Details (Click to expand)", expanded=False):
        st.write(f"**Analysis Period:** {snapshot.get('start_date')} to {snapshot.get('end_date')}")
        st.write(f"**Stocks Loaded:** {len(snapshot['stocks'])}")
        st.write(f"**Top Performer:** {snapshot['stocks'][0]['ticker']} (Score: {snapshot['stocks'][0]['score']:.2f})")
        
        # Show score distribution
        scores = [stock['score'] for stock in snapshot['stocks']]
        st.write(f"**Score Range:** {min(scores):.2f} to {max(scores):.2f}")
    
    st.dataframe(build_rank_table(snapshot), width='stretch')
else:
    st.info('No stocks loaded yet. Select a universe or enter custom tickers above, then click "Run advisor".')

st.subheader('Top Ideas')
if snapshot['stocks']:
    ideas_to_show = snapshot['stocks'][:top_pick_count]
    for position, stock in enumerate(ideas_to_show, start=1):
        st.markdown(
            f"**{position}. {stock['ticker']}**  "+
            f"Score {stock['score']:.2f} | Return {format_percent(stock['percent_change'])} | "+
            f"Volatility {format_percent(stock['volatility_pct'])} | Drawdown {format_percent(stock['drawdown_pct'])}"
        )

st.subheader('Normalized Price Performance')
try:
    if snapshot.get('stocks'):
        normalized_chart = build_normalized_chart_data(snapshot)
        if not normalized_chart.empty:
            st.line_chart(normalized_chart, width='stretch')
        else:
            st.info('Not enough price history to draw the normalized comparison chart.')
    else:
        st.info('Run the advisor first to load stock data for the normalized performance comparison.')
except Exception as e:
    st.warning(f'Could not generate normalized price chart: {str(e)}')

if 'offline_ai_messages' not in st.session_state:
    greeting = (
        build_recommendation(snapshot)
        if snapshot.get('stocks')
        else 'Run the advisor to load a watchlist and then ask follow-up questions.'
    )
    st.session_state.offline_ai_messages = [
        {'role': 'assistant', 'content': greeting}
    ]

pending_prompt = st.session_state.pop('ai_quick_prompt', None)

# Prevent duplicate processing
messages = st.session_state.get('offline_ai_messages', [])
if pending_prompt and messages and messages[-1].get('content') == pending_prompt:
    pending_prompt = None

# Display all messages
for message in st.session_state.get('offline_ai_messages', []):
    with st.chat_message(message['role']):
        st.markdown(message['content'])

# Chat input
prompt = pending_prompt or st.chat_input('Ask about the loaded stocks...')

if prompt and prompt.strip():
    try:
        # Add user message to history
        st.session_state.offline_ai_messages.append({'role': 'user', 'content': prompt})
        with st.chat_message('user'):
            st.markdown(prompt)

        # Generate response
        response = answer_prompt(prompt, snapshot)
        if not response:
            response = "I encountered an error processing your question. Please try again."
        
        # Add assistant response to history
        st.session_state.offline_ai_messages.append({'role': 'assistant', 'content': response})
        with st.chat_message('assistant'):
            st.markdown(response)
        
        # Rerun to update chat display
        st.rerun()
    except Exception as e:
        st.error(f"Error processing your question: {str(e)}")
        # Remove the failed message from history
        if st.session_state.offline_ai_messages and st.session_state.offline_ai_messages[-1]['role'] == 'user':
            st.session_state.offline_ai_messages.pop()

if st.button('Clear Chat History'):
    st.session_state.pop('offline_ai_messages', None)
    st.session_state.pop('ai_quick_prompt', None)
    st.rerun()

st.markdown('---')
st.caption('This advisor uses past return, trend versus average price, volatility, and drawdown. Past performance does not guarantee future results.')