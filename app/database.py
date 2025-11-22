import sqlite3
import os

DB_PATH = "bot_database.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_db_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_tour_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            tour_started_at TEXT,
            tour_completed_at TEXT,
            completion_time_seconds INTEGER
        )         
''')
    
    conn.commit()
    conn.close()

init_database()