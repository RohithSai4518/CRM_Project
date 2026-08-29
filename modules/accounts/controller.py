"""
CRM System - Customer (Accounts) Controller
"""

from core.http.request import Request
from core.http.response import Response
from core.security.validator import SchemaValidator
from modules.accounts.service import AccountService
from modules.auth.guard import require_permission
from config.permissions import Permission


class AccountController:
    @staticmethod
    @require_permission(Permission.ACCOUNT_VIEW)
    def list(request: Request) -> Response:
        search = request.query("search")
        tier = request.query("tier")
        status = request.query("status")
        limit = int(request.query("limit") or "50")
        offset = int(request.query("offset") or "0")

        result = AccountService.list_accounts(search=search, tier=tier, status=status, limit=limit, offset=offset)
        return Response.ok(result)

    @staticmethod
    @require_permission(Permission.ACCOUNT_VIEW)
    def get(request: Request) -> Response:
        account_id = request.path_params.get("id")
        account = AccountService.get_account_360(account_id)
        if not account:
            return Response.not_found("Customer account not found")
        return Response.ok(account)

    @staticmethod
    @require_permission(Permission.ACCOUNT_CREATE)
    def create(request: Request) -> Response:
        data = request.json()
        rules = {
            "name": {"type": str, "required": True, "min_len": 2},
            "industry": {"type": str, "required": False},
            "annual_revenue": {"type": float, "required": False, "min": 0},
            "employee_count": {"type": int, "required": False, "min": 0},
            "phone": {"type": str, "required": False},
            "website": {"type": str, "required": False},
            "tier": {"type": str, "required": False, "choices": ["STANDARD", "PREMIUM", "ENTERPRISE", "STRATEGIC"]},
            "status": {"type": str, "required": False, "choices": ["ACTIVE", "INACTIVE", "PROSPECT", "CHURNED"]}
        }
        valid, errors, cleaned = SchemaValidator(rules).validate(data)
        if not valid:
            return Response.bad_request("Validation failed", errors)

        try:
            account = AccountService.create_account(cleaned, request.user)
            return Response.created(account)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.ACCOUNT_EDIT)
    def update(request: Request) -> Response:
        account_id = request.path_params.get("id")
        data = request.json()
        try:
            updated = AccountService.update_account(account_id, data, request.user)
            return Response.ok(updated)
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.ACCOUNT_NOTES)
    def add_note(request: Request) -> Response:
        account_id = request.path_params.get("id")
        data = request.json()
        note_text = data.get("note_text")
        if not note_text or not note_text.strip():
            return Response.bad_request("Note text cannot be empty")

        try:
            note = AccountService.add_customer_note(account_id, note_text, request.user)
            return Response.created(note, "Note logged successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.ACCOUNT_ATTACHMENTS)
    def add_attachment(request: Request) -> Response:
        account_id = request.path_params.get("id")
        data = request.json()
        filename = data.get("filename")
        if not filename:
            return Response.bad_request("Filename is required")

        file_size = int(data.get("file_size", 1024))
        file_type = data.get("file_type", "Document")
        storage_path = data.get("storage_path", f"/attachments/{filename}")

        try:
            att = AccountService.add_customer_attachment(account_id, filename, file_size, file_type, storage_path, request.user)
            return Response.created(att, "Attachment recorded successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.ACCOUNT_DEACTIVATE)
    def set_status(request: Request) -> Response:
        account_id = request.path_params.get("id")
        data = request.json()
        status = data.get("status")
        if not status:
            return Response.bad_request("Status is required ('ACTIVE', 'INACTIVE', 'PROSPECT', 'CHURNED')")

        try:
            updated = AccountService.update_customer_status(account_id, status, request.user)
            return Response.ok(updated, f"Customer status updated to {status}")
        except ValueError as ve:
            return Response.bad_request(str(ve))

    @staticmethod
    @require_permission(Permission.ACCOUNT_DELETE)
    def delete(request: Request) -> Response:
        account_id = request.path_params.get("id")
        try:
            AccountService.delete_account(account_id, request.user)
            return Response.ok(None, "Customer account deleted successfully")
        except ValueError as ve:
            return Response.bad_request(str(ve))
