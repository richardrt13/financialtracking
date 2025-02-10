import streamlit as st
from pymongo import MongoClient
import bcrypt
from datetime import datetime, timedelta
import jwt
import re
from bson.objectid import ObjectId
import extra_streamlit_components as stx

class AuthManager:
    def __init__(self, mongo_uri):
        """
        Initialize authentication manager with MongoDB connection
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client['financial_tracker']
        self.users_collection = self.db['users']
        self.JWT_SECRET = st.secrets["jwt_secret"]
        self.JWT_EXPIRY_DAYS = 360
        self.cookie_manager = stx.CookieManager()
        
    def _generate_token(self, user_id: str, remember_me: bool = False) -> str:
        """Generate a JWT token for the user"""
        expiry = datetime.utcnow() + timedelta(days=self.JWT_EXPIRY_DAYS if remember_me else 1)
        return jwt.encode(
            {
                'user_id': str(user_id), 
                'exp': expiry,
                'remember_me': remember_me
            },
            self.JWT_SECRET,
            algorithm='HS256'
        )
    
    def login_user(self, email: str, password: str, remember_me: bool = False) -> tuple[bool, str]:
        """
        Login a user
        Returns: (success, token or error message)
        """
        user = self.users_collection.find_one({'email': email})
        if not user:
            return False, "Email ou senha incorretos"
            
        if not self._verify_password(password, user['password']):
            return False, "Email ou senha incorretos"
            
        token = self._generate_token(user['_id'], remember_me)
        
        # Set cookie if remember_me is True
        if remember_me:
            self.cookie_manager.set(
                'auth_token',
                token,
                expires_at=datetime.now() + timedelta(days=self.JWT_EXPIRY_DAYS),
                key='auth_cookie'
            )
        
        st.session_state['token'] = token
        return True, token
    
    def get_current_user(self) -> dict:
        """Get the current logged in user from session state or cookie"""
        # First check session state
        token = st.session_state.get('token')
        
        # If no token in session state, check cookies
        if not token:
            token = self.cookie_manager.get(key='auth_token')
            if token:
                # Validate token from cookie
                payload = self._verify_token(token)
                if payload and payload.get('remember_me'):
                    # Token is valid and was created with remember_me
                    st.session_state['token'] = token
                else:
                    # Invalid or expired token, clear cookie
                    self.cookie_manager.delete('auth_token', key='auth_cookie')
                    return None
        
        # Verify token and get user
        payload = self._verify_token(token)
        if not payload:
            return None
            
        user = self.users_collection.find_one({'_id': ObjectId(payload['user_id'])})
        return user
    
    def logout_user(self):
        """Logout the current user"""
        if 'token' in st.session_state:
            del st.session_state['token']
        # Clear auth cookie
        self.cookie_manager.delete('auth_token', key='auth_cookie')
        
        # Ensure legacy user exists
        #self._ensure_legacy_user()
        
    # def _ensure_legacy_user(self):
    #     """Ensure legacy user exists in the database"""
    #     legacy_user = self.users_collection.find_one({'email': 'admin@example.com'})
    #     if not legacy_user:
    #         # Create legacy user for existing data
    #         legacy_user = {
    #             'email': 'admin@example.com',
    #             'password': self._hash_password('Admin@123'),  # Define uma senha padrão
    #             'name': 'Admin',
    #             'created_at': datetime.utcnow(),
    #             'is_legacy': True
    #         }
    #         self.users_collection.insert_one(legacy_user)
            
    #         # Update all existing transactions to associate with legacy user
    #         self.db.transactions.update_many(
    #             {'user_id': {'$exists': False}},
    #             {'$set': {'user_id': str(legacy_user['_id'])}}
    #         )
    
    def _hash_password(self, password: str) -> bytes:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def _verify_password(self, password: str, hashed: bytes) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed)
    
    def _verify_token(self, token: str) -> dict:
        """Verify a JWT token and return the payload"""
        try:
            return jwt.decode(token, self.JWT_SECRET, algorithms=['HS256'])
        except:
            return None
            
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """
        Validate password strength
        Returns: (is_valid, message)
        """
        if len(password) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        if not re.search(r'[A-Z]', password):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        if not re.search(r'[a-z]', password):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        if not re.search(r'\d', password):
            return False, "Senha deve conter pelo menos um número"
        return True, "Senha válida"
    
    def register_user(self, email: str, password: str, name: str) -> tuple[bool, str]:
        """
        Register a new user
        Returns: (success, message)
        """
        # Validate inputs
        if not self.validate_email(email):
            return False, "Email inválido"
            
        password_valid, password_msg = self.validate_password(password)
        if not password_valid:
            return False, password_msg
            
        # Check if user already exists
        if self.users_collection.find_one({'email': email}):
            return False, "Email já cadastrado"
            
        # Create user
        user = {
            'email': email,
            'password': self._hash_password(password),
            'name': name,
            'created_at': datetime.utcnow(),
            'is_legacy': False
        }
        
        result = self.users_collection.insert_one(user)
        return True, str(result.inserted_id)
    
    def login_user(self, email: str, password: str) -> tuple[bool, str]:
        """
        Login a user
        Returns: (success, token or error message)
        """
        user = self.users_collection.find_one({'email': email})
        if not user:
            return False, "Email ou senha incorretos"
            
        if not self._verify_password(password, user['password']):
            return False, "Email ou senha incorretos"
            
        token = self._generate_token(user['_id'])
        return True, token

