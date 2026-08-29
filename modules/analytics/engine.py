"""
CRM System - Business Intelligence & Executive Analytics Engine
Calculates Pipeline Velocity, Conversion Rates, Revenue attribution, and CSAT scores
"""

from typing import Dict, Any, List
from core.database.connection import DB
from core.database.query_builder import query


class AnalyticsEngine:
    @staticmethod
    def get_executive_summary() -> Dict[str, Any]:
        """Calculates top-level KPI metrics across the entire CRM."""
        # 1. Accounts Count & Revenue
        acc_stats = DB.fetch_one("""
            SELECT 
                COUNT(*) as total_accounts,
                COALESCE(SUM(annual_revenue), 0) as total_portfolio_revenue
            FROM accounts
            WHERE status = 'ACTIVE'
        """)

        # 2. Leads Metrics
        lead_stats = DB.fetch_one("""
            SELECT 
                COUNT(*) as total_leads,
                SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) as converted_leads,
                AVG(lead_score) as avg_lead_score
            FROM leads
        """)

        total_leads = lead_stats["total_leads"] if lead_stats else 0
        converted_leads = lead_stats["converted_leads"] if lead_stats else 0
        lead_conversion_rate = round((converted_leads / total_leads * 100), 1) if total_leads > 0 else 0.0

        # 3. Opportunities & Pipeline
        opp_stats = DB.fetch_one("""
            SELECT 
                COUNT(*) as total_deals,
                SUM(CASE WHEN stage = 'CLOSED_WON' THEN 1 ELSE 0 END) as won_deals,
                SUM(CASE WHEN stage = 'CLOSED_LOST' THEN 1 ELSE 0 END) as lost_deals,
                COALESCE(SUM(CASE WHEN stage = 'CLOSED_WON' THEN amount ELSE 0 END), 0) as closed_won_revenue,
                COALESCE(SUM(CASE WHEN stage NOT IN ('CLOSED_WON', 'CLOSED_LOST') THEN amount ELSE 0 END), 0) as active_pipeline_value,
                COALESCE(SUM(CASE WHEN stage NOT IN ('CLOSED_WON', 'CLOSED_LOST') THEN (amount * win_probability / 100.0) ELSE 0 END), 0) as weighted_pipeline_value
            FROM opportunities
        """)

        total_closed = (opp_stats["won_deals"] or 0) + (opp_stats["lost_deals"] or 0)
        win_rate = round((opp_stats["won_deals"] / total_closed * 100), 1) if total_closed > 0 else 0.0

        # 4. Support Ticket & SLA Stats
        ticket_stats = DB.fetch_one("""
            SELECT 
                COUNT(*) as total_tickets,
                SUM(CASE WHEN status IN ('RESOLVED', 'CLOSED') THEN 1 ELSE 0 END) as resolved_tickets,
                SUM(CASE WHEN sla_resolution_breached = 1 THEN 1 ELSE 0 END) as sla_breached_count,
                AVG(csat_score) as avg_csat
            FROM tickets
        """)

        # 5. Marketing Stats
        mkt_stats = DB.fetch_one("""
            SELECT 
                COUNT(*) as active_campaigns,
                COALESCE(SUM(budget), 0) as total_budget,
                COALESCE(SUM(conversion_count), 0) as total_conversions
            FROM campaigns
        """)

        return {
            "accounts": {
                "active_count": acc_stats["total_accounts"] if acc_stats else 0,
                "total_portfolio_revenue": acc_stats["total_portfolio_revenue"] if acc_stats else 0.0
            },
            "leads": {
                "total": total_leads,
                "converted": converted_leads,
                "conversion_rate_pct": lead_conversion_rate,
                "avg_score": round(lead_stats["avg_lead_score"] or 0.0, 1) if lead_stats else 0.0
            },
            "pipeline": {
                "total_deals": opp_stats["total_deals"] if opp_stats else 0,
                "active_pipeline_value": opp_stats["active_pipeline_value"] if opp_stats else 0.0,
                "weighted_pipeline_value": opp_stats["weighted_pipeline_value"] if opp_stats else 0.0,
                "closed_won_revenue": opp_stats["closed_won_revenue"] if opp_stats else 0.0,
                "win_rate_pct": win_rate
            },
            "support": {
                "total_tickets": ticket_stats["total_tickets"] if ticket_stats else 0,
                "resolved_tickets": ticket_stats["resolved_tickets"] if ticket_stats else 0,
                "sla_breach_count": ticket_stats["sla_breached_count"] if ticket_stats else 0,
                "avg_csat_score": round(ticket_stats["avg_csat"] or 4.8, 1) if ticket_stats else 5.0
            },
            "marketing": {
                "campaigns_count": mkt_stats["active_campaigns"] if mkt_stats else 0,
                "total_budget": mkt_stats["total_budget"] if mkt_stats else 0.0,
                "total_conversions": mkt_stats["total_conversions"] if mkt_stats else 0
            }
        }

    @staticmethod
    def get_pipeline_by_stage() -> List[Dict[str, Any]]:
        """Returns deal count and revenue aggregate grouped by stage."""
        sql = """
            SELECT 
                stage, 
                COUNT(*) as count, 
                COALESCE(SUM(amount), 0) as total_amount,
                AVG(win_probability) as avg_prob
            FROM opportunities
            GROUP BY stage
        """
        return DB.fetch_all(sql)

    @staticmethod
    def get_leads_by_source() -> List[Dict[str, Any]]:
        """Returns lead source breakdown."""
        sql = """
            SELECT 
                lead_source, 
                COUNT(*) as count,
                AVG(lead_score) as avg_score,
                SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) as converted_count
            FROM leads
            GROUP BY lead_source
            ORDER BY count DESC
        """
        return DB.fetch_all(sql)
