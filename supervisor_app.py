# supervisor_ui.py
from flask import Flask, request, redirect, url_for, render_template
from db_utils import get_pending_questions, save_human_answer

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def pending():
    if request.method == 'POST':
        question = request.form['question']
        answer = request.form['answer']
        if answer:
            save_human_answer(question, answer)
        return redirect(url_for('pending'))

    # GET: show all pending questions
    questions = get_pending_questions()
    return render_template('pending.html', questions=questions)

if __name__ == '__main__':
    app.run(debug=True)
