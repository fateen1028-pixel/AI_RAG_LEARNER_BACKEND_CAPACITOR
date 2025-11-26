import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    
    # Gemini AI
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")
    
    # Firebase
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
    FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")
    FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")
    FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID")
    FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID")
    FIREBASE_CLIENT_CERT_URL = os.getenv("FIREBASE_CLIENT_CERT_URL")