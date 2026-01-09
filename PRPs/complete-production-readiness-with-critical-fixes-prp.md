# PRP: Complete Local LLM Research Analytics Tool - Production Readiness & Critical Refactoring

## Goal

Transform the **impressive but vulnerable** Local LLM Research Analytics Tool into a **secure, scalable enterprise platform** by addressing critical security vulnerabilities, performance bottlenecks, and architectural technical debt before adding new features.

## Why

- **Security First**: Multiple critical vulnerabilities prevent any production deployment
- **Technical Debt**: Architecture patterns need refactoring for enterprise scale
- **Performance Issues**: Current implementation cannot handle enterprise workloads
- **Code Quality**: Anti-patterns and inconsistencies will cause maintenance nightmares
- **Enterprise Requirements**: Missing essential features for production deployment

## What

**CRITICAL**: This PRP prioritizes **security hardening and refactoring** over new features. The impressive feature set is useless without addressing fundamental issues.

### Critical Security Fixes - Must Complete Before ANY Other Work

- [ ] **Authentication System**: Implement complete auth module (currently imported but non-existent)
- [ ] **Secret Management**: Replace plaintext secrets with vault-based system
- [ ] **SQL Injection Prevention**: Fix vulnerable SQL patterns in vector store
- [ ] **Input Validation**: Add comprehensive validation to all endpoints
- [ ] **CORS Security**: Replace hardcoded origins with environment-based config
- [ ] **API Authorization**: Add proper JWT-based middleware to all routes

### Critical Performance Fixes

- [ ] **Connection Pooling**: Fix resource leaks in database and agent connections
- [ ] **Memory Management**: Implement proper batching for large documents
- [ ] **Cache Strategy**: Replace memory leaks with Redis-based distributed caching
- [ ] **Query Optimization**: Add missing database indexes and optimize queries
- [ ] **Frontend Performance**: Add virtualization for large chat histories

### Essential Refactoring

- [ ] **Configuration System**: Simplify over-complex configuration management
- [ ] **Error Handling**: Create centralized error handling middleware
- [ ] **Code Duplication**: Eliminate duplicate patterns across modules
- [ ] **Frontend Architecture**: Break down god-object Zustand store
- [ ] **Async Patterns**: Standardize async/await usage throughout codebase

## All Needed Context

### 🚨 Critical Issues Found in Code Review

#### **Critical Security Vulnerabilities**

1. **Missing Authentication Module** (`src/api/routes/auth.py`):
   ```python
   # Imports non-existent module
   from src.auth import (
       JWT_ACCESS_TOKEN_EXPIRE_MINUTES,  # This module doesn't exist!
       # ... other imports
   )
   ```
   - All API endpoints currently accessible without authentication
   - JWT tokens referenced but no validation implemented

2. **Secret Management Disaster** (`.env.example`, `docker-compose.yml`):
   ```bash
   # Default passwords in plain text
   MSSQL_SA_PASSWORD=LocalLLM@2024!
   SUPERSET_ADMIN_PASSWORD=LocalLLM@2024!
   
   # Predictable secret key
   SUPERSET_SECRET_KEY="${SUPERSET_SECRET_KEY:-localllm_default_secret_key_change_me_in_production}"
   ```
   - Secrets exposed in environment files
   - Predictable default secrets vulnerable to attacks

3. **SQL Injection Risk** (`src/rag/mssql_vector_store.py:110-117`):
   ```python
   # Vulnerable DECLARE pattern
   await session.execute(text("""
       DECLARE @vec VECTOR(768) = :embedding;
       INSERT INTO vectors.document_chunks ...
   """))
   ```
   - Dynamic SQL could be vulnerable if parameters not properly sanitized

4. **CORS Security Issue** (`src/api/main.py:58-73`):
   ```python
   # Hardcoded origins in production code
   app.add_middleware(
       CORSMiddleware,
       allow_origins=[
           "http://localhost:5173",  # Should be environment-based
           # ... more hardcoded origins
       ],
       allow_methods=["*"],  # Too permissive
       allow_headers=["*"],   # Too permissive
   )
   ```

#### **Critical Performance Issues**

1. **Resource Leaks** (`src/agent/core.py:275-277`):
   ```python
   # Improper async context management
   async with self.agent:  # Created multiple times without cleanup
       result = await self.agent.run(message)
       return result.output
   ```

