# main_agent.py

import os
import json
import sqlite3
import asyncio
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, StopResponse
from livekit.agents import ChatContext, ChatMessage
from livekit.plugins import cartesia, deepgram, noise_cancellation, silero, google
from livekit.plugins.turn_detector.multilingual import MultilingualModel

# Load .env
load_dotenv()

# --- SQLite setup for escalations ---
DB_FILE = "requests.db"
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

# --- Knowledge base JSON ---
KB_FILE = "knowledge.json"
if not os.path.exists(KB_FILE):
    initial_kb = {
        "what services do you offer": "We offer haircuts, coloring, styling, manicures, pedicures, and facial treatments.",
        "what are your opening hours": "Our salon is open from 9 AM to 7 PM, Monday through Saturday.",
        "where are you located": "We are located at 123 Main Street, Springfield.",
        "who is the owner": "Our salon is owned by Alice Johnson, a professional stylist with 20 years of experience."
    }
    with open(KB_FILE, 'w') as f:
        json.dump(initial_kb, f, indent=2)

# --- Agent Definition ---
class SalonAssistant(Agent):
    def __init__(self):
        super().__init__(instructions="You are a helpful voice assistant for a salon business.")
        # we'll assign self.session in the entrypoint

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage):
        user_text = new_message.text_content
        if not user_text:
            return

        user_text_lower = user_text.lower()
        with open(KB_FILE, 'r') as f:
            knowledge = json.load(f)

        # Try to answer from KB
        for q_key, ans in knowledge.items():
            if q_key in user_text_lower:
                print(f"[KB] Answering known question: {user_text}")
                # speak via the attached session
                await self.session.say(ans)
                await turn_ctx.session.say(ans)
                raise StopResponse()

        # Unknown: escalate
        print(f"[ESCALATE] Unknown question: {user_text}")
        await self.session.say("Let me check with my supervisor and get back to you.")
        await turn_ctx.session.say("Let me check with my supervisor and get back to you.")

        # Log to SQLite
        cursor.execute(
            "INSERT INTO requests (question, status) VALUES (?, ?)",
            (user_text, "pending")
        )
        conn.commit()
        print(f"[DB] Logged pending question: {user_text}")
        print(f"[NOTIFY] Hey, I need help answering: \"{user_text}\"")
        raise StopResponse()


# --- Entrypoint to wire session + agent ---
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    # Create session with all plugins
    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=google.LLM(model="gemini-2.0-flash", temperature=0.7),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    # Instantiate agent and attach session
    assistant = SalonAssistant()

    # Run the session
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC()
        ),
    )

    # Initial greeting
    await session.say("Hello! Welcome to our salon. How can I assist you today?", allow_interruptions=False)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
