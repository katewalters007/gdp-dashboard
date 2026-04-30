#!/bin/bash
# Price Monitor Loop Script
# Run this script to check price alerts every 30 seconds
# Usage: ./price_monitor_loop.sh &
# Or add to cron: * * * * * /path/to/price_monitor_loop.sh

cd "$(dirname "$0")"  # Change to script directory

while true; do
    /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1
    sleep 30
done