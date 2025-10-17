# Security Guide

## 🔐 Overview

CameronPAD implements comprehensive security measures across authentication, authorization, data protection, and infrastructure layers. This guide covers security best practices and implementation details.

## 🛡️ Security Architecture

### Defense in Depth Strategy
```
┌─────────────────────────────────────────┐
│           External Security             │
├─────────────────────────────────────────┤
│ • Rate Limiting                         │
│ • DDoS Protection                       │
│ • WAF (Web Application Firewall)       │
│ • SSL/TLS Encryption                    │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│          Application Security           │
├─────────────────────────────────────────┤
│ • JWT Authentication                    │
│ • Role-Based Access Control (RBAC)     │
│ • Input Validation                      │
│ • SQL Injection Prevention             │
│ • XSS Protection                       │
│ • CSRF Protection                       │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           Data Security                 │
├─────────────────────────────────────────┤
│ • Encryption at Rest                    │
│ • Encryption in Transit                 │
│ • Secure Password Storage              │
│ • Data Classification                   │
│ • Audit Logging                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│        Infrastructure Security          │
├─────────────────────────────────────────┤
│ • Container Security                    │
│ • Network Segmentation                 │
│ • Secrets Management                    │
│ • Regular Updates                       │
│ • Security Monitoring                   │
└─────────────────────────────────────────┘
```

## 🔑 Authentication & Authorization

### JWT Token Security
The application uses JSON Web Tokens (JWT) for stateless authentication:

```python
# app_new/core/auth.py - Secure JWT implementation
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

class SecurityManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        """Create secure JWT token with expiration"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "sub": data.get("user_id"),
            "jti": self._generate_jti()  # JWT ID for revocation
        })
        
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True}
            )
            
            # Check if token is revoked
            if self._is_token_revoked(payload.get("jti")):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid token")
```

### Password Security
```python
class PasswordManager:
    def __init__(self):
        self.pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=12  # Strong hashing rounds
        )
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        # Validate password strength first
        self._validate_password_strength(password)
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def _validate_password_strength(self, password: str):
        """Enforce password policy"""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one number")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            raise ValueError("Password must contain at least one special character")
```

### Role-Based Access Control (RBAC)
```python
# app_new/core/permissions.py
from enum import Enum
from typing import List, Set

class Permission(Enum):
    READ_USER = "read:user"
    WRITE_USER = "write:user"
    DELETE_USER = "delete:user"
    READ_ADMIN = "read:admin"
    WRITE_ADMIN = "write:admin"
    MANAGE_PLUGINS = "manage:plugins"
    VIEW_SYSTEM = "view:system"

class Role(Enum):
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERUSER = "superuser"

ROLE_PERMISSIONS = {
    Role.GUEST: {Permission.READ_USER},
    Role.USER: {Permission.READ_USER, Permission.WRITE_USER},
    Role.MODERATOR: {
        Permission.READ_USER, Permission.WRITE_USER,
        Permission.DELETE_USER, Permission.VIEW_SYSTEM
    },
    Role.ADMIN: {
        Permission.READ_USER, Permission.WRITE_USER, Permission.DELETE_USER,
        Permission.READ_ADMIN, Permission.WRITE_ADMIN,
        Permission.MANAGE_PLUGINS, Permission.VIEW_SYSTEM
    },
    Role.SUPERUSER: set(Permission)  # All permissions
}

def check_permission(user_role: Role, required_permission: Permission) -> bool:
    """Check if user role has required permission"""
    return required_permission in ROLE_PERMISSIONS.get(user_role, set())

# Decorator for route protection
def require_permission(permission: Permission):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user from request context
            user = get_current_user()  # Implementation depends on FastAPI setup
            
            if not check_permission(user.role, permission):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage example
@router.post("/admin/users")
@require_permission(Permission.WRITE_ADMIN)
async def create_user(user_data: UserCreate):
    """Only admins can create users"""
    pass
```

## 🛡️ Input Validation & Sanitization

