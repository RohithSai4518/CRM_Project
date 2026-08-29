"""
CRM System - Activities Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.activities.service import ActivityService
from modules.auth.guard import require_permission
from config.permissions import Permission


class ActivityController:
    @staticmethod
    @require_permission(Permission.ACTIVITY_VIEW)
    def list(request: Request) -> Response:
        status = request.query("status")
        assigned_to_id = request.query("assigned_to_id")
        related_to_type = request.query("related_to_type")
        related_to_id = request.query("related_to_id")
        limit = int(request.query("limit") or "50")
        offset = int(request.query("offset") or "0")

        result = ActivityService.list_activities(
            assigned_to_id=assigned_to_id, status=status, related_to_type=related_to_type, related_to_id=related_to_id, limit=limit, offset=offset
        )
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.ACTIVITY_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "subject": {"type": str, "required": True, "min_len": 2},
            "activity_type": {"type": str, "required": False, "choices": ["CALL", "MEETING", "EMAIL", "TASK", "NOTE"]},
            "due_date": {"type": str, "required": False},
            "priority": {"type": str, "required": False, "choices": ["LOW", "MEDIUM", "HIGH", "URGENT"]},
            "related_to_type": {"type": str, "required": False},
            "related_to_id": {"type": str, "required": False},
            "description": {"type": str, "required": False}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            act = ActivityService.create_activity(cleaned, request.user)
            return Response.created(act)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.ACTIVITY_EDIT)
    def set_status(request: Request) -> Response:
        activity_id = request.path_params.get("id")
        data = request.json()
        status = data.get("status")
        if not status:
            return Response.bad_request("Status is required")

        try:
            updated = ActivityService.update_activity_status(activity_id, status, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))
