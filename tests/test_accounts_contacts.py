"""
CRM System - Unit Tests for Accounts, Customer 360 & Contacts Management
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from modules.auth.service import AuthService
from modules.accounts.service import AccountService
from modules.contacts.service import ContactService
from modules.tickets.service import TicketService
from config.permissions import UserRole


class TestAccountsAndContacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()
        email = f"acc_tester_{os.urandom(3).hex()}@crm.local"
        user = AuthService.register_user(
            email=email,
            password="Password123!",
            full_name="Account Manager",
            role=UserRole.SALES_MANAGER.value
        )
        cls.user = {"sub": user["id"], "email": user["email"]}

    def test_customer_crud_and_360_interaction_timeline(self):
        # 1. Create Customer Account
        acc = AccountService.create_account({
            "name": "Omni Corp International",
            "industry": "Aerospace",
            "annual_revenue": 50000000.0,
            "employee_count": 800,
            "tier": "STRATEGIC",
            "status": "ACTIVE",
            "owner_id": self.user["sub"]
        }, self.user)
        self.assertIsNotNone(acc["id"])
        self.assertEqual(acc["name"], "Omni Corp International")

        # 2. Add Contact linked to Customer
        contact = ContactService.create_contact({
            "account_id": acc["id"],
            "first_name": "Tony",
            "last_name": "Stark",
            "email": f"tony_{os.urandom(3).hex()}@omnicorp.example.com",
            "job_title": "Chief Technology Officer",
            "is_primary": True
        }, self.user)
        self.assertIsNotNone(contact["id"])

        # 3. Add Customer Note & Attachment
        note = AccountService.add_customer_note(
            acc["id"],
            "Completed executive briefing. Client approved Q3 roadmap.",
            self.user
        )
        self.assertIsNotNone(note["id"])

        att = AccountService.add_customer_attachment(
            acc["id"],
            "OmniCorp_Contract_2026.pdf",
            500000,
            "PDF Document",
            "/storage/contracts/OmniCorp_2026.pdf",
            self.user
        )
        self.assertIsNotNone(att["id"])

        # 4. Open a Support Ticket for the customer
        TicketService.create_ticket({
            "account_id": acc["id"],
            "contact_id": contact["id"],
            "title": "SSO SAML Configuration Assistance",
            "description": "Assistance needed connecting Okta IDP.",
            "priority": "HIGH"
        }, self.user)

        # 5. Verify Customer 360 View includes Timeline and Notes
        view360 = AccountService.get_account_360(acc["id"])
        self.assertEqual(len(view360["contacts"]), 1)
        self.assertEqual(len(view360["notes"]), 1)
        self.assertEqual(len(view360["attachments"]), 1)
        self.assertGreaterEqual(len(view360["interaction_history"]), 3)

        # 6. Deactivate & Reactivate Customer
        deactivated = AccountService.update_customer_status(acc["id"], "INACTIVE", self.user)
        self.assertEqual(deactivated["status"], "INACTIVE")

        reactivated = AccountService.update_customer_status(acc["id"], "ACTIVE", self.user)
        self.assertEqual(reactivated["status"], "ACTIVE")

        # 7. Cleanup / Delete
        ContactService.delete_contact(contact["id"], self.user)
        AccountService.delete_account(acc["id"], self.user)
        self.assertIsNone(AccountService.get_account_360(acc["id"]))


if __name__ == "__main__":
    unittest.main()
