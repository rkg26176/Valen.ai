import sqlite3
import os
import threading
from contextlib import contextmanager

DB_NAME = "valen_core.db"
DB_FILE = DB_NAME
DB_PATH = os.path.abspath(DB_NAME)

_db_lock = threading.Lock()

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Database connection failure: {str(e)}")

@contextmanager
def db_transaction():
    conn = get_db_connection()
    with _db_lock:
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

def initialize_enterprise_database():
    with db_transaction() as conn:
        cursor = conn.cursor()
        
        # 1. Conversations Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                is_pinned INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                sender TEXT CHECK(sender IN ('user', 'ai')),
                content TEXT,
                feedback TEXT CHECK(feedback IN ('like', 'dislike', 'none')) DEFAULT 'none',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES conversations(session_id) ON DELETE CASCADE
            )
        """)
        
        # 3. Free API Keys Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                key_id TEXT PRIMARY KEY,
                user_identifier TEXT,
                usage_count INTEGER DEFAULT 0,
                max_limit INTEGER DEFAULT 1000,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. Reports & Legal Issues Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                report_id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                status TEXT DEFAULT 'PENDING',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. Admin Bot Fleet Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_fleet (
                bot_id TEXT PRIMARY KEY,
                bot_name TEXT,
                status TEXT CHECK(status IN ('ACTIVE', 'OFFLINE', 'STANDBY')),
                task_description TEXT
            )
        """)
        
        # 6. Admin AI Inbox / Bug Fixes Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_inbox (
                inbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_title TEXT,
                proposed_patch TEXT,
                status TEXT CHECK(status IN ('PENDING', 'ACCEPTED', 'REJECTED')) DEFAULT 'PENDING',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("[SUCCESS] Valen.ai database and tables fully synchronized.")

if __name__ == "__main__":
    initialize_enterprise_database()