2. **Memory Scalability** (`src/rag/mssql_vector_store.py:101`):
   ```python
   # No batching for large documents
   embeddings = await self.embedder.embed_batch(chunks)  # Can exhaust memory
   ```

3. **Cache Memory Leaks** (`src/agent/core.py:92-96`):
   ```python
   # LRU cache without proper size management
   self.cache: ResponseCache[str] = get_response_cache(
       max_size=settings.cache_max_size,
       ttl_seconds=settings.cache_ttl_seconds,
       enabled=self._cache_enabled,
   )  # Can grow without bounds
   ```

#### **Architectural Technical Debt**

1. **Configuration Complexity** (`src/utils/config.py`):
   - 400+ lines of configuration with complex inheritance
   - Optional imports creating runtime uncertainty
   - Duplicate URL generation logic

2. **Frontend God Object** (`frontend/src/stores/chatStore.ts`):
   - 50+ methods and properties in single store
   - Violates single responsibility principle
   - No virtualization for large datasets

3. **Code Duplication**:
   - Authentication patterns repeated across routes
   - Database URL generation duplicated
   - Error handling scattered throughout

### Technology Stack Analysis

#### Current Stack - Keep & Fix
| Layer | Technology | Status | Critical Issues |
|-------|-------------|---------|-----------------|
| **Authentication** | ❌ Missing | Critical | No auth module implemented |
| **Security** | ❌ Inadequate | Critical | Multiple vulnerabilities |
| **Database** | SQL Server 2025 | Good | Performance issues |
| **Caching** | In-memory | Bad | Memory leaks, no distribution |
| **Frontend** | React + Zustand | Good | Architecture issues |
| **API** | FastAPI | Good | Missing middleware |

#### New Additions for Production
| Layer | Technology | Purpose |
|-------|-------------|---------|
| **Security** | JWT + bcrypt | Authentication & authorization |
| **Secrets** | HashiCorp Vault | Secure secret management |
| **Monitoring** | Prometheus + Grafana | Observability |
| **Cache** | Redis Stack | Distributed caching |
| **Database** | Connection Pooling | Performance optimization |
| **API Gateway** | Traefik/Nginx | Security & routing |

## Implementation Plan

### Phase 0: Critical Security Hardening (3-4 days) - **BLOCKER**

**Priority**: MUST complete before any other work. Security vulnerabilities make the system unusable.

#### Files to Create:
- `src/auth/__init__.py` - Complete authentication module
- `src/auth/jwt_handler.py` - JWT token management
- `src/auth/rbac.py` - Role-based access control
- `src/auth/middleware.py` - Authentication middleware
- `src/security/__init__.py` - Security utilities
- `src/security/secrets.py` - Secret management
- `src/api/middleware/` - Security and audit middleware

#### Critical Security Implementation:

