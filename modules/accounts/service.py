"""
CRM System - Customer (Accounts & Organizations) Management Service
Complete 360-Degree Profile, Interaction History Timeline, Notes & Attachments
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from core.database.connection import DB
from modules.audit.service import AuditService


class AccountService:
    @staticmethod
    def create_account(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        account_id = "acc_" + str(uuid.uuid4())[:12]
        
        record = {
            "id": account_id,
            "name": data["name"],
            "industry": data.get("industry", "Technology"),
            "annual_revenue": float(data.get("annual_revenue", 0.0)),
            "employee_count": int(data.get("employee_count", 0)),
            "phone": data.get("phone", ""),
            "website": data.get("website", ""),
            "address_street": data.get("address_street", ""),
            "address_city": data.get("address_city", ""),
            "address_state": data.get("address_state", ""),
            "address_country": data.get("address_country", "USA"),
            "tier": data.get("tier", "STANDARD"),
            "status": data.get("status", "ACTIVE"),
            "owner_id": data.get("owner_id") or current_user.get("sub")
        }

        query("accounts").insert(record)
        
        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE_CUSTOMER",
            entity_type="ACCOUNT",
            entity_id=account_id,
            change_summary=f"Created Customer '{record['name']}' (Status: {record['status']}, Tier: {record['tier']})"
        )
        
        return record

    @staticmethod
    def get_account_360(account_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves complete 360-degree Customer profile:
        - Company details & financials
        - Key contact directory
        - Open/Closed opportunities
        - Support tickets & SLAs
        - Internal notes
        - Document attachments
        - Consolidated chronological interaction history timeline
        """
        account = query("accounts").where_eq("id", account_id).first()
        if not account:
            return None

        # Fetch Owner info
        if account.get("owner_id"):
            owner = query("users").select("id", "full_name", "email", "role").where_eq("id", account["owner_id"]).first()
            account["owner"] = owner
        else:
            account["owner"] = None

        # Related Contacts
        contacts = query("contacts").where_eq("account_id", account_id).get()
        account["contacts"] = contacts

        # Related Opportunities / Deals
        opportunities = query("opportunities").where_eq("account_id", account_id).order_by("created_at", "DESC").get()
        account["opportunities"] = opportunities

        # Related Support Tickets
        tickets = query("tickets").where_eq("account_id", account_id).order_by("created_at", "DESC").get()
        account["tickets"] = tickets

        # Customer Notes
        notes = query("customer_notes").where_eq("account_id", account_id).order_by("created_at", "DESC").get()
        for n in notes:
            if n.get("author_id"):
                author = query("users").select("full_name", "avatar_url").where_eq("id", n["author_id"]).first()
                n["author_name"] = author["full_name"] if author else "Team Member"
                n["author_avatar"] = author.get("avatar_url") if author else None
        account["notes"] = notes

        # Customer Attachments
        attachments = query("customer_attachments").where_eq("account_id", account_id).order_by("created_at", "DESC").get()
        for a in attachments:
            if a.get("uploaded_by_id"):
                uploader = query("users").select("full_name").where_eq("id", a["uploaded_by_id"]).first()
                a["uploader_name"] = uploader["full_name"] if uploader else "System"
        account["attachments"] = attachments

        # Activities (Calls, Meetings, Tasks)
        activities = query("activities").where_eq("related_to_type", "ACCOUNT").where_eq("related_to_id", account_id).order_by("created_at", "DESC").get()
        account["activities"] = activities

        # -------------------------------------------------------------
        # Compile Consolidated Chronological Interaction History Timeline
        # -------------------------------------------------------------
        timeline: List[Dict[str, Any]] = []

        # 1. Activities to Timeline
        for act in activities:
            timeline.append({
                "type": act["activity_type"],
                "icon": "📞" if act["activity_type"] == "CALL" else ("📅" if act["activity_type"] == "MEETING" else "✓"),
                "title": f"{act['activity_type'].title()}: {act['subject']}",
                "description": act.get("description", ""),
                "timestamp": act.get("due_date") or act.get("created_at"),
                "status": act.get("status")
            })

        # 2. Notes to Timeline
        for n in notes:
            timeline.append({
                "type": "NOTE",
                "icon": "📝",
                "title": f"Internal Note by {n.get('author_name', 'Team Member')}",
                "description": n["note_text"],
                "timestamp": n["created_at"],
                "status": "LOGGED"
            })

        # 3. Tickets to Timeline
        for t in tickets:
            timeline.append({
                "type": "TICKET",
                "icon": "🎫",
                "title": f"Support Ticket [{t['priority']}]: {t['title']}",
                "description": t.get("description", ""),
                "timestamp": t["created_at"],
                "status": t["status"]
            })

        # 4. Opportunities to Timeline
        for o in opportunities:
            timeline.append({
                "type": "OPPORTUNITY",
                "icon": "🎯",
                "title": f"Deal: {o['name']} (${o['amount']:,.2f})",
                "description": f"Current Stage: {o['stage']} (Win Probability: {o['win_probability']}%)",
                "timestamp": o["created_at"],
                "status": o["stage"]
            })

        # 5. Attachments to Timeline
        for att in attachments:
            timeline.append({
                "type": "ATTACHMENT",
                "icon": "📎",
                "title": f"Document Attached: {att['filename']}",
                "description": f"File size: {round(att['file_size'] / 1024, 1)} KB ({att.get('file_type', 'Document')})",
                "timestamp": att["created_at"],
                "status": "UPLOADED"
            })

        # Sort timeline by timestamp descending
        timeline.sort(key=lambda x: str(x.get("timestamp") or ""), reverse=True)
        account["interaction_history"] = timeline

        return account

    @staticmethod
    def add_customer_note(account_id: str, note_text: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("accounts").where_eq("id", account_id).first()
        if not existing:
            raise ValueError("Customer account not found")

        note_id = "not_" + str(uuid.uuid4())[:12]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        note_record = {
            "id": note_id,
            "account_id": account_id,
            "author_id": current_user.get("sub"),
            "note_text": note_text.strip(),
            "category": "GENERAL",
            "created_at": now_str
        }

        query("customer_notes").insert(note_record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="ADD_CUSTOMER_NOTE",
            entity_type="ACCOUNT",
            entity_id=account_id,
            change_summary=f"Added internal note to Customer '{existing['name']}'"
        )

        author = query("users").select("full_name", "avatar_url").where_eq("id", current_user.get("sub")).first()
        note_record["author_name"] = author["full_name"] if author else "Team Member"
        note_record["author_avatar"] = author.get("avatar_url") if author else None

        return note_record

    @staticmethod
    def add_customer_attachment(
        account_id: str,
        filename: str,
        file_size: int,
        file_type: str,
        storage_path: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        existing = query("accounts").where_eq("id", account_id).first()
        if not existing:
            raise ValueError("Customer account not found")

        att_id = "att_" + str(uuid.uuid4())[:12]
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": att_id,
            "account_id": account_id,
            "uploaded_by_id": current_user.get("sub"),
            "filename": filename,
            "file_size": file_size,
            "file_type": file_type,
            "storage_path": storage_path,
            "created_at": now_str
        }

        query("customer_attachments").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="ADD_CUSTOMER_ATTACHMENT",
            entity_type="ACCOUNT",
            entity_id=account_id,
            change_summary=f"Uploaded attachment '{filename}' to Customer '{existing['name']}'"
        )

        return record

    @staticmethod
    def update_customer_status(account_id: str, new_status: str, current_user: Dict[str, Any]) -> Dict[str, Any]:
        status = new_status.upper()
        if status not in ("ACTIVE", "INACTIVE", "PROSPECT", "CHURNED"):
            raise ValueError("Status must be one of: 'ACTIVE', 'INACTIVE', 'PROSPECT', 'CHURNED'")

        existing = query("accounts").where_eq("id", account_id).first()
        if not existing:
            raise ValueError("Customer account not found")

        query("accounts").where_eq("id", account_id).update({
            "status": status,
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        })

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CUSTOMER_STATUS_CHANGE",
            entity_type="ACCOUNT",
            entity_id=account_id,
            change_summary=f"Updated status of Customer '{existing['name']}' from '{existing['status']}' to '{status}'"
        )

        return AccountService.get_account_360(account_id)

    @staticmethod
    def list_accounts(
        search: Optional[str] = None,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = query("accounts")
        if search:
            q.where_like("name", search)
        if tier:
            q.where_eq("tier", tier)
        if status:
            q.where_eq("status", status)

        total = q.count()
        records = q.order_by("name", "ASC").limit(limit).offset(offset).get()
        
        for rec in records:
            if rec.get("owner_id"):
                owner = query("users").select("full_name").where_eq("id", rec["owner_id"]).first()
                rec["owner_name"] = owner["full_name"] if owner else "Unassigned"
            else:
                rec["owner_name"] = "Unassigned"

        return {
            "total": total,
            "items": records,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def update_account(account_id: str, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("accounts").where_eq("id", account_id).first()
        if not existing:
            raise ValueError("Customer account not found")

        update_fields = {}
        for key in ["name", "industry", "annual_revenue", "employee_count", "phone", "website",
                    "address_street", "address_city", "address_state", "address_country", "tier", "status", "owner_id"]:
            if key in data:
                update_fields[key] = data[key]

        if update_fields:
            update_fields["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            query("accounts").where_eq("id", account_id).update(update_fields)
            
            AuditService.record(
                user_id=current_user.get("sub"),
                user_email=current_user.get("email"),
                action="UPDATE_CUSTOMER",
                entity_type="ACCOUNT",
                entity_id=account_id,
                change_summary=f"Updated details for Customer '{existing['name']}': {list(update_fields.keys())}"
            )

        return AccountService.get_account_360(account_id)

    @staticmethod
    def delete_account(account_id: str, current_user: Dict[str, Any]):
        existing = query("accounts").where_eq("id", account_id).first()
        if not existing:
            raise ValueError("Customer account not found")

        query("accounts").where_eq("id", account_id).delete()
        
        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="DELETE_CUSTOMER",
            entity_type="ACCOUNT",
            entity_id=account_id,
            change_summary=f"Deleted Customer account '{existing['name']}'"
        )
