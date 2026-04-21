import streamlit as st
import pandas as pd

from analytics_utils import build_profit_analytics
from page_theme import apply_page_theme, render_top_nav
from user_backend import get_transactions, init_db


st.set_page_config(page_title='Post-Login Analytics', layout='wide')

init_db()

if 'auth_user' not in st.session_state:
    st.session_state.auth_user = None

apply_page_theme('Post-Login Analytics', 'Track realized profit, estimated taxes, and net performance over time.')
render_top_nav()

nav_spacer_l, nav_col1, nav_col2, nav_col3, nav_spacer_r = st.columns([1, 1, 1, 1, 1])
with nav_col1:
    st.page_link('pages/login.py', label='Login')
with nav_col2:
    st.page_link('pages/ai_assistant.py', label='AI Assistant')
with nav_col3:
    st.page_link('pages/trading_sandbox.py', label='Trading Sandbox')

if not st.session_state.auth_user:
    st.warning('Please log in to view your analytics dashboard.')
    st.stop()

current_user = st.session_state.auth_user
st.success(f"Signed in as {current_user['email']}")

transactions = get_transactions(current_user['id'])
if not transactions:
    st.info('No transactions available yet. Add transactions in the Stock Tracker page to unlock analytics.')
    st.stop()

analytics_df = build_profit_analytics(transactions)
if analytics_df.empty:
    st.info('Not enough data to compute analytics yet.')
    st.stop()

total_realized_profit = float(analytics_df['realized_profit'].sum())
total_estimated_tax = float(analytics_df['estimated_tax'].sum())
total_net_profit = float(analytics_df['net_profit'].sum())

metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_col1.metric('Total Realized Profit', f'${total_realized_profit:,.2f}')
metric_col2.metric('Estimated Tax', f'${total_estimated_tax:,.2f}')
metric_col3.metric('Total Net Profit', f'${total_net_profit:,.2f}')

st.caption('Estimated tax is calculated per transaction using each transaction\'s selected tax area and tax rate.')

area_summary = (
    analytics_df.groupby('tax_area', as_index=False)
    .agg(
        realized_profit=('realized_profit', 'sum'),
        estimated_tax=('estimated_tax', 'sum'),
        net_profit=('net_profit', 'sum'),
    )
    .sort_values('net_profit', ascending=False)
)
st.markdown('**Tax Area Summary**')
st.dataframe(area_summary, width='stretch', hide_index=True)

st.markdown('**Profit Over Time**')
chart_df = analytics_df.copy()
chart_df['trade_date'] = pd.to_datetime(chart_df['trade_date'], errors='coerce')
chart_df = chart_df.sort_values('trade_date')
chart_df = chart_df.dropna(subset=['trade_date'])

if chart_df.empty:
    st.info('No valid transaction dates available for charting.')
else:
    chart_series = chart_df.set_index('trade_date')['cumulative_net_profit']
    st.line_chart(chart_series, width='stretch')

st.markdown('**Transaction Profit Details**')
detail_cols = [
    'trade_date',
    'ticker',
    'action',
    'quantity',
    'price',
    'tax_area',
    'tax_rate_pct',
    'realized_profit',
    'estimated_tax',
    'net_profit',
    'cumulative_net_profit',
]
st.dataframe(analytics_df[detail_cols], width='stretch', hide_index=True)
