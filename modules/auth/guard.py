"""
CRM System - Auth Guard & RBAC Permission Decorator
"""

from typing import Callable, Optional, List
from core.http.request import Request
from core.http.response import Response
from core.security.tokens import verify_access_token, TokenError
from config.permissions import UserRole, Permission, has_permission


def require_auth(handler: Callable[[Request], Response]) -> Callable[[Request], Response]:
    """Decorator ensuring request has valid authenticated session token."""
    def wrapper(request: Request) -> Response:
        token = request.authorization_token
        if not token:
            return Response.unauthorized("Authentication required. Missing Bearer token.")

        try:
            payload = verify_access_token(token)
            request.user = payload
        except TokenError as te:
            return Response.unauthorized(f"Authentication failed: {str(te)}")

        return handler(request)
    return wrapper


def require_permission(permission: Permission):
    """Decorator requiring specific granular permission for current user role."""
    def decorator(handler: Callable[[Request], Response]) -> Callable[[Request], Response]:
        def wrapper(request: Request) -> Response:
            token = request.authorization_token
            if not token:
                return Response.unauthorized("Authentication required.")

            try:
                payload = verify_access_token(token)
                request.user = payload
            except TokenError as te:
                return Response.unauthorized(f"Invalid authentication token: {str(te)}")

            user_role_str = payload.get("role")
            try:
                role_enum = UserRole(user_role_str)
            except Exception:
                return Response.forbidden(f"Unrecognized role '{user_role_str}'")

            if not has_permission(role_enum, permission):
                return Response.forbidden(f"Action requires permission '{permission.value}'")

            return handler(request)
        return wrapper
    return decorator
