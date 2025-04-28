import sqlite3
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: str = "full_data.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        # Таблица участков
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS plots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            coordinates TEXT NOT NULL,
            area REAL NOT NULL,
            type TEXT DEFAULT 'Собственный',
            status TEXT DEFAULT 'Не задан',
            status_changed TEXT,
            auto_status INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            cadastral_number TEXT,
            property_type TEXT,
            assignment_date TEXT,
            address TEXT,
            area_sqm REAL,
            land_category TEXT,
            land_use TEXT,
            cadastral_value REAL,
            owner_name TEXT,
            owner_contacts TEXT
            rental_expiry_date TEXT
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS harvests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plot_id INTEGER,
            date TEXT,
            culture TEXT,
            amount REAL,
            FOREIGN KEY(plot_id) REFERENCES plots(id) ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)

        self.conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        cursor = self.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def close(self):
        self.conn.close()
