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

#  Allow embedding in Confluence
@app.after_request
def add_headers(response):
    response.headers["X-Frame-Options"] = "ALLOWALL"
    response.headers["Content-Security-Policy"] = "frame-ancestors *"
    return response

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

        # Generate AI response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        bot_reply = response.choices[0].message.content
        return jsonify({"reply": bot_reply})

    except Exception as e:
        print(f"🔥 Error in /chat: {e}")
        return jsonify({"error": str(e), "reply": "⚠️ Something went wrong on the server."}), 500


@app.route("/create-ticket", methods=["POST"])
def create_ticket():
    """
    Creates a Jira ticket using user question and bot reply.
    Expects JSON: { "userMessage": "...", "botMessage": "..." }
    """
    try:
        data = request.get_json()
        user_message = data.get("userMessage", "").strip()
        bot_message = data.get("botMessage", "").strip()

        if not user_message or not bot_message:
            return jsonify({"error": "Missing userMessage or botMessage"}), 400

        netsol_url = os.getenv("NETSOL_URL")  # e.g., "https://your-domain.atlassian.net"
        netsol_project = os.getenv("JIRA_PROJECT_KEY")  # e.g., "SUP"
        netsol_email = os.getenv("NETSOL_EMAIL")  # Jira account email
        netsol_api_token = os.getenv("NETSOL_API_TOKEN")  # Jira API token

        payload = {
            "fields": {
                "project": {"key": jira_project},
                "summary": f"Support request: {user_message[:50]}",
                "description": f"User question:\n{user_message}\n\nBot reply:\n{bot_message}",
                "issuetype": {"name": "Task"}  # Adjust as needed (Task, Bug, Story)
            }
        }

        response = requests.post(
            f"{jira_url}/rest/api/2/issue",
            json=payload,
            auth=HTTPBasicAuth(jira_email, jira_api_token),
            headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()
        ticket_data = response.json()
        return jsonify({"ticketKey": ticket_data.get("key")})

    except Exception as e:
        print(f"🔥 Error creating Jira ticket: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
