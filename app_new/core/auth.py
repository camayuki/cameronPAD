"""
Authentication and authorization system.
"""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
import jwt

from .database import get_database_manager
from .config import get_config


class AuthError(Exception):
    """Authentication error."""
    pass


class PasswordManager:
    """Password hashing and verification using bcrypt directly."""
    
    def __init__(self):
        # Import bcrypt here to avoid issues
        import bcrypt as _bcrypt
        self.bcrypt = _bcrypt
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        password_bytes = password.encode('utf-8')
        salt = self.bcrypt.gensalt()
        hashed = self.bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        try:
            password_bytes = plain_password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return self.bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False


class TokenManager:
    """JWT token management."""
    
    def __init__(self):
        self.config = get_config().security
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.config.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired")
        except jwt.JWTError:
            raise AuthError("Invalid token")


class APIKeyManager:
    """API key management."""
    
    def __init__(self):
        self.db = get_database_manager()
    
    def generate_api_key(self) -> str:
        """Generate a secure API key."""
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def create_api_key(self, user_id: int, key_name: str, permissions: List[str] = None, expires_at: Optional[datetime] = None) -> Tuple[int, str]:
        """Create a new API key."""
        api_key = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)
        
        permissions_json = str(permissions or [])
        
        key_id = self.db.execute_update("""
            INSERT INTO api_keys (user_id, key_name, key_hash, permissions, expires_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, key_name, key_hash, permissions_json, expires_at))
        
        return key_id, api_key
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify an API key and return key info."""
        key_hash = self.hash_api_key(api_key)
        
        result = self.db.execute_query("""
            SELECT ak.id, ak.user_id, ak.key_name, ak.permissions, ak.expires_at,
                   u.username, u.is_active, u.is_admin
            FROM api_keys ak
            JOIN users u ON ak.user_id = u.id
            WHERE ak.key_hash = ? AND ak.is_active = 1
        """, (key_hash,))
        
        if not result:
            return None
        
        key_info = dict(result[0])
        
        # Check expiration
        if key_info['expires_at']:
            expires_at = datetime.fromisoformat(key_info['expires_at'])
            if datetime.now() > expires_at:
                return None
        
        # Update last used timestamp
        self.db.execute_update("""
            UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (key_info['id'],))
        
        return key_info
    
    def revoke_api_key(self, key_id: int, user_id: int) -> bool:
        """Revoke an API key."""
        affected = self.db.execute_update("""
            UPDATE api_keys SET is_active = 0 WHERE id = ? AND user_id = ?
        """, (key_id, user_id))
        
        return affected > 0


class UserManager:
    """User management and authentication."""
    
    def __init__(self):
        self.db = get_database_manager()
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.config = get_config().security
        
        # Login attempt tracking
        self.login_attempts: Dict[str, List[float]] = {}
    
    def create_user(self, username: str, password: str, email: Optional[str] = None, is_admin: bool = False) -> int:
        """Create a new user."""
        # Validate password
        if len(password) < self.config.password_min_length:
            raise AuthError(f"Password must be at least {self.config.password_min_length} characters")
        
        # Hash password
        password_hash = self.password_manager.hash_password(password)
        
        try:
            user_id = self.db.execute_update("""
                INSERT INTO users (username, email, password_hash, is_admin)
                VALUES (?, ?, ?, ?)
            """, (username, email, password_hash, is_admin))
            
            return user_id
        
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise AuthError("Username or email already exists")
            raise AuthError(f"Failed to create user: {str(e)}")
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🔐 authenticate_user called for username: '{username}'")
        
        # Check rate limiting
        if self._is_rate_limited(username):
            logger.warning(f"⚠️ Rate limited: {username}")
            raise AuthError("Too many login attempts. Please try again later.")
        
        # Get user from database - try to detect schema
        result = None
        user = None
        
        try:
            # Try old schema (hashed_password, role)
            logger.info(f"🔍 Trying old schema for '{username}'")
            result = self.db.execute_query("""
                SELECT id, username, email, hashed_password, is_active, role
                FROM users WHERE username = ?
            """, (username,))
            logger.info(f"📊 Query result: {result}")
            if result:
                user = dict(result[0])
                logger.info(f"👤 User found: ID={user.get('id')}, role={user.get('role')}, active={user.get('is_active')}")
                # Normalize is_admin field from role
                if user.get('role') == 'admin':
                    user['is_admin'] = True
                else:
                    user['is_admin'] = False
        except Exception as e:
            logger.error(f"❌ Old schema failed: {e}")
            # Try new schema (password_hash, is_admin)
            try:
                logger.info(f"🔍 Trying new schema for '{username}'")
                result = self.db.execute_query("""
                    SELECT id, username, email, password_hash as hashed_password, is_active, is_admin
                    FROM users WHERE username = ?
                """, (username,))
                if result:
                    user = dict(result[0])
                    logger.info(f"👤 User found with new schema: ID={user.get('id')}")
            except Exception as e2:
                logger.error(f"❌ New schema also failed: {e2}")
                pass
        
        if not result or not user:
            logger.warning(f"⚠️ User not found: '{username}'")
            self._record_login_attempt(username, False)
            return None
        
        # Check if user is active
        if not user['is_active']:
            logger.warning(f"⚠️ User account is disabled: '{username}'")
            self._record_login_attempt(username, False)
            raise AuthError("User account is disabled")
        
        # Verify password - use hashed_password field
        password_hash = user.get('hashed_password') or user.get('password_hash')
        logger.info(f"🔑 Password hash from DB: {password_hash[:20] if password_hash else 'None'}...")
        logger.info(f"🔑 Verifying password (length: {len(password)})")
        
        password_valid = self.password_manager.verify_password(password, password_hash) if password_hash else False
        logger.info(f"🔑 Password verification result: {password_valid}")
        
        if not password_hash or not password_valid:
            logger.warning(f"❌ Password verification failed for '{username}'")
            self._record_login_attempt(username, False)
            return None
        
        # Successful login
        logger.info(f"✅ Authentication successful for '{username}'!")
        self._record_login_attempt(username, True)
        
        # Remove password hash from return data (handle both old and new schema)
        if 'password_hash' in user:
            del user['password_hash']
        if 'hashed_password' in user:
            del user['hashed_password']
        return user
    
    def _is_rate_limited(self, username: str) -> bool:
        """Check if username is rate limited."""
        if username not in self.login_attempts:
            return False
        
        now = time.time()
        cutoff = now - (self.config.login_lockout_minutes * 60)
        
        # Remove old attempts
        self.login_attempts[username] = [
            attempt_time for attempt_time in self.login_attempts[username]
            if attempt_time > cutoff
        ]
        
        # Check if too many attempts
        return len(self.login_attempts[username]) >= self.config.max_login_attempts
    
    def _record_login_attempt(self, username: str, success: bool) -> None:
        """Record a login attempt."""
        if success:
            # Clear attempts on successful login
            if username in self.login_attempts:
                del self.login_attempts[username]
        else:
            # Record failed attempt
            if username not in self.login_attempts:
                self.login_attempts[username] = []
            self.login_attempts[username].append(time.time())
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        result = self.db.execute_query("""
            SELECT id, username, email, is_active, is_admin, created_at
            FROM users WHERE id = ?
        """, (user_id,))
        
        if result:
            return dict(result[0])
        return None
    
    def update_user(self, user_id: int, **updates) -> bool:
        """Update user information."""
        allowed_fields = ['email', 'is_active', 'is_admin']
        
        update_fields = []
        params = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return False
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        
        affected = self.db.execute_update(query, tuple(params))
        return affected > 0
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Change user password."""
        # Get current password hash
        result = self.db.execute_query("""
            SELECT password_hash FROM users WHERE id = ?
        """, (user_id,))
        
        if not result:
            return False
        
        current_hash = result[0]['password_hash']
        
        # Verify old password
        if not self.password_manager.verify_password(old_password, current_hash):
            raise AuthError("Current password is incorrect")
        
        # Validate new password
        if len(new_password) < self.config.password_min_length:
            raise AuthError(f"Password must be at least {self.config.password_min_length} characters")
        
        # Hash new password
        new_hash = self.password_manager.hash_password(new_password)
        
        # Update password
        affected = self.db.execute_update("""
            UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (new_hash, user_id))
        
        return affected > 0
    
    def create_access_token(self, user: Dict[str, Any]) -> str:
        """Create access token for user."""
        token_data = {
            "sub": str(user["id"]),
            "username": user["username"],
            "is_admin": user["is_admin"]
        }
        
        return self.token_manager.create_access_token(token_data)


# Global instances
_user_manager = None
_api_key_manager = None


def get_user_manager() -> UserManager:
    """Get global user manager."""
    global _user_manager
    if _user_manager is None:
        _user_manager = UserManager()
    return _user_manager


def get_api_key_manager() -> APIKeyManager:
    """Get global API key manager."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


class SecurityManager:
    """Combined security manager for authentication and authorization."""
    
    def __init__(self):
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.api_key_manager = APIKeyManager()
        self.user_manager = UserManager()
    
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return self.password_manager.hash_password(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return self.password_manager.verify_password(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create an access token."""
        return self.token_manager.create_access_token(data, expires_delta)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a token."""
        return self.token_manager.verify_token(token)


# Global security manager
_security_manager = None


def get_security_manager() -> SecurityManager:
    """Get global security manager."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager