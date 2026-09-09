"""Supabase JWT authentication dependency for FastAPI."""
import os
import json
import logging
from typing import Optional, Dict, Any
import jwt
import httpx
from pydantic import BaseModel
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.app.config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_JWT_SECRET

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class User(BaseModel):
    id: str
    email: str
    role: str = "authenticated"
    user_metadata: Dict[str, Any] = {}


# Pre-configured demo users for quick-switching & automated testing
DEMO_USERS = {
    "demo_user_a": User(
        id="user_a_alice",
        email="alice@visiq.ai",
        role="authenticated",
        user_metadata={"full_name": "Alice Data Analyst", "avatar_color": "#6366f1"},
    ),
    "demo_user_b": User(
        id="user_b_bob",
        email="bob@visiq.ai",
        role="authenticated",
        user_metadata={"full_name": "Bob Enterprise", "avatar_color": "#10b981"},
    ),
    "demo_default": User(
        id="user_default",
        email="guest@visiq.ai",
        role="authenticated",
        user_metadata={"full_name": "Guest User", "avatar_color": "#94a3b8"},
    ),
}


from functools import lru_cache
@lru_cache
def _jwks(issuer):
    return jwt.PyJWKClient(issuer + '/.well-known/jwks.json', timeout=5)

def _decode_jwt_token(token: str) -> User:
    from backend.app.config import ALLOW_DEMO_AUTH
    if ALLOW_DEMO_AUTH and token in DEMO_USERS:
        return DEMO_USERS[token]
    try:
        if not SUPABASE_URL:
            raise ValueError('Authentication is not configured')
        issuer = SUPABASE_URL.rstrip('/') + '/auth/v1'
        if SUPABASE_JWT_SECRET:
            key, algorithms = SUPABASE_JWT_SECRET, ['HS256']
        else:
            key, algorithms = _jwks(issuer).get_signing_key_from_jwt(token).key, ['RS256', 'ES256']
        payload = jwt.decode(token, key, algorithms=algorithms, issuer=issuer,
            audience='authenticated', options={'require': ['exp', 'iat', 'sub', 'iss', 'aud']})
        from backend.app.paths import filename
        subject = filename(payload['sub'])
        if payload.get('role') != 'authenticated':
            raise ValueError('Invalid role')
        return User(id=subject, email=payload.get('email', ''), user_metadata=payload.get('user_metadata') or {})
    except Exception:
        raise HTTPException(status_code=401, detail='Invalid authentication credentials', headers={'WWW-Authenticate': 'Bearer'})

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail='Authentication required', headers={'WWW-Authenticate': 'Bearer'})
    user = _decode_jwt_token(credentials.credentials.strip())
    from backend.app import storage
    storage.put('users', user.id, user.id, user.model_dump())
    from backend.app.auth.context import request_user_id
    context_token = request_user_id.set(user.id)
    try:
        yield user
    finally:
        request_user_id.reset(context_token)

get_optional_user = get_current_user