### Pydantic Models for Validation
```python
# app_new/api/schemas.py
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
import re

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=200)
    
    @validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class FileUpload(BaseModel):
    filename: str = Field(..., max_length=255)
    content_type: str
    size: int = Field(..., gt=0, le=10*1024*1024)  # Max 10MB
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate and sanitize filename"""
        # Remove path components
        v = os.path.basename(v)
        
        # Check for dangerous patterns
        dangerous_patterns = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com']
        if any(v.lower().endswith(pattern) for pattern in dangerous_patterns):
            raise ValueError('File type not allowed')
        
        # Sanitize filename
        v = re.sub(r'[^\w\-_\.]', '_', v)
        return v
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type"""
        allowed_types = [
            'image/jpeg', 'image/png', 'image/gif',
            'text/plain', 'text/csv',
            'application/pdf',
            'application/json'
        ]
        if v not in allowed_types:
            raise ValueError(f'Content type {v} not allowed')
        return v
```

### SQL Injection Prevention
```python
# app_new/core/database.py - Safe database operations
from sqlalchemy import text
from typing import Dict, Any

class DatabaseManager:
    async def execute_query(self, query: str, params: Dict[str, Any] = None):
        """Execute query with parameterized statements"""
        async with self.get_session() as session:
            # Always use parameterized queries
            result = await session.execute(text(query), params or {})
            await session.commit()
            return result
    
    async def search_users(self, search_term: str):
        """Safe user search with parameterized query"""
        # SAFE: Using parameters prevents SQL injection
        query = """
            SELECT id, username, email, created_at 
            FROM users 
            WHERE username ILIKE :search_term 
               OR email ILIKE :search_term
            LIMIT 50
        """
        return await self.execute_query(
            query, 
            {"search_term": f"%{search_term}%"}
        )
```

### XSS Protection
```python
# app_new/core/security.py
import html
import bleach
from markupsafe import Markup

class XSSProtection:
    def __init__(self):
        self.allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'blockquote', 'code', 'pre'
        ]
        self.allowed_attributes = {
            '*': ['class'],
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title']
        }
    
    def sanitize_html(self, content: str) -> str:
        """Sanitize HTML content to prevent XSS"""
        return bleach.clean(
            content,
            tags=self.allowed_tags,
            attributes=self.allowed_attributes,
            strip=True
        )
    
    def escape_html(self, content: str) -> str:
        """Escape HTML content"""
        return html.escape(content)
    
    def safe_render(self, content: str, allow_html: bool = False) -> Markup:
        """Safely render content for templates"""
        if allow_html:
            content = self.sanitize_html(content)
        else:
            content = self.escape_html(content)
        
        return Markup(content)

# Usage in Jinja2 templates
from jinja2 import Environment

def create_secure_jinja_env():
    env = Environment(autoescape=True)
    
    # Add security filters
    xss_protection = XSSProtection()
    env.filters['safe_html'] = xss_protection.sanitize_html
    env.filters['escape'] = xss_protection.escape_html
    
    return env
```

## 🔒 Data Protection

### Encryption at Rest
```python
# app_new/core/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    def __init__(self, password: str, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
        self.salt = salt
    
    def encrypt(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        return self.cipher.encrypt(data.encode())
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        return self.cipher.decrypt(encrypted_data).decode()

# Usage for sensitive plugin data
class SecurePluginData:
    def __init__(self, encryption_key: str):
        self.encryption = DataEncryption(encryption_key)
    
    async def store_api_key(self, plugin_name: str, api_key: str):
        """Store encrypted API key"""
        encrypted_key = self.encryption.encrypt(api_key)
        # Store in database with encryption metadata
        await self.db.store_encrypted_data(
            plugin_name, 
            "api_key", 
            encrypted_key,
            self.encryption.salt
        )
    
    async def get_api_key(self, plugin_name: str) -> str:
        """Retrieve and decrypt API key"""
        encrypted_data, salt = await self.db.get_encrypted_data(
            plugin_name, 
            "api_key"
        )
        
        # Recreate encryption with stored salt
        encryption = DataEncryption(self.encryption_key, salt)
        return encryption.decrypt(encrypted_data)
```