```python
# src/auth/__init__.py - NEW FILE
"""
Complete Authentication and Authorization System
Implements JWT-based authentication with RBAC.
"""

from .jwt_handler import JWTHandler
from .rbac import RBACManager, Role, Permission
from .middleware import AuthMiddleware, require_auth, require_permission

__all__ = [
    "JWTHandler",
    "RBACManager", 
    "Role",
    "Permission",
    "AuthMiddleware",
    "require_auth",
    "require_permission"
]

# src/auth/jwt_handler.py - NEW FILE
"""
JWT Token Management
Handles creation, validation, and refresh of JWT tokens.
"""

import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from passlib.context import CryptContext
import structlog

logger = structlog.get_logger()

class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
            
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        logger.info("access_token_created", user_id=data.get("sub"))
        return encoded_jwt
    
    def create_refresh_token(
        self, 
        user_id: str, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token."""
        if expires_delta is None:
            expires_delta = timedelta(days=7)
            
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm
        )
        
        logger.info("refresh_token_created", user_id=user_id)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("token_expired")
            return None
        except jwt.JWTError as e:
            logger.warning("token_invalid", error=str(e))
            return None

# src/auth/rbac.py - NEW FILE
"""
Role-Based Access Control (RBAC)
Implements hierarchical permissions system.
"""

from enum import Enum
from typing import Dict, Set, List, Optional
import structlog

logger = structlog.get_logger()

class Role(Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SYSTEM = "system"  # For internal services

class Permission(Enum):
    """Granular permissions for different operations."""
    
    # Data permissions
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    DELETE_DATA = "delete_data"
    EXPORT_DATA = "export_data"
    
    # Analytics permissions
    EXECUTE_QUERIES = "execute_queries"
    CREATE_DASHBOARDS = "create_dashboards"
    MANAGE_DASHBOARDS = "manage_dashboards"
    
    # System permissions
    MANAGE_USERS = "manage_users"
    MANAGE_SYSTEM = "manage_system"
    ACCESS_ADMIN_API = "access_admin_api"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    
    # ML/AI permissions
    TRAIN_MODELS = "train_models"
    USE_ADVANCED_AI = "use_advanced_ai"
    
    # Collaboration permissions
    SHARE_DASHBOARDS = "share_dashboards"
    MANAGE_COLLABORATION = "manage_collaboration"

class RBACManager:
    """Manages role-based access control."""
    
    def __init__(self):
        self.role_permissions = self._build_permission_map()
    
    def _build_permission_map(self) -> Dict[Role, Set[Permission]]:
        """Build hierarchical permission mapping."""
        return {
            Role.ADMIN: {p for p in Permission},
            Role.SYSTEM: {p for p in Permission},
            Role.DATA_SCIENTIST: {
                Permission.READ_DATA, Permission.WRITE_DATA, Permission.EXECUTE_QUERIES,
                Permission.CREATE_DASHBOARDS, Permission.MANAGE_DASHBOARDS,
                Permission.EXPORT_DATA, Permission.TRAIN_MODELS, Permission.USE_ADVANCED_AI,
                Permission.SHARE_DASHBOARDS
            },
            Role.ANALYST: {
                Permission.READ_DATA, Permission.EXECUTE_QUERIES,
                Permission.CREATE_DASHBOARDS, Permission.MANAGE_DASHBOARDS,
                Permission.EXPORT_DATA, Permission.SHARE_DASHBOARDS
            },
            Role.VIEWER: {
                Permission.READ_DATA
            }
        }
    
    def has_permission(self, user_role: Role, permission: Permission) -> bool:
        """Check if role has specific permission."""
        role_perms = self.role_permissions.get(user_role, set())
        return permission in role_perms
    
    def has_any_permission(
        self, 
        user_role: Role, 
        permissions: List[Permission]
    ) -> bool:
        """Check if role has any of the specified permissions."""
        return any(
            self.has_permission(user_role, perm) 
            for perm in permissions
        )
    
    def get_role_permissions(self, role: Role) -> Set[Permission]:
        """Get all permissions for a role."""
        return self.role_permissions.get(role, set())
    
    def validate_role_hierarchy(self, requesting_role: Role, target_role: Role) -> bool:
        """Check if requesting role can manage target role."""
        # Define role hierarchy (higher number = more privilege)
        role_hierarchy = {
            Role.VIEWER: 1,
            Role.ANALYST: 2,
            Role.DATA_SCIENTIST: 3,
            Role.ADMIN: 4,
            Role.SYSTEM: 5
        }
        
        requesting_level = role_hierarchy.get(requesting_role, 0)
        target_level = role_hierarchy.get(target_role, 0)
        
        return requesting_level >= target_level

# src/auth/middleware.py - NEW FILE
"""
Authentication Middleware for FastAPI
Provides JWT validation and user context.
"""

from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import structlog

from .jwt_handler import JWTHandler
from .rbac import RBACManager, Role, Permission

logger = structlog.get_logger()

class AuthMiddleware:
    """Authentication middleware for FastAPI."""
    
    def __init__(self, jwt_handler: JWTHandler, rbac_manager: RBACManager):
        self.jwt_handler = jwt_handler
        self.rbac_manager = rbac_manager
        self.security = HTTPBearer(auto_error=False)
    
    async def get_current_user(
        self, 
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = None
    ) -> Dict[str, Any]:
        """Get current authenticated user."""
        
        # Try to get token from Authorization header
        if credentials and credentials.scheme == "Bearer":
            token = credentials.credentials
        else:
            # Try to get from cookie (for web interface)
            token = request.cookies.get("access_token")
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token
        payload = self.jwt_handler.verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        
        logger.info("user_authenticated", user_id=user_id)
        
        return {
            "user_id": user_id,
            "role": Role(payload.get("role", "viewer")),
            "permissions": self.rbac_manager.get_role_permissions(
                Role(payload.get("role", "viewer"))
            ),
            "token_payload": payload
        }

# Dependency functions for FastAPI routes
def create_auth_dependencies(jwt_handler: JWTHandler, rbac_manager: RBACManager):
    """Create authentication dependency functions."""
    
    auth_middleware = AuthMiddleware(jwt_handler, rbac_manager)
    
    def get_current_user(request: Request):
        return auth_middleware.get_current_user(request)
    
    def require_permission(permission: Permission):
        """Create dependency that requires specific permission."""
        async def permission_dependency(
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            user_role = current_user["role"]
            if not rbac_manager.has_permission(user_role, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {permission.value}"
                )
            return current_user
        
        return permission_dependency
    
    def require_role(role: Role):
        """Create dependency that requires specific role."""
        async def role_dependency(
            current_user: Dict[str, Any] = Depends(get_current_user)
        ):
            user_role = current_user["role"]
            if user_role != role and not rbac_manager.validate_role_hierarchy(user_role, role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient role. Required: {role.value}"
                )
            return current_user
        
        return role_dependency
    
    return {
        "get_current_user": get_current_user,
        "require_permission": require_permission,
        "require_role": require_role
    }
```

