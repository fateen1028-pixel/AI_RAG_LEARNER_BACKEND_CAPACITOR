import re
from flask import jsonify

def validate_email_password(email, password):
    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 400
    
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        return jsonify({"status": "error", "message": "Invalid email format"}), 400
    
    if len(password) < 6:
        return jsonify({"status": "error", "message": "Password must be at least 6 characters"}), 400
    
    return None