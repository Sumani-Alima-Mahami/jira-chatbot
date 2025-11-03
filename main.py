from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import requests

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client using environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return "✅ Jira AI Chatbot is running!"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "")
        if not user_input:
            return jsonify({"error": "No message provided"}), 400

        # Generate response using OpenAI Chat Completions
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful Jira assistant."},
                {"role": "user", "content": user_input}
            ]
        )

        reply = response.choices[0].message.content
        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/jira-test', methods=['GET'])
def jira_test():
    try:
        jira_url = os.environ.get("JIRA_URL")
        jira_email = os.environ.get("JIRA_EMAIL")
        jira_token = os.environ.get("JIRA_API_TOKEN")

        if not all([jira_url, jira_email, jira_token]):
            return jsonify({"error": "Jira credentials missing"}), 400

        res = requests.get(
            f"{jira_url}/rest/api/3/project",
            auth=(jira_email, jira_token)
        )

        if res.status_code == 200:
            return jsonify(res.json())
        else:
            return jsonify({
                "error": "Failed to fetch Jira projects",
                "details": res.text
            }), res.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Use Render's PORT environment variable if available
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
