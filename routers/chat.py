from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import sqlite3
from database import get_db_connection, db_transaction

# Initialize Incognito Chat Router
router = APIRouter(prefix="/api/v1/chat", tags=["Incognito Chat Matrix"])

# Pydantic Model for Encrypted Chat Payloads
class IncognitoMessagePayload(BaseModel):
    session_id: str = Field(..., min_length=2, max_length=100)
    encrypted_payload: str = Field(..., min_length=1)
    client_fingerprint: str = Field(default="VALEN_LOCAL_NODE")
    expires_at: str = Field(default=None)


# --- Incognito Chat Endpoints ---

@router.post("/save")
async def save_incognito_session(payload: IncognitoMessagePayload):
    """Store encrypted incognito messages securely inside the local SQLite WAL database."""
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO incognito_sessions (session_id, encrypted_payload, client_fingerprint, expires_at, timestamp)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    encrypted_payload = excluded.encrypted_payload,
                    client_fingerprint = excluded.client_fingerprint,
                    expires_at = excluded.expires_at,
                    timestamp = CURRENT_TIMESTAMP
            """, (payload.session_id, payload.encrypted_payload, payload.client_fingerprint, payload.expires_at))
            
        return {
            "status": "success",
            "message": f"Incognito session '{payload.session_id}' synchronized securely in local vault."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save secure session: {str(e)}")


@router.get("/session/{session_id}")
async def fetch_incognito_session(session_id: str):
    """Retrieve an active encrypted incognito session by its unique ID."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM incognito_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Incognito session not found or already shredded.")
            
        return {
            "status": "success",
            "data": dict(row)
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")


@router.delete("/purge/{session_id}")
async def purge_incognito_session(session_id: str):
    """Instantly purge/shred an incognito session to ensure zero data footprint."""
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM incognito_sessions WHERE session_id = ?", (session_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Session ID not found.")
                
        return {
            "status": "success",
            "message": f"Incognito session '{session_id}' successfully purged from storage."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Purge operation failed: {str(e)}")
