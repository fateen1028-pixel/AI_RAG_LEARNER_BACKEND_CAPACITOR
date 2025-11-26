from flask import Blueprint, request, jsonify
from app.services.auth_service import AuthService
from app.utils.validators import validate_email_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")

    # Validation
    error = validate_email_password(email, password)
    if error:
        return error
    
    if not name:
        return jsonify({"status": "error", "message": "Name is required"}), 400

    result = AuthService.register_user(email, password, name)
    return jsonify(result)

@auth_bp.route("/login", methods=["POST"])
def login():
    if not request.is_json:
        return jsonify({"status": "error", "message": "Content-Type must be application/json"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON data provided"}), 400

    email = data.get("email")
    password = data.get("password")

    # Validation
    error = validate_email_password(email, password)
    if error:
        return error

    result = AuthService.login_user(email, password)
    return jsonify(result)

@auth_bp.route("/auth/firebase", methods=["POST"])
def handle_firebase_auth():
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No JSON data provided"}), 400

    firebase_token = data.get('token')
    if not firebase_token:
        return jsonify({"status": "error", "message": "Firebase token is required"}), 400

    result = AuthService.authenticate_firebase_user(firebase_token)
    return jsonify(result)

@auth_bp.route("/debug/login", methods=["POST"])
def debug_login():
    print("🔍 DEBUG: /debug/login called")
    print(f"🔍 Headers: {dict(request.headers)}")
    print(f"🔍 Content-Type: {request.content_type}")
    print(f"🔍 JSON data: {request.get_json()}")
    
    return jsonify({
        "status": "debug",
        "message": "Debug endpoint working",
        "headers": dict(request.headers),
        "content_type": request.content_type,
        "data_received": request.get_json()
    })

@auth_bp.route("/debug/firebase", methods=["GET"])
def debug_firebase():
    from app.utils.helpers import get_firebase_status
    return jsonify(get_firebase_status())