### Secure File Handling
```python
# app_new/core/files.py
import os
import hashlib
import magic
from pathlib import Path
from typing import BinaryIO

class SecureFileHandler:
    def __init__(self, upload_dir: str, max_size: int = 10*1024*1024):
        self.upload_dir = Path(upload_dir)
        self.max_size = max_size
        self.allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif',
            'text/plain', 'text/csv',
            'application/pdf', 'application/json'
        }
    
    async def save_file(self, file: BinaryIO, filename: str) -> str:
        """Securely save uploaded file"""
        # Validate file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset
        
        if size > self.max_size:
            raise ValueError(f"File too large: {size} bytes")
        
        # Read file content
        content = file.read()
        
        # Validate MIME type
        mime_type = magic.from_buffer(content, mime=True)
        if mime_type not in self.allowed_mime_types:
            raise ValueError(f"File type not allowed: {mime_type}")
        
        # Generate secure filename
        secure_filename = self._generate_secure_filename(filename)
        file_path = self.upload_dir / secure_filename
        
        # Ensure upload directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save file with restricted permissions
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # Set restrictive file permissions
        os.chmod(file_path, 0o644)
        
        return str(file_path)
    
    def _generate_secure_filename(self, filename: str) -> str:
        """Generate secure filename"""
        # Get file extension
        name, ext = os.path.splitext(filename)
        
        # Generate hash-based filename
        hash_name = hashlib.sha256(
            f"{name}{time.time()}".encode()
        ).hexdigest()[:16]
        
        return f"{hash_name}{ext}"
```

## 🌐 Network Security

### Rate Limiting
```python
# app_new/core/rate_limit.py
from typing import Dict, Optional
import time
import asyncio
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.locked_ips = set()
    
    async def check_rate_limit(
        self, 
        identifier: str, 
        max_requests: int = 100, 
        window: int = 3600
    ) -> bool:
        """Check if request is within rate limit"""
        current_time = time.time()
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if current_time - req_time < window
        ]
        
        # Check rate limit
        if len(self.requests[identifier]) >= max_requests:
            # Lock IP for extended period if repeatedly hitting limit
            if len(self.requests[identifier]) > max_requests * 2:
                self.locked_ips.add(identifier)
                # Auto-unlock after 24 hours
                asyncio.create_task(self._unlock_ip_later(identifier, 86400))
            
            return False
        
        # Check if IP is locked
        if identifier in self.locked_ips:
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True
    
    async def _unlock_ip_later(self, identifier: str, delay: int):
        """Unlock IP after delay"""
        await asyncio.sleep(delay)
        self.locked_ips.discard(identifier)

# FastAPI middleware integration
from fastapi import Request, HTTPException

class RateLimitMiddleware:
    def __init__(self, app, rate_limiter: RateLimiter):
        self.app = app
        self.rate_limiter = rate_limiter
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            
            # Get client IP
            client_ip = request.client.host
            if "x-forwarded-for" in request.headers:
                client_ip = request.headers["x-forwarded-for"].split(",")[0]
            
            # Check rate limit
            if not await self.rate_limiter.check_rate_limit(client_ip):
                response = HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                ).init_response()
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)
```

### CORS Security
```python
# app_new/main.py - Secure CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-domain.com",
        "https://app.your-domain.com"
    ],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With"
    ],
    expose_headers=["X-Total-Count"],
    max_age=3600  # Cache preflight requests
)
```

## 🔍 Security Monitoring & Logging

