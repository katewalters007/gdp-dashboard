import streamlit as st

from page_theme import apply_page_theme, render_top_nav
from user_backend import init_db, create_user, authenticate_user

st.set_page_config(page_title="Login", layout="wide")

init_db()

if "auth_user" not in st.session_state:
    st.session_state.auth_user = None

apply_page_theme("Login", "Sign in to save your watchlist and transaction history.")
render_top_nav(show_analytics=False, show_sandbox=False, show_ai=False)

if st.session_state.auth_user:
    st.success(f"You are already logged in as {st.session_state.auth_user['email']}")
    if st.button("Log out", width="stretch"):
        st.session_state.auth_user = None
        st.session_state.watchlist_loaded_for = None
        st.success("You have been logged out.")

nav_spacer_l, nav_col1, nav_spacer_r = st.columns([1.4, 1, 1.4])
with nav_col1:
    st.page_link("pages/Ai_Assistant.py", label="AI Assistant")

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
                st.switch_page("streamlit_app.py")
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
                user_id = create_user(reg_email, reg_password)
                if user_id:
                    st.session_state.auth_user = {"id": user_id, "email": reg_email}
                    st.success("Account created. You can now log in.")
                    st.switch_page("streamlit_app.py")
                else:
                    st.error("An account with this email already exists.")import os

import streamlit as st

from auth_utils import (
    authenticate_user,
    create_user,
    generate_and_store_temporary_password,
    get_user_by_email,
    is_valid_email,
    reset_password_with_temporary,
    send_password_changed_notification,
    send_temporary_password_email,
)

st.set_page_config(
    page_title='Account Access',
    page_icon='🔑',
    layout='wide',
)

