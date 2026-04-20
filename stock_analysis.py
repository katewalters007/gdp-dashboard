from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import yfinance as yf


DEFAULT_STOCK_UNIVERSES = {
    'Magnificent 7': ['AAPL', 'AMZN', 'GOOGL', 'META', 'MSFT', 'NVDA', 'TSLA'],
    'AI and Chips': ['AMD', 'AVGO', 'GOOGL', 'META', 'MSFT', 'MU', 'NVDA', 'TSM'],
    'Broad ETFs': ['DIA', 'IVV', 'QQQ', 'SPY', 'VGT', 'VTI'],
    'Dividend Leaders': ['ABBV', 'COST', 'JNJ', 'KO', 'PG', 'PEP', 'WMT', 'XOM'],
}

DEFAULT_SUGGESTED_UNIVERSE = ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL', 'AMZN', 'NFLX', 'SPY', 'QQQ']


def normalize_tickers(raw_value):
    if isinstance(raw_value, str):
        values = raw_value.split(',')
    else:
        values = raw_value or []

    cleaned = []
    for item in values:
        ticker = str(item).strip().upper()
        if ticker and ticker not in cleaned:
            cleaned.append(ticker)
    return cleaned


@st.cache_data(ttl='1h')
def get_stock_data(ticker, start_date, end_date):
    try:
        stock_data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if stock_data.empty:
            return None
        return stock_data
    except Exception:
        return None


@st.cache_data(ttl='1h')
def get_bulk_stock_data(tickers, start_date, end_date):
    ticker_data = {}
    for ticker in normalize_tickers(tickers):
        stock_data = get_stock_data(ticker, start_date, end_date)
        if stock_data is not None:
            ticker_data[ticker] = stock_data
    return ticker_data


def build_analysis_summary(ticker_data):
    summary = []

    for ticker, stock_data in ticker_data.items():
        close_prices = stock_data['Close'].dropna()
        if close_prices.empty:
            continue

        current_price = close_prices.iloc[-1].item()
        start_price = close_prices.iloc[0].item()
        high_price = stock_data['High'].max().item()
        low_price = stock_data['Low'].min().item()
        average_price = close_prices.mean().item()
        percent_change = ((current_price - start_price) / start_price) * 100 if start_price else 0.0
        daily_returns = close_prices.pct_change().dropna()
        if isinstance(daily_returns, pd.DataFrame):
            daily_returns = daily_returns.iloc[:, 0]
        daily_returns = pd.to_numeric(daily_returns, errors='coerce').dropna()
        volatility = daily_returns.std() if not daily_returns.empty else 0.0
        if isinstance(volatility, pd.Series):
            volatility = volatility.iloc[0] if not volatility.empty else 0.0
        annualized_volatility = float(volatility) * (252 ** 0.5) * 100 if volatility else 0.0
        drawdown_pct = ((current_price - high_price) / high_price) * 100 if high_price else 0.0
        trend_vs_average = ((current_price - average_price) / average_price) * 100 if average_price else 0.0

        composite_score = (
            percent_change
            + (trend_vs_average * 0.35)
            - (annualized_volatility * 0.25)
            + (drawdown_pct * 0.15)
        )

        summary.append({
            'ticker': ticker,
            'current_price': float(current_price),
            'start_price': float(start_price),
            'percent_change': float(percent_change),
            'high_price': float(high_price),
            'low_price': float(low_price),
            'average_price': float(average_price),
            'volatility_pct': float(annualized_volatility),
            'drawdown_pct': float(drawdown_pct),
            'trend_vs_average_pct': float(trend_vs_average),
            'score': float(composite_score),
        })

    return sorted(summary, key=lambda item: item['score'], reverse=True)


def build_combined_close_data(ticker_data):
    combined_data = pd.DataFrame()

    for ticker, stock_data in ticker_data.items():
        stock_data_copy = stock_data[['Close']].copy()
        stock_data_copy.columns = [ticker]
        if combined_data.empty:
            combined_data = stock_data_copy
        else:
            combined_data = combined_data.join(stock_data_copy, how='outer')

    return combined_data


def build_analysis_snapshot(ticker_data, start_date, end_date, selected_tickers):
    analysis_summary = build_analysis_summary(ticker_data)
    return {
        'generated_at': datetime.now().isoformat(),
        'start_date': str(start_date),
        'end_date': str(end_date),
        'selected_tickers': normalize_tickers(selected_tickers),
        'stocks': analysis_summary,
        'top_pick': analysis_summary[0]['ticker'] if analysis_summary else None,
    }


@st.cache_data(ttl='1h')
def get_top_performers(tickers_list, lookback_days=365, top_n=5):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    ticker_data = get_bulk_stock_data(tickers_list, start_date, end_date)
    analysis_summary = build_analysis_summary(ticker_data)
    return [item['ticker'] for item in analysis_summary[:top_n]]


@st.cache_data(ttl='1h')
def get_suggested_stocks(tickers_list=None, lookback_days=365, top_n=5):
    base_universe = tickers_list or DEFAULT_SUGGESTED_UNIVERSE
    top_tickers = get_top_performers(base_universe, lookback_days=lookback_days, top_n=top_n)
    return top_tickers or DEFAULT_SUGGESTED_UNIVERSE[:top_n]