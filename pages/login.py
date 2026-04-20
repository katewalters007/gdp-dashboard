import streamlit as st

from page_theme import apply_page_theme, render_top_nav
from user_backend import authenticate_user, init_db

st.set_page_config(page_title="Login", layout="wide")

init_db()

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

if "watchlist_loaded_for" not in st.session_state:
    st.session_state.watchlist_loaded_for = None

apply_page_theme("Login", "Sign in to save your watchlist and transaction history.")
render_top_nav(show_analytics=False, show_sandbox=False)

if st.session_state.auth_user:
    st.success(f"You are already logged in as {st.session_state.auth_user['email']}")
    if st.button("Log out", width="stretch"):
        st.session_state.auth_user = None
        st.session_state.watchlist_loaded_for = None
        st.success("You have been logged out.")

nav_spacer_l, nav_col1, nav_col2, nav_spacer_r = st.columns([1.4, 1, 1, 1.4])
with nav_col1:
    st.page_link("pages/make_account.py", label="Create Account")
with nav_col2:
    st.page_link("pages/ai_assistant.py", label="AI Assistant")

st.page_link("pages/post_login_analytics.py", label="Open Post-Login Analytics")

st.divider()

form_spacer_l, form_col, form_spacer_r = st.columns([1.2, 2, 1.2])
with form_col:
    with st.form("login_form"):
        login_email = st.text_input("Email")
        login_password = st.text_input("Password", type="password")
        login_submit = st.form_submit_button("Login", width="stretch")

if login_submit:
    user = authenticate_user(login_email, login_password)
    if user:
        st.session_state.auth_user = user
        st.success("Login successful.")
        st.switch_page("pages/post_login_analytics.py")
    else:
        st.error("Invalid email or password.")
