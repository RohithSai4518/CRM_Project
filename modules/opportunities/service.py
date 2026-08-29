"""
CRM System - Opportunities (Sales Pipeline & Deal Flow) Service
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from modules.audit.service import AuditService
from config.app_config import CONFIG


STAGE_PROBABILITY_MAP = {
    "PROSPECTING": 10,
    "QUALIFICATION": 25,
    "NEED_ANALYSIS": 40,
    "PROPOSAL": 60,
    "NEGOTIATION": 80,
    "CLOSED_WON": 100,
    "CLOSED_LOST": 0
}


class OpportunityService:
    @staticmethod
    def create_opportunity(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        opp_id = "opp_" + str(uuid.uuid4())[:12]
        stage = data.get("stage", "PROSPECTING").upper()
        default_prob = STAGE_PROBABILITY_MAP.get(stage, 10)
        
        prob = int(data.get("win_probability")) if data.get("win_probability") is not None else default_prob

        record = {
            "id": opp_id,
            "account_id": data["account_id"],
            "contact_id": data.get("contact_id"),
            "name": data["name"],
            "stage": stage,
            "amount": float(data.get("amount", 0.0)),
            "win_probability": prob,
            "expected_close_date": data.get("expected_close_date"),
            "actual_close_date": None,
            "loss_reason": None,
            "owner_id": data.get("owner_id") or current_user.get("sub")
        }

        query("opportunities").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE",
            entity_type="OPPORTUNITY",
            entity_id=opp_id,
            change_summary=f"Created Opportunity '{record['name']}' in stage {stage} for ${record['amount']:,.2f}"
        )

        return record

    @staticmethod
    def get_opportunity(opp_id: str) -> Optional[Dict[str, Any]]:
        opp = query("opportunities").where_eq("id", opp_id).first()
        if not opp:
            return None

        # Fetch Account
        if opp.get("account_id"):
            acc = query("accounts").select("id", "name", "tier").where_eq("id", opp["account_id"]).first()
            opp["account"] = acc
        else:
            opp["account"] = None

        # Fetch Contact
        if opp.get("contact_id"):
            contact = query("contacts").select("id", "first_name", "last_name", "email", "phone").where_eq("id", opp["contact_id"]).first()
            opp["contact"] = contact
        else:
            opp["contact"] = None

        # Fetch Owner
        if opp.get("owner_id"):
            owner = query("users").select("id", "full_name", "email").where_eq("id", opp["owner_id"]).first()
            opp["owner"] = owner
        else:
            opp["owner"] = None

        # Fetch Related Activities
        opp["activities"] = query("activities").where_eq("related_to_type", "OPPORTUNITY").where_eq("related_to_id", opp_id).get()

        return opp

    @staticmethod
    def list_opportunities(
        stage: Optional[str] = None,
        account_id: Optional[str] = None,
        owner_id: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        q = query("opportunities")
        if stage:
            q.where_eq("stage", stage)
        if account_id:
            q.where_eq("account_id", account_id)
        if owner_id:
            q.where_eq("owner_id", owner_id)
        if search:
            q.where_like("name", search)

        total = q.count()
        records = q.order_by("created_at", "DESC").limit(limit).offset(offset).get()

        # Augment with Account and Owner names
        for rec in records:
            if rec.get("account_id"):
                acc = query("accounts").select("name").where_eq("id", rec["account_id"]).first()
                rec["account_name"] = acc["name"] if acc else "Unknown"
            else:
                rec["account_name"] = "None"

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
    def get_kanban_pipeline() -> Dict[str, Any]:
        """Group all active opportunities by stages for interactive Kanban board."""
        stages = [s["id"] for s in CONFIG.business.opportunity_stages]
        all_opps = query("opportunities").order_by("amount", "DESC").get()

        board: Dict[str, List[Dict[str, Any]]] = {stage: [] for stage in stages}
        stage_totals: Dict[str, float] = {stage: 0.0 for stage in stages}

        for opp in all_opps:
            st = opp["stage"]
            if st not in board:
                board[st] = []
                stage_totals[st] = 0.0

            # Augment with brief account & owner
            if opp.get("account_id"):
                acc = query("accounts").select("name").where_eq("id", opp["account_id"]).first()
                opp["account_name"] = acc["name"] if acc else ""
            else:
                opp["account_name"] = ""

            board[st].append(opp)
            stage_totals[st] += float(opp.get("amount", 0.0))

        return {
            "stages": CONFIG.business.opportunity_stages,
            "board": board,
            "totals": stage_totals,
            "total_active_pipeline": sum(stage_totals[st] for st in stages if st not in ("CLOSED_WON", "CLOSED_LOST"))
        }

    @staticmethod
    def update_opportunity_stage(
        opp_id: str,
        new_stage: str,
        loss_reason: Optional[str],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        existing = query("opportunities").where_eq("id", opp_id).first()
        if not existing:
            raise ValueError("Opportunity not found")

        new_stage = new_stage.upper()
        old_stage = existing["stage"]
        new_prob = STAGE_PROBABILITY_MAP.get(new_stage, existing["win_probability"])

        update_data = {
            "stage": new_stage,
            "win_probability": new_prob
        }

        if new_stage == "CLOSED_WON":
            update_data["actual_close_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            update_data["loss_reason"] = None
        elif new_stage == "CLOSED_LOST":
            update_data["actual_close_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            update_data["loss_reason"] = loss_reason or "Competitor / Budget constraints"

        query("opportunities").where_eq("id", opp_id).update(update_data)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="UPDATE_STAGE",
            entity_type="OPPORTUNITY",
            entity_id=opp_id,
            change_summary=f"Changed Opportunity Stage from '{old_stage}' to '{new_stage}' (Probability: {new_prob}%)"
        )

        return OpportunityService.get_opportunity(opp_id)

    @staticmethod
    def update_opportunity(opp_id: str, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("opportunities").where_eq("id", opp_id).first()
        if not existing:
            raise ValueError("Opportunity not found")

        update_fields = {}
        for key in ["account_id", "contact_id", "name", "stage", "amount", "win_probability", "expected_close_date", "loss_reason", "owner_id"]:
            if key in data:
                update_fields[key] = data[key]

        if "stage" in update_fields and "win_probability" not in update_fields:
            update_fields["win_probability"] = STAGE_PROBABILITY_MAP.get(update_fields["stage"].upper(), existing["win_probability"])

        query("opportunities").where_eq("id", opp_id).update(update_fields)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="UPDATE",
            entity_type="OPPORTUNITY",
            entity_id=opp_id,
            change_summary=f"Updated Opportunity fields: {list(update_fields.keys())}"
        )

        return OpportunityService.get_opportunity(opp_id)

    @staticmethod
    def delete_opportunity(opp_id: str, current_user: Dict[str, Any]):
        existing = query("opportunities").where_eq("id", opp_id).first()
        if not existing:
            raise ValueError("Opportunity not found")

        query("opportunities").where_eq("id", opp_id).delete()

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="DELETE",
            entity_type="OPPORTUNITY",
            entity_id=opp_id,
            change_summary=f"Deleted Opportunity '{existing['name']}'"
        )
