# Price Alerts Setup Guide

This document explains how to set up and configure the price alert monitoring system.

## Overview

The price alert system consists of three components:

1. **UI Page** (`pages/Price_Alerts.py`) - Where users create and manage alerts
2. **Alert Functions** (in `auth_utils.py`) - Backend logic for alerts
3. **Price Monitor Script** (`price_monitor.py`) - External script that checks alerts periodically

## Quick Start

### 1. Configure SMTP (Email)

Edit `.streamlit/secrets.toml` with your Gmail credentials:

```toml
[smtp]
host = "smtp.gmail.com"
port = 587
username = "your-email@gmail.com"
password = "your-app-password"
from_address = "Stock Tracker <your-email@gmail.com>"
use_ssl = false
```

**Getting a Gmail App Password:**
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable "2-Step Verification" if not already enabled
3. Go to "App passwords"
4. Select "Mail" and "Windows Computer" (or your device)
5. Copy the generated 16-character password
6. Use this password in `secrets.toml`

### 2. Run the Price Monitor

The price monitor can be run in several ways:

#### Option A: Manual Testing
```bash
cd /workspaces/gdp-dashboard
python price_monitor.py
```

Output should look like:
```
============================================================
Price Alert Monitor - 2026-04-24T15:30:45.123456+00:00
============================================================
Loading SMTP configuration...
Checking price alerts...
  Fetching AAPL...
    AAPL: $182.50
  Fetching GOOGL...
    GOOGL: $140.25

============================================================
Results:
  Alerts processed: 2
  Alerts triggered: 0
  Errors: 0
============================================================
```

#### Option B: Cron Job (Linux/Mac) - RECOMMENDED

Edit your crontab:
```bash
crontab -e
```

Add this line to run every 30 seconds:
```bash
# Option 1: Multiple cron entries
* * * * * cd /workspaces/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1
* * * * * (sleep 30; cd /workspaces/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1)

# Option 2: Use the provided loop script
* * * * * /workspaces/gdp-dashboard/price_monitor_loop.sh
```

View logs:
```bash
tail -f /tmp/price_monitor.log
```

#### Option C: Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task → Name it "Stock Tracker Price Monitor"
3. Trigger: Repeat every 30 seconds
4. Action: Run program
   - Program: `C:\Python39\python.exe` (or your Python path)
   - Arguments: `C:\path\to\price_monitor.py`
5. Set to run "with highest privileges"

#### Option D: Cloud Scheduler

**Google Cloud Scheduler:**
```bash
gcloud scheduler jobs create app-engine price-monitor \
  --schedule="*/30 * * * *" \
  --http-method=POST \
  --uri="https://your-app.cloudfunctions.net/price_monitor" \
  --tz=America/New_York
```

**AWS EventBridge:**
- Create rule with cron: `cron(*/5 * * * ? *)`
- Target: Lambda function (wrapper around price_monitor.py)

**Azure Logic Apps:**
- Trigger: Recurrence (5 minutes)
- Action: Run Python script or HTTP webhook

### 3. Create Alerts via UI

After deploying your Streamlit app:

1. Go to the **Price Alerts** page (visible in sidebar after login)
2. Enter a stock ticker (e.g., AAPL)
3. Select alert type: "above" or "below"
4. Set price threshold
5. Click "Create Alert"

## How It Works

### Alert Flow

```
User creates alert
    ↓
Alert stored in data/alerts.json
    ↓
Price monitor runs (every 5 min)
    ↓
Fetches current stock prices (yfinance)
    ↓
Checks if price condition met
    ↓
If triggered:
  - Send email notification
  - Mark alert as triggered
  - Update data/alerts.json
```

### Alert Data Structure

```json
{
  "email": "user@example.com",
  "ticker": "AAPL",
  "alert_type": "above",
  "price_threshold": 180.00,
  "active": true,
  "triggered": false,
  "created_at": "2026-04-24T14:30:00.000000+00:00",
  "triggered_at": null,
  "triggered_price": null
}
```

## Troubleshooting

