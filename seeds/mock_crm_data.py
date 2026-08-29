"""
CRM System - Enterprise Seed Data Generator
Populates realistic, sanitized dummy data for testing and demonstration
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.database.migrations import run_migrations
from core.database.connection import DB
from modules.auth.service import AuthService
from modules.accounts.service import AccountService
from modules.contacts.service import ContactService
from modules.leads.service import LeadService
from modules.opportunities.service import OpportunityService
from modules.tickets.service import TicketService
from modules.marketing.service import CampaignService
from modules.activities.service import ActivityService
from config.permissions import UserRole


def seed_database():
    print("Running schema migrations...")
    run_migrations()

    # Clear existing tables for fresh seed
    for table in ["customer_notes", "customer_attachments", "password_reset_tokens", "audit_logs", "activities", "ticket_comments", "tickets", "campaigns", "opportunities", "leads", "contacts", "accounts", "users"]:
        try:
            DB.execute(f"DELETE FROM {table}")
        except Exception:
            pass

    print("Seeding Standard 5 Users & Roles...")
    admin = AuthService.register_user(
        email="admin@omnicrm.com",
        password="Password123!",
        full_name="Alex Morgan",
        role=UserRole.ADMIN.value
    )
    admin_ctx = {"sub": admin["id"], "email": admin["email"]}

    manager = AuthService.register_user(
        email="manager@omnicrm.com",
        password="Password123!",
        full_name="Sarah Jenkins",
        role=UserRole.SALES_MANAGER.value
    )
    manager_ctx = {"sub": manager["id"], "email": manager["email"]}

    rep = AuthService.register_user(
        email="rep@omnicrm.com",
        password="Password123!",
        full_name="David Chen",
        role=UserRole.SALES_REPRESENTATIVE.value
    )
    rep_ctx = {"sub": rep["id"], "email": rep["email"]}

    support = AuthService.register_user(
        email="support@omnicrm.com",
        password="Password123!",
        full_name="Elena Rostova",
        role=UserRole.SUPPORT_AGENT.value
    )
    support_ctx = {"sub": support["id"], "email": support["email"]}

    mkt = AuthService.register_user(
        email="marketing@omnicrm.com",
        password="Password123!",
        full_name="Marcus Vance",
        role=UserRole.MARKETING_EXECUTIVE.value
    )

    print("Seeding Accounts (Customers & Organizations)...")
    acc1 = AccountService.create_account({
        "name": "GlobalTech Dynamics",
        "industry": "Enterprise Software",
        "annual_revenue": 14500000.0,
        "employee_count": 450,
        "phone": "+1-555-0199",
        "website": "https://globaltech.example.com",
        "address_street": "100 Market St, Suite 400",
        "address_city": "San Francisco",
        "address_state": "CA",
        "address_country": "USA",
        "tier": "ENTERPRISE",
        "status": "ACTIVE",
        "owner_id": rep["id"]
    }, admin_ctx)

    acc2 = AccountService.create_account({
        "name": "Acme Retail Chain",
        "industry": "Retail & E-Commerce",
        "annual_revenue": 8200000.0,
        "employee_count": 280,
        "phone": "+1-555-0142",
        "website": "https://acmeretail.example.com",
        "address_street": "500 Michigan Ave",
        "address_city": "Chicago",
        "address_state": "IL",
        "address_country": "USA",
        "tier": "PREMIUM",
        "status": "ACTIVE",
        "owner_id": rep["id"]
    }, admin_ctx)

    acc3 = AccountService.create_account({
        "name": "Horizon Financial Group",
        "industry": "Financial Services & Banking",
        "annual_revenue": 28000000.0,
        "employee_count": 1200,
        "phone": "+1-555-0188",
        "website": "https://horizonfin.example.com",
        "address_street": "200 Wall St, 24th Fl",
        "address_city": "New York",
        "address_state": "NY",
        "address_country": "USA",
        "tier": "STRATEGIC",
        "status": "ACTIVE",
        "owner_id": manager["id"]
    }, admin_ctx)

    acc4 = AccountService.create_account({
        "name": "Nova Healthcare Systems",
        "industry": "Healthcare & Biotech",
        "annual_revenue": 5600000.0,
        "employee_count": 160,
        "phone": "+1-555-0177",
        "website": "https://novahealth.example.com",
        "address_street": "75 Cambridge Pkwy",
        "address_city": "Boston",
        "address_state": "MA",
        "address_country": "USA",
        "tier": "STANDARD",
        "status": "ACTIVE",
        "owner_id": rep["id"]
    }, admin_ctx)

    print("Seeding Customer Notes & Attachments...")
    AccountService.add_customer_note(
        acc1["id"],
        "Met with VP of Technology. Highly satisfied with API uptime. Exploring 500-seat expansion next quarter.",
        manager_ctx
    )
    AccountService.add_customer_note(
        acc1["id"],
        "Customer requested custom billing cycle to align with their Q3 fiscal calendar.",
        rep_ctx
    )
    AccountService.add_customer_attachment(
        acc1["id"],
        "GlobalTech_Master_Service_Agreement_2026.pdf",
        345000,
        "PDF Document",
        "/storage/contracts/GlobalTech_MSA_2026.pdf",
        admin_ctx
    )

    AccountService.add_customer_note(
        acc2["id"],
        "Executive steering committee finalized procurement requirements for retail store expansion.",
        rep_ctx
    )
    AccountService.add_customer_attachment(
        acc2["id"],
        "Acme_PointOfSale_Specification_v2.docx",
        182000,
        "DOCX Document",
        "/storage/rfp/Acme_POS_v2.docx",
        rep_ctx
    )

    print("Seeding Contacts...")
    c1 = ContactService.create_contact({
        "account_id": acc1["id"],
        "first_name": "Jonathan",
        "last_name": "Wright",
        "email": "jwright@globaltech.example.com",
        "phone": "+1-555-1101",
        "job_title": "VP of Technology",
        "department": "Engineering",
        "is_primary": True
    }, admin_ctx)

    c2 = ContactService.create_contact({
        "account_id": acc1["id"],
        "first_name": "Claire",
        "last_name": "Dunphy",
        "email": "cdunphy@globaltech.example.com",
        "phone": "+1-555-1102",
        "job_title": "Director of Procurement",
        "department": "Operations",
        "is_primary": False
    }, admin_ctx)

    c3 = ContactService.create_contact({
        "account_id": acc2["id"],
        "first_name": "Samantha",
        "last_name": "Miller",
        "email": "smiller@acmeretail.example.com",
        "phone": "+1-555-1103",
        "job_title": "Chief Information Officer",
        "department": "Executive",
        "is_primary": True
    }, admin_ctx)

    c4 = ContactService.create_contact({
        "account_id": acc3["id"],
        "first_name": "Arthur",
        "last_name": "Pendleton",
        "email": "apendleton@horizonfin.example.com",
        "phone": "+1-555-1104",
        "job_title": "Managing Director",
        "department": "Wealth Management",
        "is_primary": True
    }, admin_ctx)

    print("Seeding Leads & Calculations...")
    l1 = LeadService.create_lead({
        "first_name": "Robert",
        "last_name": "Sterling",
        "company_name": "Sterling Logistics Inc",
        "email": "rsterling@sterlinglogistics.example.com",
        "phone": "+1-555-3344",
        "lead_source": "DEMO_REQUEST",
        "estimated_value": 75000.0,
        "status": "QUALIFIED",
        "assigned_to_id": rep["id"]
    }, admin_ctx)

    l2 = LeadService.create_lead({
        "first_name": "Jessica",
        "last_name": "Alba",
        "company_name": "CloudNine Networks",
        "email": "jessica@cloudnine.example.com",
        "phone": "+1-555-3355",
        "lead_source": "REFERRAL",
        "estimated_value": 120000.0,
        "status": "NEW",
        "assigned_to_id": rep["id"]
    }, admin_ctx)

    print("Seeding Opportunities & Kanban Pipeline...")
    OpportunityService.create_opportunity({
        "account_id": acc1["id"],
        "contact_id": c1["id"],
        "name": "GlobalTech Cloud Migration Suite",
        "stage": "PROPOSAL",
        "amount": 95000.0,
        "win_probability": 60,
        "expected_close_date": "2026-10-15",
        "owner_id": rep["id"]
    }, rep_ctx)

    OpportunityService.create_opportunity({
        "account_id": acc2["id"],
        "contact_id": c3["id"],
        "name": "Acme Omnichannel Point-of-Sale Expansion",
        "stage": "NEGOTIATION",
        "amount": 140000.0,
        "win_probability": 80,
        "expected_close_date": "2026-09-30",
        "owner_id": rep["id"]
    }, rep_ctx)

    OpportunityService.create_opportunity({
        "account_id": acc3["id"],
        "contact_id": c4["id"],
        "name": "Horizon Wealth Management Security Vault",
        "stage": "CLOSED_WON",
        "amount": 350000.0,
        "win_probability": 100,
        "expected_close_date": "2026-08-20",
        "owner_id": manager["id"]
    }, manager_ctx)

    print("Seeding Helpdesk Tickets & SLAs...")
    t1 = TicketService.create_ticket({
        "account_id": acc1["id"],
        "contact_id": c1["id"],
        "title": "API Rate Limit Optimization for Realtime Feeds",
        "description": "Customer experiencing HTTP 429 throttling during peak data synchronization intervals.",
        "priority": "HIGH",
        "category": "TECHNICAL",
        "assigned_agent_id": support["id"]
    }, support_ctx)

    TicketService.add_comment(
        ticket_id=t1["id"],
        comment_text="Inspected traffic graph. Allocated temporary quota increase.",
        is_internal=True,
        current_user=support_ctx
    )

    t2 = TicketService.create_ticket({
        "account_id": acc2["id"],
        "contact_id": c3["id"],
        "title": "Billing reconciliation for Q2 invoice #9822",
        "description": "Requested breakdown of multi-seat licensing discount.",
        "priority": "MEDIUM",
        "category": "BILLING",
        "assigned_agent_id": support["id"]
    }, support_ctx)

    print("Seeding Marketing Campaigns...")
    CampaignService.create_campaign({
        "name": "Q3 Enterprise Tech Summit & Product Launch",
        "type": "EVENT",
        "status": "ACTIVE",
        "budget": 25000.0,
        "actual_cost": 18500.0,
        "target_audience": "VP & C-Suite Technology Executives",
        "sent_count": 4200,
        "open_count": 1850,
        "click_count": 720,
        "conversion_count": 64,
        "start_date": "2026-07-01",
        "end_date": "2026-09-30"
    }, admin_ctx)

    print("Seeding Activities & Tasks...")
    ActivityService.create_activity({
        "activity_type": "MEETING",
        "subject": "Executive Review & Contract Finalization",
        "description": "Review final redline agreement with Acme Retail steering committee.",
        "due_date": "2026-09-02 14:00:00",
        "priority": "HIGH",
        "related_to_type": "ACCOUNT",
        "related_to_id": acc2["id"],
        "assigned_to_id": rep["id"]
    }, rep_ctx)

    ActivityService.create_activity({
        "activity_type": "CALL",
        "subject": "Follow-up discovery call regarding API limits",
        "description": "Verify that rate limit adjustments resolved throughput issues.",
        "due_date": "2026-09-01 10:30:00",
        "priority": "MEDIUM",
        "related_to_type": "ACCOUNT",
        "related_to_id": acc1["id"],
        "assigned_to_id": support["id"]
    }, support_ctx)

    print("[SUCCESS] Database seeding completed successfully with 5 exact enterprise roles!")
    print("Default demo accounts created:")
    print(" - Admin: admin@omnicrm.com / Password123! (Role: Admin)")
    print(" - Sales Manager: manager@omnicrm.com / Password123! (Role: Sales Manager)")
    print(" - Sales Representative: rep@omnicrm.com / Password123! (Role: Sales Representative)")
    print(" - Support Agent: support@omnicrm.com / Password123! (Role: Support Agent)")
    print(" - Marketing Executive: marketing@omnicrm.com / Password123! (Role: Marketing Executive)")


if __name__ == "__main__":
    seed_database()
