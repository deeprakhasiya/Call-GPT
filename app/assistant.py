# app/assistant.py

import json
import sqlite3
from livekit.agents import Agent, ChatContext, ChatMessage, StopResponse

DB_FILE = "requests.db"
KB_FILE = "knowledge.json"

conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

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

        for q, a in kb.items():
            if q in text_lower:
                await self.session.say(a)
                raise StopResponse()

        await self.session.say("Let me check with my supervisor and get back to you.")
        cursor.execute("INSERT INTO requests (question, status) VALUES (?, 'pending')", (text,))
        conn.commit()
        print(f"[NOTIFY] New pending question: {text}")
        raise StopResponse()
