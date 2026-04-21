import streamlit as st

from page_theme import apply_page_theme, render_top_nav
from user_backend import authenticate_user, create_user, init_db

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

nav_spacer_l, nav_col1, nav_spacer_r = st.columns([1.4, 1, 1.4])
with nav_col1:
    st.page_link("pages/ai_assistant.py", label="AI Assistant")

st.page_link("pages/post_login_analytics.py", label="Open Post-Login Analytics")

st.divider()

form_spacer_l, form_col, form_spacer_r = st.columns([1.2, 2, 1.2])
with form_col:
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
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
    
    with tab2:
        with st.form("register_form"):
            reg_email = st.text_input("Email")
            reg_password = st.text_input("Password", type="password")
            reg_confirm = st.text_input("Confirm password", type="password")
            reg_submit = st.form_submit_button("Create Account", width="stretch")

        if reg_submit:
            if not reg_email or "@" not in reg_email:
                st.error("Enter a valid email address.")
            elif len(reg_password) < 8:
                st.error("Password must be at least 8 characters.")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match.")
            else:
                new_user_id = create_user(reg_email, reg_password)
                if new_user_id is None:
                    st.error("An account with this email already exists.")
                else:
                    st.success("Account created. You can now log in.")
                    st.switch_page("pages/login.py")
