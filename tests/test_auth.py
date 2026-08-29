"""
CRM System - Unit Tests for Authentication, Crypto & Tokens
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from core.database.connection import DB
from core.security.crypto import hash_password, verify_password, hmac_sign, hmac_verify
from core.security.tokens import create_access_token, verify_access_token, TokenInvalidError
from modules.auth.service import AuthService
from config.permissions import UserRole


class TestAuthAndSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()

    def test_password_hashing_and_verification(self):
        password = "SecurePassword@2026!"
        h, salt = hash_password(password)
        self.assertTrue(verify_password(password, h, salt))
        self.assertFalse(verify_password("WrongPassword", h, salt))

    def test_token_creation_and_claims(self):
        token = create_access_token(
            user_id="usr_test_123",
            email="tester@crm.local",
            role=UserRole.SALES_REPRESENTATIVE.value,
            full_name="Tester Agent"
        )
        claims = verify_access_token(token)
        self.assertEqual(claims["sub"], "usr_test_123")
        self.assertEqual(claims["email"], "tester@crm.local")
        self.assertEqual(claims["role"], UserRole.SALES_REPRESENTATIVE.value)

    def test_tampered_token_rejection(self):
        token = create_access_token("usr_1", "u1@crm.local", "Admin", "Admin")
        parts = token.split(".")
        tampered_token = f"{parts[0]}.eyJob2d1cyI6InRydWUifQ.{parts[2]}"
        with self.assertRaises(TokenInvalidError):
            verify_access_token(tampered_token)

    def test_user_registration_and_authentication(self):
        email = f"user_{os.urandom(4).hex()}@testcrm.com"
        created = AuthService.register_user(
            email=email,
            password="TestPassword123!",
            full_name="Unit Tester",
            role=UserRole.SALES_REPRESENTATIVE.value
        )
        self.assertEqual(created["email"], email)

        auth_result = AuthService.authenticate(email, "TestPassword123!")
        self.assertIn("token", auth_result)
        self.assertEqual(auth_result["user"]["email"], email)

    def test_forgot_and_reset_password_workflow(self):
        email = f"reset_{os.urandom(3).hex()}@testcrm.com"
        user = AuthService.register_user(
            email=email,
            password="OldPassword123!",
            full_name="Reset Officer",
            role=UserRole.SUPPORT_AGENT.value
        )

        # 1. Request Reset
        req_res = AuthService.request_password_reset(email)
        self.assertIn("reset_token", req_res)
        token = req_res["reset_token"]

        # 2. Reset with token
        reset_res = AuthService.reset_password(token, "NewBrandNewPassword2026!")
        self.assertIn("message", reset_res)

        # 3. Authenticate with new password
        login_res = AuthService.authenticate(email, "NewBrandNewPassword2026!")
        self.assertEqual(login_res["user"]["email"], email)

    def test_admin_role_and_status_management(self):
        admin_email = f"admin_{os.urandom(3).hex()}@testcrm.com"
        admin = AuthService.register_user(admin_email, "Pass123!", "Lead Admin", UserRole.ADMIN.value)
        admin_ctx = {"sub": admin["id"], "email": admin["email"]}

        user_email = f"member_{os.urandom(3).hex()}@testcrm.com"
        member = AuthService.register_user(user_email, "Pass123!", "Team Member", UserRole.SALES_REPRESENTATIVE.value)

        # Update Role to Sales Manager
        updated_user = AuthService.update_user_role(member["id"], "Sales Manager", admin_ctx)
        self.assertEqual(updated_user["role"], "Sales Manager")

        # Deactivate user
        AuthService.toggle_user_status(member["id"], "INACTIVE", admin_ctx)
        with self.assertRaises(ValueError):
            AuthService.authenticate(user_email, "Pass123!")

        # Reactivate user
        AuthService.toggle_user_status(member["id"], "ACTIVE", admin_ctx)
        reauth = AuthService.authenticate(user_email, "Pass123!")
        self.assertEqual(reauth["user"]["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
