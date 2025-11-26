import os
import jwt
from pymongo import MongoClient
from flask import jsonify
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from datetime import datetime

# MongoDB connection
_client = None
_db = None

def get_db():
    global _db
    if _db is None:
        initialize_db()
    return _db

def initialize_db():
    global _client, _db
    MONGO_URI = os.getenv("MONGO_URI")
    _client = MongoClient(MONGO_URI)
    _db = _client.learning_planner

def get_jwt_secret():
    return os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

# Firebase initialization
_firebase_initialized = False

def initialize_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return True
        
    try:
        if not firebase_admin._apps:
            print("🔄 Initializing Firebase Admin SDK...")
            
            private_key_value = os.getenv("FIREBASE_PRIVATE_KEY", "").strip()
            project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
            client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()
            
            if not private_key_value:
                print("❌ FIREBASE_PRIVATE_KEY is missing or empty")
                return False
            
            if not project_id:
                print("❌ FIREBASE_PROJECT_ID is missing or empty")
                return False
                
            if not client_email:
                print("❌ FIREBASE_CLIENT_EMAIL is missing or empty")
                return False
            
            # Fix the private key format
            if '\\n' in private_key_value:
                private_key_value = private_key_value.replace('\\n', '\n')
            
            firebase_config = {
                "type": "service_account",
                "project_id": project_id,
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
                "private_key": private_key_value,
                "client_email": client_email,
                "client_id": os.getenv("FIREBASE_CLIENT_ID", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL", "")
            }
            
            firebase_config = {k: v for k, v in firebase_config.items() if v is not None and v != ""}
            
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK Initialized Successfully")
        
        _firebase_initialized = True
        return True
        
    except Exception as e:
        print(f"❌ Firebase Initialization Error: {str(e)}")
        return False

def verify_firebase_token(token):
    try:
        if not _firebase_initialized:
            initialize_firebase()
        return firebase_auth.verify_id_token(token)
    except Exception as e:
        print(f"❌ Token verification failed: {str(e)}")
        return None

def get_firebase_status():
    try:
        firebase_initialized = _firebase_initialized
        
        env_status = {
            "FIREBASE_PROJECT_ID": bool(os.getenv("FIREBASE_PROJECT_ID")),
            "FIREBASE_CLIENT_EMAIL": bool(os.getenv("FIREBASE_CLIENT_EMAIL")),
            "FIREBASE_PRIVATE_KEY": bool(os.getenv("FIREBASE_PRIVATE_KEY")),
            "FIREBASE_PRIVATE_KEY_LENGTH": len(os.getenv("FIREBASE_PRIVATE_KEY", "")),
        }
        
        return {
            "firebase_initialized": firebase_initialized,
            "environment_variables": env_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "error": str(e),
            "firebase_initialized": False
        }