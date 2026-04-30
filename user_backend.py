import hashlib
import hmac
import json
import os
import smtplib
import sqlite3
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


DB_PATH = "data/app.db"
ALERTS_PATH = "data/alerts.json"


def _get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=DB_PATH):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS watchlists (
                user_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                buy_alert_price REAL,
                sell_alert_price REAL,
                PRIMARY KEY (user_id, ticker),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        watchlist_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(watchlists)").fetchall()
        }
        if "note" not in watchlist_columns:
            conn.execute(
                "ALTER TABLE watchlists ADD COLUMN note TEXT NOT NULL DEFAULT ''"
            )
        if "buy_alert_price" not in watchlist_columns:
            conn.execute(
                "ALTER TABLE watchlists ADD COLUMN buy_alert_price REAL"
            )
        if "sell_alert_price" not in watchlist_columns:
            conn.execute(
                "ALTER TABLE watchlists ADD COLUMN sell_alert_price REAL"
            )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                trade_date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                tax_area TEXT NOT NULL DEFAULT 'US-Federal',
                tax_rate REAL NOT NULL DEFAULT 0.22,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Lightweight migration for existing databases created before tax columns were added.
        tx_columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(transactions)").fetchall()
        }
        if "tax_area" not in tx_columns:
            conn.execute(
                "ALTER TABLE transactions ADD COLUMN tax_area TEXT NOT NULL DEFAULT 'US-Federal'"
            )
        if "tax_rate" not in tx_columns:
            conn.execute(
                "ALTER TABLE transactions ADD COLUMN tax_rate REAL NOT NULL DEFAULT 0.22"
            )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_strategies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                strategy_type TEXT NOT NULL,
                parameters TEXT NOT NULL,  -- JSON string
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        conn.commit()


def _hash_password(password, salt):
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000,
    )
    return derived.hex()


def hash_and_store_password(password):
    salt = os.urandom(16).hex()
    password_hash = _hash_password(password, salt)
    return f"{salt}${password_hash}"


def verify_password(password, stored_value):
    if "$" not in stored_value:
        return False
    salt, known_hash = stored_value.split("$", 1)
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, known_hash)


def create_user(email, password, db_path=DB_PATH):
    email = email.strip().lower()
    stored_hash = hash_and_store_password(password)
    created_at = datetime.utcnow().isoformat()

    try:
        with _get_connection(db_path) as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                (email, stored_hash, created_at),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None


def authenticate_user(email, password, db_path=DB_PATH):
    email = email.strip().lower()
    with _get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if not row:
        return None

    if verify_password(password, row["password_hash"]):
        return {"id": row["id"], "email": row["email"]}

    return None


def save_watchlist(user_id, tickers, db_path=DB_PATH):
    normalized = sorted({t.strip().upper() for t in tickers if t.strip()})
    with _get_connection(db_path) as conn:
        if normalized:
            placeholders = ", ".join(["?"] * len(normalized))
            conn.execute(
                f"DELETE FROM watchlists WHERE user_id = ? AND ticker NOT IN ({placeholders})",
                (user_id, *normalized),
            )
        else:
            conn.execute("DELETE FROM watchlists WHERE user_id = ?", (user_id,))

        if normalized:
            conn.executemany(
                """
                INSERT INTO watchlists (user_id, ticker)
                VALUES (?, ?)
                ON CONFLICT(user_id, ticker) DO NOTHING
                """,
                [(user_id, ticker) for ticker in normalized],
            )
        conn.commit()


def get_watchlist(user_id, db_path=DB_PATH):
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlists WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()
    return [row["ticker"] for row in rows]


