import os
import sqlite3
import uvicorn
from database import DB_FILE

def initialize_database_tables():
    """Ensure all core enterprise tables exist with WAL mode enabled on startup."""
    print("[*] Initializing Valen.ai SQLite Enterprise Tables...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Enable WAL Mode for high-concurrency performance
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # 1. Bot Registry Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bot_registry (
            bot_id TEXT PRIMARY KEY,
            bot_name TEXT NOT NULL,
            status TEXT NOT NULL,
            cpu_load REAL,
            memory_usage REAL,
            task_queue_count INTEGER DEFAULT 0,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_trace TEXT
        );
    """)
    
    # 2. Secure Cryptographic Vault Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS secure_vault (
            key_identifier TEXT PRIMARY KEY,
            encrypted_secret TEXT NOT NULL,
            access_level INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 3. Incognito Chat Sessions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS incognito_sessions (
            session_id TEXT PRIMARY KEY,
            encrypted_payload TEXT NOT NULL,
            client_fingerprint TEXT,
            expires_at TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 4. System Audit Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_level TEXT NOT NULL,
            module_name TEXT NOT NULL,
            description TEXT NOT NULL,
            ip_address TEXT DEFAULT '127.0.0.1',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # 5. System Telemetry Metrics Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_name TEXT NOT NULL,
            total_cpu REAL,
            total_ram REAL,
            active_threads INTEGER,
            network_latency_ms REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    conn.close()
    print("[+] Database schema successfully verified and synchronized.")

if __name__ == "__main__":
    # Initialize DB before launching server
    initialize_database_tables()
    
    # Get dynamic port from cloud environment (defaults to 8000 for local testing)
    port = int(os.environ.get("PORT", 8000))
    print(f"[*] Launching Valen.ai Supreme Core Engine on port {port}...")
    
    uvicorn.run("main:app", host="0.0.0.0", port=port)
