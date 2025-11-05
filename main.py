from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# ✅ Allow embedding in Confluence
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
