from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
from requests.auth import HTTPBasicAuth
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # Enable CORS

# --- API KEYS ---
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_SITE = os.getenv("JIRA_URL", "https://netsolghana.atlassian.net")
PROJECT_KEY = "NSD"


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message", "")

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": message}],
            temperature=0.7,
        )
        bot_reply = response.choices[0].message.content
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/jira-test")
def jira_test():
    jira_url = f"{JIRA_SITE}/rest/api/3/project"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}

    try:
        r = requests.get(jira_url, headers=headers, auth=auth)
        return jsonify({
            "status": r.status_code,
            "projects": r.json() if r.status_code == 200 else r.text
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "✅ Jira Chatbot Server is running!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
