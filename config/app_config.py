"""
CRM System - Application Configuration
Custom Enterprise CRM Solution
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class DatabaseSettings:
    db_type: str = "sqlite"  # 'sqlite' or 'in_memory'
    db_path: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "crm_storage.db")
    pool_size: int = 10
    timeout_seconds: int = 30
    auto_migrate: bool = True
    enable_wal_mode: bool = True


@dataclass
class SecuritySettings:
    secret_key: str = "crm-enterprise-secure-custom-key-v1-99882211"
    token_expiration_hours: int = 24
    password_salt_rounds: int = 100000
    allowed_cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit_requests_per_minute: int = 600
    session_cookie_name: str = "CRM_SESSION_TOKEN"


@dataclass
class BusinessSettings:
    company_name: str = "Apex Enterprise Systems"
    default_currency: str = "USD"
    sla_default_response_hours: int = 4
    sla_default_resolution_hours: int = 24
    lead_score_threshold_qualified: int = 65
    fiscal_year_start_month: int = 1  # January
    opportunity_stages: List[Dict[str, Any]] = field(default_factory=lambda: [
        {"id": "PROSPECTING", "name": "Prospecting", "probability": 10, "order": 1},
        {"id": "QUALIFICATION", "name": "Qualification", "probability": 25, "order": 2},
        {"id": "NEED_ANALYSIS", "name": "Needs Analysis", "probability": 40, "order": 3},
        {"id": "PROPOSAL", "name": "Proposal & Quote", "probability": 60, "order": 4},
        {"id": "NEGOTIATION", "name": "Negotiation / Review", "probability": 80, "order": 5},
        {"id": "CLOSED_WON", "name": "Closed Won", "probability": 100, "order": 6},
        {"id": "CLOSED_LOST", "name": "Closed Lost", "probability": 0, "order": 7}
    ])


@dataclass
class ServerSettings:
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    static_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "static")
    template_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "templates")


@dataclass
class AppConfig:
    app_name: str = "OmniFlow CRM Platform"
    app_version: str = "1.0.0-Enterprise"
    environment: str = "production"
    server: ServerSettings = field(default_factory=ServerSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    business: BusinessSettings = field(default_factory=BusinessSettings)


# Singleton Config Instance
CONFIG = AppConfig()
