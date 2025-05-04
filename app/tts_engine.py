# app/tts_engine.py

import os
import pyttsx3
from livekit.plugins import cartesia

USE_FALLBACK = os.getenv("USE_LOCAL_TTS", "false").lower() == "true"

class FallbackTTS:
    def __init__(self):
        self.engine = pyttsx3.init()

    async def say(self, text, **kwargs):
        self.engine.say(text)
        self.engine.runAndWait()

def get_tts_engine():
    if USE_FALLBACK:
        print("[INFO] Using fallback pyttsx3 TTS engine.")
        return FallbackTTS()
    else:
        print("[INFO] Using Cartesia TTS engine.")
        return cartesia.TTS()
