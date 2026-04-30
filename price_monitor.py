#!/usr/bin/env python3
"""
Price Alert Monitor - External Script
======================================

This script monitors price alerts and sends email notifications when thresholds are breached.

Usage:
    python price_monitor.py              # Run once and exit
    # Or use with a system cron job:
    # */30 * * * * * /usr/bin/python3 /path/to/price_monitor.py (if cron supports seconds)
    # Or use a loop for 30-second intervals

Configuration:
    - Load SMTP settings from .streamlit/secrets.toml
    - Alerts stored in data/alerts.json
    - Can be run periodically (every 30 seconds recommended)
"""

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print("ERROR: yfinance not installed. Run: pip install yfinance")
    sys.exit(1)

# Add parent directory to path for imports
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from user_backend import (
    _load_alerts,
    _save_alerts,
    send_price_alert_email,
)


def load_smtp_config() -> dict:
    """Load SMTP configuration from secrets.toml"""
    secrets_file = BASE_DIR / ".streamlit" / "secrets.toml"
    
    if not secrets_file.exists():
        raise FileNotFoundError(f"secrets.toml not found at {secrets_file}")
    
    # Simple TOML parser for [smtp] section
    config = {}
    in_smtp_section = False
    
    try:
        with open(secrets_file) as f:
            for line in f:
                line = line.strip()
                
                if line == "[smtp]":
                    in_smtp_section = True
                    continue
                elif line.startswith("["):
                    in_smtp_section = False
                    continue
                
                if not in_smtp_section or not line or line.startswith("#"):
                    continue
                
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    # Try to convert to appropriate type
                    if value.lower() == "true":
                        config[key] = True
                    elif value.lower() == "false":
                        config[key] = False
                    elif value.isdigit():
                        config[key] = int(value)
                    else:
                        config[key] = value
    except Exception as e:
        print(f"WARNING: Could not parse secrets.toml: {e}")
    
    return config


def get_current_price(ticker: str) -> float | None:
    """Fetch current price for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        
        if not data.empty and "Close" in data.columns:
            return float(data["Close"].iloc[-1])
        
        # Fallback: try to get info
        info = stock.info
        if "currentPrice" in info:
            return float(info["currentPrice"])
        
        return None
    except Exception as e:
        print(f"  Error fetching price for {ticker}: {e}")
        return None


def check_and_send_alerts(smtp_config: dict) -> dict:
    """
    Check all active alerts and send emails if thresholds are breached.
    
    Returns:
        Dictionary with stats: {'processed': int, 'triggered': int, 'errors': int}
    """
    stats = {"processed": 0, "triggered": 0, "errors": 0, "invalid_config": False}
    
    # Validate SMTP config
    if not all(
        smtp_config.get(key)
        for key in ["host", "username", "password", "from_address"]
    ):
        print(
            "WARNING: Incomplete SMTP configuration. "
            "Cannot send emails. Check .streamlit/secrets.toml"
        )
        stats["invalid_config"] = True
        return stats
    
    alerts = _load_alerts()
    
    if not alerts:
        print("No alerts to check.")
        return stats
    
    # Group alerts by ticker to minimize API calls
    tickers_to_check = set()
    ticker_alerts_map = {}
    
    for alert in alerts:
        # Check both active alerts and triggered alerts (for resetting)
        ticker = alert.get("ticker")
        tickers_to_check.add(ticker)
        if ticker not in ticker_alerts_map:
            ticker_alerts_map[ticker] = []
        ticker_alerts_map[ticker].append(alert)
    
    print(f"Checking {len(tickers_to_check)} unique tickers...")
    
    # Fetch prices and check alerts
    for ticker in tickers_to_check:
        print(f"  Fetching {ticker}...")
        current_price = get_current_price(ticker)
        
        if current_price is None:
            print(f"    Could not fetch price for {ticker}")
            continue
        
        print(f"    {ticker}: ${current_price:.2f}")
        
        for alert in ticker_alerts_map[ticker]:
            stats["processed"] += 1
            threshold = alert.get("price_threshold")
            alert_type = alert.get("alert_type")
            user_email = alert.get("user_email")
            is_active = alert.get("active", True)
            was_triggered = alert.get("triggered", False)
            
            if is_active and not was_triggered:
                # Check if active alert should trigger
                should_trigger = (
                    alert_type == "above" and current_price >= threshold
                ) or (alert_type == "below" and current_price <= threshold)
                
                if should_trigger:
                    print(f"    TRIGGER: {ticker} {alert_type} ${threshold}")
                    
                    try:
                        sent = send_price_alert_email(alert, current_price)
                        
                        if sent:
                            alert["triggered"] = True
                            alert["triggered_at"] = datetime.now(timezone.utc).isoformat()
                            alert["triggered_price"] = current_price
                            alert["active"] = False  # Deactivate after triggering
                            stats["triggered"] += 1
                            print(f"      Email sent to {user_email}")
                        else:
                            print(f"      Failed to send email")
                            stats["errors"] += 1
                    except Exception as e:
                        print(f"      Error sending email: {e}")
                        stats["errors"] += 1
            
            elif was_triggered:
                # Check if triggered alert should reset
                should_reset = (
                    (alert_type == "above" and current_price < threshold) or
                    (alert_type == "below" and current_price > threshold)
                )
                
                if should_reset:
                    print(f"    RESET: {ticker} {alert_type} ${threshold} (price moved back)")
                    alert["triggered"] = False
                    alert["triggered_at"] = None
                    alert["triggered_price"] = None
                    alert["active"] = True  # Reactivate the alert
                    print(f"      Alert reset and ready to trigger again")
    
    # Save updated alerts
    _save_alerts(alerts)
    
    return stats


def main():
    """Main entry point for the price monitor."""
    print("=" * 60)
    print(f"Price Alert Monitor - {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)
    
    try:
        # Load configuration
        print("Loading SMTP configuration...")
        smtp_config = load_smtp_config()
        
        if not smtp_config:
            print("ERROR: No SMTP configuration found in secrets.toml")
            return 1
        
        # Check and send alerts
        print("Checking price alerts...")
        stats = check_and_send_alerts(smtp_config)
        
        print("\n" + "=" * 60)
        print("Results:")
        print(f"  Alerts processed: {stats['processed']}")
        print(f"  Alerts triggered: {stats['triggered']}")
        print(f"  Errors: {stats['errors']}")
        
        if stats["invalid_config"]:
            print("\n⚠️  SMTP configuration incomplete - no emails sent")
            return 1
        
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
