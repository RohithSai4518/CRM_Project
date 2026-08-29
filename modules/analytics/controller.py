"""
CRM System - Analytics & Reporting Controller
"""

from core.http.request import Request
from core.http.response import Response
from modules.analytics.engine import AnalyticsEngine
from modules.auth.guard import require_permission
from config.permissions import Permission


class AnalyticsController:
    @staticmethod
    @require_permission(Permission.ANALYTICS_VIEW)
    def executive_summary(request: Request) -> Response:
        summary = AnalyticsEngine.get_executive_summary()
        return Response.ok(summary)

    @staticmethod
    @require_permission(Permission.ANALYTICS_VIEW)
    def pipeline_by_stage(request: Request) -> Response:
        data = AnalyticsEngine.get_pipeline_by_stage()
        return Response.ok(data)

    @staticmethod
    @require_permission(Permission.ANALYTICS_VIEW)
    def leads_by_source(request: Request) -> Response:
        data = AnalyticsEngine.get_leads_by_source()
        return Response.ok(data)
