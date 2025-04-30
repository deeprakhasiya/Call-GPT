# api_server.py
from flask import Flask, request, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
from main import handle_question  # import your existing logic

app = Flask(__name__)

# 1) Define the /ask endpoint
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    if not question:
        return jsonify({"error": "Please provide a 'question' field"}), 400

    # Capture output of handle_question
    # We’ll modify handle_question to return a dict instead of printing
    result = handle_question(question, return_dict=True)
    return jsonify(result)

# 2) Set up Swagger UI (point it at a minimal OpenAPI spec)
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'  # we’ll create this file next
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "Human-in-the-Loop AI API"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == "__main__":
    app.run(debug=True)
