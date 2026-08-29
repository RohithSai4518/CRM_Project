"""
CRM System - Cryptographic Utilities
Zero external dependencies, uses standard library hashlib, hmac, secrets
"""

import hashlib
import hmac
import secrets
import base64
import os
from typing import Tuple
from config.app_config import CONFIG


def generate_salt(length: int = 16) -> str:
    """Generate cryptographically strong random salt string."""
    return secrets.token_hex(length)


def hash_password(password: str, salt: str = None) -> Tuple[str, str]:
    """
    Hash a password using PBKDF2 with SHA-256 and configurable iterations.
    Returns (hashed_string, salt).
    """
    if salt is None:
        salt = generate_salt(16)
        
    salt_bytes = salt.encode('utf-8')
    iterations = CONFIG.security.password_salt_rounds
    
    dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        iterations
    )
    
    hash_hex = dk.hex()
    return hash_hex, salt


def verify_password(password: str, stored_hash: str, salt: str) -> bool:
    """
    Verify candidate password against stored hash in constant time.
    """
    computed_hash, _ = hash_password(password, salt)
    return hmac.compare_digest(computed_hash, stored_hash)


def hmac_sign(message: str, secret: str = None) -> str:
    """Compute HMAC-SHA256 signature for message."""
    if secret is None:
        secret = CONFIG.security.secret_key
        
    sig = hmac.new(
        secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    return base64.urlsafe_b64encode(sig).decode('utf-8').rstrip('=')


def hmac_verify(message: str, signature: str, secret: str = None) -> bool:
    """Verify HMAC signature in constant time."""
    expected_sig = hmac_sign(message, secret)
    return hmac.compare_digest(expected_sig, signature)


def generate_random_token(length: int = 32) -> str:
    """Generate secure random URL-safe token."""
    return secrets.token_urlsafe(length)