### Audit Logging
```python
# app_new/core/audit.py
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

class AuditLogger:
    def __init__(self, logger_name: str = "audit"):
        self.logger = logging.getLogger(logger_name)
        
        # Configure audit log format
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
        )
        
        # File handler for audit logs
        file_handler = logging.FileHandler('/app/logs/audit.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.setLevel(logging.INFO)
    
    def log_auth_event(
        self, 
        event_type: str, 
        user_id: Optional[str], 
        ip_address: str,
        user_agent: str,
        success: bool,
        details: Dict[str, Any] = None
    ):
        """Log authentication events"""
        event_data = {
            "type": "authentication",
            "event": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(event_data))
    
    def log_data_access(
        self, 
        user_id: str, 
        resource: str, 
        action: str,
        ip_address: str,
        success: bool = True
    ):
        """Log data access events"""
        event_data = {
            "type": "data_access",
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "success": success,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.logger.info(json.dumps(event_data))
    
    def log_admin_action(
        self, 
        admin_id: str, 
        action: str, 
        target: str,
        ip_address: str,
        details: Dict[str, Any] = None
    ):
        """Log administrative actions"""
        event_data = {
            "type": "admin_action",
            "admin_id": admin_id,
            "action": action,
            "target": target,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        self.logger.warning(json.dumps(event_data))

# Usage in authentication endpoint
audit_logger = AuditLogger()

@router.post("/auth/login")
async def login(
    credentials: UserLogin, 
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await authenticate_user(db, credentials.username, credentials.password)
        
        if user:
            token = create_access_token({"user_id": user.id})
            
            # Log successful login
            audit_logger.log_auth_event(
                "login",
                str(user.id),
                request.client.host,
                request.headers.get("user-agent", ""),
                True
            )
            
            return {"access_token": token, "token_type": "bearer"}
        else:
            # Log failed login
            audit_logger.log_auth_event(
                "login",
                None,
                request.client.host,
                request.headers.get("user-agent", ""),
                False,
                {"username": credentials.username}
            )
            
            raise HTTPException(status_code=401, detail="Invalid credentials")
    
    except Exception as e:
        # Log authentication error
        audit_logger.log_auth_event(
            "login_error",
            None,
            request.client.host,
            request.headers.get("user-agent", ""),
            False,
            {"error": str(e)}
        )
        raise
```

### Security Monitoring
```python
# app_new/core/monitoring.py
from collections import defaultdict, deque
import time
import asyncio
from typing import Dict, List

class SecurityMonitor:
    def __init__(self):
        self.failed_logins = defaultdict(deque)
        self.suspicious_activity = defaultdict(list)
        self.blocked_ips = set()
    
    async def track_failed_login(self, ip_address: str, username: str):
        """Track failed login attempts"""
        current_time = time.time()
        
        # Add failed attempt
        self.failed_logins[ip_address].append(current_time)
        
        # Keep only recent attempts (last hour)
        while (self.failed_logins[ip_address] and 
               current_time - self.failed_logins[ip_address][0] > 3600):
            self.failed_logins[ip_address].popleft()
        
        # Check for brute force pattern
        if len(self.failed_logins[ip_address]) >= 5:
            await self._handle_brute_force(ip_address, username)
    
    async def _handle_brute_force(self, ip_address: str, username: str):
        """Handle detected brute force attack"""
        # Block IP temporarily
        self.blocked_ips.add(ip_address)
        
        # Log security event
        audit_logger.log_security_event(
            "brute_force_detected",
            ip_address,
            {"username": username, "attempts": len(self.failed_logins[ip_address])}
        )
        
        # Send alert to administrators
        await self._send_security_alert(
            f"Brute force attack detected from {ip_address} targeting user {username}"
        )
        
        # Auto-unblock after 24 hours
        asyncio.create_task(self._unblock_ip_later(ip_address, 86400))
    
    async def check_suspicious_patterns(self, user_id: str, action: str, details: Dict):
        """Check for suspicious user behavior patterns"""
        current_time = time.time()
        
        # Track user actions
        self.suspicious_activity[user_id].append({
            "action": action,
            "timestamp": current_time,
            "details": details
        })
        
        # Keep only recent activity (last 24 hours)
        self.suspicious_activity[user_id] = [
            activity for activity in self.suspicious_activity[user_id]
            if current_time - activity["timestamp"] < 86400
        ]
        
        # Analyze patterns
        await self._analyze_user_behavior(user_id)
    
    async def _analyze_user_behavior(self, user_id: str):
        """Analyze user behavior for suspicious patterns"""
        activities = self.suspicious_activity[user_id]
        
        if len(activities) < 10:  # Need sufficient data
            return
        
        # Check for rapid-fire requests
        recent_actions = [
            a for a in activities 
            if time.time() - a["timestamp"] < 300  # Last 5 minutes
        ]
        
        if len(recent_actions) > 50:
            await self._flag_suspicious_user(user_id, "rapid_requests")
        
        # Check for unusual access patterns
        unique_endpoints = set(a["details"].get("endpoint", "") for a in recent_actions)
        if len(unique_endpoints) > 20:  # Accessing many different endpoints quickly
            await self._flag_suspicious_user(user_id, "endpoint_scanning")
    
    async def _flag_suspicious_user(self, user_id: str, reason: str):
        """Flag user for suspicious activity"""
        audit_logger.log_security_event(
            "suspicious_activity",
            user_id,
            {"reason": reason, "activities": len(self.suspicious_activity[user_id])}
        )
        
        # Temporarily restrict user (implement based on your needs)
        # await self._restrict_user_temporarily(user_id)

# Usage in middleware
security_monitor = SecurityMonitor()

class SecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # Track request for monitoring
        if hasattr(request.state, "user"):
            await security_monitor.check_suspicious_patterns(
                request.state.user.id,
                f"{request.method} {request.url.path}",
                {"endpoint": str(request.url.path)}
            )
        
        response = await call_next(request)
        return response
```

