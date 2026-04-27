import streamlit as st

from auth_utils import (
    create_price_alert,
    delete_price_alert,
    get_user_alerts,
)

st.set_page_config(
    page_title="Price Alerts",
    page_icon="🔔",
    layout="wide",
)

# Apply the same styling as other pages
st.markdown("""
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

        h2 {
            color: var(--deep-green) !important;
            border-left: 5px solid var(--forest-blue);
            padding-left: 12px;
        }

        h3 {
            color: var(--earth-brown) !important;
        }

        .main {
            background: linear-gradient(180deg, #F5F3F0 0%, #EBF3F7 100%);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #F4EDE3 0%, #F0F3F4 100%);
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

        [data-testid="stAlert"] {
            border-radius: 8px !important;
            border-left: 6px solid var(--forest-blue) !important;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --dark-surface: #142029;
                --dark-panel: #1E2D38;
                --dark-panel-alt: #243845;
                --dark-border: #456173;
                --dark-text: #F3F1EC;
                --dark-muted: #D7E0E3;
            }

            body,
            .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stHeader"] {
                background: linear-gradient(180deg, #0F1A22 0%, #162631 100%) !important;
                color: var(--dark-text) !important;
            }

            p,
            label,
            span,
            div,
            li,
            small {
                color: var(--dark-text) !important;
            }

            h1,
            h2,
            h3,
            h4,
            h5,
            h6 {
                color: #F4E7CE !important;
            }

            input,
            textarea,
            [data-testid="stDateInput"],
            [data-baseweb="input"] input {
                background-color: var(--dark-panel) !important;
                color: var(--dark-text) !important;
                border-color: var(--dark-border) !important;
            }

            a,
            [data-testid="stSidebar"] a {
                color: #9FD3E6 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.title("🔔 Price Alerts")
st.markdown(
    "Set up email notifications when your favorite stocks reach specific price points. "
    "Alerts are checked every 5-10 minutes and you'll receive an email when triggered."
)

# Check if user is logged in (you'll need to integrate with your Login page session state)
if "user_email" not in st.session_state:
    st.warning("Please log in to manage price alerts. Visit the Login page first.")
    st.stop()

user_email = st.session_state.user_email

# Create new alert
with st.container(border=True):
    st.subheader("Create New Alert")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ticker = st.text_input(
            "Stock Ticker",
            placeholder="e.g., AAPL",
            help="Enter the stock symbol (e.g., AAPL, GOOGL, MSFT)"
        ).upper()
    
    with col2:
        alert_type = st.selectbox(
            "Alert Type",
            ["above", "below"],
            help="Trigger when price goes above or below the threshold"
        )
    
    with col3:
        price_threshold = st.number_input(
            "Price Threshold ($)",
            min_value=0.01,
            max_value=10000.0,
            step=1.0,
            help="Price level that will trigger the alert"
        )
    
    with col4:
        create_clicked = st.button("Create Alert", width="stretch")
    
    if create_clicked:
        if not ticker or len(ticker) < 1:
            st.error("Please enter a valid ticker symbol")
        elif price_threshold <= 0:
            st.error("Price threshold must be greater than $0")
        else:
            success, message = create_price_alert(user_email, ticker, alert_type, price_threshold)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# Display existing alerts
st.subheader("Your Active Alerts")

alerts = get_user_alerts(user_email)
active_alerts = [a for a in alerts if a.get("active")]
triggered_alerts = [a for a in alerts if a.get("triggered")]

if not active_alerts and not triggered_alerts:
    st.info("No alerts created yet. Set up an alert above to get started!")
else:
    # Active alerts
    if active_alerts:
        st.markdown("#### Active Alerts")
        for idx, alert in enumerate(active_alerts):
            col1, col2, col3, col4, col5 = st.columns([1, 1.2, 1, 2, 1])
            
            with col1:
                st.metric("Ticker", alert.get("ticker"))
            
            with col2:
                alert_type = alert.get("alert_type", "unknown")
                threshold = alert.get("price_threshold", 0)
                st.metric("Condition", f"{alert_type.title()} ${threshold:.2f}")
            
            with col3:
                created = alert.get("created_at", "")[:10]
                st.caption(f"Created: {created}")
            
            with col4:
                st.caption("Alert will trigger when price condition is met")
            
            with col5:
                if st.button("Delete", key=f"delete_{idx}", use_container_width=True):
                    success, message = delete_price_alert(user_email, idx)
                    if success:
                        st.success("Alert deleted!")
                        st.rerun()
                    else:
                        st.error(message)
    
    # Triggered alerts (history)
    if triggered_alerts:
        st.divider()
        st.markdown("#### Triggered Alerts (History)")
        
        for idx, alert in enumerate(triggered_alerts):
            triggered_price = alert.get("triggered_price")
            triggered_at = alert.get("triggered_at", "")[:10]
            threshold = alert.get("price_threshold")
            alert_type = alert.get("alert_type")
            
            st.success(
                f"✅ {alert.get('ticker')} triggered on {triggered_at} "
                f"when price went {alert_type} ${threshold:.2f} "
                f"(actual: ${triggered_price:.2f})"
            )

# Setup instructions
with st.expander("📋 Setup Instructions"):
    st.markdown("""
    ### How Price Alerts Work
    
    1. **Create an Alert**: Set a stock ticker, price threshold, and alert direction (above/below)
    2. **Receive Email**: When the price condition is met, you'll receive an email notification
    3. **Alert Status**: Alerts are checked every 5-10 minutes and marked as triggered once they're sent
    
    ### Setting Up the Price Monitor
    
    For price alerts to work, you need to run the external price monitor script:
    
    **Option 1: Manual Run**
    ```bash
    python price_monitor.py
    ```
    
    **Option 2: Scheduled (Cron) - Linux/Mac**
    ```bash
    # Run every 5 minutes
    */5 * * * * /usr/bin/python3 /path/to/price_monitor.py
    
    # Add to crontab:
    crontab -e
    ```
    
    **Option 3: Scheduled (Task Scheduler) - Windows**
    - Create a scheduled task that runs `python price_monitor.py` every 5-10 minutes
    
    **Option 4: Cloud Scheduler**
    - Google Cloud Scheduler
    - AWS EventBridge
    - Azure Scheduler
    
    ### Configuration
    
    Make sure your `.streamlit/secrets.toml` has valid SMTP settings:
    ```
    [smtp]
    host = "smtp.gmail.com"
    port = 587
    username = "your-email@gmail.com"
    password = "your-app-password"
    from_address = "Stock Tracker <your-email@gmail.com>"
    use_ssl = false
    ```
    
    ### Troubleshooting
    
    - **Not receiving emails?** Check that SMTP credentials are correct in `secrets.toml`
    - **Script errors?** Run `python price_monitor.py` manually to see detailed error messages
    - **No data?** Make sure the ticker symbol is valid (check on Yahoo Finance)
    """)

st.divider()
st.caption("💡 Tip: For reliable notifications, set up the price monitor as a scheduled cron job or cloud scheduler task.")