### Issue: "Email send failed" errors

**Solution 1: Check Gmail App Password**
- Make sure you're using an App Password, not your regular Gmail password
- App passwords are 16 characters, generated at myaccount.google.com/apppasswords

**Solution 2: Enable Less Secure Apps (alternative)**
- Go to [Google Account Security](https://myaccount.google.com/security)
- Turn on "Less secure app access"
- Use your regular Gmail password

**Solution 3: Check SMTP Config**
```bash
python -c "from auth_utils import load_smtp_config; print(load_smtp_config())"
```

### Issue: Script doesn't run from cron

**Solution 1: Use absolute paths**
```bash
*/5 * * * * cd /home/user/gdp-dashboard && /usr/bin/python3 /home/user/gdp-dashboard/price_monitor.py
```

**Solution 2: Check Python environment**
```bash
which python3
python3 -c "import yfinance"  # Should work without errors
```

**Solution 3: Check logs**
```bash
tail -100 /tmp/price_monitor.log
```

### Issue: No alerts being triggered

**Check 1: Is the monitor running?**
```bash
ps aux | grep price_monitor
```

**Check 2: Are alerts stored?**
```bash
cat data/alerts.json
```

**Check 3: Manual test**
```bash
python price_monitor.py
```

**Check 4: Verify ticker symbols**
- Use `yfinance` to test:
```python
import yfinance as yf
ticker = yf.Ticker("AAPL")
print(ticker.info["currentPrice"])
```

## Performance & Scalability

### Current Limitations
- Checks prices sequentially (may be slow with many alerts)
- No batch email sending (sends one at a time)
- No retry logic for failed email sends

### For Production Use
Consider:
- Using a task queue (Celery, RQ)
- Batch fetching prices
- Database instead of JSON file
- Retry mechanism with exponential backoff
- Rate limiting on yfinance API

## Advanced Configuration

### Custom Check Interval

Edit cron for different intervals:
```bash
# Every minute
* * * * * python price_monitor.py

# Every 10 minutes
*/10 * * * * python price_monitor.py

# Every hour
0 * * * * python price_monitor.py

# Weekdays only
*/5 9-17 * * 1-5 python price_monitor.py
```

### Logging to File

Modify the cron job:
```bash
*/5 * * * * python price_monitor.py >> /var/log/price_monitor.log 2>&1
```

### Email Notifications on Errors

Create wrapper script `run_monitor.sh`:
```bash
#!/bin/bash
OUTPUT=$(cd /workspaces/gdp-dashboard && python price_monitor.py 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  echo "$OUTPUT" | mail -s "Price Monitor Error" admin@example.com
fi

echo "$OUTPUT" >> /var/log/price_monitor.log
```

Then use in cron:
```bash
*/5 * * * * /path/to/run_monitor.sh
```

## File Structure

```
gdp-dashboard/
├── auth_utils.py              # Alert functions
├── price_monitor.py           # ← External monitor script
├── pages/
│   └── Price_Alerts.py       # ← Alert UI
├── data/
│   └── alerts.json           # ← Alert storage
└── .streamlit/
    └── secrets.toml          # SMTP config
```

## API Reference

### Creating Alerts Programmatically

```python
from auth_utils import create_price_alert

success, message = create_price_alert(
    email="user@example.com",
    ticker="AAPL",
    alert_type="above",  # or "below"
    price_threshold=150.00
)

if success:
    print(message)
else:
    print(f"Error: {message}")
```

### Getting User Alerts

```python
from auth_utils import get_user_alerts

alerts = get_user_alerts("user@example.com")
for alert in alerts:
    print(f"{alert['ticker']} {alert['alert_type']} ${alert['price_threshold']}")
```

### Deleting Alerts

```python
from auth_utils import delete_price_alert

success, message = delete_price_alert("user@example.com", alert_index=0)
```

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Run `python price_monitor.py` manually for detailed error messages
3. Check `.streamlit/secrets.toml` SMTP configuration
4. Review logs at `/tmp/price_monitor.log` (if using cron)
