import sqlite3
import json
import requests

DB_FILE = "requests.db"
KB_FILE = "knowledge.json"

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

def list_pending():
    cursor.execute("SELECT id, question FROM requests WHERE status='pending'")
    rows = cursor.fetchall()
    if not rows:
        print("✅ No pending requests.")
    else:
        print("\n📌 Pending requests:")
        for id, q in rows:
            print(f"{id}: {q}")

def list_history():
    cursor.execute("SELECT id, question, answer, status, timestamp FROM requests ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    if not rows:
        print("📜 No requests in history.")
    else:
        print("\n📜 History of requests:")
        for id, q, ans, status, ts in rows:
            print(f"{id}: [{status.upper()}] \"{q}\" => \"{ans}\" (at {ts})")
    print()

def answer_request(req_id, answer_text):
    cursor.execute("SELECT question FROM requests WHERE id=? AND status='pending'", (req_id,))
    row = cursor.fetchone()
    if not row:
        print(f"❌ No pending request found with ID {req_id}.")
        return

    question_text = row[0].lower()

    # Update the request with answer
    cursor.execute("UPDATE requests SET answer=?, status='answered' WHERE id=?", (answer_text.strip(), req_id))
    conn.commit()

    # Add to KB
    try:
        with open(KB_FILE, 'r') as f:
            kb = json.load(f)
    except FileNotFoundError:
        kb = {}

    kb[question_text] = answer_text.strip()
    with open(KB_FILE, 'w') as f:
        json.dump(kb, f, indent=2)
    print(f"✅ Added to knowledge base: \"{question_text}\" -> \"{answer_text.strip()}\"")

    # 🔥 Call the running agent to speak the answer
    try:
        response = requests.post("http://127.0.0.1:8000/answer", json={"answer": answer_text.strip()})
        if response.status_code == 200:
            print(f"[SPEAK] 🗣️ Agent is now saying: \"{answer_text.strip()}\"")
        else:
            print(f"[ERROR] Agent API returned: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[ERROR] Could not reach agent to speak: {e}")

def main():
    print("=== 🧠 Supervisor Console ===")
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
                print("❌ Invalid ID.")
                continue
            if req_id == 0:
                continue
            answer_text = input("Enter the answer to provide: ").strip()
            if answer_text:
                answer_request(req_id, answer_text)
            else:
                print("❌ No answer provided.")
        elif choice == 'q':
            print("👋 Exiting supervisor console.")
            break
        else:
            print("❌ Invalid option. Please choose v, p, a, or q.")

if __name__ == "__main__":
    main()
