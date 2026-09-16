from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
import sqlite3
from database import get_db_connection, db_transaction

# Initialize Bot Fleet Router
router = APIRouter(prefix="/api/v1/bots", tags=["Bot Fleet Matrix"])

# Pydantic Model for Detailed Bot Telemetry Heartbeat
class BotHeartbeatPayload(BaseModel):
    bot_id: str = Field(..., min_length=2, max_length=50)
    bot_name: str = Field(..., min_length=2, max_length=100)
    status: str = Field(..., pattern="^(ACTIVE|OFFLINE|STANDBY|ERROR)$")
    cpu_load: float = Field(..., ge=0.0, le=100.0)
    memory_usage: float = Field(..., ge=0.0, le=100.0)
    task_queue_count: int = Field(default=0, ge=0)
    error_trace: str = Field(default=None)


# --- Bot Fleet Endpoints ---

@router.get("/fleet/status")
async def get_full_fleet_status():
    """Fetch real-time operational status and diagnostics of all registered autonomous bots."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bot_registry ORDER BY last_active DESC")
        rows = cursor.fetchall()
        conn.close()
        
        fleet_data = [dict(row) for row in rows]
        return {
            "status": "success",
            "total_bots": len(fleet_data),
            "data": fleet_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fleet matrix: {str(e)}")


@router.post("/heartbeat")
async def bot_heartbeat_sync(payload: BotHeartbeatPayload):
    """Receive live telemetry heartbeat from background sub-bots to prevent idle dropouts."""
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO bot_registry (
                    bot_id, bot_name, status, cpu_load, memory_usage, task_queue_count, last_active, error_trace
                )
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ON CONFLICT(bot_id) DO UPDATE SET
                    bot_name = excluded.bot_name,
                    status = excluded.status,
                    cpu_load = excluded.cpu_load,
                    memory_usage = excluded.memory_usage,
                    task_queue_count = excluded.task_queue_count,
                    last_active = CURRENT_TIMESTAMP,
                    error_trace = excluded.error_trace
            """, (
                payload.bot_id, 
                payload.bot_name, 
                payload.status, 
                payload.cpu_load, 
                payload.memory_usage, 
                payload.task_queue_count,
                payload.error_trace
            ))
            
        return {
            "status": "success",
            "message": f"Heartbeat acknowledged for bot ID: {payload.bot_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Heartbeat sync failed: {str(e)}")


@router.delete("/terminate/{bot_id}")
async def terminate_bot_node(bot_id: str, x_master_key: str = Header(None)):
    """Forcefully deregister and terminate a rogue or frozen sub-bot node."""
    if not x_master_key or x_master_key != "VALEN_SUPREME_SECURE_KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Master key required to terminate bot nodes."
        )
        
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM bot_registry WHERE bot_id = ?", (bot_id,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Bot ID not found in active registry.")
                
        # Log termination event in audit logs
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (event_level, module_name, description)
                VALUES ('WARNING', 'BOT_MATRIX', ?)
            """, (f"Bot node {bot_id} forcefully terminated via remote command.",))

        return {
            "status": "success",
            "message": f"Bot node {bot_id} successfully terminated and purged."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
