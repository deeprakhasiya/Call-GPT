import sqlite3

def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    # Table for answered questions (answered by human)
    c.execute('CREATE TABLE IF NOT EXISTS answers (question TEXT PRIMARY KEY, answer TEXT)')
    # Table for pending questions (unanswered)
    c.execute('CREATE TABLE IF NOT EXISTS pending (question TEXT PRIMARY KEY)')
    conn.commit()
    conn.close()

init_db()
