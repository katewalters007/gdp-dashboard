import os

import streamlit as st

from auth_utils import (
    generate_and_store_temporary_password,
    is_valid_email,
    send_temporary_password_email,
)

st.set_page_config(
    page_title="Forgot Password",
    page_icon="🔐",
    layout="centered",
)

# Add custom CSS for consistent styling across all pages
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
        
        /* Alert boxes */
        .stAlert {
            border-radius: 8px !important;
            border-left: 6px solid var(--forest-blue) !important;
            background: linear-gradient(90deg, rgba(74, 144, 164, 0.1) 0%, rgba(74, 144, 164, 0.05) 100%) !important;
        }
        
        .stAlert > div {
            color: var(--dark-grey) !important;
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
        
        /* Text styling */
        .caption {
            color: var(--sage-grey) !important;
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
    """Return SMTP settings from st.secrets[smtp] or os.getenv fallback."""
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
        # Remove spaces from password (common when copied from Google)
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
    # Remove spaces from password
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


st.title("Forgot Password")
st.write("Enter the email used to create your account. If it exists, a temporary password will be emailed to you.")

with st.form("forgot_password_form"):
    email = st.text_input("Account email", placeholder="name@example.com")
    submit = st.form_submit_button("Send temporary password")

if submit:
    normalized_email = email.strip().lower()

    if not is_valid_email(normalized_email):
        st.error("Please enter a valid email address.")
    else:
        found, temporary_password = generate_and_store_temporary_password(normalized_email)

        # Always show a neutral message — do not reveal whether an account exists.
        st.info("If an account exists for that email, a temporary password has been sent.")

        if found and temporary_password:
            smtp_config = _get_smtp_config()
            if smtp_config is None:
                st.warning(
                    "⚠️ SMTP is not configured. Fill in the 'smtp' section of "
                    "`.streamlit/secrets.toml` or set environment variables (SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD)."
                )
            else:
                sent, message = send_temporary_password_email(
                    normalized_email, temporary_password, smtp_config
                )
                if sent:
                    st.success("✅ Temporary password sent! Check your email.")
                else:
                    st.error(f"❌ Email delivery failed: {message}")

st.divider()
st.caption("After receiving your temporary password, open the Reset Password page in the sidebar.")
