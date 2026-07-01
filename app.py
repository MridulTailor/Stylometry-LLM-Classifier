import uuid
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from database import init_db, log_submission, update_appeal, get_recent_logs
from signals import analyze_with_groq, analyze_with_stylometrics, calculate_confidence
from config import Config

app = Flask(__name__)

# Initialize database
init_db()

# Configure Rate Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

def get_transparency_label(confidence: float) -> str:
    if confidence < 0.40:
        return "High-confidence human: This content exhibits natural stylistic variations and structures typical of human writing."
    elif confidence <= 0.70:
        return "Uncertain: This content exhibits mixed signals. We cannot confidently determine if it is human-written or AI-generated."
    else:
        return "High-confidence AI: This content exhibits strong structural and semantic patterns typical of AI generation."

def get_attribution(confidence: float) -> str:
    if confidence < 0.40:
        return "likely_human"
    elif confidence <= 0.70:
        return "uncertain"
    else:
        return "likely_ai"

@app.route("/submit", methods=["POST"])
@limiter.limit(Config.RATE_LIMIT)
def submit():
    data = request.get_json()
    if not data or "text" not in data or "creator_id" not in data:
        return jsonify({"error": "Missing 'text' or 'creator_id' in request body"}), 400
        
    text = data["text"]
    creator_id = data["creator_id"]
    content_id = str(uuid.uuid4())
    
    # Run signals
    groq_score = analyze_with_groq(text)
    stylo_score = analyze_with_stylometrics(text)
    
    # Calculate confidence
    confidence = calculate_confidence(groq_score, stylo_score)
    
    # Determine labels
    attribution = get_attribution(confidence)
    label = get_transparency_label(confidence)
    
    # Log submission
    log_submission(
        content_id=content_id,
        creator_id=creator_id,
        attribution=attribution,
        confidence=confidence,
        groq_score=groq_score,
        stylo_score=stylo_score
    )
    
    return jsonify({
        "content_id": content_id,
        "attribution": attribution,
        "confidence": round(confidence, 3),
        "label": label
    })

@app.route("/appeal", methods=["POST"])
def appeal():
    data = request.get_json()
    if not data or "content_id" not in data or "creator_reasoning" not in data:
        return jsonify({"error": "Missing 'content_id' or 'creator_reasoning' in request body"}), 400
        
    content_id = data["content_id"]
    creator_reasoning = data["creator_reasoning"]
    
    success = update_appeal(content_id, creator_reasoning)
    if success:
        return jsonify({"status": "success", "message": "Appeal submitted successfully. Status updated to 'under_review'."})
    else:
        return jsonify({"error": "content_id not found"}), 404

@app.route("/log", methods=["GET"])
def log_endpoint():
    # Return the 20 most recent entries for visibility
    entries = get_recent_logs(limit=20)
    return jsonify({"entries": entries})

if __name__ == "__main__":
    app.run(port=5000)
