# main.py
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize OpenAI client (v1.0+)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.json
        user_message = data.get("message")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Use the new OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )

        # Extract the model's reply
        assistant_message = response.choices[0].message.content

        return jsonify({"reply": assistant_message})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/jira-test", methods=["GET"])
def jira_test():
    # Example Jira integration placeholder
    return jsonify({"status": "Jira endpoint works!"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