def get_watchlist_entries(user_id, db_path=DB_PATH):
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT ticker, note, buy_alert_price, sell_alert_price
            FROM watchlists
            WHERE user_id = ?
            ORDER BY ticker
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_watchlist_entry(
    user_id,
    ticker,
    note,
    buy_alert_price,
    sell_alert_price,
    db_path=DB_PATH,
):
    normalized_ticker = ticker.strip().upper()
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO watchlists (user_id, ticker, note, buy_alert_price, sell_alert_price)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, ticker) DO UPDATE SET
                note = excluded.note,
                buy_alert_price = excluded.buy_alert_price,
                sell_alert_price = excluded.sell_alert_price
            """,
            (
                int(user_id),
                normalized_ticker,
                (note or "").strip(),
                float(buy_alert_price) if buy_alert_price is not None else None,
                float(sell_alert_price) if sell_alert_price is not None else None,
            ),
        )
        conn.commit()


def add_transaction(
    user_id,
    trade_date,
    ticker,
    action,
    quantity,
    price,
    tax_area,
    tax_rate,
    notes,
    db_path=DB_PATH,
):
    created_at = datetime.utcnow().isoformat()
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO transactions (
                user_id, trade_date, ticker, action, quantity, price, tax_area, tax_rate, notes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                str(trade_date),
                ticker.strip().upper(),
                action,
                float(quantity),
                float(price),
                (tax_area or "US-Federal").strip(),
                float(tax_rate),
                (notes or "").strip(),
                created_at,
            ),
        )
        conn.commit()


def get_transactions(user_id, db_path=DB_PATH):
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, trade_date, ticker, action, quantity, price, tax_area, tax_rate, notes, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY trade_date DESC, created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_transaction(
    user_id,
    transaction_id,
    trade_date,
    ticker,
    action,
    quantity,
    price,
    tax_area,
    tax_rate,
    notes,
    db_path=DB_PATH,
):
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE transactions
            SET trade_date = ?, ticker = ?, action = ?, quantity = ?, price = ?, tax_area = ?, tax_rate = ?, notes = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                str(trade_date),
                ticker.strip().upper(),
                action,
                float(quantity),
                float(price),
                (tax_area or "US-Federal").strip(),
                float(tax_rate),
                (notes or "").strip(),
                int(transaction_id),
                int(user_id),
            ),
        )
        conn.commit()
    return cursor.rowcount > 0


def delete_transaction(user_id, transaction_id, db_path=DB_PATH):
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (int(transaction_id), int(user_id)),
        )
        conn.commit()
    return cursor.rowcount > 0


def save_user_strategy(user_id, name, description, strategy_type, parameters, db_path=DB_PATH):
    import json
    with _get_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO user_strategies (user_id, name, description, strategy_type, parameters, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                name.strip(),
                (description or "").strip(),
                strategy_type.strip(),
                json.dumps(parameters),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
    return True


def get_user_strategies(user_id, db_path=DB_PATH):
    import json
    with _get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT id, name, description, strategy_type, parameters, created_at FROM user_strategies WHERE user_id = ? ORDER BY created_at DESC",
            (int(user_id),),
        ).fetchall()
    strategies = []
    for row in rows:
        strategies.append({
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'strategy_type': row['strategy_type'],
            'parameters': json.loads(row['parameters']),
            'created_at': row['created_at'],
        })
    return strategies


def update_user_strategy(strategy_id, user_id, name, description, strategy_type, parameters, db_path=DB_PATH):
    import json
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE user_strategies
            SET name = ?, description = ?, strategy_type = ?, parameters = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                name.strip(),
                (description or "").strip(),
                strategy_type.strip(),
                json.dumps(parameters),
                int(strategy_id),
                int(user_id),
            ),
        )
        conn.commit()
    return cursor.rowcount > 0


def delete_user_strategy(strategy_id, user_id, db_path=DB_PATH):
    with _get_connection(db_path) as conn:
        cursor = conn.execute(
            "DELETE FROM user_strategies WHERE id = ? AND user_id = ?",
            (int(strategy_id), int(user_id)),
        )
        conn.commit()
    return cursor.rowcount > 0


# Price Alert Functions

def _load_alerts():
    """Load alerts from JSON file"""
    if not os.path.exists(ALERTS_PATH):
        return []
    try:
        with open(ALERTS_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_alerts(alerts):
    """Save alerts to JSON file"""
    os.makedirs(os.path.dirname(ALERTS_PATH), exist_ok=True)
    with open(ALERTS_PATH, 'w') as f:
        json.dump(alerts, f, indent=2)


def get_user_alerts(user_email):
    """Get all alerts for a user"""
    alerts = _load_alerts()
    return [alert for alert in alerts if alert.get('user_email') == user_email]


def create_price_alert(user_email, ticker, alert_type, price_threshold):
    """Create a new price alert"""
    try:
        alerts = _load_alerts()
        
        # Generate new ID
        max_id = max((alert.get('id', 0) for alert in alerts), default=0)
        new_id = max_id + 1
        
        alert = {
            'id': new_id,
            'user_email': user_email,
            'ticker': ticker.upper(),
            'alert_type': alert_type,
            'price_threshold': float(price_threshold),
            'created_at': datetime.utcnow().isoformat(),
            'active': True,
            'triggered': False,
            'triggered_price': None,
            'triggered_at': None
        }
        
        alerts.append(alert)
        _save_alerts(alerts)
        
        return True, f"Alert created for {ticker} when price goes {alert_type} ${price_threshold:.2f}"
    
    except Exception as e:
        return False, f"Failed to create alert: {str(e)}"


def delete_price_alert(user_email, alert_idx):
    """Delete a price alert by index in user's alert list"""
    try:
        alerts = _load_alerts()
        user_alerts = [alert for alert in alerts if alert.get('user_email') == user_email]
        
        if 0 <= alert_idx < len(user_alerts):
            alert_to_delete = user_alerts[alert_idx]
            alerts.remove(alert_to_delete)
            _save_alerts(alerts)
            return True, "Alert deleted successfully"
        else:
            return False, "Alert not found"
    
    except Exception as e:
        return False, f"Failed to delete alert: {str(e)}"


