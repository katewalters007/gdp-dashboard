# Example Crontab Configuration for Price Alert Monitor
# =====================================================
#
# This file shows example crontab entries for running the price monitor.
# Adapt the paths to your system. On Linux/Mac, edit your crontab with:
#
#     crontab -e
#
# Then copy and paste the appropriate line below.

# OPTION 1: Run every 5 minutes (RECOMMENDED)
# Fast alerts but more API calls
# Replace /path/to with your actual path
*/5 * * * * cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1

# OPTION 2: Run every 10 minutes (Good balance)
# Less frequent but still responsive
*/10 * * * * cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1

# OPTION 3: Run every 15 minutes (Lower resource usage)
# Good for low-volume alerts or high server load
*/15 * * * * cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1

# OPTION 4: Run every hour (Just for periodic updates)
# Low cost but delayed alerts
0 * * * * cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1

# OPTION 5: Run during trading hours only (9 AM - 5 PM, weekdays)
# Only checks during market hours
*/5 9-17 * * 1-5 cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1

# OPTION 6: Run specific times (e.g., 9 AM, noon, 2 PM, 4 PM)
# For intraday check-ins
0 9,12,14,16 * * * cd /path/to/gdp-dashboard && /usr/bin/python3 price_monitor.py >> /tmp/price_monitor.log 2>&1


# INSTALLATION INSTRUCTIONS
# ==========================
#
# 1. Find your Python path:
#    which python3
#    # or
#    /usr/bin/python3 --version
#
# 2. Find your project directory:
#    pwd
#    # Make a note of: /path/to/gdp-dashboard
#
# 3. Edit your crontab:
#    crontab -e
#
# 4. Copy ONE of the lines above (adjust paths)
#
# 5. Save and exit the editor (usually Ctrl+O, Enter, Ctrl+X in nano)
#
# 6. Verify it was added:
#    crontab -l
#
# 7. Check logs periodically:
#    tail -f /tmp/price_monitor.log
#
# 8. If issues occur, run manually:
#    cd /path/to/gdp-dashboard && python3 price_monitor.py


# COMMON CRONTAB SYNTAX
# ====================
#
# Format: minute hour day month day-of-week command
#
# Minute:     0-59 (use */5 for every 5 minutes)
# Hour:       0-23 (0 is midnight)
# Day:        1-31
# Month:      1-12 (1 is January)
# Day-of-week: 0-7 (0 or 7 is Sunday, 1 is Monday)
#
# Examples:
# */5 * * * *        - Every 5 minutes
# 0 * * * *          - Every hour
# 0 0 * * *          - Daily at midnight
# 0 9 * * 1-5        - Weekdays at 9 AM
# */15 9-17 * * *    - Every 15 mins from 9 AM to 5 PM


# LOG ROTATION (Optional but recommended)
# =======================================
#
# Create /etc/logrotate.d/price_monitor with:
#
# /tmp/price_monitor.log {
#     daily
#     rotate 7
#     compress
#     delaycompress
#     missingok
#     notifempty
# }
#
# Then run: sudo logrotate -f /etc/logrotate.d/price_monitor


# MONITORING THE MONITOR (Optional)
# ==================================
#
# To send yourself alerts if the monitor fails, create a wrapper script:
# Save to: /path/to/gdp-dashboard/run_monitor.sh
#
# #!/bin/bash
# OUTPUT=$(cd /workspaces/gdp-dashboard && python3 price_monitor.py 2>&1)
# EXIT_CODE=$?
#
# if [ $EXIT_CODE -ne 0 ]; then
#   echo "Price Monitor Error at $(date)" > /tmp/monitor_error.txt
#   echo "$OUTPUT" >> /tmp/monitor_error.txt
#   mail -s "Price Monitor Error" your-email@gmail.com < /tmp/monitor_error.txt
# fi
#
# echo "$OUTPUT" >> /tmp/price_monitor.log
#
# Then in crontab:
# */5 * * * * /path/to/gdp-dashboard/run_monitor.sh


# TROUBLESHOOTING TIPS
# ====================
#
# 1. Cron not running?
#    - Check cront logs: grep CRON /var/log/syslog
#    - Ensure script has execute permissions
#    - Use full paths (no ~, no relative paths)
#
# 2. Script fails but works manually?
#    - Environment variables differ (PATH, PYTHONPATH)
#    - Use absolute paths to python3
#    - Add 'cd' command before running script
#
# 3. Permissions denied?
#    - Check file permissions: ls -la price_monitor.py
#    - Make it executable: chmod +x price_monitor.py
#
# 4. Email not working?
#    - Test SMTP config manually
#    - Check secrets.toml exists
#    - Verify Gmail App Password is correct
#
# 5. Want to disable cron job temporarily?
#    - Comment out the line with #
#    - Or remove it with: crontab -e, delete line, save
#
# 6. View current cron jobs:
#    crontab -l
#
# 7. View cron execution history (Linux):
#    grep CRON /var/log/syslog | tail -20
#
# 8. Real-time log viewing:
#    tail -f /tmp/price_monitor.log
