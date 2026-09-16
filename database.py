import sqlite3
import os
import threading
from contextlib import contextmanager

DB_NAME = "valen_core.db"
DB_PATH = os.path.abspath(DB_NAME)

# Thread lock for safe concurrent operations in asynchronous environments
_db_lock = threading.Lock()

def get_db_connection():
    """
    Establish a high-performance SQLite connection with WAL mode,
    busy timeout, and row factory configuration.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
        # Enable Write-Ahead Logging for concurrent reads and writes
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-64000;")  # 64MB cache
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"Database connection failure: {str(e)}")

@contextmanager
def db_transaction():
    """Context manager for safe database transactions with automatic rollback on error."""
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
    """
    Create all core tables required for the 10,000+ line ecosystem,
    including Bot Matrix, Telemetry, Audit Logs, and Secure Vaults.
    """
    with db_transaction() as conn:
        cursor = conn.cursor()
        
        # 1. Bot Fleet Matrix Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_registry (
                bot_id TEXT PRIMARY KEY,
                bot_name TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('ACTIVE', 'OFFLINE', 'STANDBY', 'ERROR')),
                cpu_load REAL DEFAULT 0.0,
                memory_usage REAL DEFAULT 0.0,
                task_queue_count INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                error_trace TEXT
            )
        """)
        
        # 2. System Audit Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_level TEXT NOT NULL CHECK(event_level IN ('INFO', 'WARNING', 'CRITICAL', 'SECURITY')),
                module_name TEXT NOT NULL,
                description TEXT NOT NULL,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Incognito Local Chat Sessions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS incognito_sessions (
                session_id TEXT PRIMARY KEY,
                encrypted_payload TEXT NOT NULL,
                client_fingerprint TEXT,
                expires_at TIMESTAMP,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 4. System Telemetry Snapshots Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_telemetry (
                telemetry_id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_name TEXT NOT NULL,
                total_cpu REAL,
                total_ram REAL,
                active_threads INTEGER,
                network_latency_ms REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 5. Cryptographic Vault Table for Secure Credentials
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS secure_vault (
                key_identifier TEXT PRIMARY KEY,
                encrypted_secret TEXT NOT NULL,
                access_level INTEGER DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("[SUCCESS] Enterprise database schema and tables initialized securely with WAL mode.")

if __name__ == "__main__":
    initialize_enterprise_database()
