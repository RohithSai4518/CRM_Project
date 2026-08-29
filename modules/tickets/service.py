"""
CRM System - Customer Support & Helpdesk Service
"""

import uuid
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from modules.tickets.sla import calculate_sla_deadlines, check_sla_breach
from modules.audit.service import AuditService


class TicketService:
    @staticmethod
    def create_ticket(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        ticket_id = "tck_" + str(uuid.uuid4())[:12]
        priority = data.get("priority", "MEDIUM").upper()

        resp_deadline, resol_deadline = calculate_sla_deadlines(priority)

        record = {
            "id": ticket_id,
            "account_id": data.get("account_id"),
            "contact_id": data.get("contact_id"),
            "title": data["title"],
            "description": data["description"],
            "priority": priority,
            "status": "OPEN",
            "category": data.get("category", "GENERAL").upper(),
            "sla_response_deadline": resp_deadline,
            "sla_resolution_deadline": resol_deadline,
            "sla_response_breached": 0,
            "sla_resolution_breached": 0,
            "assigned_agent_id": data.get("assigned_agent_id") or current_user.get("sub"),
            "csat_score": None
        }

        query("tickets").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE",
            entity_type="TICKET",
            entity_id=ticket_id,
            change_summary=f"Opened [{priority}] Ticket '{record['title']}' (SLA Deadline: {resol_deadline})"
        )

        return record

    @staticmethod
    def get_ticket(ticket_id: str) -> Optional[Dict[str, Any]]:
        ticket = query("tickets").where_eq("id", ticket_id).first()
        if not ticket:
            return None

        # Check live SLA breach status
        r_breach, res_breach = check_sla_breach(ticket)
        if r_breach != bool(ticket["sla_response_breached"]) or res_breach != bool(ticket["sla_resolution_breached"]):
            query("tickets").where_eq("id", ticket_id).update({
                "sla_response_breached": 1 if r_breach else 0,
                "sla_resolution_breached": 1 if res_breach else 0
            })
            ticket["sla_response_breached"] = 1 if r_breach else 0
            ticket["sla_resolution_breached"] = 1 if res_breach else 0

        # Fetch Account & Contact
        if ticket.get("account_id"):
            ticket["account"] = query("accounts").select("id", "name").where_eq("id", ticket["account_id"]).first()
        if ticket.get("contact_id"):
            ticket["contact"] = query("contacts").select("id", "first_name", "last_name", "email").where_eq("id", ticket["contact_id"]).first()
        if ticket.get("assigned_agent_id"):
            ticket["assigned_agent"] = query("users").select("id", "full_name", "email").where_eq("id", ticket["assigned_agent_id"]).first()

        # Fetch comments & internal notes
        comments = query("ticket_comments").where_eq("ticket_id", ticket_id).order_by("created_at", "ASC").get()
        for c in comments:
            if c.get("author_id"):
                author = query("users").select("full_name", "role", "avatar_url").where_eq("id", c["author_id"]).first()
                c["author"] = author
        ticket["comments"] = comments

        return ticket

    @staticmethod
    def add_comment(
        ticket_id: str,
        comment_text: str,
        is_internal: bool,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        existing = query("tickets").where_eq("id", ticket_id).first()
        if not existing:
            raise ValueError("Ticket not found")

        cid = "tcm_" + str(uuid.uuid4())[:12]
        comment_record = {
            "id": cid,
            "ticket_id": ticket_id,
            "author_id": current_user.get("sub"),
            "comment_text": comment_text,
            "is_internal": 1 if is_internal else 0
        }
        query("ticket_comments").insert(comment_record)

        # If replying on an OPEN ticket, transition status to IN_PROGRESS
        if existing["status"] == "OPEN":
            query("tickets").where_eq("id", ticket_id).update({"status": "IN_PROGRESS"})

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="COMMENT",
            entity_type="TICKET",
            entity_id=ticket_id,
            change_summary=f"Added {'internal note' if is_internal else 'customer reply'}"
        )

        return comment_record

    @staticmethod
    def list_tickets(
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_agent_id: Optional[str] = None,
        account_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = query("tickets")
        if status:
            q.where_eq("status", status)
        if priority:
            q.where_eq("priority", priority)
        if assigned_agent_id:
            q.where_eq("assigned_agent_id", assigned_agent_id)
        if account_id:
            q.where_eq("account_id", account_id)

        total = q.count()
        records = q.order_by("created_at", "DESC").limit(limit).offset(offset).get()

        for rec in records:
            if rec.get("account_id"):
                acc = query("accounts").select("name").where_eq("id", rec["account_id"]).first()
                rec["account_name"] = acc["name"] if acc else "Independent"
            else:
                rec["account_name"] = "Independent"

            if rec.get("assigned_agent_id"):
                agent = query("users").select("full_name").where_eq("id", rec["assigned_agent_id"]).first()
                rec["agent_name"] = agent["full_name"] if agent else "Unassigned"
            else:
                rec["agent_name"] = "Unassigned"

        return {
            "total": total,
            "items": records,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def update_ticket(ticket_id: str, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("tickets").where_eq("id", ticket_id).first()
        if not existing:
            raise ValueError("Ticket not found")

        update_fields = {}
        for key in ["title", "description", "priority", "status", "category", "assigned_agent_id", "csat_score"]:
            if key in data:
                update_fields[key] = data[key]

        query("tickets").where_eq("id", ticket_id).update(update_fields)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="UPDATE",
            entity_type="TICKET",
            entity_id=ticket_id,
            change_summary=f"Updated Ticket attributes: {list(update_fields.keys())}"
        )

        return TicketService.get_ticket(ticket_id)
