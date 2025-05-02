from dotenv import load_dotenv
from google import genai
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions , ChatMessage 
from livekit.plugins import (
    openai,
    cartesia,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from my_gemini_llm import GeminiLLM
import os
load_dotenv()

llm_model = GeminiLLM()

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions="You are a helpful voice AI assistant.")

    async def on_message(self, message: ChatMessage) -> None:
        print(f"👂 User said: {message.text}")

        # Use your GeminiLLM class
        reply_text = await llm_model.complete(message.text)

        print(f"📤 Replied: {reply_text}")
        return reply_text  # Automatically spoken by TTS engine






async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        stt=deepgram.STT(model="nova-3", language="multi"),
        llm=GeminiLLM(),
        tts=cartesia.TTS(),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=Assistant(),
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


    # DEEPGRAM_API_URL = os.getenv("DEEPGRAM_API_URL")
    # CARTESIAN_API_URL = os.getenv("CARTESIAN_API_URL")
    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))