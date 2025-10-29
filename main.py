
# main.py
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import os
import logging
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configure CORS with specific origins for production
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
CORS(app, origins=cors_origins)

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY environment variable not set")
    raise ValueError("OPENAI_API_KEY must be set")

client = OpenAI(api_key=OPENAI_API_KEY)

# Configuration
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 4000))
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1000))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))


def validate_request(f):
    """Decorator to validate request data"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
        return f(*args, **kwargs)
    return decorated_function


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "model": MODEL}), 200


@app.route("/chat", methods=["POST"])
@validate_request
def chat():
    """
    Chat endpoint that processes user messages and returns AI responses.
    
    Request body:
        {
            "message": str (required),
            "conversation_history": list (optional),
            "temperature": float (optional, 0-2),
            "max_tokens": int (optional)
        }
    
    Returns:
        {
            "reply": str,
            "model": str,
            "tokens_used": int
        }
    """
    try:
        data = request.json
        user_message = data.get("message", "").strip()
        
        # Validate message
        if not user_message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(user_message) > MAX_MESSAGE_LENGTH:
            return jsonify({
                "error": f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters"
            }), 400
        
        # Build message history
        messages = []
        conversation_history = data.get("conversation_history", [])
        
        # Add conversation history if provided
        if isinstance(conversation_history, list):
            messages.extend(conversation_history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get optional parameters with defaults
        temperature = data.get("temperature", TEMPERATURE)
        max_tokens = data.get("max_tokens", MAX_TOKENS)
        
        # Validate temperature
        if not 0 <= temperature <= 2:
            return jsonify({"error": "Temperature must be between 0 and 2"}), 400
        
        logger.info(f"Processing chat request with {len(messages)} messages")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        answer = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        logger.info(f"Successfully generated response using {tokens_used} tokens")
        
        return jsonify({
            "reply": answer,
            "model": response.model,
            "tokens_used": tokens_used
        }), 200
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({"error": f"Validation error: {str(e)}"}), 400
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({
            "error": "An error occurred processing your request",
            "details": str(e) if app.debug else None
        }), 500


@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    
    logger.info(f"Starting Flask server on port {port}")
    logger.info(f"Using model: {MODEL}")
    logger.info(f"Debug mode: {debug}")
    
    app.run(host="0.0.0.0", port=port, debug=debug)
