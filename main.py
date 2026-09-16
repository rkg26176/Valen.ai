from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import sqlite3
import traceback

# Import local database and all feature routers (Vault, Bots, Chat, Audit, Telemetry)
from database import get_db_connection, db_transaction
from routers import vault, bots, chat, audit, telemetry

# Initialize Master FastAPI App for Valen.ai Ecosystem
app = FastAPI(
    title="Valen.ai Supreme Core Engine",
    description="Production-grade autonomous AI ecosystem backend with zero-error architecture.",
    version="1.0.0"
)

# Register All Feature Routers
app.include_router(vault.router)
app.include_router(bots.router)
app.include_router(chat.router)
app.include_router(audit.router)
app.include_router(telemetry.router)

# Initialize Jinja2 Templates Directory for Multi-Page Frontend UI
templates = Jinja2Templates(directory="templates")

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


# --- Multi-Page Clean URL Route Handlers (Jinja2 Templates Integration) ---

@app.get("/", response_class=HTMLResponse)
async def serve_landing(request: Request):
    """Valen.ai Public Landing Portal"""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def serve_login(request: Request):
    """Secure Admin Authentication Portal"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Supreme Admin Control Center"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/bots", response_class=HTMLResponse)
async def serve_bots_page(request: Request):
    """Live Bot Fleet Matrix Page"""
    return templates.TemplateResponse("bots.html", {"request": request})

@app.get("/vault", response_class=HTMLResponse)
async def serve_vault_page(request: Request):
    """Cryptographic Security Vault Page"""
    return templates.TemplateResponse("vault.html", {"request": request})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
