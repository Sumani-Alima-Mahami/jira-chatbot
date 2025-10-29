from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import json
from requests.auth import HTTPBasicAuth
from openai import OpenAI  # New OpenAI client

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- API KEYS ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_SITE = os.getenv("JIRA_URL", "https://netsolghana.atlassian.net")
PROJECT_KEY = "NSD"

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.json.get("message")
        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # --- Step 1: Get AI response ---
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": user_message}],
            temperature=0.5
        )
        bot_reply = response.choices[0].message.content

        # --- Step 2: If unresolved, create Jira ticket ---
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
            jira_response = requests.post(jira_url, headers=headers, data=payload, auth=auth)

            if jira_response.status_code == 201:
                return jsonify({"reply": f"{bot_reply}\n✅ Ticket created successfully!"})
            else:
                return jsonify({"reply": f"{bot_reply}\n⚠️ Ticket creation failed."})

        return jsonify({"reply": bot_reply})

    except Exception as e:
        app.logger.error(f"Error in /chat: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/jira-test")
def jira_test():
    try:
        jira_url = f"{JIRA_SITE}/rest/api/3/project"
        auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
        headers = {"Accept": "application/json"}

        r = requests.get(jira_url, headers=headers, auth=auth)
        return jsonify({
            "status": r.status_code,
            "projects": r.json() if r.status_code == 200 else r.text
        })
    except Exception as e:
        app.logger.error(f"Error in /jira-test: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "✅ Jira Chatbot Server is running!"


# Global error handler (returns JSON for any uncaught exception)
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {e}", exc_info=True)
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
