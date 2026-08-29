"""
CRM System - Marketing Campaigns Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.marketing.service import CampaignService
from modules.auth.guard import require_permission
from config.permissions import Permission


class MarketingController:
    @staticmethod
    @require_permission(Permission.CAMPAIGN_VIEW)
    def list(request: Request) -> Response:
        limit = int(request.query("limit") or "50")
        offset = int(request.query("offset") or "0")
        result = CampaignService.list_campaigns(limit=limit, offset=offset)
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.CAMPAIGN_VIEW)
    def get(request: Request) -> Response:
        campaign_id = request.path_params.get("id")
        campaign = CampaignService.get_campaign(campaign_id)
        if not campaign:
            return Response.not_found("Campaign not found")
        return Response.ok(campaign)

    @staticmethod
    @require_permission(Permission.CAMPAIGN_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "name": {"type": str, "required": True, "min_len": 2},
            "type": {"type": str, "required": False, "choices": ["EMAIL", "WEBINAR", "SOCIAL", "EVENT", "PAID_AD"]},
            "budget": {"type": float, "required": False, "min": 0},
            "actual_cost": {"type": float, "required": False, "min": 0},
            "target_audience": {"type": str, "required": False}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            campaign = CampaignService.create_campaign(cleaned, request.user)
            return Response.created(campaign)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.CAMPAIGN_EDIT)
    def update(request: Request) -> Response:
        campaign_id = request.path_params.get("id")
        data = request.json()
        try:
            updated = CampaignService.update_campaign(campaign_id, data, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))
