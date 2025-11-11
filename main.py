from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests
from requests.auth import HTTPBasicAuth

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# Allow embedding in Confluence or other iframes
@app.after_request
def add_headers(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

# OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Jira configuration
netsol_url = os.getenv("NETSOL_URL")
jira_project_key = os.getenv("JIRA_PROJECT_KEY")
netsol_email = os.getenv("NETSOL_EMAIL")
netsol_api_token = os.getenv("NETSOL_API_TOKEN")


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        messages = data.get("messages", [])

        if not messages:
            return jsonify({"reply": "Please say something!"}), 400

        # Ensure system prompt is first
        if not any(m['role'] == 'system' for m in messages):
            messages.insert(0, {
                "role": "system",
                "content": (
                    "You are a helpful, concise, and professional support assistant for the NetSol Support team. "
                    "Answer in structured steps or bullets. Use a friendly tone. Assist with NetSol queries. "
                    "Keep responses short and easy to read in a chat interface."
                )
            })

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        bot_reply = response.choices[0].message.content
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": str(e), "reply": "⚠️ Something went wrong on the server."}), 500


@app.route("/create-ticket", methods=["POST"])
def create_ticket():
    try:
        data = request.get_json()
        user_message = data.get("userMessage", "")
        bot_message = data.get("botMessage", "")

        if not user_message or not bot_message:
            return jsonify({"error": "Missing message content"}), 400

        # Prepare Jira issue payload
        issue_data = {
            "fields": {
                "project": {"key": jira_project_key},
                "summary": f"Support request from chatbot: {user_message[:50]}",
                "description": f"User Message:\n{user_message}\n\nBot Response:\n{bot_message}",
                "issuetype": {"name": "Task"}
            }
        }

        # Debug prints
        print("Jira payload:", issue_data)
        print("Sending to:", netsol_url)
        print("Using project key:", jira_project_key)

        response = requests.post(
            f"{netsol_url}/rest/api/3/issue",
            json=issue_data,
            auth=HTTPBasicAuth(netsol_email, netsol_api_token),
            headers={"Accept": "application/json", "Content-Type": "application/json"}
        )

        print("Jira response status:", response.status_code)
        print("Jira response body:", response.text)

        if response.status_code == 201:
            ticket_key = response.json().get("key")
            return jsonify({"ticketKey": ticket_key})
        else:
            print(f"Jira API error: {response.status_code} {response.text}")
            return jsonify({"error": "Failed to create ticket"}), 500

    except Exception as e:
        print(f"Error in /create-ticket: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
