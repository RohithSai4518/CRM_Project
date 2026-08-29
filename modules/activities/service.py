"""
CRM System - Activities, Tasks & Calendar Service
"""

import uuid
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from modules.audit.service import AuditService


class ActivityService:
    @staticmethod
    def create_activity(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        act_id = "act_" + str(uuid.uuid4())[:12]

        record = {
            "id": act_id,
            "activity_type": data.get("activity_type", "TASK").upper(),
            "subject": data["subject"],
            "description": data.get("description", ""),
            "due_date": data.get("due_date"),
            "status": data.get("status", "PENDING").upper(),
            "priority": data.get("priority", "MEDIUM").upper(),
            "related_to_type": data.get("related_to_type", "ACCOUNT").upper() if data.get("related_to_type") else None,
            "related_to_id": data.get("related_to_id"),
            "assigned_to_id": data.get("assigned_to_id") or current_user.get("sub")
        }

        query("activities").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE",
            entity_type="ACTIVITY",
            entity_id=act_id,
            change_summary=f"Created {record['activity_type']} '{record['subject']}'"
        )

        return record

    @staticmethod
    def list_activities(
        assigned_to_id: Optional[str] = None,
        status: Optional[str] = None,
        related_to_type: Optional[str] = None,
        related_to_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = query("activities")
        if assigned_to_id:
            q.where_eq("assigned_to_id", assigned_to_id)
        if status:
            q.where_eq("status", status)
        if related_to_type and related_to_id:
            q.where_eq("related_to_type", related_to_type.upper()).where_eq("related_to_id", related_to_id)

        total = q.count()
        records = q.order_by("due_date", "ASC").limit(limit).offset(offset).get()

        for rec in records:
            if rec.get("assigned_to_id"):
                owner = query("users").select("full_name").where_eq("id", rec["assigned_to_id"]).first()
                rec["assigned_name"] = owner["full_name"] if owner else "Unassigned"
            else:
                rec["assigned_name"] = "Unassigned"

        return {
            "total": total,
            "items": records,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def update_activity_status(activity_id: str, status: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("activities").where_eq("id", activity_id).first()
        if not existing:
            raise ValueError("Activity not found")

        status = status.upper()
        query("activities").where_eq("id", activity_id).update({"status": status})

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="UPDATE_STATUS",
            entity_type="ACTIVITY",
            entity_id=activity_id,
            change_summary=f"Changed activity status to {status}"
        )

        return query("activities").where_eq("id", activity_id).first()
