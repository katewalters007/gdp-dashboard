import hashlib
import hmac
import os
import sqlite3
from datetime import datetime


DB_PATH = "data/app.db"


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
