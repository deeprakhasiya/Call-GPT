# main_agent.py

import os, json, sqlite3, asyncio, threading
from dotenv import load_dotenv
from fastapi import Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, StopResponse
from livekit.agents import ChatContext, ChatMessage
from livekit.plugins import cartesia, deepgram, noise_cancellation, silero, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# ─── GLOBALS ──────────────────────────────────────────────────────────────────
agent_session: AgentSession = None
agent_loop: asyncio.AbstractEventLoop = None

# ─── LOAD CONFIG ──────────────────────────────────────────────────────────────
load_dotenv()   # LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET, DEEPGRAM_API_KEY, etc.

# ─── PERSISTENCE SETUP ────────────────────────────────────────────────────────
DB_FILE = "requests.db"
KB_FILE = "knowledge.json"

# SQLite init
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT,
    status TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

# JSON KB init
if not os.path.exists(KB_FILE):
    with open(KB_FILE, "w") as f:
        json.dump({
            "what services do you offer": "We offer haircuts, coloring, styling, manicures, pedicures, and facial treatments.",
            "what are your opening hours": "Our salon is open 9 AM–7 PM, Mon–Sat.",
            "where are you located": "123 Main Street, Springfield.",
            "who is the owner": "Alice Johnson, founder and lead stylist."
        }, f, indent=2)

# ─── FASTAPI SUPERVISOR UI ────────────────────────────────────────────────────
app = FastAPI(title="Supervisor API")
templates = Jinja2Templates(directory="templates")

class AnswerPayload(BaseModel):
    answer: str

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
    if agent_session is None or agent_loop is None:
        raise HTTPException(503, "Agent session not ready yet. Try again shortly.")

    # Check that this ID is pending
    cursor.execute(
        "SELECT question FROM requests WHERE id=? AND status='pending'",
        (req_id,)
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(404, f"No pending request with id={req_id}")

    question_text = row[0]

    # Update DB + KB
    cursor.execute(
        "UPDATE requests SET answer=?, status='answered' WHERE id=?",
        (payload.answer.strip(), req_id)
    )
    conn.commit()

    # Update JSON knowledge base
    with open(KB_FILE, "r+") as f:
        kb = json.load(f)
        kb[question_text.lower()] = payload.answer.strip()
        f.seek(0); f.truncate()
        json.dump(kb, f, indent=2)

    # Schedule TTS on agent’s loop
    def speak():
        return agent_session.say(payload.answer.strip())

    agent_loop.call_soon_threadsafe(
    lambda: asyncio.create_task(speak_with_followup(payload.answer.strip())))


    return {
        "status":   "spoken",
        "id":       req_id,
        "question": question_text,
        "answer":   payload.answer
    }
@app.post("/answer_ui/{req_id}")
async def answer_from_ui(req_id: int, answer: str = Form(...)):
    global agent_loop
    # This updates DB and KB
    payload = AnswerPayload(answer=answer)
    await post_answer(req_id, payload)  # Optional: this updates DB & KB

    # 🔥 Trigger speak on agent loop manually (to ensure it works from UI)
    # if agent_loop:
    #     agent_loop.call_soon_threadsafe(
    #         lambda: asyncio.create_task(speak_with_followup(answer.strip()))
    #     )

    return RedirectResponse(url="/dashboard", status_code=303)

async def speak_with_followup(answer: str):
    await agent_session.say(answer)
    await agent_session.say("You can ask me another question anytime. Thank you!")

def start_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

# ─── AGENT DEFINITION ─────────────────────────────────────────────────────────
class SalonAssistant(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful salon assistant.")

    async def on_user_turn_completed(self, ctx: ChatContext, new_message: ChatMessage):
        text = new_message.text_content
        if not text:
            return
        text_lower = text.lower()
        with open(KB_FILE) as f:
            kb = json.load(f)
        # Known?
        for q, a in kb.items():
            if q in text_lower:
                await self.session.say(a)
                raise StopResponse()
        # Else escalate
        await self.session.say("Let me check with my supervisor and get back to you.")
        cursor.execute("INSERT INTO requests (question, status) VALUES (?, 'pending')", (text,))
        conn.commit()
        print(f"[NOTIFY] New pending question: {text}")
        raise StopResponse()


# ─── ENTRYPOINT ───────────────────────────────────────────────────────────────
async def entrypoint(ctx: agents.JobContext):
    global agent_session, agent_loop
    await ctx.connect()
    # 1) Create session
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=google.LLM(model="gemini-2.0-flash", temperature=0.7),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )
    # 2) Assign globals *before* API starts
    agent_session = session
    agent_loop = asyncio.get_running_loop()
    # 3) Start API in background
    threading.Thread(target=start_api, daemon=True).start()
    # 4) Start LiveKit agent
    assistant = SalonAssistant()
    await session.start(room=ctx.room, agent=assistant,
                        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    # 5) Greet
    await session.say("Hello! Welcome to our salon. How can I assist you today?", allow_interruptions=False)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