st.markdown(r"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;600;700&display=swap');

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

        body {
            background: linear-gradient(135deg, #F5F3F0 0%, #EBF3F7 100%);
            color: var(--dark-grey);
        }

        h1, h2 {
            font-family: 'Playfair Display', serif !important;
            letter-spacing: 1.5px;
        }

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

        input, textarea, [data-testid="stDateInput"] {
            border: 2px solid var(--light-grey) !important;
            border-radius: 6px !important;
            background-color: white !important;
        }

        input:focus, textarea:focus {
            border-color: var(--forest-blue) !important;
            box-shadow: 0 0 0 3px rgba(74, 144, 164, 0.15) !important;
        }

        hr {
            background: linear-gradient(90deg, var(--earth-brown) 0%, transparent 50%, var(--forest-blue) 100%) !important;
            height: 2px !important;
            opacity: 0.6;
        }

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

        .stAlert {
            border-radius: 8px !important;
            border-left: 6px solid var(--forest-blue) !important;
            background: linear-gradient(90deg, rgba(74, 144, 164, 0.1) 0%, rgba(74, 144, 164, 0.05) 100%) !important;
        }

        .stAlert > div {
            color: var(--dark-grey) !important;
        }

        .caption {
            color: var(--sage-grey) !important;
        }

        /* Tab styling */
        [data-testid="stTabs"] button {
            color: var(--dark-grey) !important;
        }

        [data-testid="stTabs"] button:hover {
            color: var(--forest-green) !important;
            border-bottom-color: var(--forest-blue) !important;
        }

        @media (prefers-color-scheme: dark) {
            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"] {
                background: linear-gradient(180deg, #0F1A22 0%, #162631 100%) !important;
                color: #F3F1EC !important;
            }

            p, label, span, div, li, small, .stMarkdown, .stMarkdownContainer,
            [data-testid="stMetricLabel"],
            [data-testid="stMetricValue"],
            [data-testid="stMetricDelta"],
            [data-testid="stSidebar"] * {
                color: #F3F1EC !important;
            }

            h1, h2, h3, h4, h5, h6 {
                color: #F4E7CE !important;
            }

            .main, [data-testid="stVerticalBlock"] > div {
                background: linear-gradient(180deg, rgba(20, 32, 41, 0.96) 0%, rgba(30, 45, 56, 0.96) 100%) !important;
            }

            [data-testid="stSidebar"] {
                background: #000000 !important;
            }

            input, textarea, [data-testid="stDateInput"], [data-baseweb="input"] input {
                background-color: #1E2D38 !important;
                color: #F3F1EC !important;
                border-color: #456173 !important;
            }

            a, [data-testid="stSidebar"] a {
                color: #9FD3E6 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)


def _get_smtp_config() -> dict | None:
    try:
        s = st.secrets["smtp"]
        cfg = {
            "host": s["host"],
            "port": s.get("port", 587),
            "username": s["username"],
            "password": s["password"],
            "from_address": s.get("from_address") or s["username"],
            "use_ssl": s.get("use_ssl", False),
        }
        if " " in cfg["password"]:
            cfg["password"] = cfg["password"].replace(" ", "")
        return cfg
    except (KeyError, FileNotFoundError):
        pass

    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    if not all([host, username, password]):
        return None
    if " " in password:
        password = password.replace(" ", "")
    return {
        "host": host,
        "port": int(os.getenv("SMTP_PORT", "587").strip()),
        "username": username,
        "password": password,
        "from_address": os.getenv("SMTP_FROM", "").strip() or username,
        "use_ssl": os.getenv("SMTP_USE_SSL", "false").lower() == "true",
    }

st.title("Account Access")
st.write("Use the tabs below to sign in, create a new account, or request a temporary password.")

tabs = st.tabs(["Sign In", "Create Account", "Forgot Password", "Reset Password"])

with tabs[0]:
    with st.form("login_form"):
        login_email = st.text_input("Email", key="login_email", placeholder="name@example.com")
        login_password = st.text_input("Password", type="password", key="login_password")
        login_submit = st.form_submit_button("Sign In")

    if login_submit:
        normalized_email = login_email.strip().lower()
        if not is_valid_email(normalized_email):
            st.error("Please enter a valid email address.")
        elif not login_password:
            st.error("Password is required.")
        else:
            success, message = authenticate_user(normalized_email, login_password)
            if success:
                user = get_user_by_email(normalized_email)
                st.session_state.auth_user = user
                st.session_state.authenticated_user_email = normalized_email
                st.success(message)
                st.switch_page("streamlit_app.py")
            else:
                st.error(message)

with tabs[1]:
    with st.form("create_account_form"):
        signup_email = st.text_input("Email", key="signup_email", placeholder="name@example.com")
        signup_password = st.text_input("Password", type="password", key="signup_password")
        signup_confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        signup_submit = st.form_submit_button("Create Account")

    if signup_submit:
        normalized_email = signup_email.strip().lower()
        if not is_valid_email(normalized_email):
            st.error("Please enter a valid email address.")
        elif signup_password != signup_confirm_password:
            st.error("Passwords do not match.")
        else:
            success, message = create_user(normalized_email, signup_password)
            if success:
                user = get_user_by_email(normalized_email)
                st.session_state.auth_user = user
                st.session_state.authenticated_user_email = normalized_email
                st.success(message)
                st.switch_page("streamlit_app.py")
            else:
                st.error(message)

with tabs[2]:
    st.write("Enter the email used for your account. If it exists, a temporary password will be sent.")
    with st.form("forgot_password_form"):
        forgot_email = st.text_input("Account email", key="forgot_email", placeholder="name@example.com")
        forgot_submit = st.form_submit_button("Send Temporary Password")

    if forgot_submit:
        normalized_email = forgot_email.strip().lower()
        if not is_valid_email(normalized_email):
            st.error("Please enter a valid email address.")
        else:
            found, temporary_password = generate_and_store_temporary_password(normalized_email)
            st.info("If an account exists for that email, a temporary password has been sent.")

            if found and temporary_password:
                smtp_config = _get_smtp_config()
                if smtp_config is None:
                    st.warning(
                        "⚠️ SMTP is not configured. Fill in the 'smtp' section of `.streamlit/secrets.toml` or set environment variables (SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD)."
                    )
                else:
                    sent, message = send_temporary_password_email(
                        normalized_email, temporary_password, smtp_config
                    )
                    if sent:
                        st.success("✅ Temporary password sent! Check your email.")
                    else:
                        st.error(f"❌ Email delivery failed: {message}")

    st.caption("After receiving your temporary password, return to the Sign In tab and log in with the temporary password.")

with tabs[3]:
    st.write("Use the temporary password sent to your email, then choose a new password.")
    with st.form("reset_password_form"):
        reset_email = st.text_input("Email", key="reset_email", placeholder="name@example.com")
        reset_temporary_password = st.text_input("Temporary password", type="password", key="reset_temporary_password")
        reset_new_password = st.text_input("New password", type="password", key="reset_new_password")
        reset_confirm_password = st.text_input("Confirm new password", type="password", key="reset_confirm_password")
        reset_submit = st.form_submit_button("Reset Password")

    if reset_submit:
        normalized_email = reset_email.strip().lower()

        if not is_valid_email(normalized_email):
            st.error("Please enter a valid email address.")
        elif not reset_temporary_password:
            st.error("Temporary password is required.")
        elif reset_new_password != reset_confirm_password:
            st.error("New password and confirmation do not match.")
        else:
            success, message = reset_password_with_temporary(
                normalized_email,
                reset_temporary_password,
                reset_new_password,
            )
            if success:
                st.success("Your password has been reset successfully.")
                smtp_config = _get_smtp_config()
                if smtp_config:
                    sent, info_message = send_password_changed_notification(normalized_email, smtp_config)
                    if sent:
                        st.info(f"A confirmation email has been sent to {normalized_email}.")
                st.info("Return to the Sign In tab to log in with your new password.")
            else:
                st.error(message)

    st.caption("If you need a temporary password, use the Forgot Password tab first.")

