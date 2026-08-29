"""
CRM System - Unit Tests for Support Tickets & SLA Engine
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from modules.auth.service import AuthService
from modules.tickets.service import TicketService
from modules.tickets.sla import calculate_sla_deadlines, check_sla_breach


class TestTicketsAndSLA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()
        email = f"agent_tester_{os.urandom(3).hex()}@crm.local"
        user = AuthService.register_user(
            email=email,
            password="Password123!",
            full_name="Support Test Officer",
            role="SUPPORT_AGENT"
        )
        cls.dummy_user = {"sub": user["id"], "email": user["email"]}

    def test_sla_deadline_computation(self):
        resp_urgent, res_urgent = calculate_sla_deadlines("URGENT")
        resp_low, res_low = calculate_sla_deadlines("LOW")
        self.assertIsNotNone(resp_urgent)
        self.assertIsNotNone(res_low)

    def test_ticket_creation_and_commenting(self):
        ticket = TicketService.create_ticket({
            "title": "Database replication delay alert",
            "description": "Replica node lagging by 450ms.",
            "priority": "HIGH",
            "category": "TECHNICAL",
            "assigned_agent_id": self.dummy_user["sub"]
        }, self.dummy_user)

        self.assertEqual(ticket["priority"], "HIGH")
        self.assertEqual(ticket["status"], "OPEN")

        # Add internal comment
        comment = TicketService.add_comment(
            ticket["id"],
            "Investigated replica logs. Re-synced binary logs.",
            is_internal=True,
            current_user=self.dummy_user
        )
        self.assertEqual(comment["is_internal"], 1)

        # Re-fetch ticket to verify status moved to IN_PROGRESS
        fetched = TicketService.get_ticket(ticket["id"])
        self.assertEqual(fetched["status"], "IN_PROGRESS")
        self.assertEqual(len(fetched["comments"]), 1)


if __name__ == "__main__":
    unittest.main()
