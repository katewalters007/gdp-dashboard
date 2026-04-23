import streamlit as st


def apply_page_theme(page_title, subtitle=None):
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;600;700&display=swap');

            :root {
                --forest-green: #1B4332;
                --deep-green: #2D6A4F;
                --forest-blue: #4A90A4;
                --light-grey: #D4DCDE;
                --dark-grey: #3A3A3A;
                --cream: #F5F3F0;
                --blue-wash: #EBF3F7;
                --brown-wash: #F4EDE3;
            }

            body {
                background: linear-gradient(135deg, var(--cream) 0%, var(--blue-wash) 100%);
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

            .stButton > button {
                background: linear-gradient(135deg, var(--deep-green) 0%, var(--forest-green) 100%) !important;
                color: white !important;
                border: 2px solid var(--forest-green) !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
            }

            input, textarea, [data-testid="stDateInput"] {
                border: 2px solid var(--light-grey) !important;
                border-radius: 6px !important;
                background-color: white !important;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, var(--brown-wash) 0%, var(--blue-wash) 100%);
            }

            [data-testid="metric-container"] {
                background: linear-gradient(135deg, #F9F7F5 0%, var(--blue-wash) 100%);
                border-left: 6px solid #8B5A3C;
                border-radius: 10px;
                padding: 14px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <h1 style='font-family: "Playfair Display", serif; text-align: center; letter-spacing: 2px; font-size: 48px; color: #1B4332;'>
            {page_title}
        </h1>
        """,
        unsafe_allow_html=True,
    )

    if subtitle:
        st.markdown(
            f"<p style='text-align: center; color: #3A3A3A; font-size: 14px;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )

    st.divider()


def render_top_nav(show_analytics=True, show_sandbox=True):
    left, c1, c2, c3, c4, right = st.columns([0.8, 1, 1, 1, 1, 0.8])
    with c1:
        st.page_link("streamlit_app.py", label="Stock Tracker")
    with c2:
        st.page_link("pages/Login.py", label="Login")
    with c3:
        if show_analytics:
            st.page_link("pages/post_login_analytics.py", label="Analytics")
    with c4:
        if show_sandbox:
            st.page_link("pages/trading_sandbox.py", label="Trading Sandbox")
