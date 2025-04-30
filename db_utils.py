# db_utils.py
import sqlite3

DB_PATH = 'data.db'

def get_answer_from_db(question):
    """Return the human-verified answer for the question, or None if not found."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT answer FROM answers WHERE question = ?", (question,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def save_human_answer(question, answer):
    """Save a human-verified answer and remove from pending."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("REPLACE INTO answers (question, answer) VALUES (?, ?)", (question, answer))
    c.execute("DELETE FROM pending WHERE question = ?", (question,))
    conn.commit()
    conn.close()

def add_pending_question(question):
    """Add a question to the pending table (if not already present)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO pending (question) VALUES (?)", (question,))
    conn.commit()
    conn.close()

def get_pending_questions():
    """Return a list of pending questions needing human answers."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT question FROM pending")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]
