"""
CRM System - Helpdesk SLA & Escalation Engine
Calculates response and resolution windows based on ticket priority
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Tuple


SLA_HOURS_MATRIX = {
    "URGENT": {"response_hours": 1, "resolution_hours": 6},
    "HIGH": {"response_hours": 2, "resolution_hours": 12},
    "MEDIUM": {"response_hours": 4, "resolution_hours": 24},
    "LOW": {"response_hours": 8, "resolution_hours": 48}
}


def calculate_sla_deadlines(priority: str, start_time: datetime = None) -> Tuple[str, str]:
    """Calculate ISO timestamps for SLA response and resolution deadlines."""
    if start_time is None:
        start_time = datetime.now(timezone.utc)

    p = priority.upper()
    config = SLA_HOURS_MATRIX.get(p, SLA_HOURS_MATRIX["MEDIUM"])

    response_dt = start_time + timedelta(hours=config["response_hours"])
    resolution_dt = start_time + timedelta(hours=config["resolution_hours"])

    return response_dt.strftime("%Y-%m-%d %H:%M:%S"), resolution_dt.strftime("%Y-%m-%d %H:%M:%S")


def check_sla_breach(ticket: Dict[str, Any]) -> Tuple[bool, bool]:
    """
    Evaluates whether response or resolution deadlines have been breached.
    Returns (response_breached, resolution_breached).
    """
    now = datetime.now(timezone.utc)
    resp_breached = False
    resol_breached = False

    resp_deadline_str = ticket.get("sla_response_deadline")
    resol_deadline_str = ticket.get("sla_resolution_deadline")

    if resp_deadline_str and ticket.get("status") == "OPEN":
        resp_dt = datetime.strptime(resp_deadline_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if now > resp_dt:
            resp_breached = True

    if resol_deadline_str and ticket.get("status") not in ("RESOLVED", "CLOSED"):
        resol_dt = datetime.strptime(resol_deadline_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        if now > resol_dt:
            resol_breached = True

    return resp_breached, resol_breached