## 🔧 Plugin Security

### Plugin Sandboxing
```python
# app_new/plugins/security.py
import ast
import sys
from typing import Set, List
from contextlib import contextmanager

class PluginSecurityValidator:
    """Validate plugin code for security risks"""
    
    DANGEROUS_IMPORTS = {
        'os', 'sys', 'subprocess', 'socket', 'urllib',
        'requests', 'http', 'ftplib', 'smtplib',
        'pickle', 'marshal', 'shelve', 'dill',
        '__builtin__', 'builtins', 'imp', 'importlib'
    }
    
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', 'open', '__import__',
        'getattr', 'setattr', 'delattr', 'hasattr',
        'globals', 'locals', 'vars', 'dir'
    }
    
    def validate_plugin_code(self, code: str) -> List[str]:
        """Validate plugin code and return security warnings"""
        warnings = []
        
        try:
            tree = ast.parse(code)
            warnings.extend(self._check_imports(tree))
            warnings.extend(self._check_function_calls(tree))
            warnings.extend(self._check_dangerous_patterns(tree))
        except SyntaxError as e:
            warnings.append(f"Syntax error: {e}")
        
        return warnings
    
    def _check_imports(self, tree: ast.AST) -> List[str]:
        """Check for dangerous imports"""
        warnings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.DANGEROUS_IMPORTS:
                        warnings.append(f"Dangerous import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module in self.DANGEROUS_IMPORTS:
                    warnings.append(f"Dangerous import from: {node.module}")
        
        return warnings
    
    def _check_function_calls(self, tree: ast.AST) -> List[str]:
        """Check for dangerous function calls"""
        warnings = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.DANGEROUS_FUNCTIONS:
                        warnings.append(f"Dangerous function call: {node.func.id}")
        
        return warnings

class PluginSandbox:
    """Secure execution environment for plugins"""
    
    def __init__(self, allowed_modules: Set[str] = None):
        self.allowed_modules = allowed_modules or {
            'json', 'datetime', 'math', 'random',
            'hashlib', 'uuid', 'base64', 'typing'
        }
    
    @contextmanager
    def secure_execution_context(self):
        """Create secure execution context for plugin code"""
        # Save original import function
        original_import = __builtins__['__import__']
        
        def secure_import(name, *args, **kwargs):
            if name not in self.allowed_modules:
                raise ImportError(f"Import of '{name}' not allowed in plugin")
            return original_import(name, *args, **kwargs)
        
        try:
            # Replace import function
            __builtins__['__import__'] = secure_import
            yield
        finally:
            # Restore original import function
            __builtins__['__import__'] = original_import
```

## 🚨 Incident Response

