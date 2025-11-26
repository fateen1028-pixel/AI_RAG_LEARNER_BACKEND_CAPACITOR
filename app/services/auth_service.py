import bcrypt
import jwt
from datetime import datetime, timedelta
from bson import ObjectId
from app.models.user import User
from app.utils.helpers import get_db, get_jwt_secret, initialize_firebase, verify_firebase_token

class AuthService:
    @staticmethod
    def register_user(email, password, name):
        users_col = get_db().users
        
        # Check if user already exists
        if users_col.find_one({"email": email}):
            return {"status": "error", "message": "User already exists"}, 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        # Create user
        user_doc = User.create_user_doc(email, hashed_password, name)
        result = users_col.insert_one(user_doc)
        user_id = str(result.inserted_id)

        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, get_jwt_secret(), algorithm="HS256")

        return {
            "status": "success",
            "message": "User registered successfully",
            "token": token,
            "user": User.get_public_user_data(user_doc)
        }

    @staticmethod
    def login_user(email, password):
        users_col = get_db().users
        
        user = users_col.find_one({"email": email})
        if not user:
            return {"status": "error", "message": "Invalid credentials"}, 401

        # Check if user has a password (Firebase users might not)
        if 'password' not in user:
            return {
                "status": "error", 
                "message": "This account uses Google authentication. Please sign in with Google."
            }, 401

        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password']):
            token = jwt.encode({
                'user_id': str(user['_id']),
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, get_jwt_secret(), algorithm="HS256")

            return {
                "status": "success",
                "message": "Login successful",
                "token": token,
                "user": User.get_public_user_data(user)
            }
        else:
            return {"status": "error", "message": "Invalid credentials"}, 401

    @staticmethod
    def authenticate_firebase_user(firebase_token):
        try:
            # Check if Firebase is initialized
            if not initialize_firebase():
                return {
                    "status": "error", 
                    "message": "Firebase service not available. Please try again later."
                }, 503

            # Verify Firebase token
            decoded_token = verify_firebase_token(firebase_token)
            if not decoded_token:
                return {"status": "error", "message": "Invalid Firebase token"}, 401

            email = decoded_token.get('email')
            name = decoded_token.get('name', email.split('@')[0] if email else 'User')
            firebase_uid = decoded_token.get('uid')
            picture = decoded_token.get('picture')

            if not email:
                return {"status": "error", "message": "Email not found in token"}, 401

            users_col = get_db().users
            
            # Check if user exists
            user = users_col.find_one({"email": email})
            
            if not user:
                # Create new user
                user_doc = User.create_user_doc(email, None, name, firebase_uid, picture)
                result = users_col.insert_one(user_doc)
                user_id = str(result.inserted_id)
            else:
                user_id = str(user['_id'])

            # Generate JWT token
            jwt_token = jwt.encode({
                'user_id': user_id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, get_jwt_secret(), algorithm="HS256")

            return {
                "status": "success",
                "message": "Authentication successful",
                "token": jwt_token,
                "user": {
                    "id": user_id,
                    "email": email,
                    "name": name,
                    "avatar": picture
                }
            }
            
        except Exception as e:
            print(f"❌ Firebase auth error: {str(e)}")
            return {
                "status": "error", 
                "message": f"Authentication failed: {str(e)}"
            }, 500