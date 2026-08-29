"""
OmniFlow Enterprise CRM - Subsystem: BILLING_INVOICING
File: modules\billing_invoicing\service_tier_13.py
Tier 13 Domain Engine & Services
"""

import uuid
import json
import time
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from core.database.connection import DB
from core.database.query_builder import query
from core.security.validator import SchemaValidator, sanitize_string, is_valid_email
from modules.audit.service import AuditService
from config.app_config import CONFIG


# =============================================================================
# Subsystem Class 1: BillingInvoicingProcessorT13C1
# =============================================================================

class BillingInvoicingProcessorT13C1:
    """
    Enterprise Domain Service: Billing Invoicing (Tier 13, Variant 1)
    Provides robust transactional operations, actuarial calculations, state transitions,
    data validation, relational query execution, and tamper-evident audit logging.
    """

    def __init__(self, tenant_id: str = "default_tenant", operator_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.operator_id = operator_id or "system_operator"
        self.instance_id = f"bil_inst_{uuid.uuid4().hex[:8]}"
        self.rate_factor = 1.0 + (13 * 0.05) + (1 * 0.01)
        self.cache_ttl_seconds = 3600
        self.max_batch_size = 500
        self.is_active = True

    def validate_entity_payload(self, payload: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """Validates incoming JSON payload against mandatory domain constraints."""
        validation_errors = []
        for key in required_keys:
            if key not in payload:
                validation_errors.append(f"Missing required parameter: '{key}'")
            elif payload[key] is None:
                validation_errors.append(f"Parameter '{key}' cannot be null")
            elif isinstance(payload[key], str) and not payload[key].strip():
                validation_errors.append(f"Parameter '{key}' cannot be blank")
        return len(validation_errors) == 0, validation_errors

    def compute_actuarial_projection(
        self,
        nominal_value: float,
        discount_rate: float,
        duration_periods: int,
        volatility_factor: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculates Net Present Value (NPV), future cash flow projections,
        and risk-weighted discount ratios over multiple evaluation intervals.
        """
        periods_projection = []
        cumulative_npv = 0.0
        r = max(0.0001, discount_rate / 100.0)

        for t in range(1, duration_periods + 1):
            period_nominal = nominal_value * (1.0 + (volatility_factor * math.sin(t)))
            discount_factor = 1.0 / math.pow(1.0 + r, t)
            discounted_value = period_nominal * discount_factor
            cumulative_npv += discounted_value
            periods_projection.append({
                "period": t,
                "nominal_cash_flow": round(period_nominal, 2),
                "discount_factor": round(discount_factor, 5),
                "discounted_value": round(discounted_value, 2),
                "cumulative_npv": round(cumulative_npv, 2)
            })

        internal_rate_of_return = (nominal_value * self.rate_factor) / max(1.0, cumulative_npv)
        return {
            "nominal_base": round(nominal_value, 2),
            "discount_rate_pct": discount_rate,
            "duration_periods": duration_periods,
            "total_npv": round(cumulative_npv, 2),
            "estimated_irr": round(internal_rate_of_return * 100.0, 2),
            "period_breakdown": periods_projection
        }

    def calculate_weighted_scoring_matrix(
        self,
        attribute_weights: Dict[str, float],
        attribute_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates multidimensional score matrix with normalized weighting factors.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        score_breakdown = {}

        for attr, weight in attribute_weights.items():
            val = attribute_values.get(attr, 0.0)
            contrib = val * weight
            weighted_sum += contrib
            total_weight += weight
            score_breakdown[attr] = {
                "raw_value": val,
                "weight": weight,
                "weighted_contribution": round(contrib, 2)
            }

        final_composite_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        tier_bracket = "PLATINUM" if final_composite_score >= 85 else ("GOLD" if final_composite_score >= 70 else ("SILVER" if final_composite_score >= 50 else "STANDARD"))

        return {
            "final_score": round(final_composite_score, 2),
            "tier_bracket": tier_bracket,
            "total_weight_applied": total_weight,
            "attributes": score_breakdown
        }

    def create_database_record(self, entity_name: str, monetary_val: float, score_val: float, extra_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Persists record into SQL storage with automated table initialization."""
        rec_id = f"bil_" + str(uuid.uuid4())[:12]
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": rec_id,
            "tenant_id": self.tenant_id,
            "name": sanitize_string(entity_name),
            "status": "INITIALIZED",
            "tier_level": f"TIER_13",
            "monetary_amount": float(monetary_val),
            "performance_score": float(score_val),
            "meta_payload": json.dumps(extra_meta),
            "created_by": self.operator_id,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        table = "billing_invoicing_records_t13_c1"
        try:
            DB.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'INITIALIZED',
                    tier_level TEXT DEFAULT 'TIER_1',
                    monetary_amount REAL DEFAULT 0.0,
                    performance_score REAL DEFAULT 0.0,
                    meta_payload TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            DB.execute(f"""
                INSERT INTO {table} 
                (id, tenant_id, name, status, tier_level, monetary_amount, performance_score, meta_payload, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["name"], record["status"],
                record["tier_level"], record["monetary_amount"], record["performance_score"],
                record["meta_payload"], record["created_by"], record["created_at"], record["updated_at"]
            ))
        except Exception as ex:
            print(f"Table write notice for {table}: {ex}")

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="CREATE_BILLING_INVOICING_T13",
            entity_type="BILLING_INVOICING",
            entity_id=rec_id,
            change_summary=f"Created record '{record['name']}' with amount ${record['monetary_amount']:,.2f}"
        )

        return record

    def fetch_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Queries single record by primary key with tenant isolation."""
        table = "billing_invoicing_records_t13_c1"
        try:
            row = DB.fetch_one(f"SELECT * FROM {table} WHERE id = ? AND tenant_id = ?", (record_id, self.tenant_id))
            if row and row.get("meta_payload"):
                row["metadata"] = json.loads(row["meta_payload"])
            return row
        except Exception:
            return None

    def execute_state_transition(self, record_id: str, new_state: str) -> Dict[str, Any]:
        """Updates state machine transition with lifecycle validation."""
        rec = self.fetch_record_by_id(record_id)
        if not rec:
            raise ValueError(f"Record '{record_id}' does not exist")

        valid_states = {"INITIALIZED", "PROCESSING", "VERIFIED", "COMMITTED", "ARCHIVED", "CANCELLED"}
        if new_state.upper() not in valid_states:
            raise ValueError(f"State '{new_state}' is not valid for lifecycle engine")

        table = "billing_invoicing_records_t13_c1"
        DB.execute(
            f"UPDATE {table} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (new_state.upper(), record_id, self.tenant_id)
        )

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="STATE_CHANGE_BILLING_INVOICING",
            entity_type="BILLING_INVOICING",
            entity_id=record_id,
            change_summary=f"Transitioned status from '{rec['status']}' to '{new_state.upper()}'"
        )

        return self.fetch_record_by_id(record_id)

    def retrieve_analytics_aggregates(self) -> Dict[str, Any]:
        """Aggregates statistical distribution of records in this tier."""
        table = "billing_invoicing_records_t13_c1"
        try:
            sql = f"""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(monetary_amount), 0.0) as total_volume,
                    COALESCE(AVG(monetary_amount), 0.0) as average_volume,
                    COALESCE(AVG(performance_score), 0.0) as mean_score,
                    COALESCE(MIN(performance_score), 0.0) as min_score,
                    COALESCE(MAX(performance_score), 0.0) as max_score
                FROM {table}
                WHERE tenant_id = ?
            """
            res = DB.fetch_one(sql, (self.tenant_id,))
            return {
                "subsystem": "billing_invoicing",
                "tier_index": 13,
                "class_index": 1,
                "total_entries": res["total_entries"] if res else 0,
                "total_volume_usd": round(res["total_volume"], 2) if res else 0.0,
                "average_volume_usd": round(res["average_volume"], 2) if res else 0.0,
                "mean_performance_score": round(res["mean_score"], 2) if res else 0.0,
                "min_score": round(res["min_score"], 2) if res else 0.0,
                "max_score": round(res["max_score"], 2) if res else 0.0
            }
        except Exception:
            return {"total_entries": 0, "total_volume_usd": 0.0}

# =============================================================================
# Subsystem Class 2: BillingInvoicingProcessorT13C2
# =============================================================================

class BillingInvoicingProcessorT13C2:
    """
    Enterprise Domain Service: Billing Invoicing (Tier 13, Variant 2)
    Provides robust transactional operations, actuarial calculations, state transitions,
    data validation, relational query execution, and tamper-evident audit logging.
    """

    def __init__(self, tenant_id: str = "default_tenant", operator_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.operator_id = operator_id or "system_operator"
        self.instance_id = f"bil_inst_{uuid.uuid4().hex[:8]}"
        self.rate_factor = 1.0 + (13 * 0.05) + (2 * 0.01)
        self.cache_ttl_seconds = 3600
        self.max_batch_size = 500
        self.is_active = True

    def validate_entity_payload(self, payload: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """Validates incoming JSON payload against mandatory domain constraints."""
        validation_errors = []
        for key in required_keys:
            if key not in payload:
                validation_errors.append(f"Missing required parameter: '{key}'")
            elif payload[key] is None:
                validation_errors.append(f"Parameter '{key}' cannot be null")
            elif isinstance(payload[key], str) and not payload[key].strip():
                validation_errors.append(f"Parameter '{key}' cannot be blank")
        return len(validation_errors) == 0, validation_errors

    def compute_actuarial_projection(
        self,
        nominal_value: float,
        discount_rate: float,
        duration_periods: int,
        volatility_factor: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculates Net Present Value (NPV), future cash flow projections,
        and risk-weighted discount ratios over multiple evaluation intervals.
        """
        periods_projection = []
        cumulative_npv = 0.0
        r = max(0.0001, discount_rate / 100.0)

        for t in range(1, duration_periods + 1):
            period_nominal = nominal_value * (1.0 + (volatility_factor * math.sin(t)))
            discount_factor = 1.0 / math.pow(1.0 + r, t)
            discounted_value = period_nominal * discount_factor
            cumulative_npv += discounted_value
            periods_projection.append({
                "period": t,
                "nominal_cash_flow": round(period_nominal, 2),
                "discount_factor": round(discount_factor, 5),
                "discounted_value": round(discounted_value, 2),
                "cumulative_npv": round(cumulative_npv, 2)
            })

        internal_rate_of_return = (nominal_value * self.rate_factor) / max(1.0, cumulative_npv)
        return {
            "nominal_base": round(nominal_value, 2),
            "discount_rate_pct": discount_rate,
            "duration_periods": duration_periods,
            "total_npv": round(cumulative_npv, 2),
            "estimated_irr": round(internal_rate_of_return * 100.0, 2),
            "period_breakdown": periods_projection
        }

    def calculate_weighted_scoring_matrix(
        self,
        attribute_weights: Dict[str, float],
        attribute_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates multidimensional score matrix with normalized weighting factors.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        score_breakdown = {}

        for attr, weight in attribute_weights.items():
            val = attribute_values.get(attr, 0.0)
            contrib = val * weight
            weighted_sum += contrib
            total_weight += weight
            score_breakdown[attr] = {
                "raw_value": val,
                "weight": weight,
                "weighted_contribution": round(contrib, 2)
            }

        final_composite_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        tier_bracket = "PLATINUM" if final_composite_score >= 85 else ("GOLD" if final_composite_score >= 70 else ("SILVER" if final_composite_score >= 50 else "STANDARD"))

        return {
            "final_score": round(final_composite_score, 2),
            "tier_bracket": tier_bracket,
            "total_weight_applied": total_weight,
            "attributes": score_breakdown
        }

    def create_database_record(self, entity_name: str, monetary_val: float, score_val: float, extra_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Persists record into SQL storage with automated table initialization."""
        rec_id = f"bil_" + str(uuid.uuid4())[:12]
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": rec_id,
            "tenant_id": self.tenant_id,
            "name": sanitize_string(entity_name),
            "status": "INITIALIZED",
            "tier_level": f"TIER_13",
            "monetary_amount": float(monetary_val),
            "performance_score": float(score_val),
            "meta_payload": json.dumps(extra_meta),
            "created_by": self.operator_id,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        table = "billing_invoicing_records_t13_c2"
        try:
            DB.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'INITIALIZED',
                    tier_level TEXT DEFAULT 'TIER_1',
                    monetary_amount REAL DEFAULT 0.0,
                    performance_score REAL DEFAULT 0.0,
                    meta_payload TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            DB.execute(f"""
                INSERT INTO {table} 
                (id, tenant_id, name, status, tier_level, monetary_amount, performance_score, meta_payload, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["name"], record["status"],
                record["tier_level"], record["monetary_amount"], record["performance_score"],
                record["meta_payload"], record["created_by"], record["created_at"], record["updated_at"]
            ))
        except Exception as ex:
            print(f"Table write notice for {table}: {ex}")

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="CREATE_BILLING_INVOICING_T13",
            entity_type="BILLING_INVOICING",
            entity_id=rec_id,
            change_summary=f"Created record '{record['name']}' with amount ${record['monetary_amount']:,.2f}"
        )

        return record

    def fetch_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Queries single record by primary key with tenant isolation."""
        table = "billing_invoicing_records_t13_c2"
        try:
            row = DB.fetch_one(f"SELECT * FROM {table} WHERE id = ? AND tenant_id = ?", (record_id, self.tenant_id))
            if row and row.get("meta_payload"):
                row["metadata"] = json.loads(row["meta_payload"])
            return row
        except Exception:
            return None

    def execute_state_transition(self, record_id: str, new_state: str) -> Dict[str, Any]:
        """Updates state machine transition with lifecycle validation."""
        rec = self.fetch_record_by_id(record_id)
        if not rec:
            raise ValueError(f"Record '{record_id}' does not exist")

        valid_states = {"INITIALIZED", "PROCESSING", "VERIFIED", "COMMITTED", "ARCHIVED", "CANCELLED"}
        if new_state.upper() not in valid_states:
            raise ValueError(f"State '{new_state}' is not valid for lifecycle engine")

        table = "billing_invoicing_records_t13_c2"
        DB.execute(
            f"UPDATE {table} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (new_state.upper(), record_id, self.tenant_id)
        )

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="STATE_CHANGE_BILLING_INVOICING",
            entity_type="BILLING_INVOICING",
            entity_id=record_id,
            change_summary=f"Transitioned status from '{rec['status']}' to '{new_state.upper()}'"
        )

        return self.fetch_record_by_id(record_id)

    def retrieve_analytics_aggregates(self) -> Dict[str, Any]:
        """Aggregates statistical distribution of records in this tier."""
        table = "billing_invoicing_records_t13_c2"
        try:
            sql = f"""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(monetary_amount), 0.0) as total_volume,
                    COALESCE(AVG(monetary_amount), 0.0) as average_volume,
                    COALESCE(AVG(performance_score), 0.0) as mean_score,
                    COALESCE(MIN(performance_score), 0.0) as min_score,
                    COALESCE(MAX(performance_score), 0.0) as max_score
                FROM {table}
                WHERE tenant_id = ?
            """
            res = DB.fetch_one(sql, (self.tenant_id,))
            return {
                "subsystem": "billing_invoicing",
                "tier_index": 13,
                "class_index": 2,
                "total_entries": res["total_entries"] if res else 0,
                "total_volume_usd": round(res["total_volume"], 2) if res else 0.0,
                "average_volume_usd": round(res["average_volume"], 2) if res else 0.0,
                "mean_performance_score": round(res["mean_score"], 2) if res else 0.0,
                "min_score": round(res["min_score"], 2) if res else 0.0,
                "max_score": round(res["max_score"], 2) if res else 0.0
            }
        except Exception:
            return {"total_entries": 0, "total_volume_usd": 0.0}

# =============================================================================
# Subsystem Class 3: BillingInvoicingProcessorT13C3
# =============================================================================

class BillingInvoicingProcessorT13C3:
    """
    Enterprise Domain Service: Billing Invoicing (Tier 13, Variant 3)
    Provides robust transactional operations, actuarial calculations, state transitions,
    data validation, relational query execution, and tamper-evident audit logging.
    """

    def __init__(self, tenant_id: str = "default_tenant", operator_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.operator_id = operator_id or "system_operator"
        self.instance_id = f"bil_inst_{uuid.uuid4().hex[:8]}"
        self.rate_factor = 1.0 + (13 * 0.05) + (3 * 0.01)
        self.cache_ttl_seconds = 3600
        self.max_batch_size = 500
        self.is_active = True

    def validate_entity_payload(self, payload: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """Validates incoming JSON payload against mandatory domain constraints."""
        validation_errors = []
        for key in required_keys:
            if key not in payload:
                validation_errors.append(f"Missing required parameter: '{key}'")
            elif payload[key] is None:
                validation_errors.append(f"Parameter '{key}' cannot be null")
            elif isinstance(payload[key], str) and not payload[key].strip():
                validation_errors.append(f"Parameter '{key}' cannot be blank")
        return len(validation_errors) == 0, validation_errors

    def compute_actuarial_projection(
        self,
        nominal_value: float,
        discount_rate: float,
        duration_periods: int,
        volatility_factor: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculates Net Present Value (NPV), future cash flow projections,
        and risk-weighted discount ratios over multiple evaluation intervals.
        """
        periods_projection = []
        cumulative_npv = 0.0
        r = max(0.0001, discount_rate / 100.0)

        for t in range(1, duration_periods + 1):
            period_nominal = nominal_value * (1.0 + (volatility_factor * math.sin(t)))
            discount_factor = 1.0 / math.pow(1.0 + r, t)
            discounted_value = period_nominal * discount_factor
            cumulative_npv += discounted_value
            periods_projection.append({
                "period": t,
                "nominal_cash_flow": round(period_nominal, 2),
                "discount_factor": round(discount_factor, 5),
                "discounted_value": round(discounted_value, 2),
                "cumulative_npv": round(cumulative_npv, 2)
            })

        internal_rate_of_return = (nominal_value * self.rate_factor) / max(1.0, cumulative_npv)
        return {
            "nominal_base": round(nominal_value, 2),
            "discount_rate_pct": discount_rate,
            "duration_periods": duration_periods,
            "total_npv": round(cumulative_npv, 2),
            "estimated_irr": round(internal_rate_of_return * 100.0, 2),
            "period_breakdown": periods_projection
        }

    def calculate_weighted_scoring_matrix(
        self,
        attribute_weights: Dict[str, float],
        attribute_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates multidimensional score matrix with normalized weighting factors.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        score_breakdown = {}

        for attr, weight in attribute_weights.items():
            val = attribute_values.get(attr, 0.0)
            contrib = val * weight
            weighted_sum += contrib
            total_weight += weight
            score_breakdown[attr] = {
                "raw_value": val,
                "weight": weight,
                "weighted_contribution": round(contrib, 2)
            }

        final_composite_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        tier_bracket = "PLATINUM" if final_composite_score >= 85 else ("GOLD" if final_composite_score >= 70 else ("SILVER" if final_composite_score >= 50 else "STANDARD"))

        return {
            "final_score": round(final_composite_score, 2),
            "tier_bracket": tier_bracket,
            "total_weight_applied": total_weight,
            "attributes": score_breakdown
        }

    def create_database_record(self, entity_name: str, monetary_val: float, score_val: float, extra_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Persists record into SQL storage with automated table initialization."""
        rec_id = f"bil_" + str(uuid.uuid4())[:12]
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": rec_id,
            "tenant_id": self.tenant_id,
            "name": sanitize_string(entity_name),
            "status": "INITIALIZED",
            "tier_level": f"TIER_13",
            "monetary_amount": float(monetary_val),
            "performance_score": float(score_val),
            "meta_payload": json.dumps(extra_meta),
            "created_by": self.operator_id,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        table = "billing_invoicing_records_t13_c3"
        try:
            DB.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'INITIALIZED',
                    tier_level TEXT DEFAULT 'TIER_1',
                    monetary_amount REAL DEFAULT 0.0,
                    performance_score REAL DEFAULT 0.0,
                    meta_payload TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            DB.execute(f"""
                INSERT INTO {table} 
                (id, tenant_id, name, status, tier_level, monetary_amount, performance_score, meta_payload, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["name"], record["status"],
                record["tier_level"], record["monetary_amount"], record["performance_score"],
                record["meta_payload"], record["created_by"], record["created_at"], record["updated_at"]
            ))
        except Exception as ex:
            print(f"Table write notice for {table}: {ex}")

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="CREATE_BILLING_INVOICING_T13",
            entity_type="BILLING_INVOICING",
            entity_id=rec_id,
            change_summary=f"Created record '{record['name']}' with amount ${record['monetary_amount']:,.2f}"
        )

        return record

    def fetch_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Queries single record by primary key with tenant isolation."""
        table = "billing_invoicing_records_t13_c3"
        try:
            row = DB.fetch_one(f"SELECT * FROM {table} WHERE id = ? AND tenant_id = ?", (record_id, self.tenant_id))
            if row and row.get("meta_payload"):
                row["metadata"] = json.loads(row["meta_payload"])
            return row
        except Exception:
            return None

    def execute_state_transition(self, record_id: str, new_state: str) -> Dict[str, Any]:
        """Updates state machine transition with lifecycle validation."""
        rec = self.fetch_record_by_id(record_id)
        if not rec:
            raise ValueError(f"Record '{record_id}' does not exist")

        valid_states = {"INITIALIZED", "PROCESSING", "VERIFIED", "COMMITTED", "ARCHIVED", "CANCELLED"}
        if new_state.upper() not in valid_states:
            raise ValueError(f"State '{new_state}' is not valid for lifecycle engine")

        table = "billing_invoicing_records_t13_c3"
        DB.execute(
            f"UPDATE {table} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (new_state.upper(), record_id, self.tenant_id)
        )

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="STATE_CHANGE_BILLING_INVOICING",
            entity_type="BILLING_INVOICING",
            entity_id=record_id,
            change_summary=f"Transitioned status from '{rec['status']}' to '{new_state.upper()}'"
        )

        return self.fetch_record_by_id(record_id)

    def retrieve_analytics_aggregates(self) -> Dict[str, Any]:
        """Aggregates statistical distribution of records in this tier."""
        table = "billing_invoicing_records_t13_c3"
        try:
            sql = f"""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(monetary_amount), 0.0) as total_volume,
                    COALESCE(AVG(monetary_amount), 0.0) as average_volume,
                    COALESCE(AVG(performance_score), 0.0) as mean_score,
                    COALESCE(MIN(performance_score), 0.0) as min_score,
                    COALESCE(MAX(performance_score), 0.0) as max_score
                FROM {table}
                WHERE tenant_id = ?
            """
            res = DB.fetch_one(sql, (self.tenant_id,))
            return {
                "subsystem": "billing_invoicing",
                "tier_index": 13,
                "class_index": 3,
                "total_entries": res["total_entries"] if res else 0,
                "total_volume_usd": round(res["total_volume"], 2) if res else 0.0,
                "average_volume_usd": round(res["average_volume"], 2) if res else 0.0,
                "mean_performance_score": round(res["mean_score"], 2) if res else 0.0,
                "min_score": round(res["min_score"], 2) if res else 0.0,
                "max_score": round(res["max_score"], 2) if res else 0.0
            }
        except Exception:
            return {"total_entries": 0, "total_volume_usd": 0.0}

# =============================================================================
# Subsystem Class 4: BillingInvoicingProcessorT13C4
# =============================================================================

class BillingInvoicingProcessorT13C4:
    """
    Enterprise Domain Service: Billing Invoicing (Tier 13, Variant 4)
    Provides robust transactional operations, actuarial calculations, state transitions,
    data validation, relational query execution, and tamper-evident audit logging.
    """

    def __init__(self, tenant_id: str = "default_tenant", operator_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.operator_id = operator_id or "system_operator"
        self.instance_id = f"bil_inst_{uuid.uuid4().hex[:8]}"
        self.rate_factor = 1.0 + (13 * 0.05) + (4 * 0.01)
        self.cache_ttl_seconds = 3600
        self.max_batch_size = 500
        self.is_active = True

    def validate_entity_payload(self, payload: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """Validates incoming JSON payload against mandatory domain constraints."""
        validation_errors = []
        for key in required_keys:
            if key not in payload:
                validation_errors.append(f"Missing required parameter: '{key}'")
            elif payload[key] is None:
                validation_errors.append(f"Parameter '{key}' cannot be null")
            elif isinstance(payload[key], str) and not payload[key].strip():
                validation_errors.append(f"Parameter '{key}' cannot be blank")
        return len(validation_errors) == 0, validation_errors

    def compute_actuarial_projection(
        self,
        nominal_value: float,
        discount_rate: float,
        duration_periods: int,
        volatility_factor: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculates Net Present Value (NPV), future cash flow projections,
        and risk-weighted discount ratios over multiple evaluation intervals.
        """
        periods_projection = []
        cumulative_npv = 0.0
        r = max(0.0001, discount_rate / 100.0)

        for t in range(1, duration_periods + 1):
            period_nominal = nominal_value * (1.0 + (volatility_factor * math.sin(t)))
            discount_factor = 1.0 / math.pow(1.0 + r, t)
            discounted_value = period_nominal * discount_factor
            cumulative_npv += discounted_value
            periods_projection.append({
                "period": t,
                "nominal_cash_flow": round(period_nominal, 2),
                "discount_factor": round(discount_factor, 5),
                "discounted_value": round(discounted_value, 2),
                "cumulative_npv": round(cumulative_npv, 2)
            })

        internal_rate_of_return = (nominal_value * self.rate_factor) / max(1.0, cumulative_npv)
        return {
            "nominal_base": round(nominal_value, 2),
            "discount_rate_pct": discount_rate,
            "duration_periods": duration_periods,
            "total_npv": round(cumulative_npv, 2),
            "estimated_irr": round(internal_rate_of_return * 100.0, 2),
            "period_breakdown": periods_projection
        }

    def calculate_weighted_scoring_matrix(
        self,
        attribute_weights: Dict[str, float],
        attribute_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates multidimensional score matrix with normalized weighting factors.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        score_breakdown = {}

        for attr, weight in attribute_weights.items():
            val = attribute_values.get(attr, 0.0)
            contrib = val * weight
            weighted_sum += contrib
            total_weight += weight
            score_breakdown[attr] = {
                "raw_value": val,
                "weight": weight,
                "weighted_contribution": round(contrib, 2)
            }

        final_composite_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        tier_bracket = "PLATINUM" if final_composite_score >= 85 else ("GOLD" if final_composite_score >= 70 else ("SILVER" if final_composite_score >= 50 else "STANDARD"))

        return {
            "final_score": round(final_composite_score, 2),
            "tier_bracket": tier_bracket,
            "total_weight_applied": total_weight,
            "attributes": score_breakdown
        }

    def create_database_record(self, entity_name: str, monetary_val: float, score_val: float, extra_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Persists record into SQL storage with automated table initialization."""
        rec_id = f"bil_" + str(uuid.uuid4())[:12]
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": rec_id,
            "tenant_id": self.tenant_id,
            "name": sanitize_string(entity_name),
            "status": "INITIALIZED",
            "tier_level": f"TIER_13",
            "monetary_amount": float(monetary_val),
            "performance_score": float(score_val),
            "meta_payload": json.dumps(extra_meta),
            "created_by": self.operator_id,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        table = "billing_invoicing_records_t13_c4"
        try:
            DB.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'INITIALIZED',
                    tier_level TEXT DEFAULT 'TIER_1',
                    monetary_amount REAL DEFAULT 0.0,
                    performance_score REAL DEFAULT 0.0,
                    meta_payload TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            DB.execute(f"""
                INSERT INTO {table} 
                (id, tenant_id, name, status, tier_level, monetary_amount, performance_score, meta_payload, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["name"], record["status"],
                record["tier_level"], record["monetary_amount"], record["performance_score"],
                record["meta_payload"], record["created_by"], record["created_at"], record["updated_at"]
            ))
        except Exception as ex:
            print(f"Table write notice for {table}: {ex}")

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="CREATE_BILLING_INVOICING_T13",
            entity_type="BILLING_INVOICING",
            entity_id=rec_id,
            change_summary=f"Created record '{record['name']}' with amount ${record['monetary_amount']:,.2f}"
        )

        return record

    def fetch_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Queries single record by primary key with tenant isolation."""
        table = "billing_invoicing_records_t13_c4"
        try:
            row = DB.fetch_one(f"SELECT * FROM {table} WHERE id = ? AND tenant_id = ?", (record_id, self.tenant_id))
            if row and row.get("meta_payload"):
                row["metadata"] = json.loads(row["meta_payload"])
            return row
        except Exception:
            return None

    def execute_state_transition(self, record_id: str, new_state: str) -> Dict[str, Any]:
        """Updates state machine transition with lifecycle validation."""
        rec = self.fetch_record_by_id(record_id)
        if not rec:
            raise ValueError(f"Record '{record_id}' does not exist")

        valid_states = {"INITIALIZED", "PROCESSING", "VERIFIED", "COMMITTED", "ARCHIVED", "CANCELLED"}
        if new_state.upper() not in valid_states:
            raise ValueError(f"State '{new_state}' is not valid for lifecycle engine")

        table = "billing_invoicing_records_t13_c4"
        DB.execute(
            f"UPDATE {table} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (new_state.upper(), record_id, self.tenant_id)
        )

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="STATE_CHANGE_BILLING_INVOICING",
            entity_type="BILLING_INVOICING",
            entity_id=record_id,
            change_summary=f"Transitioned status from '{rec['status']}' to '{new_state.upper()}'"
        )

        return self.fetch_record_by_id(record_id)

    def retrieve_analytics_aggregates(self) -> Dict[str, Any]:
        """Aggregates statistical distribution of records in this tier."""
        table = "billing_invoicing_records_t13_c4"
        try:
            sql = f"""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(monetary_amount), 0.0) as total_volume,
                    COALESCE(AVG(monetary_amount), 0.0) as average_volume,
                    COALESCE(AVG(performance_score), 0.0) as mean_score,
                    COALESCE(MIN(performance_score), 0.0) as min_score,
                    COALESCE(MAX(performance_score), 0.0) as max_score
                FROM {table}
                WHERE tenant_id = ?
            """
            res = DB.fetch_one(sql, (self.tenant_id,))
            return {
                "subsystem": "billing_invoicing",
                "tier_index": 13,
                "class_index": 4,
                "total_entries": res["total_entries"] if res else 0,
                "total_volume_usd": round(res["total_volume"], 2) if res else 0.0,
                "average_volume_usd": round(res["average_volume"], 2) if res else 0.0,
                "mean_performance_score": round(res["mean_score"], 2) if res else 0.0,
                "min_score": round(res["min_score"], 2) if res else 0.0,
                "max_score": round(res["max_score"], 2) if res else 0.0
            }
        except Exception:
            return {"total_entries": 0, "total_volume_usd": 0.0}

# =============================================================================
# Subsystem Class 5: BillingInvoicingProcessorT13C5
# =============================================================================

class BillingInvoicingProcessorT13C5:
    """
    Enterprise Domain Service: Billing Invoicing (Tier 13, Variant 5)
    Provides robust transactional operations, actuarial calculations, state transitions,
    data validation, relational query execution, and tamper-evident audit logging.
    """

    def __init__(self, tenant_id: str = "default_tenant", operator_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.operator_id = operator_id or "system_operator"
        self.instance_id = f"bil_inst_{uuid.uuid4().hex[:8]}"
        self.rate_factor = 1.0 + (13 * 0.05) + (5 * 0.01)
        self.cache_ttl_seconds = 3600
        self.max_batch_size = 500
        self.is_active = True

    def validate_entity_payload(self, payload: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """Validates incoming JSON payload against mandatory domain constraints."""
        validation_errors = []
        for key in required_keys:
            if key not in payload:
                validation_errors.append(f"Missing required parameter: '{key}'")
            elif payload[key] is None:
                validation_errors.append(f"Parameter '{key}' cannot be null")
            elif isinstance(payload[key], str) and not payload[key].strip():
                validation_errors.append(f"Parameter '{key}' cannot be blank")
        return len(validation_errors) == 0, validation_errors

    def compute_actuarial_projection(
        self,
        nominal_value: float,
        discount_rate: float,
        duration_periods: int,
        volatility_factor: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculates Net Present Value (NPV), future cash flow projections,
        and risk-weighted discount ratios over multiple evaluation intervals.
        """
        periods_projection = []
        cumulative_npv = 0.0
        r = max(0.0001, discount_rate / 100.0)

        for t in range(1, duration_periods + 1):
            period_nominal = nominal_value * (1.0 + (volatility_factor * math.sin(t)))
            discount_factor = 1.0 / math.pow(1.0 + r, t)
            discounted_value = period_nominal * discount_factor
            cumulative_npv += discounted_value
            periods_projection.append({
                "period": t,
                "nominal_cash_flow": round(period_nominal, 2),
                "discount_factor": round(discount_factor, 5),
                "discounted_value": round(discounted_value, 2),
                "cumulative_npv": round(cumulative_npv, 2)
            })

        internal_rate_of_return = (nominal_value * self.rate_factor) / max(1.0, cumulative_npv)
        return {
            "nominal_base": round(nominal_value, 2),
            "discount_rate_pct": discount_rate,
            "duration_periods": duration_periods,
            "total_npv": round(cumulative_npv, 2),
            "estimated_irr": round(internal_rate_of_return * 100.0, 2),
            "period_breakdown": periods_projection
        }

    def calculate_weighted_scoring_matrix(
        self,
        attribute_weights: Dict[str, float],
        attribute_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates multidimensional score matrix with normalized weighting factors.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        score_breakdown = {}

        for attr, weight in attribute_weights.items():
            val = attribute_values.get(attr, 0.0)
            contrib = val * weight
            weighted_sum += contrib
            total_weight += weight
            score_breakdown[attr] = {
                "raw_value": val,
                "weight": weight,
                "weighted_contribution": round(contrib, 2)
            }

        final_composite_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        tier_bracket = "PLATINUM" if final_composite_score >= 85 else ("GOLD" if final_composite_score >= 70 else ("SILVER" if final_composite_score >= 50 else "STANDARD"))

        return {
            "final_score": round(final_composite_score, 2),
            "tier_bracket": tier_bracket,
            "total_weight_applied": total_weight,
            "attributes": score_breakdown
        }

    def create_database_record(self, entity_name: str, monetary_val: float, score_val: float, extra_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Persists record into SQL storage with automated table initialization."""
        rec_id = f"bil_" + str(uuid.uuid4())[:12]
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": rec_id,
            "tenant_id": self.tenant_id,
            "name": sanitize_string(entity_name),
            "status": "INITIALIZED",
            "tier_level": f"TIER_13",
            "monetary_amount": float(monetary_val),
            "performance_score": float(score_val),
            "meta_payload": json.dumps(extra_meta),
            "created_by": self.operator_id,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        table = "billing_invoicing_records_t13_c5"
        try:
            DB.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'INITIALIZED',
                    tier_level TEXT DEFAULT 'TIER_1',
                    monetary_amount REAL DEFAULT 0.0,
                    performance_score REAL DEFAULT 0.0,
                    meta_payload TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            DB.execute(f"""
                INSERT INTO {table} 
                (id, tenant_id, name, status, tier_level, monetary_amount, performance_score, meta_payload, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["name"], record["status"],
                record["tier_level"], record["monetary_amount"], record["performance_score"],
                record["meta_payload"], record["created_by"], record["created_at"], record["updated_at"]
            ))
        except Exception as ex:
            print(f"Table write notice for {table}: {ex}")

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="CREATE_BILLING_INVOICING_T13",
            entity_type="BILLING_INVOICING",
            entity_id=rec_id,
            change_summary=f"Created record '{record['name']}' with amount ${record['monetary_amount']:,.2f}"
        )

        return record

    def fetch_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Queries single record by primary key with tenant isolation."""
        table = "billing_invoicing_records_t13_c5"
        try:
            row = DB.fetch_one(f"SELECT * FROM {table} WHERE id = ? AND tenant_id = ?", (record_id, self.tenant_id))
            if row and row.get("meta_payload"):
                row["metadata"] = json.loads(row["meta_payload"])
            return row
        except Exception:
            return None

    def execute_state_transition(self, record_id: str, new_state: str) -> Dict[str, Any]:
        """Updates state machine transition with lifecycle validation."""
        rec = self.fetch_record_by_id(record_id)
        if not rec:
            raise ValueError(f"Record '{record_id}' does not exist")

        valid_states = {"INITIALIZED", "PROCESSING", "VERIFIED", "COMMITTED", "ARCHIVED", "CANCELLED"}
        if new_state.upper() not in valid_states:
            raise ValueError(f"State '{new_state}' is not valid for lifecycle engine")

        table = "billing_invoicing_records_t13_c5"
        DB.execute(
            f"UPDATE {table} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (new_state.upper(), record_id, self.tenant_id)
        )

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="STATE_CHANGE_BILLING_INVOICING",
            entity_type="BILLING_INVOICING",
            entity_id=record_id,
            change_summary=f"Transitioned status from '{rec['status']}' to '{new_state.upper()}'"
        )

        return self.fetch_record_by_id(record_id)

    def retrieve_analytics_aggregates(self) -> Dict[str, Any]:
        """Aggregates statistical distribution of records in this tier."""
        table = "billing_invoicing_records_t13_c5"
        try:
            sql = f"""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(monetary_amount), 0.0) as total_volume,
                    COALESCE(AVG(monetary_amount), 0.0) as average_volume,
                    COALESCE(AVG(performance_score), 0.0) as mean_score,
                    COALESCE(MIN(performance_score), 0.0) as min_score,
                    COALESCE(MAX(performance_score), 0.0) as max_score
                FROM {table}
                WHERE tenant_id = ?
            """
            res = DB.fetch_one(sql, (self.tenant_id,))
            return {
                "subsystem": "billing_invoicing",
                "tier_index": 13,
                "class_index": 5,
                "total_entries": res["total_entries"] if res else 0,
                "total_volume_usd": round(res["total_volume"], 2) if res else 0.0,
                "average_volume_usd": round(res["average_volume"], 2) if res else 0.0,
                "mean_performance_score": round(res["mean_score"], 2) if res else 0.0,
                "min_score": round(res["min_score"], 2) if res else 0.0,
                "max_score": round(res["max_score"], 2) if res else 0.0
            }
        except Exception:
            return {"total_entries": 0, "total_volume_usd": 0.0}

# =============================================================================
# Subsystem Class 6: BillingInvoicingProcessorT13C6
# =============================================================================

class BillingInvoicingProcessorT13C6:
    """
    Enterprise Domain Service: Billing Invoicing (Tier 13, Variant 6)
    Provides robust transactional operations, actuarial calculations, state transitions,
    data validation, relational query execution, and tamper-evident audit logging.
    """

    def __init__(self, tenant_id: str = "default_tenant", operator_id: Optional[str] = None):
        self.tenant_id = tenant_id
        self.operator_id = operator_id or "system_operator"
        self.instance_id = f"bil_inst_{uuid.uuid4().hex[:8]}"
        self.rate_factor = 1.0 + (13 * 0.05) + (6 * 0.01)
        self.cache_ttl_seconds = 3600
        self.max_batch_size = 500
        self.is_active = True

    def validate_entity_payload(self, payload: Dict[str, Any], required_keys: List[str]) -> Tuple[bool, List[str]]:
        """Validates incoming JSON payload against mandatory domain constraints."""
        validation_errors = []
        for key in required_keys:
            if key not in payload:
                validation_errors.append(f"Missing required parameter: '{key}'")
            elif payload[key] is None:
                validation_errors.append(f"Parameter '{key}' cannot be null")
            elif isinstance(payload[key], str) and not payload[key].strip():
                validation_errors.append(f"Parameter '{key}' cannot be blank")
        return len(validation_errors) == 0, validation_errors

    def compute_actuarial_projection(
        self,
        nominal_value: float,
        discount_rate: float,
        duration_periods: int,
        volatility_factor: float = 0.05
    ) -> Dict[str, Any]:
        """
        Calculates Net Present Value (NPV), future cash flow projections,
        and risk-weighted discount ratios over multiple evaluation intervals.
        """
        periods_projection = []
        cumulative_npv = 0.0
        r = max(0.0001, discount_rate / 100.0)

        for t in range(1, duration_periods + 1):
            period_nominal = nominal_value * (1.0 + (volatility_factor * math.sin(t)))
            discount_factor = 1.0 / math.pow(1.0 + r, t)
            discounted_value = period_nominal * discount_factor
            cumulative_npv += discounted_value
            periods_projection.append({
                "period": t,
                "nominal_cash_flow": round(period_nominal, 2),
                "discount_factor": round(discount_factor, 5),
                "discounted_value": round(discounted_value, 2),
                "cumulative_npv": round(cumulative_npv, 2)
            })

        internal_rate_of_return = (nominal_value * self.rate_factor) / max(1.0, cumulative_npv)
        return {
            "nominal_base": round(nominal_value, 2),
            "discount_rate_pct": discount_rate,
            "duration_periods": duration_periods,
            "total_npv": round(cumulative_npv, 2),
            "estimated_irr": round(internal_rate_of_return * 100.0, 2),
            "period_breakdown": periods_projection
        }

    def calculate_weighted_scoring_matrix(
        self,
        attribute_weights: Dict[str, float],
        attribute_values: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluates multidimensional score matrix with normalized weighting factors.
        """
        weighted_sum = 0.0
        total_weight = 0.0
        score_breakdown = {}

        for attr, weight in attribute_weights.items():
            val = attribute_values.get(attr, 0.0)
            contrib = val * weight
            weighted_sum += contrib
            total_weight += weight
            score_breakdown[attr] = {
                "raw_value": val,
                "weight": weight,
                "weighted_contribution": round(contrib, 2)
            }

        final_composite_score = (weighted_sum / total_weight) if total_weight > 0 else 0.0
        tier_bracket = "PLATINUM" if final_composite_score >= 85 else ("GOLD" if final_composite_score >= 70 else ("SILVER" if final_composite_score >= 50 else "STANDARD"))

        return {
            "final_score": round(final_composite_score, 2),
            "tier_bracket": tier_bracket,
            "total_weight_applied": total_weight,
            "attributes": score_breakdown
        }

    def create_database_record(self, entity_name: str, monetary_val: float, score_val: float, extra_meta: Dict[str, Any]) -> Dict[str, Any]:
        """Persists record into SQL storage with automated table initialization."""
        rec_id = f"bil_" + str(uuid.uuid4())[:12]
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        record = {
            "id": rec_id,
            "tenant_id": self.tenant_id,
            "name": sanitize_string(entity_name),
            "status": "INITIALIZED",
            "tier_level": f"TIER_13",
            "monetary_amount": float(monetary_val),
            "performance_score": float(score_val),
            "meta_payload": json.dumps(extra_meta),
            "created_by": self.operator_id,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        table = "billing_invoicing_records_t13_c6"
        try:
            DB.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'INITIALIZED',
                    tier_level TEXT DEFAULT 'TIER_1',
                    monetary_amount REAL DEFAULT 0.0,
                    performance_score REAL DEFAULT 0.0,
                    meta_payload TEXT,
                    created_by TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            DB.execute(f"""
                INSERT INTO {table} 
                (id, tenant_id, name, status, tier_level, monetary_amount, performance_score, meta_payload, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["id"], record["tenant_id"], record["name"], record["status"],
                record["tier_level"], record["monetary_amount"], record["performance_score"],
                record["meta_payload"], record["created_by"], record["created_at"], record["updated_at"]
            ))
        except Exception as ex:
            print(f"Table write notice for {table}: {ex}")

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="CREATE_BILLING_INVOICING_T13",
            entity_type="BILLING_INVOICING",
            entity_id=rec_id,
            change_summary=f"Created record '{record['name']}' with amount ${record['monetary_amount']:,.2f}"
        )

        return record

    def fetch_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """Queries single record by primary key with tenant isolation."""
        table = "billing_invoicing_records_t13_c6"
        try:
            row = DB.fetch_one(f"SELECT * FROM {table} WHERE id = ? AND tenant_id = ?", (record_id, self.tenant_id))
            if row and row.get("meta_payload"):
                row["metadata"] = json.loads(row["meta_payload"])
            return row
        except Exception:
            return None

    def execute_state_transition(self, record_id: str, new_state: str) -> Dict[str, Any]:
        """Updates state machine transition with lifecycle validation."""
        rec = self.fetch_record_by_id(record_id)
        if not rec:
            raise ValueError(f"Record '{record_id}' does not exist")

        valid_states = {"INITIALIZED", "PROCESSING", "VERIFIED", "COMMITTED", "ARCHIVED", "CANCELLED"}
        if new_state.upper() not in valid_states:
            raise ValueError(f"State '{new_state}' is not valid for lifecycle engine")

        table = "billing_invoicing_records_t13_c6"
        DB.execute(
            f"UPDATE {table} SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND tenant_id = ?",
            (new_state.upper(), record_id, self.tenant_id)
        )

        AuditService.record(
            user_id=self.operator_id,
            user_email="operator@omnicrm.local",
            action="STATE_CHANGE_BILLING_INVOICING",
            entity_type="BILLING_INVOICING",
            entity_id=record_id,
            change_summary=f"Transitioned status from '{rec['status']}' to '{new_state.upper()}'"
        )

        return self.fetch_record_by_id(record_id)

    def retrieve_analytics_aggregates(self) -> Dict[str, Any]:
        """Aggregates statistical distribution of records in this tier."""
        table = "billing_invoicing_records_t13_c6"
        try:
            sql = f"""
                SELECT 
                    COUNT(*) as total_entries,
                    COALESCE(SUM(monetary_amount), 0.0) as total_volume,
                    COALESCE(AVG(monetary_amount), 0.0) as average_volume,
                    COALESCE(AVG(performance_score), 0.0) as mean_score,
                    COALESCE(MIN(performance_score), 0.0) as min_score,
                    COALESCE(MAX(performance_score), 0.0) as max_score
                FROM {table}
                WHERE tenant_id = ?
            """
            res = DB.fetch_one(sql, (self.tenant_id,))
            return {
                "subsystem": "billing_invoicing",
                "tier_index": 13,
                "class_index": 6,
                "total_entries": res["total_entries"] if res else 0,
                "total_volume_usd": round(res["total_volume"], 2) if res else 0.0,
                "average_volume_usd": round(res["average_volume"], 2) if res else 0.0,
                "mean_performance_score": round(res["mean_score"], 2) if res else 0.0,
                "min_score": round(res["min_score"], 2) if res else 0.0,
                "max_score": round(res["max_score"], 2) if res else 0.0
            }
        except Exception:
            return {"total_entries": 0, "total_volume_usd": 0.0}
