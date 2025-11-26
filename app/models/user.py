from datetime import datetime

class User:
    @staticmethod
    def create_user_doc(email, password, name, firebase_uid=None, avatar=None):
        return {
            "email": email,
            "password": password,
            "name": name,
            "firebaseUid": firebase_uid,
            "avatar": avatar,
            "createdAt": datetime.now(),
            "updatedAt": datetime.now()
        }
    
    @staticmethod
    def get_public_user_data(user):
        return {
            "id": str(user['_id']),
            "email": user['email'],
            "name": user['name'],
            "avatar": user.get('avatar')
        }