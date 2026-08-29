"""
CRM System - Roles, Permissions, and Access Control Definitions
Standardized for Enterprise Operations
"""

from enum import Enum
from typing import Set, Dict, List


class UserRole(str, Enum):
    ADMIN = "Admin"
    SALES_MANAGER = "Sales Manager"
    SALES_REPRESENTATIVE = "Sales Representative"
    SUPPORT_AGENT = "Support Agent"
    MARKETING_EXECUTIVE = "Marketing Executive"


class Permission(str, Enum):
    # Accounts & Customer Management
    ACCOUNT_VIEW = "account:view"
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_EDIT = "account:edit"
    ACCOUNT_DELETE = "account:delete"
    ACCOUNT_DEACTIVATE = "account:deactivate"
    ACCOUNT_EXPORT = "account:export"
    ACCOUNT_NOTES = "account:notes"
    ACCOUNT_ATTACHMENTS = "account:attachments"

    # Contacts
    CONTACT_VIEW = "contact:view"
    CONTACT_CREATE = "contact:create"
    CONTACT_EDIT = "contact:edit"
    CONTACT_DELETE = "contact:delete"

    # Leads & Opportunities
    LEAD_VIEW = "lead:view"
    LEAD_CREATE = "lead:create"
    LEAD_EDIT = "lead:edit"
    LEAD_DELETE = "lead:delete"
    LEAD_CONVERT = "lead:convert"

    OPPORTUNITY_VIEW = "opportunity:view"
    OPPORTUNITY_CREATE = "opportunity:create"
    OPPORTUNITY_EDIT = "opportunity:edit"
    OPPORTUNITY_DELETE = "opportunity:delete"
    OPPORTUNITY_CLOSE = "opportunity:close"

    # Support / Tickets
    TICKET_VIEW = "ticket:view"
    TICKET_CREATE = "ticket:create"
    TICKET_EDIT = "ticket:edit"
    TICKET_RESOLVE = "ticket:resolve"
    TICKET_DELETE = "ticket:delete"
    SLA_MANAGE = "sla:manage"

    # Marketing
    CAMPAIGN_VIEW = "campaign:view"
    CAMPAIGN_CREATE = "campaign:create"
    CAMPAIGN_EDIT = "campaign:edit"
    CAMPAIGN_DELETE = "campaign:delete"
    SEGMENT_MANAGE = "segment:manage"

    # Activities & Calendar
    ACTIVITY_VIEW = "activity:view"
    ACTIVITY_CREATE = "activity:create"
    ACTIVITY_EDIT = "activity:edit"
    ACTIVITY_DELETE = "activity:delete"

    # Analytics & Reports
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"
    CUSTOM_REPORT_BUILD = "analytics:custom_report"

    # Administration & Audit
    USER_MANAGE = "admin:users"
    SYSTEM_SETTINGS = "admin:settings"
    AUDIT_LOG_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"


