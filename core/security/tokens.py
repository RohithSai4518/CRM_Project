"""
CRM System - Custom Signed Session Tokens
Zero external JWT library dependency
"""

import json
import base64
import time
from typing import Dict, Any, Optional
from core.security.crypto import hmac_sign, hmac_verify
from config.app_config import CONFIG


class TokenError(Exception):
    pass


class TokenExpiredError(TokenError):
    pass


class TokenInvalidError(TokenError):
    pass


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')


def _b64_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data.encode('utf-8'))


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    full_name: str,
    tenant_id: str = "default_tenant",
    expires_in_hours: Optional[int] = None
) -> str:
    """Create a tamper-evident signed token containing user claims."""
    if expires_in_hours is None:
        expires_in_hours = CONFIG.security.token_expiration_hours
        
    now = int(time.time())
    exp = now + (expires_in_hours * 3600)
    
    header = {
        "alg": "HS256",
        "typ": "CRM_TOKEN"
    }
    
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": full_name,
        "tenant_id": tenant_id,
        "iat": now,
        "exp": exp
    }
    
    header_b64 = _b64_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    payload_b64 = _b64_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac_sign(signing_input)
    
    return f"{signing_input}.{signature}"


def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify signature and expiration of an access token."""
    parts = token.split('.')
    if len(parts) != 3:
        raise TokenInvalidError("Malformed token structure")
        
    header_b64, payload_b64, signature = parts
    signing_input = f"{header_b64}.{payload_b64}"
    
    if not hmac_verify(signing_input, signature):
        raise TokenInvalidError("Invalid token signature")
        
    try:
        payload_bytes = _b64_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
    except Exception:
        raise TokenInvalidError("Failed to decode token payload")
        
    now = int(time.time())
    if payload.get("exp", 0) < now:
        raise TokenExpiredError("Token has expired")
        
    return payload
