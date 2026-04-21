import os

import openai
import streamlit as st

from page_theme import apply_page_theme, render_top_nav


st.set_page_config(page_title='AI Assistant', layout='wide')

apply_page_theme('AI Assistant', 'Ask about stocks, market trends, and portfolio ideas.')
render_top_nav()

nav_spacer_l, nav_col1, nav_col2, nav_col3, nav_spacer_r = st.columns([1, 1, 1, 1, 1])
with nav_col1:
    st.page_link('pages/login.py', label='Login')
with nav_col2:
    st.page_link('pages/post_login_analytics.py', label='Analytics')
with nav_col3:
    st.page_link('pages/trading_sandbox.py', label='Trading Sandbox')

openai_api_key = os.getenv('OPENAI_API_KEY') or st.secrets.get('openai_api_key')

if not openai_api_key:
    st.error('Please set your OpenAI API key in environment variables or Streamlit secrets.')
    st.info(
        'To get an API key: 1) Visit https://platform.openai.com/api-keys 2) Create a key '
        '3) Set OPENAI_API_KEY or add openai_api_key to .streamlit/secrets.toml'
    )
    st.stop()

client = openai.OpenAI(api_key=openai_api_key)

if 'messages' not in st.session_state:
    st.session_state.messages = [
        {
            'role': 'system',
            'content': (
                'You are a helpful AI assistant specializing in stock market analysis, investment strategies, '
                'and financial education. Provide clear educational guidance and remind users to do their own '
                'research and consult professionals for financial decisions.'
            ),
        }
    ]

for message in st.session_state.messages[1:]:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input('Ask me about stocks...'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    with st.chat_message('user'):
        st.markdown(prompt)

    with st.chat_message('assistant'):
        try:
            response = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=st.session_state.messages,
                max_tokens=500,
                temperature=0.7,
            )

            ai_response = response.choices[0].message.content
            st.markdown(ai_response)
            st.session_state.messages.append({'role': 'assistant', 'content': ai_response})

        except Exception as e:
            st.error(f'Error getting AI response: {str(e)}')
            st.info('Please check your API key and try again.')

if st.button('Clear Chat History', width='stretch'):
    st.session_state.messages = [st.session_state.messages[0]]
    st.rerun()

st.markdown('---')
st.caption('This AI assistant provides educational information only and is not financial advice.')