ROLE_PERMISSIONS_MAP: Dict[UserRole, Set[Permission]] = {
    # 1. Admin - Full Privileges
    UserRole.ADMIN: set(Permission),

    # 2. Sales Manager - Pipeline, Customer 360, Analytics, Team Management
    UserRole.SALES_MANAGER: {
        Permission.ACCOUNT_VIEW, Permission.ACCOUNT_CREATE, Permission.ACCOUNT_EDIT, 
        Permission.ACCOUNT_DEACTIVATE, Permission.ACCOUNT_EXPORT, Permission.ACCOUNT_NOTES, Permission.ACCOUNT_ATTACHMENTS,
        Permission.CONTACT_VIEW, Permission.CONTACT_CREATE, Permission.CONTACT_EDIT, Permission.CONTACT_DELETE,
        Permission.LEAD_VIEW, Permission.LEAD_CREATE, Permission.LEAD_EDIT, Permission.LEAD_DELETE, Permission.LEAD_CONVERT,
        Permission.OPPORTUNITY_VIEW, Permission.OPPORTUNITY_CREATE, Permission.OPPORTUNITY_EDIT, Permission.OPPORTUNITY_DELETE, Permission.OPPORTUNITY_CLOSE,
        Permission.ACTIVITY_VIEW, Permission.ACTIVITY_CREATE, Permission.ACTIVITY_EDIT, Permission.ACTIVITY_DELETE,
        Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT, Permission.CUSTOM_REPORT_BUILD,
        Permission.AUDIT_LOG_VIEW,
    },

    # 3. Sales Representative - Accounts, Contacts, Leads, Deals, Activities
    UserRole.SALES_REPRESENTATIVE: {
        Permission.ACCOUNT_VIEW, Permission.ACCOUNT_CREATE, Permission.ACCOUNT_EDIT, Permission.ACCOUNT_NOTES, Permission.ACCOUNT_ATTACHMENTS,
        Permission.CONTACT_VIEW, Permission.CONTACT_CREATE, Permission.CONTACT_EDIT,
        Permission.LEAD_VIEW, Permission.LEAD_CREATE, Permission.LEAD_EDIT, Permission.LEAD_CONVERT,
        Permission.OPPORTUNITY_VIEW, Permission.OPPORTUNITY_CREATE, Permission.OPPORTUNITY_EDIT, Permission.OPPORTUNITY_CLOSE,
        Permission.ACTIVITY_VIEW, Permission.ACTIVITY_CREATE, Permission.ACTIVITY_EDIT,
        Permission.ANALYTICS_VIEW,
    },

    # 4. Support Agent - Customer Support, Tickets, SLA tracking, Customer Notes
    UserRole.SUPPORT_AGENT: {
        Permission.ACCOUNT_VIEW, Permission.ACCOUNT_NOTES, Permission.ACCOUNT_ATTACHMENTS,
        Permission.CONTACT_VIEW,
        Permission.TICKET_VIEW, Permission.TICKET_CREATE, Permission.TICKET_EDIT, Permission.TICKET_RESOLVE,
        Permission.ACTIVITY_VIEW, Permission.ACTIVITY_CREATE, Permission.ACTIVITY_EDIT,
        Permission.ANALYTICS_VIEW,
    },

    # 5. Marketing Executive - Lead Generation, Campaigns, Segments, Analytics
    UserRole.MARKETING_EXECUTIVE: {
        Permission.ACCOUNT_VIEW, Permission.CONTACT_VIEW,
        Permission.LEAD_VIEW, Permission.LEAD_CREATE, Permission.LEAD_EDIT,
        Permission.CAMPAIGN_VIEW, Permission.CAMPAIGN_CREATE, Permission.CAMPAIGN_EDIT, Permission.CAMPAIGN_DELETE,
        Permission.SEGMENT_MANAGE,
        Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT,
    }
}


def normalize_role(role_str: str) -> UserRole:
    """Normalize input string to standard UserRole enum."""
    if not role_str:
        return UserRole.SALES_REPRESENTATIVE

    cleaned = role_str.strip().replace("_", " ").lower()
    mapping = {
        "admin": UserRole.ADMIN,
        "super admin": UserRole.ADMIN,
        "super_admin": UserRole.ADMIN,
        "sales manager": UserRole.SALES_MANAGER,
        "sales_manager": UserRole.SALES_MANAGER,
        "sales director": UserRole.SALES_MANAGER,
        "sales representative": UserRole.SALES_REPRESENTATIVE,
        "sales_representative": UserRole.SALES_REPRESENTATIVE,
        "sales rep": UserRole.SALES_REPRESENTATIVE,
        "sales_rep": UserRole.SALES_REPRESENTATIVE,
        "support agent": UserRole.SUPPORT_AGENT,
        "support_agent": UserRole.SUPPORT_AGENT,
        "support lead": UserRole.SUPPORT_AGENT,
        "marketing executive": UserRole.MARKETING_EXECUTIVE,
        "marketing_executive": UserRole.MARKETING_EXECUTIVE,
        "marketing manager": UserRole.MARKETING_EXECUTIVE,
        "marketing_manager": UserRole.MARKETING_EXECUTIVE
    }
    return mapping.get(cleaned, UserRole.SALES_REPRESENTATIVE)


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a given role has the requested permission."""
    perms = ROLE_PERMISSIONS_MAP.get(role, set())
    return permission in perms


def get_permissions_for_role(role: UserRole) -> List[str]:
    """Get list of string permission codes for a role."""
    return [p.value for p in ROLE_PERMISSIONS_MAP.get(role, set())]
