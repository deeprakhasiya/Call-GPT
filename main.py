# main.py
from gemini_utils import query_gemini
from db_utils import init_db, get_answer_from_db, add_pending_question
from config import CONFIDENCE_THRESHOLD

def handle_question(question):
    init_db()
    human = get_answer_from_db(question)
    if human:
        print(f"[DB] {human}")
        return
    ai_ans, conf = query_gemini(question)
    if conf >= CONFIDENCE_THRESHOLD:
        print(f"[AI] {ai_ans} ({conf:.1f}%)")
    else:
        add_pending_question(question)
        print(f"[Pending] Low confidence ({conf:.1f}%), escalated to human.")

if __name__ == '__main__':
    while True:
        q = input("Enter question (or 'exit'): ")
        if q.lower()=='exit':
            break
        handle_question(q)
