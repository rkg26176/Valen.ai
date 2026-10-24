from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import uuid
from database import initialize_enterprise_database, db_transaction

app = FastAPI(title="Valen.ai Enterprise Ecosystem")

initialize_enterprise_database()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.post("/api/chat")
async def chat_endpoint(session_id: str = Form(...), prompt: str = Form(...)):
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (session_id, sender, content) VALUES (?, 'user', ?)", (session_id, prompt))
        
        ai_reply = f"Hello! I am Valen.ai. I received your message: '{prompt}'. How can I assist you further today?"
        
        cursor.execute("INSERT INTO messages (session_id, sender, content) VALUES (?, 'ai', ?)", (session_id, ai_reply))
        conn.commit()
    
    return {"status": "success", "reply": ai_reply}

@app.post("/api/report")
async def submit_report(description: str = Form(...)):
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO reports (description) VALUES (?)", (description,))
        conn.commit()
    return {"status": "success", "message": "Report submitted to admin panel successfully."}

@app.post("/api/generate_key")
async def generate_api_key(user_id: str = Form("guest")):
    with db_transaction() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM api_keys WHERE user_identifier = ?", (user_id,))
        row = cursor.fetchone()
        if row["cnt"] >= 3:
            raise HTTPException(status_code=400, detail="Monthly limit reached: Max 3 free API keys allowed.")
        
        new_key = f"valen_live_{uuid.uuid4().hex[:16]}"
        cursor.execute("INSERT INTO api_keys (key_id, user_identifier) VALUES (?, ?)", (new_key, user_id))
        conn.commit()
    return {"status": "success", "api_key": new_key}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
