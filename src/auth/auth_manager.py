"""
Simple authentication manager for SAP BW Chatbot
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Dict, Optional, List

class AuthManager:
    def __init__(self, users_file: str = "data/users.json"):
        self.users_file = users_file
        self.users = self._load_users()
        
    def _load_users(self) -> Dict:
        """Load users from JSON file or create default users"""
        if not os.path.exists(self.users_file):
            # Create default admin and user accounts
            default_users = {
                "admin": {
                    "password_hash": self._hash_password("admin123"),
                    "role": "admin",
                    "email": "admin@company.com",
                    "created_date": datetime.now().isoformat(),
                    "is_active": True,
                    "last_login": None
                },
                "user": {
                    "password_hash": self._hash_password("user123"),
                    "role": "user", 
                    "email": "user@company.com",
                    "created_date": datetime.now().isoformat(),
                    "is_active": True,
                    "last_login": None
                }
            }
            self._save_users(default_users)
            return default_users
        
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
    
    def _save_users(self, users: Dict) -> None:
        """Save users to JSON file"""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with username/password"""
        if username not in self.users:
            return None
        
        user = self.users[username]
        if not user.get("is_active", False):
            return None
        
        password_hash = self._hash_password(password)
        if password_hash == user["password_hash"]:
            # Update last login
            self.users[username]["last_login"] = datetime.now().isoformat()
            self._save_users(self.users)
            
            return {
                "username": username,
                "role": user["role"],
                "email": user["email"],
                "last_login": user["last_login"]
            }
        
        return None
    
    def create_user(self, username: str, password: str, email: str, role: str = "user") -> bool:
        """Create new user"""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password_hash": self._hash_password(password),
            "role": role,
            "email": email,
            "created_date": datetime.now().isoformat(),
            "is_active": True,
            "last_login": None
        }
        
        self._save_users(self.users)
        return True
    
    def get_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        return [
            {
                "username": username,
                "role": user["role"],
                "email": user["email"],
                "is_active": user["is_active"],
                "last_login": user.get("last_login")
            }
            for username, user in self.users.items()
        ] 