#### Security Middleware Implementation:

```python
# src/api/middleware/security.py - NEW FILE
"""
Security middleware for API protection.
"""

from fastapi import Request, Response, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from typing import Dict, List
import time
import structlog
from collections import defaultdict, deque

logger = structlog.get_logger()

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:"
        )
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with configurable limits."""
    
    def __init__(
        self, 
        app, 
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        self._cleanup_old_requests(client_ip, current_time)
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                "rate_limit_exceeded",
                client_ip=client_ip,
                requests=len(self.requests[client_ip])
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            max(0, self.requests_per_minute - len(self.requests[client_ip]))
        )
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP considering proxies."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def _cleanup_old_requests(self, client_ip: str, current_time: float):
        """Remove requests older than 1 minute."""
        if client_ip in self.requests:
            cutoff_time = current_time - 60
            while (
                self.requests[client_ip] and 
                self.requests[client_ip][0] < cutoff_time
            ):
                self.requests[client_ip].popleft()

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Comprehensive audit logging for security events."""
    
    async def dispatch(
        self, 
        request: Request, 
        call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.time()
        
        # Log request
        await self._log_request(request)
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        await self._log_response(request, response, process_time)
        
        return response
    
    async def _log_request(self, request: Request):
        """Log incoming request details."""
        logger.info(
            "api_request",
            method=request.method,
            url=str(request.url),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            content_length=request.headers.get("content-length"),
            timestamp=time.time()
        )
    
    async def _log_response(
        self, 
        request: Request, 
        response: Response, 
        process_time: float
    ):
        """Log response details."""
        logger.info(
            "api_response",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            response_size=response.headers.get("content-length"),
            timestamp=time.time()
        )
        
        # Log error responses for security monitoring
        if response.status_code >= 400:
            logger.warning(
                "api_error_response",
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP considering proxies."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host
```

### Phase 1: Performance Critical Fixes (2-3 days)

**Files to modify:**
- `src/rag/mssql_vector_store.py` - Fix batching and SQL injection
- `src/agent/core.py` - Fix resource leaks and caching
- `src/performance/` - New performance optimization module
- `src/database/` - New database connection management

#### Performance Implementation:

