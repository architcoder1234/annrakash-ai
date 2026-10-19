"""
auth.py - Authentication, Identity and Access Control Module for AnnRakshak AI.
Implements:
- Constant-time password verification using bcrypt (12 salt rounds)
- Protection against user enumeration via dummy bcrypt hash comparison
- Login throttling (5 failed attempts per username/session -> 5-minute lockout)
- Login attempts audit logging in login_attempts table
- Strict minimum password length (>= 10 characters)
- Zero hardcoded passwords or PIN bypasses: authentication strictly validates against stored hash
"""

import bcrypt
import sqlite3
import os
import uuid
import secrets
from typing import Optional, Dict, Any, Tuple
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

IST = ZoneInfo("Asia/Kolkata")

# Pre-computed valid bcrypt hash used for constant-time comparison when username does not exist.
# This prevents timing attacks for username enumeration.
DUMMY_BCRYPT_HASH = "$2b$12$7kP2x3.N92y65m88W/f4p.XFh8V2dZ8vA5cQ4c7m1n3o5p7q9r1t"

MIN_PASSWORD_LENGTH = 10
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_WINDOW_MINUTES = 5
SESSION_IDLE_TIMEOUT_MINUTES = 30
GENERIC_AUTH_ERROR = "Invalid credentials or account locked."

def hash_password(password: str) -> str:
    """Hash password securely using bcrypt with 12 salt rounds."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    """Verify candidate password against bcrypt hash using constant-time check."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def is_account_locked(username: str, db_path: Optional[str] = None) -> bool:
    """Checks if username has exceeded max failed attempts in the lockout window (5 mins)."""
    if not username:
        return False
    from database import get_connection
    conn = get_connection(db_path=db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                session_id TEXT,
                ip_address TEXT,
                attempt_time TEXT NOT NULL,
                success INTEGER NOT NULL
            );
        """)
        cursor.execute("""
            SELECT COUNT(*) FROM login_attempts
            WHERE LOWER(username) = LOWER(?)
              AND success = 0
              AND attempt_time >= datetime('now', '-5 minutes');
        """, (username.strip(),))
        row = cursor.fetchone()
        return bool(row and row[0] >= MAX_FAILED_LOGIN_ATTEMPTS)
    except Exception:
        return False
    finally:
        conn.close()

def record_login_attempt(
    username: str,
    success: bool,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    db_path: Optional[str] = None
) -> None:
    """Audit logs every authentication attempt with timestamp and status."""
    if not username:
        return
    from database import get_connection, _db_lock
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with _db_lock:
        conn = get_connection(db_path=db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    session_id TEXT,
                    ip_address TEXT,
                    attempt_time TEXT NOT NULL,
                    success INTEGER NOT NULL
                );
            """)
            cursor.execute("""
                INSERT INTO login_attempts (username, session_id, ip_address, attempt_time, success)
                VALUES (?, ?, ?, ?, ?);
            """, (username.strip(), session_id, ip_address, now_utc, 1 if success else 0))
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
        finally:
            conn.close()

def authenticate_user(
    username: str,
    password: str,
    session_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    db_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Validates user credentials against database.
    Authentication succeeds ONLY via verify_password on the stored hash.
    Enforces login throttling (5 failed attempts -> 5 min lockout),
    constant-time comparison for nonexistent accounts, and audit logging.
    """
    if not username or not password:
        return None

    clean_user = username.strip()

    # 1. Throttling / Lockout check: 5 failed attempts in 5 minutes -> lock
    if is_account_locked(clean_user, db_path=db_path):
        verify_password(password, DUMMY_BCRYPT_HASH)
        record_login_attempt(clean_user, False, session_id, ip_address, db_path=db_path)
        return None

    from database import get_connection
    conn = get_connection(db_path=db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.password_hash, u.role, u.org_id, u.is_active,
                   COALESCE(d.name, n.name, 'System Administrator') as org_name
            FROM users u
            LEFT JOIN donors d ON u.org_id = d.id
            LEFT JOIN ngos n ON u.org_id = n.id
            WHERE LOWER(u.username) = LOWER(?);
        """, (clean_user,))
        row = cursor.fetchone()

        if not row:
            # Constant-time timing attack defense: run dummy bcrypt compare
            verify_password(password, DUMMY_BCRYPT_HASH)
            record_login_attempt(clean_user, False, session_id, ip_address, db_path=db_path)
            return None

        if not bool(row["is_active"]):
            # Inactive account
            verify_password(password, DUMMY_BCRYPT_HASH)
            record_login_attempt(clean_user, False, session_id, ip_address, db_path=db_path)
            return None

        # Verify candidate password against stored bcrypt hash ONLY
        if verify_password(password, row["password_hash"]):
            record_login_attempt(clean_user, True, session_id, ip_address, db_path=db_path)
            return {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "org_id": row["org_id"],
                "org_name": row["org_name"],
                "is_active": bool(row["is_active"])
            }
        else:
            record_login_attempt(clean_user, False, session_id, ip_address, db_path=db_path)
            return None
    finally:
        conn.close()

