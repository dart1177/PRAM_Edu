import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from database import Database
from ai_engine import AIEngine
from auth import init_jwt, admin_required, create_token

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
db = Database()
ai = AIEngine()
jwt = init_jwt(app)

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
        
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "student")
    
    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
    
    if "@" not in email:
        return jsonify({"error": "Invalid email"}), 400
        
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
        
    user_id = db.register_user(name, email, password, role)
    if user_id is None:
        return jsonify({"error": "Email already registered"}), 409
        
    db.log_action(user_id, "REGISTER", "/api/register", request.remote_addr, 201, "User registered")
    logger.info(f"New user registered: {email}")
    
    return jsonify({"message": "User registered successfully", "user_id": user_id}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400
        
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400
        
    user = db.verify_login(email, password)
    temp_user = db.get_user_by_email(email)
    temp_user_id = temp_user["id"] if temp_user else None
    
    if user:
        access_token = create_token(user)
        db.log_action(user["id"], "LOGIN_SUCCESS", "/api/login", request.remote_addr, 200, "Successful login")
        logger.info(f"User login successful: {email}")
        
        user_data = dict(user)
        del user_data["password_hash"]
        
        return jsonify({
            "access_token": access_token,
            "user": user_data
        }), 200
    else:
        if temp_user_id:
            db.log_action(temp_user_id, "LOGIN_FAILED", "/api/login", request.remote_addr, 401, "Invalid password")
        else:
            db.log_action(None, "LOGIN_FAILED", "/api/login", request.remote_addr, 401, f"Unknown email: {email}")
            
        logger.warning(f"Failed login attempt for email: {email}")
        return jsonify({"error": "Invalid credentials"}), 401

@app.route("/api/query", methods=["POST"])
@jwt_required()
def query_ai():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get("question"):
        return jsonify({"error": "Missing question"}), 400
        
    question = data.get("question")
    
    res = ai.process_query(question)
    
    query_id = db.save_query(user_id, question, res["answer"], res["response_time_ms"])
    
    db.log_action(user_id, "AI_QUERY", "/api/query", request.remote_addr, 200, f"Intent: {res['intent']}")
    logger.info(f"User {user_id} queried AI. Intent: {res['intent']}")
    
    return jsonify(res), 200

@app.route("/api/history", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    history = db.get_user_history(user_id)
    return jsonify(history), 200

@app.route("/api/admin/suspicious", methods=["GET"])
@admin_required()
def get_suspicious():
    users = db.get_suspicious_users()
    return jsonify(users), 200

@app.route("/api/admin/performance", methods=["GET"])
@admin_required()
def get_performance():
    stats = db.get_ai_performance()
    return jsonify(stats), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
