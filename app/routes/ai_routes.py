from flask import Blueprint, request, jsonify
from app.middleware.auth import token_required
from app.services.ai_service import AIService

ai_bp = Blueprint('ai', __name__)

@ai_bp.route("/ask-about-task", methods=["POST"])
@token_required
def ask_about_task():
    data = request.json
    user_id = request.user_id
    
    result = AIService.ask_about_task(user_id, data)
    return jsonify(result)

@ai_bp.route("/ai-env/materials", methods=["POST"])
@token_required
def get_learning_materials():
    data = request.json
    topic = data.get("topic")
    
    result = AIService.get_learning_materials(topic)
    return jsonify(result)

@ai_bp.route("/ai-env/chat", methods=["POST"])
@token_required
def ai_env_chat():
    data = request.json
    user_id = request.user_id
    
    result = AIService.handle_ai_chat(user_id, data)
    return jsonify(result)

@ai_bp.route("/ai-env/flashcards", methods=["POST"])
@token_required
def generate_flashcards():
    data = request.json
    result = AIService.generate_flashcards(data)
    return jsonify(result)

@ai_bp.route("/ai-env/study-guide", methods=["POST"])
@token_required
def generate_study_guide():
    data = request.json
    result = AIService.generate_study_guide(data)
    return jsonify(result)