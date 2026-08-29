"""
CRM System - Unit Tests for BI Analytics Engine
"""

import unittest
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from modules.analytics.engine import AnalyticsEngine


class TestAnalytics(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        run_migrations()

    def test_executive_summary_calculation(self):
        summary = AnalyticsEngine.get_executive_summary()
        self.assertIn("accounts", summary)
        self.assertIn("leads", summary)
        self.assertIn("pipeline", summary)
        self.assertIn("support", summary)
        self.assertIn("marketing", summary)

    def test_pipeline_and_leads_breakdown(self):
        pipeline_stages = AnalyticsEngine.get_pipeline_by_stage()
        self.assertIsInstance(pipeline_stages, list)

        sources = AnalyticsEngine.get_leads_by_source()
        self.assertIsInstance(sources, list)


if __name__ == "__main__":
    unittest.main()
