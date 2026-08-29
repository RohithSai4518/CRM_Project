"""
CRM System - Tickets Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.tickets.service import TicketService
from modules.auth.guard import require_permission
from config.permissions import Permission


class TicketController:
    @staticmethod
    @require_permission(Permission.TICKET_VIEW)
    def list(request: Request) -> Response:
        status = request.query("status")
        priority = request.query("priority")
        assigned_agent_id = request.query("assigned_agent_id")
        account_id = request.query("account_id")
        limit = int(request.query("limit") or "50")
        offset = int(request.query("offset") or "0")

        result = TicketService.list_tickets(
            status=status, priority=priority, assigned_agent_id=assigned_agent_id, account_id=account_id, limit=limit, offset=offset
        )
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.TICKET_VIEW)
    def get(request: Request) -> Response:
        ticket_id = request.path_params.get("id")
        ticket = TicketService.get_ticket(ticket_id)
        if not ticket:
            return Response.not_found("Ticket not found")
        return Response.ok(ticket)

    @staticmethod
    @require_permission(Permission.TICKET_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "title": {"type": str, "required": True, "min_len": 3},
            "description": {"type": str, "required": True, "min_len": 5},
            "priority": {"type": str, "required": False, "choices": ["LOW", "MEDIUM", "HIGH", "URGENT"]},
            "category": {"type": str, "required": False},
            "account_id": {"type": str, "required": False},
            "contact_id": {"type": str, "required": False},
            "assigned_agent_id": {"type": str, "required": False}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            ticket = TicketService.create_ticket(cleaned, request.user)
            return Response.created(ticket)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.TICKET_EDIT)
    def update(request: Request) -> Response:
        ticket_id = request.path_params.get("id")
        data = request.json()
        try:
            updated = TicketService.update_ticket(ticket_id, data, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.TICKET_EDIT)
    def add_comment(request: Request) -> Response:
        ticket_id = request.path_params.get("id")
        data = request.json()
        comment_text = data.get("comment_text")
        is_internal = bool(data.get("is_internal", False))

        if not comment_text or not comment_text.strip():
            return Response.bad_request("Comment text cannot be empty")

        try:
            comment = TicketService.add_comment(ticket_id, comment_text, is_internal, request.user)
            return Response.created(comment)
        except ValueError as ve:
            return Response.bad_request(str(ve))