```python
# src/performance/batch_processor.py - NEW FILE
"""
Batch processing for memory-efficient operations.
"""

import asyncio
from typing import List, Any, Callable, Optional
import structlog
from dataclasses import dataclass

logger = structlog.get_logger()

@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    batch_size: int = 100
    max_concurrent_batches: int = 5
    processing_timeout: int = 300
    memory_threshold_mb: int = 1024  # Stop if memory usage exceeds this

class BatchProcessor:
    """Efficient batch processing for large datasets."""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_batches)
    
    async def process_chunks(
        self, 
        chunks: List[str], 
        processor_func: Callable[[List[str]], Any]
    ) -> List[Any]:
        """Process chunks in configurable batches."""
        if not chunks:
            return []
        
        batches = self._create_batches(chunks)
        
        # Process batches concurrently with semaphore
        tasks = []
        for batch_idx, batch in enumerate(batches):
            task = self._process_batch_with_semaphore(
                batch_idx, batch, processor_func
            )
            tasks.append(task)
        
        # Wait for all batches to complete
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions and flatten results
        results = []
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(
                    "batch_processing_failed",
                    batch_index=i,
                    error=str(result)
                )
                raise result
            results.extend(result)
        
        return results
    
    def _create_batches(self, items: List[str]) -> List[List[str]]:
        """Create batches from items."""
        batches = []
        for i in range(0, len(items), self.config.batch_size):
            batch = items[i:i + self.config.batch_size]
            batches.append(batch)
        return batches
    
    async def _process_batch_with_semaphore(
        self, 
        batch_idx: int, 
        batch: List[str], 
        processor_func: Callable[[List[str]], Any]
    ) -> Any:
        """Process single batch with semaphore control."""
        async with self.semaphore:
            try:
                logger.info(
                    "processing_batch",
                    batch_index=batch_idx,
                    batch_size=len(batch)
                )
                
                result = await asyncio.wait_for(
                    processor_func(batch),
                    timeout=self.config.processing_timeout
                )
                
                logger.info(
                    "batch_completed",
                    batch_index=batch_idx,
                    batch_size=len(batch)
                )
                
                return result
                
            except asyncio.TimeoutError:
                logger.error(
                    "batch_timeout",
                    batch_index=batch_idx,
                    timeout=self.config.processing_timeout
                )
                raise
            except Exception as e:
                logger.error(
                    "batch_error",
                    batch_index=batch_idx,
                    error=str(e)
                )
                raise

# src/performance/memory_manager.py - NEW FILE
"""
Memory management utilities.
"""

import gc
import psutil
import os
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()

class MemoryManager:
    """Monitor and manage memory usage."""
    
    def __init__(self, memory_threshold_mb: int = 2048):
        self.memory_threshold_mb = memory_threshold_mb
        self.process = psutil.Process(os.getpid())
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": memory_percent,
            "threshold_mb": self.memory_threshold_mb,
            "near_threshold": (memory_info.rss / 1024 / 1024) > (self.memory_threshold_mb * 0.9)
        }
    
    def check_memory_pressure(self) -> bool:
        """Check if memory usage exceeds threshold."""
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        if memory_mb > self.memory_threshold_mb:
            logger.warning(
                "memory_threshold_exceeded",
                current_mb=memory_mb,
                threshold_mb=self.memory_threshold_mb
            )
            return True
        
        return False
    
    def force_garbage_collection(self) -> int:
        """Force garbage collection and return freed objects."""
        before_count = len(gc.get_objects())
        collected = gc.collect()
        after_count = len(gc.get_objects())
        
        freed_objects = before_count - after_count
        
        if freed_objects > 0:
            logger.info(
                "garbage_collected",
                freed_objects=freed_objects,
                before_count=before_count,
                after_count=after_count
            )
        
        return freed_objects
    
    async def with_memory_management(
        self, 
        func, 
        *args, 
        check_interval: int = 10,
        **kwargs
    ):
        """Execute function with periodic memory checks."""
        # Initial memory check
        if self.check_memory_pressure():
            self.force_garbage_collection()
        
        # Execute function with periodic checks
        if asyncio.iscoroutinefunction(func):
            return await self._async_with_memory_management(
                func, args, kwargs, check_interval
            )
        else:
            return self._sync_with_memory_management(
                func, args, kwargs, check_interval
            )
    
    async def _async_with_memory_management(
        self, 
        func, 
        args: tuple, 
        kwargs: dict, 
        check_interval: int
    ):
        """Execute async function with memory management."""
        task = asyncio.create_task(func(*args, **kwargs))
        
        while not task.done():
            await asyncio.sleep(check_interval)
            
            if self.check_memory_pressure():
                self.force_garbage_collection()
                
                # If still under pressure, warn but continue
                if self.check_memory_pressure():
                    logger.warning(
                        "high_memory_pressure_continuing",
                        **self.get_memory_usage()
                    )
        
        return await task
    
    def _sync_with_memory_management(
        self, 
        func, 
        args: tuple, 
        kwargs: dict, 
        check_interval: int
    ):
        """Execute sync function with memory management."""
        # For sync functions, just call with pre/post checks
        self.check_memory_pressure()
        result = func(*args, **kwargs)
        self.check_memory_pressure()
        return result

# src/database/connection_manager.py - NEW FILE
"""
Advanced database connection management with pooling.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import event
from contextlib import asynccontextmanager
import structlog
import time
from typing import Dict, Any, Optional

logger = structlog.get_logger()

class DatabaseConnectionManager:
    """Advanced database connection management with monitoring."""
    
    def __init__(
        self, 
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        
        self.engine = create_async_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,
            echo=False  # Set to True for SQL debugging in development
        )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Register connection event listeners
        self._register_event_listeners()
        
        self.stats = {
            "connections_created": 0,
            "connections_checked_out": 0,
            "connections_returned": 0,
            "connection_errors": 0
        }
    
    def _register_event_listeners(self):
        """Register SQLAlchemy event listeners for monitoring."""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            self.stats["connections_created"] += 1
            logger.debug("database_connection_created")
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            self.stats["connections_checked_out"] += 1
            logger.debug("database_connection_checked_out")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            self.stats["connections_returned"] += 1
            logger.debug("database_connection_returned")
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with proper error handling."""
        session = self.session_factory()
        
        try:
            yield session
            await session.commit()
            logger.debug("database_transaction_committed")
        except Exception as e:
            await session.rollback()
            self.stats["connection_errors"] += 1
            logger.error(
                "database_transaction_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        finally:
            await session.close()
            logger.debug("database_session_closed")
    
    async def execute_query(
        self, 
        query: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute query with timing and error handling."""
        start_time = time.time()
        
        try:
            async with self.get_session() as session:
                result = await session.execute(query, params or {})
                
                execution_time = time.time() - start_time
                logger.info(
                    "query_executed",
                    execution_time=execution_time,
                    query_preview=query[:100] + "..." if len(query) > 100 else query
                )
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                "query_execution_failed",
                execution_time=execution_time,
                error=str(e),
                query_preview=query[:100] + "..." if len(query) > 100 else query
            )
            raise
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        pool = self.engine.pool
        
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "current_connections": pool.size(),
            "checked_out_connections": pool.checkedout(),
            "overflow_connections": pool.overflow(),
            "invalid_connections": pool.invalid(),
            "stats": self.stats.copy()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            async with self.get_session() as session:
                result = await session.execute("SELECT 1 as health_check")
                row = result.fetchone()
                
                if row and row[0] == 1:
                    stats = await self.get_connection_stats()
                    return {
                        "status": "healthy",
                        "database": "connected",
                        "connection_stats": stats
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "database": "connected",
                        "error": "Health check query returned unexpected result"
                    }
                    
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
    
    async def close(self):
        """Close all connections and cleanup."""
        await self.engine.dispose()
        logger.info("database_connections_closed")
```

