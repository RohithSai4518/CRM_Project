"""
CRM System - Unit Tests for Core Database Query Builder & Router
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from core.database.query_builder import query
from core.http.router import Router
from core.http.request import Request
from core.http.response import Response


class TestCoreEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()

    def test_query_builder_crud(self):
        # Insert
        acc_id = f"acc_test_{os.urandom(3).hex()}"
        query("accounts").insert({
            "id": acc_id,
            "name": "Acme Unit Test Corp",
            "industry": "Testing",
            "annual_revenue": 500000.0,
            "tier": "STANDARD",
            "status": "ACTIVE"
        })

        # Select
        record = query("accounts").where_eq("id", acc_id).first()
        self.assertIsNotNone(record)
        self.assertEqual(record["name"], "Acme Unit Test Corp")

        # Update
        query("accounts").where_eq("id", acc_id).update({"annual_revenue": 750000.0})
        updated = query("accounts").where_eq("id", acc_id).first()
        self.assertEqual(updated["annual_revenue"], 750000.0)

        # Delete
        query("accounts").where_eq("id", acc_id).delete()
        deleted = query("accounts").where_eq("id", acc_id).first()
        self.assertIsNone(deleted)

    def test_http_router_path_matching(self):
        r = Router()
        r.get("/api/accounts/:id", lambda req: Response.ok({"id": req.path_params.get("id")}))
        r.post("/api/leads", lambda req: Response.created())

        handler, params, _ = r.resolve("GET", "/api/accounts/acc_9988")
        self.assertIsNotNone(handler)
        self.assertEqual(params.get("id"), "acc_9988")

        handler_post, _, _ = r.resolve("POST", "/api/leads")
        self.assertIsNotNone(handler_post)

        handler_not_found, _, other = r.resolve("DELETE", "/api/leads")
        self.assertIsNone(handler_not_found)
        self.assertTrue(other)


if __name__ == "__main__":
    unittest.main()
