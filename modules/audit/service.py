"""
CRM System - Immutable Audit Logging Service
"""

import uuid
from typing import Optional, Dict, Any, List
from core.database.query_builder import query


class AuditService:
    @staticmethod
    def record(
        user_id: Optional[str],
        user_email: Optional[str],
        action: str,
        entity_type: str,
        entity_id: str,
        change_summary: str,
        ip_address: Optional[str] = None
    ):
        """Record an immutable entry in the audit trail."""
        audit_id = "aud_" + str(uuid.uuid4())[:12]
        data = {
            "id": audit_id,
            "user_id": user_id,
            "user_email": user_email or "system@omnicrm.local",
            "action": action.upper(),
            "entity_type": entity_type.upper(),
            "entity_id": str(entity_id),
            "change_summary": change_summary,
            "ip_address": ip_address or "127.0.0.1"
        }
        try:
            query("audit_logs").insert(data)
        except Exception as ex:
            print(f"Failed to record audit log: {ex}")

    @staticmethod
    def get_logs(entity_type: Optional[str] = None, entity_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        q = query("audit_logs").order_by("created_at", "DESC").limit(limit)
        if entity_type:
            q.where_eq("entity_type", entity_type.upper())
        if entity_id:
            q.where_eq("entity_id", str(entity_id))
        return q.get()
