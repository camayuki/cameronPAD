"""
Tests for the authentication and authorization system.
"""
import pytest
from datetime import datetime, timedelta

from app_new.core.auth import UserManager, APIKeyManager, AuthError
from app_new.core.database import DatabaseManager


class TestUserManager:
    """Test user management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_user(self, database_manager: DatabaseManager, clean_database):
        """Test user creation."""
        user_manager = UserManager()
        
        user_id = user_manager.create_user(
            username="testuser",
            password="testpassword123",
            email="test@example.com"
        )
        
        assert user_id > 0
        
        # Verify user was created
        user = user_manager.get_user_by_id(user_id)
        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@example.com"
        assert user["is_active"] is True
        assert user["is_admin"] is False
    
    @pytest.mark.asyncio
    async def test_create_duplicate_user(self, database_manager: DatabaseManager, clean_database):
        """Test creating duplicate user fails."""
        user_manager = UserManager()
        
        # Create first user
        user_manager.create_user(
            username="testuser",
            password="testpassword123",
            email="test@example.com"
        )
        
        # Try to create duplicate
        with pytest.raises(AuthError, match="Username or email already exists"):
            user_manager.create_user(
                username="testuser",
                password="anotherpassword123",
                email="different@example.com"
            )
    
    @pytest.mark.asyncio
    async def test_weak_password(self, database_manager: DatabaseManager, clean_database):
        """Test weak password rejection."""
        user_manager = UserManager()
        
        with pytest.raises(AuthError, match="Password must be at least"):
            user_manager.create_user(
                username="testuser",
                password="weak",
                email="test@example.com"
            )
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, test_user: dict):
        """Test user authentication."""
        user_manager = UserManager()
        
        # Successful authentication
        user = user_manager.authenticate_user("testuser", "testpassword123")
        assert user is not None
        assert user["username"] == "testuser"
        assert "password_hash" not in user
        
        # Failed authentication
        user = user_manager.authenticate_user("testuser", "wrongpassword")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, test_user: dict):
        """Test login rate limiting."""
        user_manager = UserManager()
        user_manager.config.max_login_attempts = 3
        user_manager.config.login_lockout_minutes = 1
        
        # Make multiple failed attempts
        for i in range(3):
            user = user_manager.authenticate_user("testuser", "wrongpassword")
            assert user is None
        
        # Next attempt should be rate limited
        with pytest.raises(AuthError, match="Too many login attempts"):
            user_manager.authenticate_user("testuser", "wrongpassword")
        
        # Even correct password should be rate limited
        with pytest.raises(AuthError, match="Too many login attempts"):
            user_manager.authenticate_user("testuser", "testpassword123")
    
    @pytest.mark.asyncio
    async def test_change_password(self, test_user: dict):
        """Test password change."""
        user_manager = UserManager()
        
        # Successful password change
        success = user_manager.change_password(
            test_user["id"],
            "testpassword123",
            "newpassword123"
        )
        assert success
        
        # Verify new password works
        user = user_manager.authenticate_user("testuser", "newpassword123")
        assert user is not None
        
        # Verify old password doesn't work
        user = user_manager.authenticate_user("testuser", "testpassword123")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, test_user: dict):
        """Test password change with wrong current password."""
        user_manager = UserManager()
        
        with pytest.raises(AuthError, match="Current password is incorrect"):
            user_manager.change_password(
                test_user["id"],
                "wrongpassword",
                "newpassword123"
            )
    
    @pytest.mark.asyncio
    async def test_update_user(self, test_user: dict):
        """Test user update."""
        user_manager = UserManager()
        
        # Update user
        success = user_manager.update_user(
            test_user["id"],
            email="newemail@example.com",
            is_admin=True
        )
        assert success
        
        # Verify update
        user = user_manager.get_user_by_id(test_user["id"])
        assert user["email"] == "newemail@example.com"
        assert user["is_admin"] is True
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, test_user: dict):
        """Test access token creation."""
        user_manager = UserManager()
        
        token = user_manager.create_access_token(test_user)
        assert token is not None
        assert len(token) > 0
        
        # Verify token can be decoded
        payload = user_manager.token_manager.verify_token(token)
        assert payload["sub"] == str(test_user["id"])
        assert payload["username"] == test_user["username"]


class TestAPIKeyManager:
    """Test API key management functionality."""
    
    @pytest.mark.asyncio
    async def test_create_api_key(self, test_user: dict):
        """Test API key creation."""
        api_key_manager = APIKeyManager()
        
        key_id, api_key = api_key_manager.create_api_key(
            user_id=test_user["id"],
            key_name="test_key",
            permissions=["read", "write"]
        )
        
        assert key_id > 0
        assert api_key is not None
        assert len(api_key) > 0
    
    @pytest.mark.asyncio
    async def test_verify_api_key(self, api_key: tuple[int, str], test_user: dict):
        """Test API key verification."""
        api_key_manager = APIKeyManager()
        key_id, key = api_key
        
        # Verify valid key
        key_info = api_key_manager.verify_api_key(key)
        assert key_info is not None
        assert key_info["user_id"] == test_user["id"]
        assert key_info["username"] == test_user["username"]
        assert key_info["key_name"] == "test_key"
        
        # Verify invalid key
        key_info = api_key_manager.verify_api_key("invalid_key")
        assert key_info is None
    
    @pytest.mark.asyncio
    async def test_revoke_api_key(self, api_key: tuple[int, str], test_user: dict):
        """Test API key revocation."""
        api_key_manager = APIKeyManager()
        key_id, key = api_key
        
        # Verify key works before revocation
        key_info = api_key_manager.verify_api_key(key)
        assert key_info is not None
        
        # Revoke key
        success = api_key_manager.revoke_api_key(key_id, test_user["id"])
        assert success
        
        # Verify key no longer works
        key_info = api_key_manager.verify_api_key(key)
        assert key_info is None
    
    @pytest.mark.asyncio
    async def test_api_key_expiration(self, test_user: dict):
        """Test API key expiration."""
        api_key_manager = APIKeyManager()
        
        # Create key that expires in 1 second
        expires_at = datetime.now() + timedelta(seconds=1)
        key_id, api_key = api_key_manager.create_api_key(
            user_id=test_user["id"],
            key_name="expiring_key",
            expires_at=expires_at
        )
        
        # Key should work initially
        key_info = api_key_manager.verify_api_key(api_key)
        assert key_info is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Key should no longer work
        key_info = api_key_manager.verify_api_key(api_key)
        assert key_info is None


class TestPasswordManager:
    """Test password hashing and verification."""
    
    def test_hash_password(self):
        """Test password hashing."""
        from app_new.core.auth import PasswordManager
        
        pwd_manager = PasswordManager()
        password = "testpassword123"
        
        hashed = pwd_manager.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password(self):
        """Test password verification."""
        from app_new.core.auth import PasswordManager
        
        pwd_manager = PasswordManager()
        password = "testpassword123"
        
        hashed = pwd_manager.hash_password(password)
        
        # Correct password should verify
        assert pwd_manager.verify_password(password, hashed)
        
        # Wrong password should not verify
        assert not pwd_manager.verify_password("wrongpassword", hashed)


class TestTokenManager:
    """Test JWT token management."""
    
    def test_create_token(self):
        """Test token creation."""
        from app_new.core.auth import TokenManager
        
        token_manager = TokenManager()
        data = {"user_id": 1, "username": "testuser"}
        
        token = token_manager.create_access_token(data)
        assert token is not None
        assert len(token) > 0
    
    def test_verify_token(self):
        """Test token verification."""
        from app_new.core.auth import TokenManager
        
        token_manager = TokenManager()
        data = {"user_id": 1, "username": "testuser"}
        
        token = token_manager.create_access_token(data)
        payload = token_manager.verify_token(token)
        
        assert payload["user_id"] == 1
        assert payload["username"] == "testuser"
        assert "exp" in payload
    
    def test_verify_invalid_token(self):
        """Test invalid token verification."""
        from app_new.core.auth import TokenManager
        
        token_manager = TokenManager()
        
        with pytest.raises(AuthError, match="Invalid token"):
            token_manager.verify_token("invalid_token")
    
    def test_verify_expired_token(self):
        """Test expired token verification."""
        from app_new.core.auth import TokenManager
        
        token_manager = TokenManager()
        data = {"user_id": 1, "username": "testuser"}
        
        # Create token with very short expiration
        expires_delta = timedelta(seconds=-1)  # Already expired
        token = token_manager.create_access_token(data, expires_delta)
        
        with pytest.raises(AuthError, match="Token has expired"):
            token_manager.verify_token(token)