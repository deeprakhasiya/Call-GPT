# app/main.py
import asyncio
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions
from livekit.plugins import cartesia, deepgram, silero, noise_cancellation,google
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from app.assistant import SalonAssistant
from app.tts_engine import get_tts_engine
from app.api_routes import start_api

agent_session = None
agent_loop = None

async def entrypoint(ctx: agents.JobContext):
    global agent_session, agent_loop
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="en"),
        llm=google.LLM(model="gemini-2.0-flash", temperature=0.7),
        tts=get_tts_engine(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    agent_session = session
    agent_loop = asyncio.get_running_loop()
    start_api(session, agent_loop)

    assistant = SalonAssistant()
    await session.start(room=ctx.room, agent=assistant,
                        room_input_options=RoomInputOptions(noise_cancellation=noise_cancellation.BVC()))
    await session.say("Hello! Welcome to our salon. How can I assist you today?", allow_interruptions=False)

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
