"""
CRM System - Authentication, Password Reset & User Management Service
"""

import uuid
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from core.database.query_builder import query
from core.database.connection import DB
from core.security.crypto import hash_password, verify_password
from core.security.tokens import create_access_token
from config.permissions import UserRole, normalize_role
from modules.audit.service import AuditService


class AuthService:
    @staticmethod
    def register_user(
        email: str,
        password: str,
        full_name: str,
        role: str = UserRole.SALES_REPRESENTATIVE.value,
        avatar_url: Optional[str] = None
    ) -> Dict[str, Any]:
        email = email.strip().lower()
        existing = query("users").where_eq("email", email).first()
        if existing:
            raise ValueError(f"User with email '{email}' already exists")

        # Normalize role to standard 5 roles
        standard_role = normalize_role(role).value

        # Hash password securely
        pwd_hash, salt = hash_password(password)
        user_id = "usr_" + str(uuid.uuid4())[:12]

        user_data = {
            "id": user_id,
            "email": email,
            "password_hash": pwd_hash,
            "salt": salt,
            "full_name": full_name,
            "role": standard_role,
            "status": "ACTIVE",
            "avatar_url": avatar_url or f"https://ui-avatars.com/api/?name={full_name.replace(' ', '+')}&background=0D8ABC&color=fff"
        }

        query("users").insert(user_data)

        AuditService.record(
            user_id=user_id,
            user_email=email,
            action="USER_REGISTERED",
            entity_type="USER",
            entity_id=user_id,
            change_summary=f"User registered with role {standard_role}"
        )
        
        user_data.pop("password_hash")
        user_data.pop("salt")
        return user_data

    @staticmethod
    def authenticate(email: str, password: str) -> Dict[str, Any]:
        email = email.strip().lower()
        user = query("users").where_eq("email", email).first()
        if not user:
            raise ValueError("Invalid email or password")

        if user["status"] != "ACTIVE":
            raise ValueError("User account has been deactivated. Please contact an administrator.")

        if not verify_password(password, user["password_hash"], user["salt"]):
            raise ValueError("Invalid email or password")

        token = create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            full_name=user["full_name"]
        )

        AuditService.record(
            user_id=user["id"],
            user_email=user["email"],
            action="USER_LOGIN",
            entity_type="AUTH",
            entity_id=user["id"],
            change_summary="User authenticated successfully"
        )

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user["role"],
                "status": user["status"],
                "avatar_url": user.get("avatar_url")
            }
        }

    @staticmethod
    def request_password_reset(email: str) -> Dict[str, Any]:
        """Generate a time-limited cryptographically secure password reset token."""
        email = email.strip().lower()
        user = query("users").where_eq("email", email).first()
        if not user:
            # For security, return success message even if email not found
            return {"message": "If this email is registered, password reset instructions have been dispatched."}

        reset_id = "rst_" + str(uuid.uuid4())[:12]
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            DB.execute("""
                INSERT INTO password_reset_tokens (id, user_id, email, token, expires_at, is_used)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (reset_id, user["id"], email, token, expires_at))
        except Exception:
            pass

        AuditService.record(
            user_id=user["id"],
            user_email=email,
            action="PASSWORD_RESET_REQUESTED",
            entity_type="AUTH",
            entity_id=user["id"],
            change_summary="Password reset token issued"
        )

        return {
            "message": "Password reset token generated successfully",
            "reset_token": token,
            "expires_at": expires_at
        }

    @staticmethod
    def reset_password(token: str, new_password: str) -> Dict[str, Any]:
        """Verify reset token validity and update user password."""
        token_record = DB.fetch_one("""
            SELECT * FROM password_reset_tokens 
            WHERE token = ? AND is_used = 0
        """, (token,))

        if not token_record:
            raise ValueError("Invalid or already utilized password reset token")

        # Verify expiration
        exp_dt = datetime.strptime(token_record["expires_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp_dt:
            raise ValueError("Password reset token has expired")

        user_id = token_record["user_id"]
        pwd_hash, salt = hash_password(new_password)

        # Update password
        query("users").where_eq("id", user_id).update({
            "password_hash": pwd_hash,
            "salt": salt,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })

        # Mark token used
        DB.execute("UPDATE password_reset_tokens SET is_used = 1 WHERE id = ?", (token_record["id"],))

        AuditService.record(
            user_id=user_id,
            user_email=token_record["email"],
            action="PASSWORD_RESET_COMPLETED",
            entity_type="AUTH",
            entity_id=user_id,
            change_summary="Password updated via verified reset token"
        )

        return {"message": "Password updated successfully. You may now log in."}

    @staticmethod
    def update_user_role(user_id: str, new_role: str, current_admin: Dict[str, Any]) -> Dict[str, Any]:
        standard_role = normalize_role(new_role).value
        existing = query("users").where_eq("id", user_id).first()
        if not existing:
            raise ValueError("User not found")

        query("users").where_eq("id", user_id).update({
            "role": standard_role,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })

        AuditService.record(
            user_id=current_admin.get("sub"),
            user_email=current_admin.get("email"),
            action="ROLE_UPDATED",
            entity_type="USER",
            entity_id=user_id,
            change_summary=f"Changed role of '{existing['full_name']}' from '{existing['role']}' to '{standard_role}'"
        )

        return AuthService.get_user_by_id(user_id)

    @staticmethod
    def toggle_user_status(user_id: str, status: str, current_admin: Dict[str, Any]) -> Dict[str, Any]:
        status = status.upper()
        if status not in ("ACTIVE", "INACTIVE"):
            raise ValueError("Status must be either 'ACTIVE' or 'INACTIVE'")

        existing = query("users").where_eq("id", user_id).first()
        if not existing:
            raise ValueError("User not found")

        query("users").where_eq("id", user_id).update({
            "status": status,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })

        AuditService.record(
            user_id=current_admin.get("sub"),
            user_email=current_admin.get("email"),
            action="STATUS_CHANGED",
            entity_type="USER",
            entity_id=user_id,
            change_summary=f"Changed user status to {status}"
        )

        return AuthService.get_user_by_id(user_id)

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        user = query("users").where_eq("id", user_id).first()
        if user:
            user.pop("password_hash", None)
            user.pop("salt", None)
        return user

    @staticmethod
    def list_users() -> List[Dict[str, Any]]:
        users = query("users").select("id", "email", "full_name", "role", "status", "avatar_url", "created_at").get()
        return users