### Phase 2: Critical Refactoring (2-3 days)

**Configuration System Simplification:**
```python
# src/config/core.py - NEW FILE
"""
Simplified configuration management.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import structlog

logger = structlog.get_logger()

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / ".env")

class Environment(str, Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    # Core connection settings
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=1433, description="Database port")
    database: str = Field(default="master", description="Database name")
    username: str = Field(default="", description="Database username")
    password: str = Field(default="", description="Database password")
    
    # Connection settings
    pool_size: int = Field(default=20, description="Connection pool size")
    max_overflow: int = Field(default=30, description="Max overflow connections")
    pool_timeout: int = Field(default=30, description="Connection timeout")
    pool_recycle: int = Field(default=3600, description="Connection recycle time")
    
    # Security settings
    encrypt: bool = Field(default=True, description="Encrypt connection")
    trust_cert: bool = Field(default=False, description="Trust server certificate")
    
    @property
    def connection_url(self) -> str:
        """Generate database connection URL."""
        # URL encode password
        encoded_password = self.password.replace("@", "%40").replace(":", "%3A")
        
        connection_string = (
            f"mssql+pyodbc://{self.username}:{encoded_password}@"
            f"{self.host}:{self.port}/{self.database}"
            f"?driver=ODBC+Driver+18+for+SQL+Server"
        )
        
        if self.encrypt:
            connection_string += "&Encrypt=yes"
        else:
            connection_string += "&Encrypt=no"
            
        if self.trust_cert:
            connection_string += "&TrustServerCertificate=yes"
            
        return connection_string

class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    
    provider: str = Field(default="ollama", description="LLM provider")
    model: str = Field(default="qwen3:30b", description="Model name")
    
    # Ollama settings
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama host")
    ollama_timeout: int = Field(default=300, description="Ollama request timeout")
    
    # Foundry settings
    foundry_endpoint: str = Field(
        default="http://127.0.0.1:53760", 
        description="Foundry endpoint"
    )
    foundry_model: str = Field(
        default="phi-4-mini", 
        description="Foundry model"
    )

class SecurityConfig(BaseSettings):
    """Security configuration."""
    
    jwt_secret: str = Field(
        description="JWT secret key (required in production)"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_expire_minutes: int = Field(
        default=15, 
        description="Access token expiration time"
    )
    jwt_refresh_expire_days: int = Field(
        default=7, 
        description="Refresh token expiration time"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=60, 
        description="Rate limit per minute"
    )
    rate_limit_burst: int = Field(
        default=10, 
        description="Rate limit burst size"
    )
    
    @field_validator("jwt_secret")
    def validate_jwt_secret(cls, v):
        if not v or len(v) < 32:
            raise ValueError("JWT secret must be at least 32 characters long")
        return v

class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Environment
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment"
    )
    
    # Application settings
    name: str = Field(default="Local LLM Research Agent", description="Application name")
    version: str = Field(default="2.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    # Feature flags
    enable_auth: bool = Field(default=True, description="Enable authentication")
    enable_rbac: bool = Field(default=True, description="Enable RBAC")
    enable_audit_logs: bool = Field(default=True, description="Enable audit logging")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    
    class Config:
        env_nested_delimiter = "__"
        case_sensitive = False

@lru_cache()
def get_config() -> AppConfig:
    """Get cached configuration instance."""
    return AppConfig()

# Example usage:
# config = get_config()
# db_url = config.database.connection_url
# model = config.llm.model
```

