# my_gemini_llm.py
from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()  # Load environment variables from .env file
# Initialize the Gemini client (make sure to set your API key as shown above)
API = os.getenv('GOOGLE_API_KEY')

class GeminiLLM:
    def __init__(self, model='gemini-pro'):
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(model)

    async def complete(self, prompt: str):
        response = self.model.generate_content(prompt)
        return response.text