### Security Incident Handling
```python
# app_new/core/incident_response.py
import asyncio
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityIncident:
    def __init__(
        self, 
        incident_type: str,
        severity: IncidentSeverity,
        description: str,
        affected_resources: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.id = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        self.incident_type = incident_type
        self.severity = severity
        self.description = description
        self.affected_resources = affected_resources or []
        self.metadata = metadata or {}
        self.created_at = datetime.utcnow()
        self.status = "open"

class IncidentResponseManager:
    def __init__(self):
        self.active_incidents = {}
        self.incident_handlers = {
            "brute_force": self._handle_brute_force,
            "data_breach": self._handle_data_breach,
            "malicious_upload": self._handle_malicious_upload,
            "privilege_escalation": self._handle_privilege_escalation
        }
    
    async def report_incident(self, incident: SecurityIncident):
        """Report and handle security incident"""
        self.active_incidents[incident.id] = incident
        
        # Log incident
        audit_logger.log_security_incident(incident)
        
        # Handle based on type
        handler = self.incident_handlers.get(incident.incident_type)
        if handler:
            await handler(incident)
        
        # Send alerts based on severity
        if incident.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]:
            await self._send_immediate_alert(incident)
    
    async def _handle_brute_force(self, incident: SecurityIncident):
        """Handle brute force attack"""
        ip_address = incident.metadata.get("ip_address")
        
        if ip_address:
            # Block IP immediately
            await self._block_ip_address(ip_address)
            
            # Increase monitoring for this IP
            await self._enhance_monitoring(ip_address)
    
    async def _handle_data_breach(self, incident: SecurityIncident):
        """Handle potential data breach"""
        # Immediate containment
        affected_user = incident.metadata.get("user_id")
        if affected_user:
            await self._suspend_user_account(affected_user)
        
        # Revoke all sessions for affected user
        await self._revoke_user_sessions(affected_user)
        
        # Enable enhanced logging
        await self._enable_enhanced_logging()
    
    async def _send_immediate_alert(self, incident: SecurityIncident):
        """Send immediate alert for high-severity incidents"""
        alert_message = f"""
        🚨 SECURITY INCIDENT ALERT 🚨
        
        Incident ID: {incident.id}
        Type: {incident.incident_type}
        Severity: {incident.severity.value.upper()}
        Time: {incident.created_at.isoformat()}
        
        Description: {incident.description}
        
        Affected Resources: {', '.join(incident.affected_resources)}
        
        Immediate action may be required.
        """
        
        # Send to admin channels
        await self._send_discord_alert(alert_message)
        await self._send_email_alert(alert_message)
```

## 📋 Security Checklist

### Pre-Production Security Checklist

#### Authentication & Authorization
- [ ] Strong password policy enforced
- [ ] JWT tokens properly configured with expiration
- [ ] Role-based access control implemented
- [ ] Multi-factor authentication available
- [ ] Session management secure
- [ ] Password reset flow secure

#### Input Validation
- [ ] All inputs validated with Pydantic models
- [ ] SQL injection prevention implemented
- [ ] XSS protection enabled
- [ ] File upload restrictions enforced
- [ ] CSRF protection enabled
- [ ] Content type validation

#### Data Protection
- [ ] Sensitive data encrypted at rest
- [ ] TLS encryption for data in transit
- [ ] Database access properly secured
- [ ] API keys encrypted in storage
- [ ] Audit logging implemented
- [ ] Data backup encryption

#### Infrastructure Security
- [ ] Docker containers run as non-root user
- [ ] Network segmentation implemented
- [ ] Rate limiting configured
- [ ] Reverse proxy properly configured
- [ ] Security headers implemented
- [ ] Regular security updates scheduled

#### Monitoring & Response
- [ ] Security monitoring implemented
- [ ] Intrusion detection configured
- [ ] Incident response plan documented
- [ ] Security alerts configured
- [ ] Regular security audits scheduled
- [ ] Penetration testing completed

#### Plugin Security
- [ ] Plugin validation implemented
- [ ] Plugin sandboxing configured
- [ ] Plugin permissions model defined
- [ ] Plugin security review process
- [ ] Plugin update security checks

### Regular Security Maintenance

#### Daily
- [ ] Review security logs
- [ ] Check for failed login attempts
- [ ] Monitor rate limiting effectiveness
- [ ] Verify backup completion

#### Weekly
- [ ] Update security signatures
- [ ] Review user access patterns
- [ ] Check for system updates
- [ ] Validate SSL certificates

#### Monthly
- [ ] Security vulnerability scan
- [ ] Review user permissions
- [ ] Update security documentation
- [ ] Test incident response procedures

#### Quarterly
- [ ] Penetration testing
- [ ] Security architecture review
- [ ] Update security policies
- [ ] Security awareness training

This security guide provides comprehensive protection for CameronPAD. Implement these measures based on your security requirements and risk tolerance.