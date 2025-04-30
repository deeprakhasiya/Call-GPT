# main.py
from gemini_utils import query_gemini
from db_utils import get_answer_from_db, save_human_answer, add_pending_question
from config import CONFIDENCE_THRESHOLD

from data import init_db

def handle_question(question, return_dict=False):
    init_db()
    # 1) Check DB
    human = get_answer_from_db(question)
    if human:
        result = {"source": "db", "answer": human}
        return result if return_dict else print(f"[DB] {human}")

    # 2) AI call
    ai_ans, conf = query_gemini(question)
    if conf >= CONFIDENCE_THRESHOLD:
        result = {
          "source": "ai",
          "answer": ai_ans,
          "confidence": conf
        }
    else:
        add_pending_question(question)
        result = {
          "source": "pending",
          "message": "Low confidence; escalated to human",
          "confidence": conf
        }
    return result if return_dict else print(result)

if __name__ == '__main__':
    while True:
        user_q = input("\nEnter question (or 'exit' to quit): ")
        if user_q.lower() == 'exit':
            break
        handle_question(user_q)
# http://localhost:5000/swagger , use swaager ui to test the api