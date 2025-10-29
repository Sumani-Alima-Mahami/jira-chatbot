from flask import Flask, request, jsonify
from flask_cors import CORS  # <--- import CORS
import requests
import openai
import os
import json
from requests.auth import HTTPBasicAuth

app = Flask(__name__)
CORS(app)  # <--- enable CORS for all routes

# --- API KEYS ---
openai.api_key = os.getenv("OPENAI_API_KEY")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_SITE = os.getenv("JIRA_URL", "https://netsolghana.atlassian.net")  # use env var if set
PROJECT_KEY = "NSD"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")

    # Step 1: Get AI response
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": user_message}],
        temperature=0.5
    )
    bot_reply = response["choices"][0]["message"]["content"]

    # Step 2: If unresolved, create Jira ticket
    if "create ticket" in bot_reply.lower():
        jira_url = f"{JIRA_SITE}/rest/api/3/issue"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = json.dumps({
            "fields": {
                "project": {"key": PROJECT_KEY},
                "summary": user_message[:50],
                "description": f"AI Chatbot created ticket for: {user_message}",
                "issuetype": {"name": "Service Request"}
            }
        })
        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        response = requests.post(jira_url, headers=headers, data=payload, auth=auth)
        if response.status_code == 201:
            return jsonify({"reply": f"{bot_reply}\n✅ Ticket created successfully!"})
        else:
            return jsonify({"reply": f"{bot_reply}\n⚠️ Ticket creation failed."})

    return jsonify({"reply": bot_reply})

@app.route("/jira-test")
def jira_test():
    jira_url = f"{JIRA_SITE}/rest/api/3/project"
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}

    r = requests.get(jira_url, headers=headers, auth=auth)
    return jsonify({
        "status": r.status_code,
        "projects": r.json() if r.status_code == 200 else r.text
    })

@app.route("/")
def home():
    return "✅ Jira Chatbot Server is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
