"""
CRM System - Multi-Tenant Organization Isolation & Metamodel Engine
Enterprise Data Partitioning, Custom Fields, Feature Flags, and Tenant Quotas
"""

import uuid
import json
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from core.database.query_builder import query
from core.database.connection import DB
from modules.audit.service import AuditService


class TenantMetamodel:
    """
    Dynamic schema extension and custom fields registry for multi-tenant isolation.
    Enables enterprise clients to define dynamic fields on Accounts, Contacts, Leads, and Deals.
    """
    FIELD_TYPES = {"STRING", "NUMBER", "DATE", "BOOLEAN", "SELECT", "MULTI_SELECT", "CURRENCY", "URL", "PHONE"}

    @staticmethod
    def register_custom_field(
        tenant_id: str,
        entity_name: str,
        field_key: str,
        field_label: str,
        field_type: str,
        is_required: bool = False,
        default_value: Any = None,
        options: Optional[List[str]] = None,
        validation_regex: Optional[str] = None
    ) -> Dict[str, Any]:
        if field_type.upper() not in TenantMetamodel.FIELD_TYPES:
            raise ValueError(f"Unsupported custom field type: {field_type}")

        field_id = "fld_" + str(uuid.uuid4())[:12]
        record = {
            "id": field_id,
            "tenant_id": tenant_id,
            "entity_name": entity_name.upper(),
            "field_key": field_key.lower().replace(" ", "_"),
            "field_label": field_label,
            "field_type": field_type.upper(),
            "is_required": 1 if is_required else 0,
            "default_value": json.dumps(default_value) if default_value is not None else None,
            "options": json.dumps(options or []),
            "validation_regex": validation_regex,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Check existing table or store in metadata repository
        try:
            DB.execute("""
                CREATE TABLE IF NOT EXISTS custom_field_definitions (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    field_key TEXT NOT NULL,
                    field_label TEXT NOT NULL,
                    field_type TEXT NOT NULL,
                    is_required INTEGER DEFAULT 0,
                    default_value TEXT,
                    options TEXT,
                    validation_regex TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tenant_id, entity_name, field_key)
                )
            """)
            DB.execute("""
                CREATE TABLE IF NOT EXISTS custom_field_values (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    entity_name TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    field_id TEXT NOT NULL,
                    field_key TEXT NOT NULL,
                    value_text TEXT,
                    value_numeric REAL,
                    value_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (field_id) REFERENCES custom_field_definitions(id) ON DELETE CASCADE,
                    UNIQUE(tenant_id, entity_name, entity_id, field_key)
                )
            """)
            DB.execute("""
                INSERT INTO custom_field_definitions 
                (id, tenant_id, entity_name, field_key, field_label, field_type, is_required, default_value, options, validation_regex, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["entity_name"], record["field_key"],
                record["field_label"], record["field_type"], record["is_required"],
                record["default_value"], record["options"], record["validation_regex"], record["created_at"]
            ))
        except Exception as e:
            raise ValueError(f"Failed to register custom field definition: {e}")

        return record

    @staticmethod
    def get_custom_fields_for_entity(tenant_id: str, entity_name: str) -> List[Dict[str, Any]]:
        try:
            rows = DB.fetch_all("""
                SELECT * FROM custom_field_definitions
                WHERE tenant_id = ? AND entity_name = ?
                ORDER BY field_label ASC
            """, (tenant_id, entity_name.upper()))
            for r in rows:
                r["options"] = json.loads(r["options"]) if r.get("options") else []
                r["default_value"] = json.loads(r["default_value"]) if r.get("default_value") else None
            return rows
        except Exception:
            return []

    @staticmethod
    def save_entity_custom_values(
        tenant_id: str,
        entity_name: str,
        entity_id: str,
        field_values: Dict[str, Any]
    ):
        fields = TenantMetamodel.get_custom_fields_for_entity(tenant_id, entity_name)
        fields_by_key = {f["field_key"]: f for f in fields}

        for key, val in field_values.items():
            field_def = fields_by_key.get(key)
            if not field_def:
                continue

            val_text = None
            val_num = None
            val_json = None

            if isinstance(val, (int, float)):
                val_num = float(val)
                val_text = str(val)
            elif isinstance(val, (dict, list)):
                val_json = json.dumps(val)
                val_text = str(val)
            else:
                val_text = str(val) if val is not None else None

            val_id = "cfv_" + str(uuid.uuid4())[:12]
            DB.execute("""
                INSERT INTO custom_field_values 
                (id, tenant_id, entity_name, entity_id, field_id, field_key, value_text, value_numeric, value_json, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(tenant_id, entity_name, entity_id, field_key) 
                DO UPDATE SET value_text=excluded.value_text, value_numeric=excluded.value_numeric, value_json=excluded.value_json, updated_at=CURRENT_TIMESTAMP
            """, (val_id, tenant_id, entity_name.upper(), entity_id, field_def["id"], key, val_text, val_num, val_json))


class TenantManager:
    """
    Manages tenant quotas, subscriptions, storage limits, and license enforcement.
    """
    @staticmethod
    def initialize_tenant_tables():
        DB.execute("""
            CREATE TABLE IF NOT EXISTS tenant_organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                domain TEXT UNIQUE NOT NULL,
                plan_tier TEXT DEFAULT 'ENTERPRISE',
                max_users INTEGER DEFAULT 50,
                max_storage_mb INTEGER DEFAULT 10240,
                is_active INTEGER DEFAULT 1,
                feature_flags TEXT,
                billing_email TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        DB.execute("""
            CREATE TABLE IF NOT EXISTS tenant_user_memberships (
                id TEXT PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role_in_tenant TEXT NOT NULL DEFAULT 'MEMBER',
                is_active INTEGER DEFAULT 1,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tenant_id) REFERENCES tenant_organizations(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(tenant_id, user_id)
            )
        """)

    @staticmethod
    def create_tenant(
        name: str,
        domain: str,
        plan_tier: str = "ENTERPRISE",
        max_users: int = 100,
        billing_email: str = "billing@tenant.local",
        feature_flags: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        TenantManager.initialize_tenant_tables()
        tenant_id = "ten_" + str(uuid.uuid4())[:12]
        flags = feature_flags or {
            "ai_lead_scoring": True,
            "automated_workflows": True,
            "custom_reporting": True,
            "voip_telephony": True,
            "customer_portal": True,
            "billing_invoicing": True,
            "contract_signatures": True
        }

        record = {
            "id": tenant_id,
            "name": name,
            "domain": domain.lower().strip(),
            "plan_tier": plan_tier,
            "max_users": max_users,
            "max_storage_mb": 50000,
            "is_active": 1,
            "feature_flags": json.dumps(flags),
            "billing_email": billing_email
        }

        DB.execute("""
            INSERT INTO tenant_organizations (id, name, domain, plan_tier, max_users, max_storage_mb, is_active, feature_flags, billing_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record["id"], record["name"], record["domain"], record["plan_tier"],
            record["max_users"], record["max_storage_mb"], record["is_active"],
            record["feature_flags"], record["billing_email"]
        ))

        return record

    @staticmethod
    def get_tenant_by_id(tenant_id: str) -> Optional[Dict[str, Any]]:
        TenantManager.initialize_tenant_tables()
        row = DB.fetch_one("SELECT * FROM tenant_organizations WHERE id = ?", (tenant_id,))
        if row:
            row["feature_flags"] = json.loads(row["feature_flags"]) if row.get("feature_flags") else {}
        return row

    @staticmethod
    def check_feature_access(tenant_id: str, feature_key: str) -> bool:
        tenant = TenantManager.get_tenant_by_id(tenant_id)
        if not tenant or not tenant.get("is_active"):
            return False
        flags = tenant.get("feature_flags", {})
        return flags.get(feature_key, False)
