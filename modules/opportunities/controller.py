"""
CRM System - Opportunities Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.opportunities.service import OpportunityService
from modules.auth.guard import require_permission
from config.permissions import Permission


class OpportunityController:
    @staticmethod
    @require_permission(Permission.OPPORTUNITY_VIEW)
    def list(request: Request) -> Response:
        stage = request.query("stage")
        account_id = request.query("account_id")
        owner_id = request.query("owner_id")
        search = request.query("search")
        limit = int(request.query("limit") or "100")
        offset = int(request.query("offset") or "0")

        result = OpportunityService.list_opportunities(
            stage=stage, account_id=account_id, owner_id=owner_id, search=search, limit=limit, offset=offset
        )
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.OPPORTUNITY_VIEW)
    def kanban(request: Request) -> Response:
        board_data = OpportunityService.get_kanban_pipeline()
        return Response.ok(board_data)

    @staticmethod
    @require_permission(Permission.OPPORTUNITY_VIEW)
    def get(request: Request) -> Response:
        opp_id = request.path_params.get("id")
        opp = OpportunityService.get_opportunity(opp_id)
        if not opp:
            return Response.not_found("Opportunity not found")
        return Response.ok(opp)

    @staticmethod
    @require_permission(Permission.OPPORTUNITY_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "name": {"type": str, "required": True, "min_len": 2},
            "account_id": {"type": str, "required": True},
            "contact_id": {"type": str, "required": False},
            "stage": {"type": str, "required": False},
            "amount": {"type": float, "required": True, "min": 0},
            "win_probability": {"type": int, "required": False, "min": 0, "max": 100},
            "expected_close_date": {"type": str, "required": False}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            opp = OpportunityService.create_opportunity(cleaned, request.user)
            return Response.created(opp)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.OPPORTUNITY_EDIT)
    def update(request: Request) -> Response:
        opp_id = request.path_params.get("id")
        data = request.json()
        try:
            updated = OpportunityService.update_opportunity(opp_id, data, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.OPPORTUNITY_EDIT)
    def set_stage(request: Request) -> Response:
        opp_id = request.path_params.get("id")
        data = request.json()
        stage = data.get("stage")
        loss_reason = data.get("loss_reason")

        if not stage:
            return Response.bad_request("Missing stage parameter")

        try:
            updated = OpportunityService.update_opportunity_stage(opp_id, stage, loss_reason, request.user)
            return Response.ok(updated, "Opportunity stage updated")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.OPPORTUNITY_DELETE)
    def delete(request: Request) -> Response:
        opp_id = request.path_params.get("id")
        try:
            OpportunityService.delete_opportunity(opp_id, request.user)
            return Response.ok(None, "Opportunity deleted successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))
