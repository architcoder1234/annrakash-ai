-- Migration 004: Security Hardening, Throttling Audit Log, and Canonical Status Repair
-- Enforces login audit tracking, 5-minute lockout windows, and cleans legacy status strings.

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    session_id TEXT,
    ip_address TEXT,
    attempt_time TEXT NOT NULL,
    success INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_login_attempts_username_time ON login_attempts(username, attempt_time);

-- Repair any legacy status records to match canonical WorkflowStatus
UPDATE donations SET status = 'Requested' WHERE status IN ('Pickup Requested', 'Pending');
UPDATE pickup_requests SET status = 'Requested' WHERE status IN ('Pickup Requested', 'Pending');
UPDATE donations SET status = 'Confirmed' WHERE status = 'Accepted';
UPDATE pickup_requests SET status = 'Confirmed' WHERE status = 'Accepted';
