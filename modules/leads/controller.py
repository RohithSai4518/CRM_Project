"""
CRM System - Leads Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.leads.service import LeadService
from modules.auth.guard import require_permission
from config.permissions import Permission


class LeadController:
    @staticmethod
    @require_permission(Permission.LEAD_VIEW)
    def list(request: Request) -> Response:
        status = request.query("status")
        search = request.query("search")
        min_score = int(request.query("min_score")) if request.query("min_score") else None
        limit = int(request.query("limit") or "50")
        offset = int(request.query("offset") or "0")

        result = LeadService.list_leads(status=status, search=search, min_score=min_score, limit=limit, offset=offset)
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.LEAD_VIEW)
    def get(request: Request) -> Response:
        lead_id = request.path_params.get("id")
        lead = LeadService.get_lead(lead_id)
        if not lead:
            return Response.not_found("Lead not found")
        return Response.ok(lead)

    @staticmethod
    @require_permission(Permission.LEAD_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "first_name": {"type": str, "required": True, "min_len": 1},
            "last_name": {"type": str, "required": True, "min_len": 1},
            "company_name": {"type": str, "required": False},
            "email": {"type": str, "required": True, "format": "email"},
            "phone": {"type": str, "required": False},
            "lead_source": {"type": str, "required": False},
            "estimated_value": {"type": float, "required": False, "min": 0},
            "status": {"type": str, "required": False}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            lead = LeadService.create_lead(cleaned, request.user)
            return Response.created(lead)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.LEAD_EDIT)
    def update(request: Request) -> Response:
        lead_id = request.path_params.get("id")
        data = request.json()
        try:
            updated = LeadService.update_lead(lead_id, data, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.LEAD_CONVERT)
    def convert(request: Request) -> Response:
        lead_id = request.path_params.get("id")
        data = request.json() or {}
        opp_name = data.get("opportunity_name")
        try:
            result = LeadService.convert_lead(lead_id, opp_name, request.user)
            return Response.ok(result, "Lead successfully converted")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.LEAD_DELETE)
    def delete(request: Request) -> Response:
        lead_id = request.path_params.get("id")
        try:
            LeadService.delete_lead(lead_id, request.user)
            return Response.ok(None, "Lead deleted successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))
