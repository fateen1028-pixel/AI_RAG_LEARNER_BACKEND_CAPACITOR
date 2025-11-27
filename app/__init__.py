from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

import os

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object('app.config.Config')
    
    # CORS
    CORS(app, supports_credentials=True)
    
    # Initialize Firebase (if needed)
    from app.utils.helpers import initialize_firebase
    initialize_firebase()
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.plans import plans_bp
    from app.routes.todos import todos_bp
    from app.routes.ai_routes import ai_bp
    from app.routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(plans_bp)
    app.register_blueprint(todos_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(dashboard_bp)
    
    # Add headers middleware
    @app.after_request
    def add_header(response):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Surrogate-Control'] = 'no-store'
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"status": "error", "message": "Endpoint not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"status": "error", "message": "Internal server error"}, 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        print(f"❌ Unhandled exception: {str(e)}")
        return {"status": "error", "message": "An unexpected error occurred"}, 500
    
    return app