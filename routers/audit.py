from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
import sqlite3
from database import get_db_connection, db_transaction

# Initialize Audit Logs Router
router = APIRouter(prefix="/api/v1/audit", tags=["System Audit Matrix"])

# Pydantic Model for Audit Log Ingestion
class AuditLogPayload(BaseModel):
    event_level: str = Field(..., pattern="^(INFO|WARNING|CRITICAL|SECURITY)$")
    module_name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=5)
    ip_address: str = Field(default="127.0.0.1")


# --- Audit Logs Endpoints ---

@router.get("/logs")
async def fetch_audit_logs(limit: int = 50, x_master_key: str = Header(None)):
    """Fetch recent system audit logs and security event traces."""
    if not x_master_key or x_master_key != "VALEN_SUPREME_SECURE_KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Master key required to inspect security audit logs."
        )
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        logs = [dict(row) for row in rows]
        return {
            "status": "success",
            "count": len(logs),
            "data": logs
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")


@router.post("/log/record")
async def record_audit_event(payload: AuditLogPayload):
    """Securely record an operational or security event into the audit trail."""
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (event_level, module_name, description, ip_address, timestamp)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (payload.event_level, payload.module_name, payload.description, payload.ip_address))
            
        return {
            "status": "success",
            "message": "Audit event recorded successfully."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record audit log: {str(e)}")


@router.delete("/purge/all")
async def purge_audit_logs(x_master_key: str = Header(None)):
    """Permanently clear all audit logs (Emergency wipe command)."""
    if not x_master_key or x_master_key != "VALEN_SUPREME_SECURE_KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Master key required for audit purge."
        )
        
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM audit_logs")
            
        return {
            "status": "success",
            "message": "All system audit logs have been successfully shredded."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit purge failed: {str(e)}")
