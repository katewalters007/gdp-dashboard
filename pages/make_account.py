import streamlit as st

from page_theme import apply_page_theme, render_top_nav
from user_backend import create_user, init_db

st.set_page_config(page_title="Create Account", layout="wide")

init_db()

apply_page_theme("Create Account", "Create an account to save your watchlist and transactions.")
render_top_nav(show_analytics=False, show_sandbox=False)

nav_spacer_l, nav_col1, nav_col2, nav_spacer_r = st.columns([1.4, 1, 1, 1.4])
with nav_col1:
    st.page_link("pages/login.py", label="Login")
with nav_col2:
    st.page_link("pages/ai_assistant.py", label="AI Assistant")

st.divider()

form_spacer_l, form_col, form_spacer_r = st.columns([1.2, 2, 1.2])
with form_col:
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
