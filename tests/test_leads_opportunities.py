"""
CRM System - Unit Tests for Leads, Opportunity Pipeline & Conversion
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from modules.auth.service import AuthService
from modules.leads.service import LeadService
from modules.leads.scoring import calculate_lead_score
from modules.opportunities.service import OpportunityService


class TestLeadsAndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()
        # Create a valid test user in DB for FK constraints
        email = f"lead_tester_{os.urandom(3).hex()}@crm.local"
        user = AuthService.register_user(
            email=email,
            password="Password123!",
            full_name="Lead Test Officer",
            role="SALES_REP"
        )
        cls.dummy_user = {"sub": user["id"], "email": user["email"]}

    def test_lead_scoring_algorithm(self):
        high_val_lead = {
            "email": "cto@fortune500.com",
            "phone": "+1-555-9000",
            "company_name": "Fortune 500 Co",
            "lead_source": "DEMO_REQUEST",
            "estimated_value": 85000.0
        }
        score = calculate_lead_score(high_val_lead)
        self.assertGreaterEqual(score, 75)

        low_val_lead = {
            "email": "random@gmail.com",
            "lead_source": "COLD_OUTREACH",
            "estimated_value": 500.0
        }
        low_score = calculate_lead_score(low_val_lead)
        self.assertLess(low_score, 40)

    def test_lead_lifecycle_and_conversion(self):
        # 1. Create Lead
        lead = LeadService.create_lead({
            "first_name": "Oliver",
            "last_name": "Queen",
            "company_name": "Queen Industries",
            "email": "oliver@queenind.example.com",
            "phone": "+1-555-8888",
            "lead_source": "DEMO_REQUEST",
            "estimated_value": 150000.0,
            "assigned_to_id": self.dummy_user["sub"]
        }, self.dummy_user)

        self.assertIsNotNone(lead["id"])
        self.assertEqual(lead["status"], "NEW")

        # 2. Convert Lead
        conversion = LeadService.convert_lead(
            lead["id"],
            "Queen Industries Annual SaaS License",
            self.dummy_user
        )

        self.assertIsNotNone(conversion["account_id"])
        self.assertIsNotNone(conversion["contact_id"])
        self.assertIsNotNone(conversion["opportunity_id"])

        # 3. Verify Opportunity Stage Transition
        opp = OpportunityService.get_opportunity(conversion["opportunity_id"])
        self.assertEqual(opp["stage"], "QUALIFICATION")

        updated_opp = OpportunityService.update_opportunity_stage(
            opp["id"], "CLOSED_WON", None, self.dummy_user
        )
        self.assertEqual(updated_opp["stage"], "CLOSED_WON")
        self.assertEqual(updated_opp["win_probability"], 100)


if __name__ == "__main__":
    unittest.main()
