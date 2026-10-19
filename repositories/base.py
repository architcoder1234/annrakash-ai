"""
Base repository providing thread-safe SQLite connection handling,
BEGIN IMMEDIATE transactions, and strictly parameter-bound queries.
"""

import sqlite3
import threading
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from database import get_connection

class BaseRepository:
    _lock = threading.Lock()

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_conn(self) -> sqlite3.Connection:
        return get_connection(self.db_path)

    @contextmanager
    def transaction(self):
        """Context manager for explicit BEGIN IMMEDIATE transaction with write lock."""
        with self._lock:
            conn = self.get_conn()
            try:
                conn.execute("BEGIN IMMEDIATE;")
                yield conn
                conn.execute("COMMIT;")
            except Exception:
                conn.execute("ROLLBACK;")
                raise
            finally:
                conn.close()

    def execute_query(self, query: str, params: Tuple = (), conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        """Executes a read query with parameter binding and returns list of dictionaries."""
        target_conn = conn or self.get_conn()
        try:
            cursor = target_conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            if conn is None:
                target_conn.close()

    def execute_one(self, query: str, params: Tuple = (), conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        """Executes a read query with parameter binding and returns a single dictionary."""
        target_conn = conn or self.get_conn()
        try:
            cursor = target_conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            if conn is None:
                target_conn.close()

    def execute_non_query(self, query: str, params: Tuple = (), conn: Optional[sqlite3.Connection] = None) -> int:
        """Executes a write query under write lock."""
        if conn is not None:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount
        else:
            with self._lock:
                target_conn = self.get_conn()
                try:
                    cursor = target_conn.cursor()
                    cursor.execute(query, params)
                    return cursor.rowcount
                finally:
                    target_conn.close()
