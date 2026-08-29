"""
CRM System - Database Connection & Transaction Manager
Uses standard library sqlite3 with thread safety and WAL journaling
"""

import sqlite3
import threading
from typing import Optional, Any, List, Dict, Tuple
from config.app_config import CONFIG


class DatabaseConnectionManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnectionManager, cls).__new__(cls)
                cls._instance._init_manager()
            return cls._instance

    def _init_manager(self):
        self.db_path = CONFIG.database.db_path
        self._local = threading.local()

    def get_connection(self) -> sqlite3.Connection:
        """Get or create thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=CONFIG.database.timeout_seconds,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Return dict-like row objects
            
            # Enable WAL mode for high concurrent read/write throughput
            if CONFIG.database.enable_wal_mode:
                conn.execute("PRAGMA journal_mode=WAL;")
            
            # Enable foreign key enforcement
            conn.execute("PRAGMA foreign_keys=ON;")
            self._local.connection = conn
            
        return self._local.connection

    def execute(self, sql: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute a query and auto-commit if outside manual transaction."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor

    def fetch_all(self, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Fetch all matching rows as dictionaries."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def fetch_one(self, sql: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """Fetch single matching row as dictionary."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def execute_script(self, script: str):
        """Execute multiple SQL statements."""
        conn = self.get_connection()
        conn.executescript(script)
        conn.commit()

    def close(self):
        """Close thread-local connection."""
        if hasattr(self._local, "connection") and self._local.connection is not None:
            self._local.connection.close()
            self._local.connection = None


# Global DB Manager
DB = DatabaseConnectionManager()