**Frontend Refactoring:**
```typescript
// frontend/src/stores/modules/chatStore.ts - NEW FILE
"""
Refactored chat store with separation of concerns.
"""

import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import type { Message } from '@/types';

// Separate concerns into smaller stores
interface ChatState {
  // Core conversation state
  currentConversationId: number | null;
  messages: Message[];
  isStreaming: boolean;
  streamingContent: string;
  
  // Actions
  setCurrentConversation: (id: number | null) => void;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (id: number, updates: Partial<Message>) => void;
  deleteMessage: (id: number) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;
}

interface ModelState {
  // LLM configuration
  selectedProvider: string;
  selectedModel: string;
  modelParameters: {
    temperature: number;
    topP: number;
    maxTokens: number;
  };
  systemPrompt: string;
  
  // Actions
  setSelectedProvider: (provider: string) => void;
  setSelectedModel: (model: string) => void;
  setModelParameters: (params: Partial<ModelState['modelParameters']>) => void;
  setSystemPrompt: (prompt: string) => void;
}

interface MCPState {
  // MCP server state
  selectedServers: string[];
  serverStatus: Record<string, 'connected' | 'disconnected' | 'error'>;
  
  // Actions
  setSelectedServers: (servers: string[]) => void;
  toggleServer: (serverId: string) => void;
  updateServerStatus: (serverId: string, status: MCPState['serverStatus'][string]) => void;
}

// Create focused stores
const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        currentConversationId: null,
        messages: [],
        isStreaming: false,
        streamingContent: '',
        
        // Actions
        setCurrentConversation: (id) => set({ currentConversationId: id }),
        
        setMessages: (messages) => set({ messages }),
        
        addMessage: (message) => set((state) => ({
          messages: [...state.messages, message]
        })),
        
        updateMessage: (id, updates) => set((state) => ({
          messages: state.messages.map(msg => 
            msg.id === id ? { ...msg, ...updates } : msg
          )
        })),
        
        deleteMessage: (id) => set((state) => ({
          messages: state.messages.filter(msg => msg.id !== id)
        })),
        
        setIsStreaming: (isStreaming) => set({ isStreaming }),
        
        appendStreamingContent: (content) => set((state) => ({
          streamingContent: state.streamingContent + content
        })),
        
        clearStreamingContent: () => set({ streamingContent: '' })
      }),
      {
        name: 'chat-store',
        partialize: (state) => ({
          currentConversationId: state.currentConversationId,
          messages: state.messages.slice(-100) // Keep only last 100 messages
        })
      }
    )
  )
);

const useModelStore = create<ModelState>()(
  devtools(
    persist(
      (set) => ({
        // Initial state
        selectedProvider: 'ollama',
        selectedModel: 'qwen3:30b',
        modelParameters: {
          temperature: 0.7,
          topP: 0.9,
          maxTokens: 2048
        },
        systemPrompt: '',
        
        // Actions
        setSelectedProvider: (provider) => set({ selectedProvider: provider }),
        setSelectedModel: (model) => set({ selectedModel: model }),
        setModelParameters: (params) => set((state) => ({
          modelParameters: { ...state.modelParameters, ...params }
        })),
        setSystemPrompt: (prompt) => set({ systemPrompt: prompt })
      }),
      {
        name: 'model-store'
      }
    )
  )
);

const useMCPStore = create<MCPState>()(
  devtools(
    (set, get) => ({
      // Initial state
      selectedServers: [],
      serverStatus: {},
      
      // Actions
      setSelectedServers: (servers) => set({ selectedServers: servers }),
      
      toggleServer: (serverId) => set((state) => ({
        selectedServers: state.selectedServers.includes(serverId)
          ? state.selectedServers.filter(id => id !== serverId)
          : [...state.selectedServers, serverId]
      })),
      
      updateServerStatus: (serverId, status) => set((state) => ({
        serverStatus: {
          ...state.serverStatus,
          [serverId]: status
        }
      }))
    })
  )
);

// Combined store for backward compatibility
export const useChatCombinedStore = create()((set, get) => ({
  // Getters that combine states
  get chat() { return useChatStore.getState(); },
  get model() { return useModelStore.getState(); },
  get mcp() { return useMCPStore.getState(); },
  
  // Action dispatcher
  dispatch: (action: any) => {
    switch (action.type) {
      case 'chat/addMessage':
        useChatStore.getState().addMessage(action.payload);
        break;
      case 'model/setSelectedModel':
        useModelStore.getState().setSelectedModel(action.payload);
        break;
      case 'mcp/toggleServer':
        useMCPStore.getState().toggleServer(action.payload);
        break;
      // ... more actions
    }
  }
}));

export { useChatStore, useModelStore, useMCPStore, useChatCombinedStore };
```

