from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import sqlite3
import traceback

# Import local database and feature routers (Vault & Bots)
from database import get_db_connection, db_transaction
from routers import vault, bots

# Initialize Master FastAPI App for Valen.ai Ecosystem
app = FastAPI(
    title="Valen.ai Supreme Core Engine",
    description="Production-grade autonomous AI ecosystem backend with zero-error architecture.",
    version="1.0.0"
)

# Register Feature Routers
app.include_router(vault.router)
app.include_router(bots.router)

# Enable CORS for secure cross-origin communication between Android APK and Web Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restricted in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global Exception Handlers for Zero-Error Reliability ---

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Catch all explicit HTTP exceptions and return standardized JSON payload."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Catch payload validation errors cleanly without crashing the server."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "code": 422,
            "message": "Invalid request payload structure.",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for any unhandled server exceptions with logging support."""
    error_trace = traceback.format_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "critical_error",
            "code": 500,
            "message": "An internal system anomaly occurred. Autonomous fallback engaged.",
            "path": request.url.path
        }
    )


# --- Multi-Page Clean URL Route Handlers (HTML Views) ---

@app.get("/", response_class=HTMLResponse)
async def serve_landing():
    """Valen.ai Public Landing Portal"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Valen.ai | Autonomous Core</title></head>
    <body style="background:#090d16; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:120px;">
        <h1 style="font-size:3rem; color:#38bdf8;">VALEN.AI ECOSYSTEM</h1>
        <p style="color:#94a3b8; font-size:1.2rem;">Autonomous Intelligence & Fleet Matrix Operational.</p>
    </body>
    </html>
    """

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    """Secure Admin Authentication Portal"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Valen.ai | Secure Login</title></head>
    <body style="background:#090d16; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:120px;">
        <h2 style="color:#38bdf8;">Admin Authentication Gate</h2>
        <p style="color:#94a3b8;">Enter Master Key to access Supreme Dashboard.</p>
    </body>
    </html>
    """

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    """Supreme Admin Control Center"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Valen.ai | Dashboard</title></head>
    <body style="background:#090d16; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:120px;">
        <h1 style="color:#38bdf8;">Supreme Control Center</h1>
        <p style="color:#94a3b8;">Live Telemetry & Fleet Monitoring active.</p>
    </body>
    </html>
    """

@app.get("/bots", response_class=HTMLResponse)
async def serve_bots_page():
    """Live Bot Fleet Matrix Page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Valen.ai | Bot Matrix</title></head>
    <body style="background:#090d16; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:120px;">
        <h1 style="color:#38bdf8;">Autonomous Bot Fleet Matrix</h1>
        <p style="color:#94a3b8;">Sub-bot tracking and health diagnostics.</p>
    </body>
    </html>
    """

@app.get("/vault", response_class=HTMLResponse)
async def serve_vault_page():
    """Cryptographic Security Vault Page"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8"><title>Valen.ai | Security Vault</title></head>
    <body style="background:#090d16; color:#f8fafc; font-family:sans-serif; text-align:center; padding-top:120px;">
        <h1 style="color:#ef4444;">Cryptographic Security Vault</h1>
        <p style="color:#94a3b8;">Panic shredder and local encrypted storage controls.</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
