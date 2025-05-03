# 💇‍♀️ AI-Powered Salon Voice Assistant

A smart, real-time salon assistant powered by:
- 🧠 Google Gemini for intelligent answers
- 🗣️ Deepgram for speech recognition (STT)
- 🔊 Cartesia for text-to-speech (TTS)
- 🧘 FastAPI-based supervisor interface
- 💾 SQLite + JSON for persistent knowledge base
- 🎙️ LiveKit Agent SDK for real-time conversation

---

## 🚀 Features

- Responds to customer questions in natural language
- Escalates unknown queries to a human supervisor
- Supervisor can answer pending questions via REST API
- Learns new Q&A over time (KB auto-updated)
- Real-time voice conversations with speaker output
- Thread-safe `asyncio` + FastAPI + LiveKit Agent integration

---

## 🔧 Tech Stack

| Component      | Tech Used                |
|----------------|--------------------------|
| LLM            | Google Gemini            |
| Speech to Text | Deepgram Nova            |
| Text to Speech | Cartesia (or Google)     |
| Agent System   | LiveKit Agents SDK       |
| Voice Activity | Silero + Multilingual EOU|
| API Backend    | FastAPI                  |
| Persistence    | SQLite + JSON            |
| Runtime        | Python 3.10+             |

---
