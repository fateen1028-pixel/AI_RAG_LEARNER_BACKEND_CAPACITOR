from flask import Blueprint, request, jsonify
from app.middleware.auth import token_required
from app.services.user_service import UserService

users_bp = Blueprint('users', __name__)

@users_bp.route("/user/me", methods=["GET"])
@token_required
def get_current_user():
    user_data = UserService.get_current_user_data(request.current_user)
    return jsonify({"status": "success", "user": user_data})

@users_bp.route("/user/profile", methods=["PUT"])
@token_required
def update_profile():
    data = request.json
    user_id = request.user_id
    
    result = UserService.update_user_profile(user_id, data)
    return jsonify(result)

@users_bp.route("/user/password", methods=["PUT"])
@token_required
def change_password():
    data = request.json
    user_id = request.user_id
    
    result = UserService.change_password(user_id, data)
    return jsonify(result)

@users_bp.route("/user/email", methods=["PUT"])
@token_required
def change_email():
    data = request.json
    user_id = request.user_id
    
    result = UserService.change_email(user_id, data)
    return jsonify(result)