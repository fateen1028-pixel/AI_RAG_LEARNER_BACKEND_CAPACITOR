import jwt
from functools import wraps
from flask import request, jsonify
from bson import ObjectId
from app.utils.helpers import get_db, get_jwt_secret

def token_required(f):
    """
    Decorator to validate JWT tokens and authenticate users.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        # Check if Authorization header exists
        if not auth_header:
            print(f"❌ [AUTH] No Authorization header - Path: {request.path}")
            return jsonify({
                "status": "error", 
                "message": "Token is missing"
            }), 401
        
        try:
            # Extract token from "Bearer <token>" format
            if not auth_header.startswith('Bearer '):
                print(f"❌ [AUTH] Invalid token format: {auth_header[:30]}...")
                return jsonify({
                    "status": "error", 
                    "message": "Invalid token format. Expected 'Bearer <token>'"
                }), 401
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            if not token or token == 'null' or token == 'undefined':
                print(f"❌ [AUTH] Empty or invalid token value")
                return jsonify({
                    "status": "error", 
                    "message": "Invalid token"
                }), 401
            
            # Decode and verify JWT token
            try:
                data = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                print(f"❌ [AUTH] Token expired")
                return jsonify({
                    "status": "error", 
                    "message": "Token has expired. Please login again."
                }), 401
            except jwt.InvalidTokenError as e:
                print(f"❌ [AUTH] Invalid token: {str(e)}")
                return jsonify({
                    "status": "error", 
                    "message": "Invalid token"
                }), 401
            
            # Get user from database
            user_id = data.get('user_id')
            if not user_id:
                print(f"❌ [AUTH] No user_id in token payload")
                return jsonify({
                    "status": "error", 
                    "message": "Invalid token payload"
                }), 401
            
            try:
                users_col = get_db().users
                current_user = users_col.find_one({"_id": ObjectId(user_id)})
            except Exception as e:
                print(f"❌ [AUTH] Database error: {str(e)}")
                return jsonify({
                    "status": "error", 
                    "message": "Database error"
                }), 500
            
            if not current_user:
                print(f"❌ [AUTH] User not found: {user_id}")
                return jsonify({
                    "status": "error", 
                    "message": "User not found"
                }), 401
            
            # Success - attach user info to request
            request.current_user = current_user
            request.user_id = str(current_user['_id'])
            
            print(f"✅ [AUTH] User authenticated: {current_user.get('email')} - Path: {request.path}")
            
        except Exception as e:
            print(f"❌ [AUTH] Unexpected error: {str(e)}")
            return jsonify({
                "status": "error", 
                "message": "Authentication error"
            }), 401
        
        return f(*args, **kwargs)
    
    return decorated