def get_user_by_id(user_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch user context by user ID."""
    from database import get_connection
    conn = get_connection(db_path=db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.org_id, u.is_active,
                   COALESCE(d.name, n.name, 'System Administrator') as org_name
            FROM users u
            LEFT JOIN donors d ON u.org_id = d.id
            LEFT JOIN ngos n ON u.org_id = n.id
            WHERE u.id = ?;
        """, (user_id,))
        row = cursor.fetchone()
        if row and bool(row["is_active"]):
            return {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "org_id": row["org_id"],
                "org_name": row["org_name"],
                "is_active": bool(row["is_active"])
            }
        return None
    finally:
        conn.close()

def get_user_by_username(username: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Fetch user context by username (for demo session convenience when DEMO_MODE=True)."""
    from database import get_connection
    conn = get_connection(db_path=db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.org_id, u.is_active,
                   COALESCE(d.name, n.name, 'System Administrator') as org_name
            FROM users u
            LEFT JOIN donors d ON u.org_id = d.id
            LEFT JOIN ngos n ON u.org_id = n.id
            WHERE LOWER(u.username) = LOWER(?);
        """, (username.strip(),))
        row = cursor.fetchone()
        if row and bool(row["is_active"]):
            return {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "org_id": row["org_id"],
                "org_name": row["org_name"],
                "is_active": bool(row["is_active"])
            }
        return None
    finally:
        conn.close()

def create_user(
    username: str,
    password: str,
    role: str,
    org_id: Optional[str] = None,
    db_path: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """Creates a new active user account. Enforces min password length >= 10."""
    if role not in ('donor', 'ngo', 'admin'):
        return False, f"Invalid role: {role}", None
    if not username or len(username.strip()) < 3:
        return False, "Username must be at least 3 characters.", None
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters.", None

    from database import get_connection, _db_lock
    user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
    pwd_hash = hash_password(password)
    now_iso = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")

    with _db_lock:
        conn = get_connection(db_path=db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("""
                INSERT INTO users (id, username, password_hash, role, org_id, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?);
            """, (user_id, username.strip(), pwd_hash, role, org_id, now_iso))
            conn.execute("COMMIT;")
            return True, f"User {username} created successfully.", user_id
        except sqlite3.IntegrityError:
            conn.execute("ROLLBACK;")
            return False, f"Username '{username}' already exists.", None
        except Exception as e:
            conn.execute("ROLLBACK;")
            return False, f"Error creating user: {str(e)}", None
        finally:
            conn.close()

def update_user_password(
    user_id: str,
    new_password: str,
    db_path: Optional[str] = None
) -> Tuple[bool, str]:
    """Updates user password hash. Enforces minimum length >= 10."""
    if not new_password or len(new_password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters."

    new_hash = hash_password(new_password)
    from database import get_connection, _db_lock
    with _db_lock:
        conn = get_connection(db_path=db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?;", (new_hash, user_id))
            if cursor.rowcount == 0:
                conn.execute("ROLLBACK;")
                return False, f"User '{user_id}' not found."
            conn.execute("COMMIT;")
            return True, "Password updated successfully."
        except Exception as e:
            try:
                conn.execute("ROLLBACK;")
            except Exception:
                pass
            return False, f"Failed to update password: {str(e)}"
        finally:
            conn.close()
