from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import os
import requests

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder="static")
CORS(app)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    # Serve the chatbot UI (index.html)
    return send_from_directory("static", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "").strip()

        if not user_input:
            return jsonify({"reply": "Please say something!"}), 400

        # Generate OpenAI response
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
        print(f"🔥 Error in /chat: {e}")
        return jsonify({"error": str(e), "reply": "⚠️ Something went wrong on the server."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
