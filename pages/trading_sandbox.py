import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json

from page_theme import apply_page_theme, render_top_nav
from user_backend import (
    init_db,
    get_user_strategies,
    save_user_strategy,
    update_user_strategy,
    delete_user_strategy,
)


st.set_page_config(page_title='Trading Strategy Sandbox', layout='wide')

init_db()

if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

apply_page_theme('Trading Strategy Sandbox', 'Test and create custom trading strategies on historical data.')
render_top_nav(show_sandbox=False)

nav_spacer_l, nav_col1, nav_col2, nav_spacer_r = st.columns([1, 1, 1, 1])
with nav_col1:
    st.page_link('pages/Ai_Assistant.py', label='AI Assistant')
with nav_col2:
    st.page_link('pages/post_login_analytics.py', label='Analytics')

if not st.session_state.auth_user:
    st.warning('Please log in to access the trading strategy sandbox.')
    st.stop()

current_user = st.session_state.auth_user
st.success(f"Signed in as {current_user['email']}")

# Utility functions for indicators
def calculate_sma(data, period):
    return data.rolling(window=period).mean()

def calculate_rsi(data, period=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Predefined strategies
PREDEFINED_STRATEGIES = {
    'MA Crossover': {
        'description': 'Buy when short MA crosses above long MA, sell when below.',
        'parameters': {'short_period': 10, 'long_period': 50},
    },
    'RSI Oversold': {
        'description': 'Buy when RSI < 30, sell when RSI > 70.',
        'parameters': {'rsi_period': 14, 'oversold': 30, 'overbought': 70},
    },
    'Simple MA': {
        'description': 'Buy when price > MA, sell when price < MA.',
        'parameters': {'ma_period': 20},
    },
}

# Backtest function
def backtest_strategy(data, strategy_type, params, initial_cash=10000):
    cash = initial_cash
    position = 0  # shares
    trades = []
    portfolio_values = []

    close_prices = data['Close']
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.squeeze(axis=1)
        if isinstance(close_prices, pd.DataFrame):
            close_prices = close_prices.iloc[:, 0]

    if strategy_type == 'MA Crossover':
        short_ma = calculate_sma(close_prices, params['short_period'])
        long_ma = calculate_sma(close_prices, params['long_period'])
        signal = (short_ma > long_ma).astype(int) - (short_ma < long_ma).astype(int)
        signal = signal.fillna(0)
    elif strategy_type == 'RSI Oversold':
        rsi = calculate_rsi(close_prices, params['rsi_period'])
        signal = pd.Series(0, index=data.index)
        signal[rsi < params['oversold']] = 1
        signal[rsi > params['overbought']] = -1
        signal = signal.fillna(0)
    elif strategy_type == 'Simple MA':
        ma = calculate_sma(close_prices, params['ma_period'])
        signal = (close_prices > ma).astype(int) - (close_prices < ma).astype(int)
        signal = signal.fillna(0)
    else:
        return None, None, None

    if isinstance(signal, pd.DataFrame):
        signal = signal.squeeze()
    signal = signal.astype(int)

    for i in range(1, len(data)):
        date = data.index[i]
        price = close_prices.iloc[i]
        prev_signal = int(signal.iloc[i-1]) if i > 0 else 0
        curr_signal = int(signal.iloc[i])

        # Execute trades
        if curr_signal == 1 and position == 0:  # Buy
            shares = int(cash // price)
            if shares > 0:
                cash -= shares * price
                position += shares
                trades.append({'date': date, 'action': 'BUY', 'shares': shares, 'price': price, 'cash': cash, 'position': position})
        elif curr_signal == -1 and position > 0:  # Sell
            cash += position * price
            trades.append({'date': date, 'action': 'SELL', 'shares': position, 'price': price, 'cash': cash, 'position': 0})
            position = 0

        portfolio_value = cash + position * price
        portfolio_values.append({'date': date, 'portfolio_value': portfolio_value, 'cash': cash, 'position': position})

    return pd.DataFrame(trades), pd.DataFrame(portfolio_values), cash + position * close_prices.iloc[-1] if not data.empty else initial_cash

# Main UI
st.header('Trading Strategy Sandbox')

if 'edit_strategy' in st.session_state:
    with st.container(border=True):
        strat = st.session_state.edit_strategy
        st.subheader(f'Editing: {strat["name"]}')
        edit_name = st.text_input('Name', value=strat['name'], key='edit_name')
        edit_desc = st.text_area('Description', value=strat['description'], key='edit_desc')
        edit_type = st.selectbox('Type', list(PREDEFINED_STRATEGIES.keys()), index=list(PREDEFINED_STRATEGIES.keys()).index(strat['strategy_type']), key='edit_type')
        edit_params = {}
        base_params = PREDEFINED_STRATEGIES[edit_type]['parameters']
        for param, default in base_params.items():
            current_val = strat['parameters'].get(param, default)
            edit_params[param] = st.number_input(f'{param.replace("_", " ").title()}', value=current_val, key=f'edit_{param}')
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Update Strategy'):
                update_user_strategy(strat['id'], current_user['id'], edit_name, edit_desc, edit_type, edit_params)
                st.success('Strategy updated!')
                del st.session_state.edit_strategy
                st.rerun()
        with col2:
            if st.button('Cancel'):
                del st.session_state.edit_strategy
                st.rerun()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader('Strategy Setup')
    
    ticker = st.text_input('Stock Ticker', value='AAPL').upper()
    start_date = st.date_input('Start Date', value=datetime.now() - timedelta(days=365))
    end_date = st.date_input('End Date', value=datetime.now())
    initial_cash = st.number_input('Initial Cash ($)', value=10000, min_value=1000, step=1000)
    
    strategy_tabs = st.tabs(['Predefined', 'My Strategies', 'Create New'])
    
    selected_strategy = None
    strategy_params = {}
    
    with strategy_tabs[0]:
        st.write('Choose a predefined strategy:')
        for name, info in PREDEFINED_STRATEGIES.items():
            if st.button(f'Select {name}', key=f'predef_{name}'):
                selected_strategy = name
                strategy_params = info['parameters'].copy()
                st.session_state.selected_strategy = selected_strategy
                st.session_state.strategy_params = strategy_params
                st.rerun()
    
    with strategy_tabs[1]:
        user_strategies = get_user_strategies(current_user['id'])
        if user_strategies:
            for strat in user_strategies:
                strat_col1, strat_col2, strat_col3 = st.columns([3, 1, 1])
                with strat_col1:
                    if st.button(f'Select {strat["name"]}', key=f'user_{strat["id"]}'):
                        selected_strategy = strat['strategy_type']
                        strategy_params = strat['parameters'].copy()
                        st.session_state.selected_strategy = selected_strategy
                        st.session_state.strategy_params = strategy_params
                        st.rerun()
                with strat_col2:
                    if st.button('Edit', key=f'edit_{strat["id"]}'):
                        st.session_state.edit_strategy = strat
                        st.rerun()
                with strat_col3:
                    if st.button('Delete', key=f'del_{strat["id"]}'):
                        delete_user_strategy(strat['id'], current_user['id'])
                        st.success('Strategy deleted!')
                        st.rerun()
        else:
            st.info('No saved strategies yet. Create one in the "Create New" tab.')
    
    with strategy_tabs[2]:
        new_name = st.text_input('Strategy Name')
        new_desc = st.text_area('Description')
        new_type = st.selectbox('Strategy Type', list(PREDEFINED_STRATEGIES.keys()))
        if new_type:
            base_params = PREDEFINED_STRATEGIES[new_type]['parameters']
            edited_params = {}
            for param, default in base_params.items():
                edited_params[param] = st.number_input(f'{param.replace("_", " ").title()}', value=default, key=f'new_{param}')
            if st.button('Save Strategy'):
                save_user_strategy(current_user['id'], new_name, new_desc, new_type, edited_params)
                st.success('Strategy saved!')
                st.rerun()

# Handle editing
# Get selected strategy from session
if 'selected_strategy' in st.session_state:
    selected_strategy = st.session_state.selected_strategy
    strategy_params = st.session_state.strategy_params

with col2:
    if selected_strategy:
        st.subheader(f'Backtesting: {selected_strategy}')
        
        # Edit parameters
        st.write('Adjust parameters:')
        for param in strategy_params:
            strategy_params[param] = st.number_input(
                param.replace('_', ' ').title(),
                value=strategy_params[param],
                key=f'param_{param}'
            )
        
        if st.button('Run Backtest'):
            # Fetch data
            data = yf.download(ticker, start=start_date, end=end_date)
            if data.empty:
                st.error('No data found for this ticker and date range.')
            else:
                trades_df, portfolio_df, final_value = backtest_strategy(data, selected_strategy, strategy_params, initial_cash)
                
                if trades_df is not None:
                    st.subheader('Performance Summary')
                    total_return = (final_value - initial_cash) / initial_cash * 100
                    st.metric('Total Return', f'{total_return:.2f}%')
                    st.metric('Final Portfolio Value', f'${final_value:.2f}')
                    
                    if not portfolio_df.empty:
                        st.line_chart(portfolio_df.set_index('date')['portfolio_value'], width='stretch')
                    
                    st.subheader('Trades')
                    if not trades_df.empty:
                        st.dataframe(trades_df)
                    else:
                        st.info('No trades were triggered by this strategy in the selected period. '
                                'Try adjusting the parameters or extending the date range.')
                else:
                    st.error('Strategy not supported.')
    else:
        st.info('Select a strategy to start backtesting.')