from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def home():
    return "✅ Jira AI Chatbot is running!"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get("message", "")

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
        jira_url = os.getenv("JIRA_URL")
        jira_email = os.getenv("JIRA_EMAIL")
        jira_token = os.getenv("JIRA_API_TOKEN")

        if not all([jira_url, jira_email, jira_token]):
            return jsonify({"error": "Jira credentials missing in .env"}), 400

        res = requests.get(
            f"{jira_url}/rest/api/3/project",
            auth=(jira_email, jira_token)
        )

        if res.status_code == 200:
            return jsonify(res.json())
        else:
            return jsonify({"error": "Failed to fetch Jira projects", "details": res.text}), res.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

