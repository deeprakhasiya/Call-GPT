# gemini_utils.py
from google import genai
import random
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
# Initialize the Gemini client (make sure to set your API key as shown above)
API = os.getenv('GOOGLE_API_KEY')
gemini_client = genai.Client(api_key=API)

def query_gemini(question):
    """Call the Gemini model to answer the question."""
    response = gemini_client.models.generate_content(
        model='gemini-2.0-flash-001',
        contents=question
    )
    answer_text = response.text.strip()
    # NOTE: Gemini API does not return a 'confidence' by default.
    # Here we simulate it for demonstration/testing purposes.
    confidence = random.uniform(0, 100)  # simulate confidence score (0-100)
    # confidence = 100
    return answer_text, confidence
