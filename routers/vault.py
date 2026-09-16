from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
import sqlite3
import os
from database import get_db_connection, db_transaction

# Initialize Vault Router
router = APIRouter(prefix="/api/v1/vault", tags=["Security Vault"])

# Pydantic Model for Storing Secrets
class VaultSecretPayload(BaseModel):
    key_identifier: str = Field(..., min_length=2, max_length=100)
    encrypted_secret: str = Field(..., min_length=5)
    access_level: int = Field(default=1, ge=1, le=5)


# --- Vault Endpoints ---

@app_router_placeholder := router.post("/store")
async def store_secret(payload: VaultSecretPayload, x_master_key: str = Header(None)):
    """Store or update sensitive API keys or credentials securely in the vault."""
    # Simple master key validation safeguard
    if not x_master_key or x_master_key != "VALEN_SUPREME_SECURE_KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access: Invalid or missing Master Key."
        )
    
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO secure_vault (key_identifier, encrypted_secret, access_level, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key_identifier) DO UPDATE SET
                    encrypted_secret = excluded.encrypted_secret,
                    access_level = excluded.access_level,
                    updated_at = CURRENT_TIMESTAMP
            """, (payload.key_identifier, payload.encrypted_secret, payload.access_level))
            
        return {
            "status": "success",
            "message": f"Secret '{payload.key_identifier}' encrypted and stored in vault."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/shred/{key_identifier}")
async def cryptographic_shred(key_identifier: str, x_master_key: str = Header(None)):
    """Permanently shred a specific secret from the local secure vault."""
    if not x_master_key or x_master_key != "VALEN_SUPREME_SECURE_KEY":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized access: Panic shred command rejected."
        )
    
    try:
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM secure_vault WHERE key_identifier = ?", (key_identifier,))
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Secret key identifier not found.")
                
        # Log the security panic event in audit logs
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (event_level, module_name, description)
                VALUES ('SECURITY', 'VAULT_SHRED', ?)
            """, (f"Cryptographic shred executed on key: {key_identifier}",))

        return {
            "status": "success",
            "message": f"Key '{key_identifier}' has been permanently shredded from storage."
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