## Validation Checkpoints

### After Phase 0: Security Hardening
- [ ] All API endpoints require authentication
- [ ] JWT tokens validate and expire properly
- [ ] RBAC permissions enforced correctly
- [ ] SQL injection vulnerabilities eliminated
- [ ] Security headers present on all responses
- [ ] Rate limiting prevents abuse
- [ ] Audit logs capture all security events

### After Phase 1: Performance Fixes
- [ ] Memory usage stays below 2GB for large documents
- [ ] Database connection pooling works under load
- [ ] Batch processing prevents memory exhaustion
- [ ] Query execution times under 500ms for 95% of queries
- [ ] Frontend performs well with 1000+ chat messages

### After Phase 2: Refactoring
- [ ] Configuration simplified and validated
- [ ] Frontend stores follow single responsibility principle
- [ ] Code duplication eliminated
- [ ] Error handling centralized
- [ ] All async patterns consistent

## Out of Scope

- New feature development until critical issues resolved
- Cloud deployment preparation
- UI/UX redesign (security first)
- Plugin marketplace (architecture first)
- Advanced analytics (stability first)

## Notes for Implementation

### **IMPORTANT**: Security Blockers
1. **DO NOT** deploy to production until Phase 0 complete
2. **DO NOT** expose any API without authentication
3. **DO NOT** use default passwords in production
4. **DO NOT** skip security validation

### **IMPORTANT**: Performance Requirements
1. Memory usage must stay < 2GB during document processing
2. Database connections must be properly pooled
3. Frontend must handle 1000+ messages without degradation
4. API response times must be < 500ms for 95% of requests

### **IMPORTANT**: Refactoring Principles
1. Maintain backward compatibility during refactoring
2. All new code must be fully typed
3. Follow single responsibility principle
4. Implement comprehensive error handling
5. Add extensive tests for refactored components

---

## Risk Assessment

### **Critical Risk**: Current System Unusable for Production
- Multiple security vulnerabilities make deployment unsafe
- Performance issues prevent enterprise usage
- Technical debt will cause maintenance problems

### **Mitigation**: Complete Phase 0 before any other work
- Security hardening is non-negotiable
- Performance fixes required for usability
- Refactoring necessary for maintainability

This enhanced PRP addresses the **critical security vulnerabilities and technical debt** that make the current impressive codebase unsuitable for production use. By completing these essential fixes first, we create a solid foundation for the advanced features planned in the original PRP.

**Timeline**: 7-10 days for critical fixes, then proceed with original feature enhancement plan.
**Priority**: Phase 0 (Security) > Phase 1 (Performance) > Phase 2 (Refactoring) > New Features.