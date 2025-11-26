import bcrypt
import re
from bson import ObjectId
from datetime import datetime
from app.models.user import User
from app.utils.helpers import get_db

class UserService:
    @staticmethod
    def get_current_user_data(current_user):
        return User.get_public_user_data(current_user)

    @staticmethod
    def update_user_profile(user_id, data):
        users_col = get_db().users
        
        update_data = {}
        
        # Update name if provided
        if 'name' in data and data['name']:
            update_data['name'] = data['name']
        
        # Update avatar if provided
        if 'avatar' in data and data['avatar']:
            update_data['avatar'] = data['avatar']
        
        # Update email if provided
        if 'email' in data and data['email']:
            # Check if email is already taken
            existing_user = users_col.find_one({"email": data['email'], "_id": {"$ne": ObjectId(user_id)}})
            if existing_user:
                return {"status": "error", "message": "Email is already in use"}, 400
            update_data['email'] = data['email']
        
        if update_data:
            update_data['updatedAt'] = datetime.now()
            result = users_col.update_one(
                {"_id": ObjectId(user_id)}, 
                {"$set": update_data}
            )
            
            # Fetch updated user
            updated_user = users_col.find_one({"_id": ObjectId(user_id)})
            
            response_data = {
                "status": "success",
                "message": "Profile updated successfully",
                "user": User.get_public_user_data(updated_user)
            }
            
            return response_data
        else:
            return {"status": "error", "message": "No valid fields to update"}, 400

    @staticmethod
    def change_password(user_id, data):
        users_col = get_db().users
        
        current_password = data.get('currentPassword')
        new_password = data.get('newPassword')
        
        if not current_password or not new_password:
            return {
                "status": "error",
                "message": "Current password and new password are required"
            }, 400
        
        # Get user from database
        user = users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"status": "error", "message": "User not found"}, 404
        
        # Verify current password
        if 'password' in user and not bcrypt.checkpw(current_password.encode('utf-8'), user['password']):
            return {"status": "error", "message": "Current password is incorrect"}, 400
        
        # Hash new password
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Update password
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "password": hashed_new_password,
                "updatedAt": datetime.now()
            }}
        )
        
        return {"status": "success", "message": "Password updated successfully"}

    @staticmethod
    def change_email(user_id, data):
        users_col = get_db().users
        
        new_email = data.get('newEmail')
        password = data.get('password')
        
        if not new_email or not password:
            return {
                "status": "error",
                "message": "New email and password are required"
            }, 400
        
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', new_email):
            return {"status": "error", "message": "Invalid email format"}, 400
        
        # Get user from database
        user = users_col.find_one({"_id": ObjectId(user_id)})
        if not user:
            return {"status": "error", "message": "User not found"}, 404
        
        # Verify password
        if 'password' in user and not bcrypt.checkpw(password.encode('utf-8'), user['password']):
            return {"status": "error", "message": "Password is incorrect"}, 400
        
        # Check if email is already taken
        existing_user = users_col.find_one({"email": new_email, "_id": {"$ne": ObjectId(user_id)}})
        if existing_user:
            return {"status": "error", "message": "Email is already in use"}, 400
        
        # Update email
        users_col.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "email": new_email,
                "updatedAt": datetime.now()
            }}
        )
        
        return {"status": "success", "message": "Email updated successfully"}