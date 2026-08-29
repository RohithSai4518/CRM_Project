"""
OmniFlow CRM - Main Enterprise Application Server
Zero external web framework dependencies
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.http.server import CRMServer
from core.http.request import Request
from core.http.response import Response
from core.database.migrations import run_migrations
from seeds.mock_crm_data import seed_database
from config.app_config import CONFIG

# Import Module Controllers
from modules.auth.controller import AuthController
from modules.accounts.controller import AccountController
from modules.contacts.controller import ContactController
from modules.leads.controller import LeadController
from modules.opportunities.controller import OpportunityController
from modules.tickets.controller import TicketController
from modules.marketing.controller import MarketingController
from modules.activities.controller import ActivityController
from modules.analytics.controller import AnalyticsController
from modules.audit.controller import AuditController


def create_crm_app() -> CRMServer:
    # 1. Run migrations to ensure DB schema is ready
    run_migrations()

    server = CRMServer(host=CONFIG.server.host, port=CONFIG.server.port)
    r = server.router

    # -------------------------------------------------------------
    # Web UI Template Routes
    # -------------------------------------------------------------
    def render_index(req: Request) -> Response:
        template_file = os.path.join(CONFIG.server.template_dir, "index.html")
        if os.path.exists(template_file):
            with open(template_file, "r", encoding="utf-8") as f:
                html = f.read()
            return Response.html(html)
        return Response.not_found("Template file index.html not found")

    r.get("/", render_index)
    r.get("/index.html", render_index)

    # -------------------------------------------------------------
    # 1. Authentication & User Management Routes
    # -------------------------------------------------------------
    r.post("/api/auth/register", AuthController.register)
    r.post("/api/auth/login", AuthController.login)
    r.post("/api/auth/forgot-password", AuthController.forgot_password)
    r.post("/api/auth/reset-password", AuthController.reset_password)
    r.get("/api/auth/me", AuthController.me)
    r.get("/api/auth/users", AuthController.list_users)
    r.post("/api/auth/users/:id/role", AuthController.update_role)
    r.post("/api/auth/users/:id/status", AuthController.toggle_status)

    # -------------------------------------------------------------
    # 2. Accounts (Customers & Organizations) Routes
    # -------------------------------------------------------------
    r.get("/api/accounts", AccountController.list)
    r.post("/api/accounts", AccountController.create)
    r.get("/api/accounts/:id", AccountController.get)
    r.put("/api/accounts/:id", AccountController.update)
    r.post("/api/accounts/:id/notes", AccountController.add_note)
    r.post("/api/accounts/:id/attachments", AccountController.add_attachment)
    r.post("/api/accounts/:id/status", AccountController.set_status)
    r.delete("/api/accounts/:id", AccountController.delete)

    # -------------------------------------------------------------
    # 3. Contacts Routes
    # -------------------------------------------------------------
    r.get("/api/contacts", ContactController.list)
    r.post("/api/contacts", ContactController.create)
    r.get("/api/contacts/:id", ContactController.get)
    r.put("/api/contacts/:id", ContactController.update)
    r.delete("/api/contacts/:id", ContactController.delete)

    # -------------------------------------------------------------
    # 4. Inbound Leads Routes
    # -------------------------------------------------------------
    r.get("/api/leads", LeadController.list)
    r.post("/api/leads", LeadController.create)
    r.get("/api/leads/:id", LeadController.get)
    r.put("/api/leads/:id", LeadController.update)
    r.post("/api/leads/:id/convert", LeadController.convert)
    r.delete("/api/leads/:id", LeadController.delete)

    # -------------------------------------------------------------
    # 5. Opportunities & Kanban Pipeline Routes
    # -------------------------------------------------------------
    r.get("/api/opportunities", OpportunityController.list)
    r.get("/api/opportunities/kanban", OpportunityController.kanban)
    r.post("/api/opportunities", OpportunityController.create)
    r.get("/api/opportunities/:id", OpportunityController.get)
    r.put("/api/opportunities/:id", OpportunityController.update)
    r.post("/api/opportunities/:id/stage", OpportunityController.set_stage)
    r.delete("/api/opportunities/:id", OpportunityController.delete)

    # -------------------------------------------------------------
    # 6. Customer Support & Tickets Routes
    # -------------------------------------------------------------
    r.get("/api/tickets", TicketController.list)
    r.post("/api/tickets", TicketController.create)
    r.get("/api/tickets/:id", TicketController.get)
    r.put("/api/tickets/:id", TicketController.update)
    r.post("/api/tickets/:id/comments", TicketController.add_comment)

    # -------------------------------------------------------------
    # 7. Marketing Campaigns Routes
    # -------------------------------------------------------------
    r.get("/api/campaigns", MarketingController.list)
    r.post("/api/campaigns", MarketingController.create)
    r.get("/api/campaigns/:id", MarketingController.get)
    r.put("/api/campaigns/:id", MarketingController.update)

    # -------------------------------------------------------------
    # 8. Activities, Tasks & Calendar Routes
    # -------------------------------------------------------------
    r.get("/api/activities", ActivityController.list)
    r.post("/api/activities", ActivityController.create)
    r.post("/api/activities/:id/status", ActivityController.set_status)

    # -------------------------------------------------------------
    # 9. Executive Analytics & BI Routes
    # -------------------------------------------------------------
    r.get("/api/analytics/summary", AnalyticsController.executive_summary)
    r.get("/api/analytics/pipeline-by-stage", AnalyticsController.pipeline_by_stage)
    r.get("/api/analytics/leads-by-source", AnalyticsController.leads_by_source)

    # -------------------------------------------------------------
    # 10. Audit & Compliance Vault Routes
    # -------------------------------------------------------------
    r.get("/api/audit", AuditController.list_logs)

    return server


if __name__ == "__main__":
    if not os.path.exists(CONFIG.database.db_path):
        print("Database not found. Generating initial seed dataset...")
        seed_database()

    app = create_crm_app()
    app.start()
