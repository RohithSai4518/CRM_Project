"""
CRM System - Leads Service & Conversion Pipeline
"""

import uuid
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from core.database.connection import DB
from modules.leads.scoring import calculate_lead_score
from modules.accounts.service import AccountService
from modules.contacts.service import ContactService
from modules.audit.service import AuditService
from config.app_config import CONFIG


class LeadService:
    @staticmethod
    def create_lead(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        lead_id = "led_" + str(uuid.uuid4())[:12]
        
        # Calculate intelligent qualification score
        score = calculate_lead_score(data)
        
        record = {
            "id": lead_id,
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "company_name": data.get("company_name", ""),
            "email": data["email"].strip().lower(),
            "phone": data.get("phone", ""),
            "status": data.get("status", "NEW"),
            "lead_source": data.get("lead_source", "INBOUND_WEBSITE"),
            "lead_score": score,
            "estimated_value": float(data.get("estimated_value", 0.0)),
            "assigned_to_id": data.get("assigned_to_id") or current_user.get("sub"),
            "converted_account_id": None,
            "converted_contact_id": None,
            "converted_opportunity_id": None
        }

        query("leads").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE",
            entity_type="LEAD",
            entity_id=lead_id,
            change_summary=f"Created Lead {record['first_name']} {record['last_name']} with Score {score}/100"
        )

        return record

    @staticmethod
    def get_lead(lead_id: str) -> Optional[Dict[str, Any]]:
        lead = query("leads").where_eq("id", lead_id).first()
        if not lead:
            return None

        if lead.get("assigned_to_id"):
            owner = query("users").select("id", "full_name", "email").where_eq("id", lead["assigned_to_id"]).first()
            lead["assigned_user"] = owner
        else:
            lead["assigned_user"] = None

        return lead

    @staticmethod
    def list_leads(
        status: Optional[str] = None,
        search: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = query("leads")
        if status:
            q.where_eq("status", status)
        if search:
            q.where_like("first_name", search)
        if min_score is not None:
            q.where("lead_score", ">=", min_score)

        total = q.count()
        records = q.order_by("lead_score", "DESC").limit(limit).offset(offset).get()

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
    def update_lead(lead_id: str, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("leads").where_eq("id", lead_id).first()
        if not existing:
            raise ValueError("Lead not found")

        update_fields = {}
        for key in ["first_name", "last_name", "company_name", "email", "phone", "status", "lead_source", "estimated_value", "assigned_to_id"]:
            if key in data:
                update_fields[key] = data[key]

        # Recalculate score if key attributes changed
        merged = dict(existing)
        merged.update(update_fields)
        new_score = calculate_lead_score(merged)
        update_fields["lead_score"] = new_score

        query("leads").where_eq("id", lead_id).update(update_fields)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="UPDATE",
            entity_type="LEAD",
            entity_id=lead_id,
            change_summary=f"Updated Lead details. Re-scored to {new_score}"
        )

        return LeadService.get_lead(lead_id)

    @staticmethod
    def convert_lead(
        lead_id: str,
        opportunity_name: Optional[str],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Converts a qualified lead into:
        1. An Account (Company)
        2. A Contact
        3. An Opportunity (Deal in pipeline)
        """
        lead = query("leads").where_eq("id", lead_id).first()
        if not lead:
            raise ValueError("Lead not found")

        if lead.get("status") == "CONVERTED":
            raise ValueError("Lead has already been converted")

        # 1. Create or Find Account
        company_name = lead.get("company_name") or f"{lead['first_name']} {lead['last_name']} (Organization)"
        existing_acc = query("accounts").where_eq("name", company_name).first()
        if existing_acc:
            account_id = existing_acc["id"]
        else:
            acc_data = {
                "name": company_name,
                "phone": lead.get("phone", ""),
                "owner_id": current_user.get("sub")
            }
            new_acc = AccountService.create_account(acc_data, current_user)
            account_id = new_acc["id"]

        # 2. Create Contact
        contact_data = {
            "account_id": account_id,
            "first_name": lead["first_name"],
            "last_name": lead["last_name"],
            "email": lead["email"],
            "phone": lead.get("phone", ""),
            "lead_source": lead.get("lead_source", "INBOUND_WEBSITE"),
            "is_primary": True
        }
        new_contact = ContactService.create_contact(contact_data, current_user)
        contact_id = new_contact["id"]

        # 3. Create Opportunity
        opp_id = "opp_" + str(uuid.uuid4())[:12]
        opp_title = opportunity_name or f"{company_name} - New Enterprise Contract"
        opp_data = {
            "id": opp_id,
            "account_id": account_id,
            "contact_id": contact_id,
            "name": opp_title,
            "stage": "QUALIFICATION",
            "amount": float(lead.get("estimated_value") or 10000.0),
            "win_probability": 25,
            "expected_close_date": None,
            "owner_id": current_user.get("sub")
        }
        query("opportunities").insert(opp_data)

        # 4. Mark Lead as Converted
        query("leads").where_eq("id", lead_id).update({
            "status": "CONVERTED",
            "converted_account_id": account_id,
            "converted_contact_id": contact_id,
            "converted_opportunity_id": opp_id
        })

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CONVERT",
            entity_type="LEAD",
            entity_id=lead_id,
            change_summary=f"Converted Lead to Account ({account_id}), Contact ({contact_id}), and Opportunity ({opp_id})"
        )

        return {
            "lead_id": lead_id,
            "account_id": account_id,
            "contact_id": contact_id,
            "opportunity_id": opp_id,
            "message": "Lead converted successfully"
        }

    @staticmethod
    def delete_lead(lead_id: str, current_user: Dict[str, Any]):
        existing = query("leads").where_eq("id", lead_id).first()
        if not existing:
            raise ValueError("Lead not found")

        query("leads").where_eq("id", lead_id).delete()

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="DELETE",
            entity_type="LEAD",
            entity_id=lead_id,
            change_summary=f"Deleted Lead {existing['first_name']} {existing['last_name']}"
        )
