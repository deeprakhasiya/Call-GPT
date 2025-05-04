# app/api_routes.py

import json, sqlite3, asyncio, threading
from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

DB_FILE = "requests.db"
KB_FILE = "knowledge.json"

app = FastAPI(title="Supervisor API")
templates = Jinja2Templates(directory="templates")

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

class AnswerPayload(BaseModel):
    answer: str

def start_api(session, loop):
    def run_api():
        global agent_session, agent_loop
        agent_session = session
        agent_loop = loop
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
    threading.Thread(target=run_api, daemon=True).start()

@app.get("/pending")
def get_pending():
    cursor.execute("SELECT id, question FROM requests WHERE status='pending'")
    return [{"id": r[0], "question": r[1]} for r in cursor.fetchall()]

@app.get("/history")
def get_history():
    cursor.execute("SELECT id, question, answer, status, timestamp FROM requests ORDER BY timestamp DESC")
    return [
        {"id": r[0], "question": r[1], "answer": r[2], "status": r[3], "time": r[4]}
        for r in cursor.fetchall()
    ]

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    cursor.execute("SELECT id, question FROM requests WHERE status='pending'")
    questions = [{"id": row[0], "question": row[1]} for row in cursor.fetchall()]
    return templates.TemplateResponse("dashboard.html", {"request": request, "questions": questions})

@app.post("/answer/{req_id}")
async def post_answer(req_id: int, payload: AnswerPayload):
    global agent_session, agent_loop
    cursor.execute("SELECT question FROM requests WHERE id=? AND status='pending'", (req_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, f"No pending request with id={req_id}")
    question_text = row[0]

    cursor.execute("UPDATE requests SET answer=?, status='answered' WHERE id=?", (payload.answer.strip(), req_id))
    conn.commit()

    with open(KB_FILE, "r+") as f:
        kb = json.load(f)
        kb[question_text.lower()] = payload.answer.strip()
        f.seek(0); f.truncate()
        json.dump(kb, f, indent=2)

    def speak():
        return agent_session.say(payload.answer.strip())

    agent_loop.call_soon_threadsafe(lambda: asyncio.create_task(speak_with_followup(payload.answer.strip())))

    return {
        "status": "spoken",
        "id": req_id,
        "question": question_text,
        "answer": payload.answer
    }

@app.post("/answer_ui/{req_id}")
async def answer_from_ui(req_id: int, answer: str = Form(...)):
    payload = AnswerPayload(answer=answer)
    await post_answer(req_id, payload)
    return RedirectResponse(url="/dashboard", status_code=303)

async def speak_with_followup(answer: str):
    await agent_session.say(answer)
    await agent_session.say("You can ask me another question anytime. Thank you!")

def start_api(session, loop):
    global agent_session, agent_loop
    agent_session = session
    agent_loop = loop
    threading.Thread(target=lambda: uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning"), daemon=True).start()

