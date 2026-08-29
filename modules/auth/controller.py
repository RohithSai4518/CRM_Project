"""
CRM System - Authentication & User Management Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.auth.service import AuthService
from modules.auth.guard import require_auth, require_permission
from config.permissions import get_permissions_for_role, UserRole, normalize_role, Permission


class AuthController:
    @staticmethod
    def register(request: Request) -> Response:
        data = request.json()
        rules = {
            "email": {"type": str, "required": True, "format": "email"},
            "password": {"type": str, "required": True, "min_len": 6},
            "full_name": {"type": str, "required": True, "min_len": 2},
            "role": {"type": str, "required": False}
        }
        
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            user = AuthService.register_user(
                email=cleaned["email"],
                password=cleaned["password"],
                full_name=cleaned["full_name"],
                role=cleaned.get("role") or UserRole.SALES_REPRESENTATIVE.value
            )
            return Response.created(user, "User registered successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    def login(request: Request) -> Response:
        data = request.json()
        rules = {
            "email": {"type": str, "required": True, "format": "email"},
            "password": {"type": str, "required": True}
        }
        
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            auth_result = AuthService.authenticate(cleaned["email"], cleaned["password"])
            res = Response.ok(auth_result, "Authentication successful")
            res.set_cookie("CRM_SESSION_TOKEN", auth_result["token"], max_age=86400)
            return res
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    def forgot_password(request: Request) -> Response:
        data = request.json()
        email = data.get("email")
        if not email:
            return Response.bad_request("Email address is required")

        result = AuthService.request_password_reset(email)
        return Response.ok(result)

    @staticmethod
    def reset_password(request: Request) -> Response:
        data = request.json()
        token = data.get("token")
        new_password = data.get("new_password")

        if not token or not new_password:
            return Response.bad_request("Reset token and new password are required")
        if len(new_password) < 6:
            return Response.bad_request("New password must be at least 6 characters")

        try:
            result = AuthService.reset_password(token, new_password)
            return Response.ok(result)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_auth
    def me(request: Request) -> Response:
        user_info = request.user
        role_enum = normalize_role(user_info["role"])
        permissions = get_permissions_for_role(role_enum)
        
        return Response.ok({
            "user": user_info,
            "permissions": permissions
        })

    @staticmethod
    @require_auth
    def list_users(request: Request) -> Response:
        users = AuthService.list_users()
        return Response.ok(users)

    @staticmethod
    @require_permission(Permission.USER_MANAGE)
    def update_role(request: Request) -> Response:
        user_id = request.path_params.get("id")
        data = request.json()
        new_role = data.get("role")
        if not new_role:
            return Response.bad_request("Role parameter is required")

        try:
            updated = AuthService.update_user_role(user_id, new_role, request.user)
            return Response.ok(updated, "User role updated successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.USER_MANAGE)
    def toggle_status(request: Request) -> Response:
        user_id = request.path_params.get("id")
        data = request.json()
        status = data.get("status")
        if not status:
            return Response.bad_request("Status parameter ('ACTIVE' or 'INACTIVE') is required")

        try:
            updated = AuthService.toggle_user_status(user_id, status, request.user)
            return Response.ok(updated, f"User status set to {status}")
        except ValueError as ve:
            return Response.bad_request(str(ve))