def send_price_alert_email(alert, current_price):
    """Send email notification for triggered alert"""
    try:
        # Load SMTP config from secrets
        secrets_path = ".streamlit/secrets.toml"
        if not os.path.exists(secrets_path):
            print(f"SMTP config not found at {secrets_path}")
            return False

        # Simple TOML parser
        config = {}
        with open(secrets_path, 'r') as f:
            current_section = None
            for line in f:
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                elif '=' in line and current_section == 'smtp':
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"')
                    config[key] = value

        if not all(k in config for k in ['host', 'port', 'username', 'password', 'from_address']):
            print("Incomplete SMTP configuration")
            return False

        # Create HTML email (less likely to go to spam)
        msg = MIMEMultipart('alternative')
        msg['From'] = config['from_address']
        msg['To'] = alert['user_email']
        msg['Subject'] = f"📈 {alert['ticker']} Alert: Price Target Reached!"

        # Add headers to improve deliverability
        msg['X-Priority'] = '1'  # High priority
        msg['X-MSMail-Priority'] = 'High'
        msg['Importance'] = 'High'
        msg['Return-Path'] = config['username']
        msg['Reply-To'] = config['from_address']

        # HTML body (more professional and less spammy)
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #2e7d32; border-bottom: 3px solid #4caf50; padding-bottom: 20px; margin-bottom: 30px; }}
                .alert-box {{ background: #e8f5e8; border-left: 5px solid #4caf50; padding: 20px; margin: 20px 0; }}
                .price-info {{ background: #fff3e0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
                .highlight {{ font-weight: bold; color: #2e7d32; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Stock Price Alert</h1>
                    <p>Your personalized stock monitoring service</p>
                </div>

                <div class="alert-box">
                    <h2>🚨 Alert Triggered!</h2>
                    <p><strong>{alert['ticker']}</strong> has reached your target price.</p>
                </div>

                <div class="price-info">
                    <h3>Alert Details:</h3>
                    <ul>
                        <li><strong>Stock:</strong> {alert['ticker']}</li>
                        <li><strong>Condition:</strong> Price went <span class="highlight">{alert['alert_type']}</span> ${alert['price_threshold']:.2f}</li>
                        <li><strong>Current Price:</strong> <span class="highlight">${current_price:.2f}</span></li>
                        <li><strong>Triggered:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                    </ul>
                </div>

                <div class="alert-box" style="background: #e3f2fd; border-left-color: #2196f3;">
                    <h3>🔄 Reusable Alert</h3>
                    <p>This alert will <strong>automatically reset</strong> when {alert['ticker']} moves back {alert['alert_type']} ${alert['price_threshold']:.2f} and can trigger again.</p>
                    <p><em>Example: If you set "AAPL above $100", it will notify you each time AAPL crosses above $100.</em></p>
                </div>

                <p>This alert has been marked as triggered and will no longer send notifications until it resets.</p>

                <div class="footer">
                    <p><strong>Stock Tracker</strong> - Your Personal Stock Monitoring Assistant</p>
                    <p>To manage your alerts, visit the Price Alerts page in your dashboard.</p>
                    <p>If you no longer wish to receive these alerts, you can delete them from your account.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text fallback
        text_body = f"""Stock Price Alert - {alert['ticker']}

ALERT TRIGGERED!

Stock: {alert['ticker']}
Condition: Price went {alert['alert_type']} ${alert['price_threshold']:.2f}
Current Price: ${current_price:.2f}
Triggered: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

REUSABLE ALERT:
This alert will automatically reset when {alert['ticker']} moves back {alert['alert_type']} ${alert['price_threshold']:.2f}
and can trigger again. For example, if you set "AAPL above $100", it will notify you each time AAPL crosses above $100.

This alert has been marked as triggered and will no longer send notifications until it resets.

---
Stock Tracker - Your Personal Stock Monitoring Assistant
To manage your alerts, visit the Price Alerts page in your dashboard.
"""

        # Attach both HTML and plain text versions
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        server = smtplib.SMTP(config['host'], int(config['port']))
        if config.get('use_ssl', 'false').lower() == 'true':
            server.starttls()
        else:
            server.starttls()  # Most SMTP requires TLS

        server.login(config['username'], config['password'])
        server.send_message(msg)
        server.quit()

        return True

    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False
