import json
import os
import secrets
import smtplib
import string
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "data" / "users.json"


def _ensure_users_file() -> None:
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        USERS_FILE.write_text("[]", encoding="utf-8")


def _load_users() -> list[dict[str, Any]]:
    _ensure_users_file()
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_users(users: list[dict[str, Any]]) -> None:
    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _find_user_index_by_email(users: list[dict[str, Any]], email: str) -> int | None:
    normalized_email = _normalize_email(email)
    for idx, user in enumerate(users):
        if _normalize_email(user.get("email", "")) == normalized_email:
            return idx
    return None


def hash_password(password: str) -> str:
    return sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def is_valid_email(email: str) -> bool:
    email = _normalize_email(email)
    if "@" not in email or "." not in email:
        return False
    local, _, domain = email.partition("@")
    return bool(local and domain and "." in domain)


def is_valid_password(password: str) -> bool:
    # Basic policy for reset flow.
    return len(password) >= 8


def create_temporary_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _is_temporary_password_expired(iso_datetime: str | None) -> bool:
    if not iso_datetime:
        return True

    try:
        expires_at = datetime.fromisoformat(iso_datetime)
    except ValueError:
        return True

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return datetime.now(timezone.utc) > expires_at


def create_user(email: str, password: str) -> tuple[bool, str]:
    if not is_valid_email(email):
        return False, "Please provide a valid email address."
    if not is_valid_password(password):
        return False, "Password must be at least 8 characters long."

    users = _load_users()
    if _find_user_index_by_email(users, email) is not None:
        return False, "An account with this email already exists."

    users.append(
        {
            "email": _normalize_email(email),
            "password_hash": hash_password(password),
            "requires_password_change": False,
            "temporary_password_expires_at": None,
        }
    )
    _save_users(users)
    return True, "Account created successfully."


def authenticate_user(email: str, password: str) -> tuple[bool, str]:
    users = _load_users()
    user_index = _find_user_index_by_email(users, email)

    if user_index is None:
        return False, "Invalid email or password."

    user = users[user_index]
    if not verify_password(password, user.get("password_hash", "")):
        return False, "Invalid email or password."

    if user.get("requires_password_change", False):
        if _is_temporary_password_expired(user.get("temporary_password_expires_at")):
            return False, "Temporary password expired. Request a new one from Forgot Password."
        return False, "Temporary password accepted. Please reset your password now."

    return True, "Login successful."


def get_user_by_email(email: str) -> dict[str, Any] | None:
    """Retrieve user data by email."""
    users = _load_users()
    user_index = _find_user_index_by_email(users, email)
    
    if user_index is None:
        return None
    
    user = users[user_index]
    return {"email": user.get("email"), "id": user_index}


def generate_and_store_temporary_password(email: str, expires_minutes: int = 30) -> tuple[bool, str | None]:
    normalized_email = _normalize_email(email)
    users = _load_users()

    for user in users:
        if _normalize_email(user.get("email", "")) == normalized_email:
            temp_password = create_temporary_password()
            user["password_hash"] = hash_password(temp_password)
            user["temporary_password_expires_at"] = (
                datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
            ).isoformat()
            user["requires_password_change"] = True
            _save_users(users)
            return True, temp_password

    return False, None


def _send_email(to_email: str, subject: str, body: str, smtp_config: dict) -> tuple[bool, str]:
    """Low-level helper that sends a single email using the supplied SMTP config dict."""
    smtp_host = smtp_config.get("host", "").strip()
    smtp_username = smtp_config.get("username", "").strip()
    smtp_password = smtp_config.get("password", "").strip()
    smtp_from = (smtp_config.get("from_address") or smtp_username).strip()
    smtp_use_ssl = str(smtp_config.get("use_ssl", "false")).lower() == "true"

    # Remove spaces from password if present
    smtp_password = smtp_password.replace(" ", "")

    try:
        port_value = smtp_config.get("port", 587)
        # Handle both int and string port values
        if isinstance(port_value, str):
            smtp_port = int(port_value.strip())
        else:
            smtp_port = int(port_value)
    except (ValueError, TypeError):
        smtp_port = 587

    if not all([smtp_host, smtp_username, smtp_password, smtp_from]):
        missing = []
        if not smtp_host:
            missing.append("host")
        if not smtp_username:
            missing.append("username")
        if not smtp_password:
            missing.append("password")
        if not smtp_from:
            missing.append("from_address")
        return False, f"SMTP settings incomplete. Missing: {', '.join(missing)}. Check your secrets.toml or environment variables."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_from
    msg["To"] = to_email
    msg.set_content(body)

    try:
        if smtp_use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10) as server:
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
        return True, "Email sent successfully."
    except smtplib.SMTPAuthenticationError as e:
        return False, f"SMTP authentication failed. Check app password: {str(e)}"
    except smtplib.SMTPConnectError as e:
        return False, f"Could not connect to SMTP server ({smtp_host}:{smtp_port}): {str(e)}"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as exc:
        return False, f"Email send failed: {type(exc).__name__}: {exc}"


