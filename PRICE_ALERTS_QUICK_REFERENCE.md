# Price Alerts Implementation - Quick Reference

## What Was Implemented

A complete external price alert monitoring system that sends email notifications when stock prices reach user-defined thresholds.

## New Files

### 1. `price_monitor.py` (★ Main Script)
**Purpose**: Standalone Python script to check price alerts periodically
- Reads alerts from `data/alerts.json`
- Fetches current prices using yfinance
- Sends email notifications when thresholds are breached
- Runs independently (not part of Streamlit app)

**How to run:**
```bash
python price_monitor.py          # One-time check
*/5 * * * * python price_monitor.py  # Add to crontab
```

### 2. `pages/Price_Alerts.py` (★ UI Page)
**Purpose**: User interface for managing price alerts
- Create new alerts
- View active alerts
- Delete alerts
- See triggered alert history
- Setup instructions

**Visible in**: Streamlit sidebar under Pages (after login)

### 3. `PRICE_ALERTS_SETUP.md` (★ Documentation)
**Purpose**: Comprehensive setup and troubleshooting guide
- SMTP configuration
- Running the monitor (all platforms)
- Cron job setup
- Cloud scheduler examples
- Troubleshooting tips

## Updated Files

### 1. `auth_utils.py`
**New functions added:**
- `create_price_alert()` - Create alert
- `get_user_alerts()` - Retrieve alerts
- `delete_price_alert()` - Remove alert
- `send_price_alert_email()` - Send notification
- Helper functions for JSON persistence

### 2. `README.md`
**Updates:**
- Added price alerts to features list
- Added setup instructions section
- Link to PRICE_ALERTS_SETUP.md

## Data Files

### `data/alerts.json` (NEW)
**Storage for all alerts:**
```json
[
  {
    "email": "user@example.com",
    "ticker": "AAPL",
    "alert_type": "above",
    "price_threshold": 180.00,
    "active": true,
    "triggered": false,
    "created_at": "2026-04-24T...",
    "triggered_at": null,
    "triggered_price": null
  }
]
```

## System Architecture

```
┌─────────────────┐
│  Streamlit App  │
│  (Web UI)       │
│ - Stock Tracker │
│ - Price Alerts  │
│ - Login Page    │
└────────┬────────┘
         │ stores
         ▼
    ┌────────────┐
    │ alerts.json│
    └────────────┘
         ▲
         │ reads every 5 min
         │
    ┌────────────────────┐
    │  price_monitor.py  │  ← Runs independently
    │  (External Script) │     (cron/scheduler)
    └────────┬───────────┘
             │
             ├─ Fetches prices (yfinance)
             │
             └─ Sends emails (SMTP)
                ▼
            User's Email ✉️
```

## Key Features

✅ **Email Notifications** - Get alerts via email
✅ **Multiple Alert Types** - "above" or "below" price thresholds
✅ **Persistent Storage** - Alerts saved in JSON
✅ **Simple UI** - Create and manage alerts easily
✅ **External Monitoring** - Independent script (doesn't block web app)
✅ **Cloud Ready** - Works with any cloud scheduler
✅ **Error Handling** - Graceful failures, detailed logging
✅ **Security** - No hardcoded credentials exposed

## Setup Checklist

- [ ] Configure SMTP in `.streamlit/secrets.toml`
- [ ] Test `python price_monitor.py` manually
- [ ] Set up cron job (or scheduler)
- [ ] Create test alert via UI
- [ ] Verify email is received
- [ ] Check logs: `tail /tmp/price_monitor.log`

## Common Commands

```bash
# Test the monitor
python price_monitor.py

# View cron jobs
crontab -l

# Edit cron jobs
crontab -e

# View monitor logs
tail -f /tmp/price_monitor.log

# Check if price monitor process is running
ps aux | grep price_monitor

# Get current price for a stock
python -c "import yfinance as yf; print(yf.Ticker('AAPL').info['currentPrice'])"
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No emails received | Check SMTP config in secrets.toml |
| Script won't run | Verify yfinance is installed |
| Cron not working | Use absolute paths, check logs |
| Invalid ticker | Verify symbol on Yahoo Finance |
| Email errors | Run `python price_monitor.py` manually for details |

## Files Modified

1. `auth_utils.py` - Added ~80 lines of alert functions
2. `README.md` - Added setup section and feature mention
3. `.streamlit/secrets.toml` - Replaced exposed credentials (already done)
4. `Stock_Tracker.py` - Fixed CSS font typo (already done)

## Files Created

1. `price_monitor.py` - ~270 lines
2. `pages/Price_Alerts.py` - ~320 lines
3. `PRICE_ALERTS_SETUP.md` - Comprehensive guide
4. This file - Quick reference

## Testing

To verify everything works:

```bash
# 1. Check syntax
python3 -m py_compile price_monitor.py pages/Price_Alerts.py

# 2. Test imports
python3 -c "from auth_utils import create_price_alert; print('OK')"

# 3. Run monitor once
python3 price_monitor.py

# 4. Check alert storage
cat data/alerts.json
```

## Performance Notes

- Monitor runs in ~5-30 seconds depending on number of alerts
- API calls are limited by yfinance (fair use)
- JSON file is thread-safe for typical volume
- Email sending is sequential (not parallel)

For high volume (1000+ alerts), consider:
- Switching to SQLite database
- Batch price fetching
- Parallel email sending
- Redis queue for job management

## Support & Documentation

- Full setup guide: `PRICE_ALERTS_SETUP.md`
- Code comments: See `price_monitor.py` and alert functions in `auth_utils.py`
- Examples: Check `PRICE_ALERTS_SETUP.md` for setup examples

## Next Steps

1. ✅ Implementation complete
2. → User sets up SMTP credentials
3. → User creates cron job or scheduler task
4. → Users create price alerts via UI
5. → System sends email notifications automatically
