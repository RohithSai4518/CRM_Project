"""
CRM System - Contacts Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.contacts.service import ContactService
from modules.auth.guard import require_permission
from config.permissions import Permission


class ContactController:
    @staticmethod
    @require_permission(Permission.CONTACT_VIEW)
    def list(request: Request) -> Response:
        account_id = request.query("account_id")
        search = request.query("search")
        limit = int(request.query("limit") or "50")
        offset = int(request.query("offset") or "0")

        result = ContactService.list_contacts(account_id=account_id, search=search, limit=limit, offset=offset)
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.CONTACT_VIEW)
    def get(request: Request) -> Response:
        contact_id = request.path_params.get("id")
        contact = ContactService.get_contact(contact_id)
        if not contact:
            return Response.not_found("Contact not found")
        return Response.ok(contact)

    @staticmethod
    @require_permission(Permission.CONTACT_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "first_name": {"type": str, "required": True, "min_len": 1},
            "last_name": {"type": str, "required": True, "min_len": 1},
            "email": {"type": str, "required": True, "format": "email"},
            "phone": {"type": str, "required": False},
            "account_id": {"type": str, "required": False},
            "job_title": {"type": str, "required": False},
            "department": {"type": str, "required": False},
            "is_primary": {"type": bool, "required": False},
            "notes": {"type": str, "required": False}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            contact = ContactService.create_contact(cleaned, request.user)
            return Response.created(contact)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.CONTACT_EDIT)
    def update(request: Request) -> Response:
        contact_id = request.path_params.get("id")
        data = request.json()
        try:
            updated = ContactService.update_contact(contact_id, data, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.CONTACT_DELETE)
    def delete(request: Request) -> Response:
        contact_id = request.path_params.get("id")
        try:
            ContactService.delete_contact(contact_id, request.user)
            return Response.ok(None, "Contact deleted successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))