def send_temporary_password_email(
    to_email: str, temporary_password: str, smtp_config: dict
) -> tuple[bool, str]:
    subject = "Your temporary password — Stock Tracker"
    body = (
        "Hello,\n\n"
        "A password reset was requested for your Stock Tracker account.\n\n"
        f"Temporary password: {temporary_password}\n\n"
        "This password expires in 30 minutes.\n"
        "Visit the Reset Password page to choose a new password.\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    return _send_email(to_email, subject, body, smtp_config)


def send_password_changed_notification(to_email: str, smtp_config: dict) -> tuple[bool, str]:
    subject = "Your password was changed — Stock Tracker"
    body = (
        "Hello,\n\n"
        "This is a confirmation that the password for your Stock Tracker account "
        f"({to_email}) was just changed successfully.\n\n"
        "If you did not make this change, please request a new temporary password "
        "immediately using the Forgot Password page."
    )
    return _send_email(to_email, subject, body, smtp_config)


def reset_password_with_temporary(
    email: str,
    temporary_password: str,
    new_password: str,
) -> tuple[bool, str]:
    normalized_email = _normalize_email(email)
    users = _load_users()

    for user in users:
        if _normalize_email(user.get("email", "")) != normalized_email:
            continue

        if not user.get("requires_password_change", False):
            return False, "No active temporary password reset request was found."

        if _is_temporary_password_expired(user.get("temporary_password_expires_at")):
            return False, "Temporary password has expired. Please request a new one."

        stored_hash = user.get("password_hash", "")
        if not verify_password(temporary_password, stored_hash):
            return False, "Temporary password is incorrect."

        if not is_valid_password(new_password):
            return False, "New password must be at least 8 characters long."

        user["password_hash"] = hash_password(new_password)
        user["requires_password_change"] = False
        user["temporary_password_expires_at"] = None
        _save_users(users)
        return True, "Password reset successful."

    # Keep account existence private in this endpoint.
    return False, "Password reset could not be completed."


# ============================================================================
# PRICE ALERT FUNCTIONS
# ============================================================================

ALERTS_FILE = BASE_DIR / "data" / "alerts.json"


def _ensure_alerts_file() -> None:
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not ALERTS_FILE.exists():
        ALERTS_FILE.write_text("[]", encoding="utf-8")


def _load_alerts() -> list[dict[str, Any]]:
    _ensure_alerts_file()
    try:
        return json.loads(ALERTS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_alerts(alerts: list[dict[str, Any]]) -> None:
    ALERTS_FILE.write_text(json.dumps(alerts, indent=2), encoding="utf-8")


def create_price_alert(
    email: str, ticker: str, alert_type: str, price_threshold: float
) -> tuple[bool, str]:
    """
    Create a price alert for a user.
    
    Args:
        email: User email address
        ticker: Stock ticker symbol (will be uppercased)
        alert_type: 'above' or 'below'
        price_threshold: Price threshold in dollars
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not is_valid_email(email):
        return False, "Invalid email address."
    
    if alert_type not in ["above", "below"]:
        return False, "Alert type must be 'above' or 'below'."
    
    if price_threshold <= 0:
        return False, "Price threshold must be greater than zero."
    
    normalized_email = _normalize_email(email)
    alerts = _load_alerts()
    
    # Check if alert already exists
    for alert in alerts:
        if (
            _normalize_email(alert.get("email", "")) == normalized_email
            and alert.get("ticker") == ticker.upper()
            and alert.get("alert_type") == alert_type
            and alert.get("active")
        ):
            return False, f"An active alert for {ticker} at ${price_threshold} already exists."
    
    new_alert = {
        "email": normalized_email,
        "ticker": ticker.upper(),
        "alert_type": alert_type,
        "price_threshold": float(price_threshold),
        "active": True,
        "triggered": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "triggered_at": None,
        "triggered_price": None,
    }
    
    alerts.append(new_alert)
    _save_alerts(alerts)
    return True, f"Alert created: {ticker} will trigger when price goes {alert_type} ${price_threshold}."


def get_user_alerts(email: str) -> list[dict[str, Any]]:
    """Get all alerts for a user."""
    normalized_email = _normalize_email(email)
    alerts = _load_alerts()
    return [a for a in alerts if _normalize_email(a.get("email", "")) == normalized_email]


def delete_price_alert(email: str, alert_id: int) -> tuple[bool, str]:
    """Delete a specific alert by index."""
    normalized_email = _normalize_email(email)
    alerts = _load_alerts()
    
    user_alerts = [
        (idx, a)
        for idx, a in enumerate(alerts)
        if _normalize_email(a.get("email", "")) == normalized_email
    ]
    
    if alert_id < 0 or alert_id >= len(user_alerts):
        return False, "Alert not found."
    
    global_idx, _ = user_alerts[alert_id]
    alerts.pop(global_idx)
    _save_alerts(alerts)
    return True, "Alert deleted."


def send_price_alert_email(to_email: str, ticker: str, current_price: float, threshold: float, alert_type: str, smtp_config: dict) -> tuple[bool, str]:
    """Send price alert notification email."""
    direction_text = "above" if alert_type == "above" else "below"
    subject = f"Price Alert: {ticker} reached your {direction_text} threshold"
    body = (
        f"Hello,\n\n"
        f"Your Stock Tracker price alert has triggered!\n\n"
        f"Ticker: {ticker}\n"
        f"Alert Type: {direction_text}\n"
        f"Threshold: ${threshold:.2f}\n"
        f"Current Price: ${current_price:.2f}\n\n"
        f"Log in to your Stock Tracker account to set new alerts or manage your preferences.\n\n"
        f"Best regards,\n"
        f"Stock Tracker"
    )
    return _send_email(to_email, subject, body, smtp_config)
