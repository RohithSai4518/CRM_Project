"""
CRM System - Unit Tests for Marketing, Activities & Audit Trail
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from modules.auth.service import AuthService
from modules.marketing.service import CampaignService
from modules.activities.service import ActivityService
from modules.audit.service import AuditService


class TestMarketingActivitiesAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()
        email = f"mkt_tester_{os.urandom(3).hex()}@crm.local"
        user = AuthService.register_user(
            email=email,
            password="Password123!",
            full_name="Marketing Specialist",
            role="MARKETING_MANAGER"
        )
        cls.user = {"sub": user["id"], "email": user["email"]}

    def test_campaign_metrics_and_crud(self):
        cmp = CampaignService.create_campaign({
            "name": "Global Cloud Conference 2026",
            "type": "EVENT",
            "budget": 20000.0,
            "actual_cost": 15000.0,
            "sent_count": 1000,
            "open_count": 500,
            "click_count": 250,
            "conversion_count": 50
        }, self.user)

        fetched = CampaignService.get_campaign(cmp["id"])
        self.assertEqual(fetched["open_rate_pct"], 50.0)
        self.assertEqual(fetched["click_through_pct"], 25.0)
        self.assertEqual(fetched["conversion_rate_pct"], 5.0)
        self.assertEqual(fetched["cost_per_conversion"], 300.0)

    def test_activity_lifecycle(self):
        act = ActivityService.create_activity({
            "activity_type": "TASK",
            "subject": "Prepare Q4 Business Review Slide Deck",
            "priority": "HIGH",
            "assigned_to_id": self.user["sub"]
        }, self.user)

        self.assertEqual(act["status"], "PENDING")
        updated = ActivityService.update_activity_status(act["id"], "COMPLETED", self.user)
        self.assertEqual(updated["status"], "COMPLETED")

    def test_audit_trail_logging(self):
        AuditService.record(
            user_id=self.user["sub"],
            user_email=self.user["email"],
            action="EXPORT",
            entity_type="SYSTEM",
            entity_id="ALL",
            change_summary="Exported annual financial performance ledger"
        )

        logs = AuditService.get_logs(entity_type="SYSTEM", limit=10)
        self.assertGreaterEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "EXPORT")


if __name__ == "__main__":
    unittest.main()
