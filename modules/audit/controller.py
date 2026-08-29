"""
CRM System - Audit Log Controller
"""

from core.http.request import Request
from core.http.response import Response
from modules.auth.guard import require_permission
from config.permissions import Permission
from modules.audit.service import AuditService


class AuditController:
    @staticmethod
    @require_permission(Permission.AUDIT_LOG_VIEW)
    def list_logs(request: Request) -> Response:
        entity_type = request.query("entity_type")
        entity_id = request.query("entity_id")
        limit = int(request.query("limit") or "50")
        
        logs = AuditService.get_logs(entity_type=entity_type, entity_id=entity_id, limit=limit)
        return Response.ok(logs)
