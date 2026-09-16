from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import sqlite3
from database import get_db_connection, db_transaction

# Initialize Telemetry Router
router = APIRouter(prefix="/api/v1/telemetry", tags=["System Telemetry Matrix"])

# Pydantic Model for Telemetry Snapshot Ingestion
class TelemetryPayload(BaseModel):
    node_name: str = Field(..., min_length=2, max_length=100)
    total_cpu: float = Field(..., ge=0.0, le=100.0)
    total_ram: float = Field(..., ge=0.0, le=100.0)
    active_threads: int = Field(..., ge=1)
    network_latency_ms: float = Field(..., ge=0.0)


# --- Telemetry Endpoints ---

@router.get("/snapshot/latest")
async def fetch_latest_telemetry():
    """Fetch the most recent system performance snapshot across active nodes."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_telemetry ORDER BY timestamp DESC LIMIT 10")
        rows = cursor.fetchall()
        conn.close()
        
        snapshots = [dict(row) for row in rows]
        return {
            "status": "success",
            "count": len(snapshots),
            "data": snapshots
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry snapshots: {str(e)}")


@router.post("/snapshot/record")
async def record_telemetry_snapshot(payload: TelemetryPayload):
    """Record a new performance snapshot for system health monitoring."""
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_telemetry (node_name, total_cpu, total_ram, active_threads, network_latency_ms, timestamp)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                payload.node_name,
                payload.total_cpu,
                payload.total_ram,
                payload.active_threads,
                payload.network_latency_ms
            ))
            
        return {
            "status": "success",
            "message": f"Telemetry snapshot recorded for node '{payload.node_name}'."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record telemetry: {str(e)}")
