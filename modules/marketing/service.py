"""
CRM System - Marketing Campaigns & Lead Generation Service
"""

import uuid
from typing import Dict, Any, List, Optional
from core.database.query_builder import query
from modules.audit.service import AuditService


class CampaignService:
    @staticmethod
    def create_campaign(data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        campaign_id = "cmp_" + str(uuid.uuid4())[:12]
        
        record = {
            "id": campaign_id,
            "name": data["name"],
            "type": data.get("type", "EMAIL").upper(),
            "status": data.get("status", "PLANNING").upper(),
            "budget": float(data.get("budget", 0.0)),
            "actual_cost": float(data.get("actual_cost", 0.0)),
            "target_audience": data.get("target_audience", "All Active Accounts"),
            "sent_count": int(data.get("sent_count", 0)),
            "open_count": int(data.get("open_count", 0)),
            "click_count": int(data.get("click_count", 0)),
            "conversion_count": int(data.get("conversion_count", 0)),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date")
        }

        query("campaigns").insert(record)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="CREATE",
            entity_type="CAMPAIGN",
            entity_id=campaign_id,
            change_summary=f"Created {record['type']} Campaign '{record['name']}'"
        )

        return record

    @staticmethod
    def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
        campaign = query("campaigns").where_eq("id", campaign_id).first()
        if not campaign:
            return None

        # Compute calculated performance KPIs
        sent = campaign.get("sent_count") or 0
        opens = campaign.get("open_count") or 0
        clicks = campaign.get("click_count") or 0
        conversions = campaign.get("conversion_count") or 0
        actual_cost = float(campaign.get("actual_cost") or 0.0)

        campaign["open_rate_pct"] = round((opens / sent * 100), 2) if sent > 0 else 0.0
        campaign["click_through_pct"] = round((clicks / sent * 100), 2) if sent > 0 else 0.0
        campaign["conversion_rate_pct"] = round((conversions / sent * 100), 2) if sent > 0 else 0.0
        campaign["cost_per_conversion"] = round(actual_cost / conversions, 2) if conversions > 0 else 0.0

        return campaign

    @staticmethod
    def list_campaigns(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        total = query("campaigns").count()
        records = query("campaigns").order_by("created_at", "DESC").limit(limit).offset(offset).get()
        
        for r in records:
            sent = r.get("sent_count") or 0
            opens = r.get("open_count") or 0
            clicks = r.get("click_count") or 0
            r["open_rate_pct"] = round((opens / sent * 100), 1) if sent > 0 else 0.0
            r["click_through_pct"] = round((clicks / sent * 100), 1) if sent > 0 else 0.0

        return {
            "total": total,
            "items": records,
            "limit": limit,
            "offset": offset
        }

    @staticmethod
    def update_campaign(campaign_id: str, data: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        existing = query("campaigns").where_eq("id", campaign_id).first()
        if not existing:
            raise ValueError("Campaign not found")

        update_fields = {}
        for key in ["name", "type", "status", "budget", "actual_cost", "target_audience", "sent_count", "open_count", "click_count", "conversion_count", "start_date", "end_date"]:
            if key in data:
                update_fields[key] = data[key]

        query("campaigns").where_eq("id", campaign_id).update(update_fields)

        AuditService.record(
            user_id=current_user.get("sub"),
            user_email=current_user.get("email"),
            action="UPDATE",
            entity_type="CAMPAIGN",
            entity_id=campaign_id,
            change_summary=f"Updated Campaign fields: {list(update_fields.keys())}"
        )

        return CampaignService.get_campaign(campaign_id)
