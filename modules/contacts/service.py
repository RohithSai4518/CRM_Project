"""
CRM System - Contacts Service
"""

import uuid
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from modules.audit.service import AuditService


class ContactService:
    @staticmethod
    def create_contact(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        contact_id = "cnt_" + str(uuid.uuid4())[:12]
        
        record = {
            "id": contact_id,
            "account_id": data.get("account_id"),
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "email": data["email"].strip().lower(),
            "phone": data.get("phone", ""),
            "job_title": data.get("job_title", ""),
            "department": data.get("department", ""),
            "lead_source": data.get("lead_source", "DIRECT"),
            "is_primary": 1 if data.get("is_primary") else 0,
            "notes": data.get("notes", "")
        }

        query("contacts").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE",
            entity_type="CONTACT",
            entity_id=contact_id,
            change_summary=f"Created Contact {record['first_name']} {record['last_name']} ({record['email']})"
        )

        return record

    @staticmethod
    def get_contact(contact_id: str) -> Optional[Dict[str, Any]]:
        contact = query("contacts").where_eq("id", contact_id).first()
        if not contact:
            return None

        # Fetch associated account info
        if contact.get("account_id"):
            account = query("accounts").select("id", "name", "tier").where_eq("id", contact["account_id"]).first()
            contact["account"] = account
        else:
            contact["account"] = None

        # Fetch associated opportunities
        contact["opportunities"] = query("opportunities").where_eq("contact_id", contact_id).get()
        
        # Fetch associated tickets
        contact["tickets"] = query("tickets").where_eq("contact_id", contact_id).get()

        return contact

    @staticmethod
    def list_contacts(
        account_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = query("contacts")
        if account_id:
            q.where_eq("account_id", account_id)
        if search:
            q.where_like("first_name", search)

        total = q.count()
        records = q.order_by("first_name", "ASC").limit(limit).offset(offset).get()
        
        # Attach account name
        for rec in records:
            if rec.get("account_id"):
                acc = query("accounts").select("name").where_eq("id", rec["account_id"]).first()
                rec["account_name"] = acc["name"] if acc else "Independent"
            else:
                rec["account_name"] = "Independent"

        return {
            "total": total,
            "items": records,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def update_contact(contact_id: str, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("contacts").where_eq("id", contact_id).first()
        if not existing:
            raise ValueError("Contact not found")

        update_fields = {}
        for key in ["account_id", "first_name", "last_name", "email", "phone", "job_title", "department", "lead_source", "is_primary", "notes"]:
            if key in data:
                if key == "is_primary":
                    update_fields[key] = 1 if data[key] else 0
                elif key == "email":
                    update_fields[key] = data[key].strip().lower()
                else:
                    update_fields[key] = data[key]

        if update_fields:
            query("contacts").where_eq("id", contact_id).update(update_fields)
            
            AuditService.record(
                user_id=current_user.get("sub"),
                user_email=current_user.get("email"),
                action="UPDATE",
                entity_type="CONTACT",
                entity_id=contact_id,
                change_summary=f"Updated Contact fields: {list(update_fields.keys())}"
            )

        return ContactService.get_contact(contact_id)

    @staticmethod
    def delete_contact(contact_id: str, current_user: Dict[str, Any]):
        existing = query("contacts").where_eq("id", contact_id).first()
        if not existing:
            raise ValueError("Contact not found")

        query("contacts").where_eq("id", contact_id).delete()
        
        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="DELETE",
            entity_type="CONTACT",
            entity_id=contact_id,
            change_summary=f"Deleted Contact {existing['first_name']} {existing['last_name']}"
        )
