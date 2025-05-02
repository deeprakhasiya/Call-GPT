# supervisor_console.py

import sqlite3
import json

DB_FILE = "requests.db"
KB_FILE = "knowledge.json"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

def list_pending():
    cursor.execute("SELECT id, question FROM requests WHERE status='pending'")
    rows = cursor.fetchall()
    if not rows:
        print("No pending requests.")
    else:
        print("Pending requests:")
        for id, q in rows:
            print(f"{id}: {q}")

def list_history():
    cursor.execute("SELECT id, question, answer, status, timestamp FROM requests")
    rows = cursor.fetchall()
    if not rows:
        print("No requests in history.")
    else:
        print("\nHistory of requests:")
        for id, q, ans, status, ts in rows:
            print(f"{id}: [{status}] \"{q}\" => \"{ans}\" (at {ts})")
    print()

def answer_request(req_id, answer_text):
    # Update the request with answer
    cursor.execute("UPDATE requests SET answer=?, status='answered' WHERE id=?", (answer_text, req_id))
    conn.commit()
    # Add to knowledge base JSON
    with open(KB_FILE, 'r') as f:
        kb = json.load(f)
    # Normalize key to lowercase
    with open("requests.db"):
        pass  # ensure file exists
    kb_key = answer_text.strip().lower()
    # Use the original question as key
    cursor.execute("SELECT question FROM requests WHERE id=?", (req_id,))
    row = cursor.fetchone()
    if row:
        question_text = row[0].lower()
        kb[question_text] = answer_text.strip()
        with open(KB_FILE, 'w') as f:
            json.dump(kb, f, indent=2)
        print(f"Added to knowledge base: \"{question_text}\" -> \"{answer_text.strip()}\"")
    # Simulate agent reply (console output)
    print(f"\n[SPEAK] Agent would now reply: \"{answer_text.strip()}\"\n")

def main():
    print("=== Supervisor Console ===")
    while True:
        print("\nOptions: (v)iew history, (p)ending requests, (a)nswer request, (q)uit")
        choice = input("Enter option: ").strip().lower()
        if choice == 'v':
            list_history()
        elif choice == 'p':
            list_pending()
        elif choice == 'a':
            list_pending()
            try:
                req_id = int(input("Enter request ID to answer (or 0 to cancel): ").strip())
            except ValueError:
                print("Invalid ID.")
                continue
            if req_id == 0:
                continue
            answer_text = input("Enter the answer to provide: ").strip()
            if answer_text:
                answer_request(req_id, answer_text)
            else:
                print("No answer provided.")
        elif choice == 'q':
            print("Exiting supervisor console.")
            break
        else:
            print("Invalid option. Please choose v, p, a, or q.")

if __name__ == "__main__":
    main()
