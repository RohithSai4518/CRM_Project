"""
CRM System - Data Validation & Input Sanitization
"""

import re
import html
from typing import Dict, Any, List, Optional, Tuple


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+?[0-9\s\-\(\)\.]{7,25}$")


def sanitize_string(val: Optional[str]) -> str:
    """Strip dangerous characters and escape HTML."""
    if val is None:
        return ""
    return html.escape(val.strip())


def is_valid_email(email: Optional[str]) -> bool:
    if not email:
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: Optional[str]) -> bool:
    if not phone:
        return True  # Phone is optional in many fields
    return bool(PHONE_REGEX.match(phone.strip()))


class SchemaValidator:
    def __init__(self, rules: Dict[str, Dict[str, Any]]):
        """
        Rules format:
        {
            "name": {"type": str, "required": True, "min_len": 2, "max_len": 100},
            "email": {"type": str, "required": True, "format": "email"},
            "age": {"type": int, "required": False, "min": 0, "max": 120}
        }
        """
        self.rules = rules

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Dict[str, str], Dict[str, Any]]:
        errors: Dict[str, str] = {}
        cleaned_data: Dict[str, Any] = {}

        for field, rule in self.rules.items():
            val = data.get(field)
            req = rule.get("required", False)
            expected_type = rule.get("type", str)

            if val is None or (isinstance(val, str) and not val.strip()):
                if req:
                    errors[field] = f"Field '{field}' is required"
                else:
                    cleaned_data[field] = rule.get("default", None)
                continue

            # Type conversion/check
            try:
                if expected_type == int:
                    val = int(val)
                elif expected_type == float:
                    val = float(val)
                elif expected_type == bool:
                    val = bool(val) if not isinstance(val, str) else val.lower() in ("true", "1", "yes")
                elif expected_type == str:
                    val = str(val).strip()
            except (ValueError, TypeError):
                errors[field] = f"Field '{field}' must be of type {expected_type.__name__}"
                continue

            # Length bounds for strings
            if isinstance(val, str):
                if "min_len" in rule and len(val) < rule["min_len"]:
                    errors[field] = f"Field '{field}' must be at least {rule['min_len']} characters"
                if "max_len" in rule and len(val) > rule["max_len"]:
                    errors[field] = f"Field '{field}' must not exceed {rule['max_len']} characters"
                if rule.get("format") == "email" and not is_valid_email(val):
                    errors[field] = f"Field '{field}' is not a valid email address"
                if rule.get("format") == "phone" and not is_valid_phone(val):
                    errors[field] = f"Field '{field}' is not a valid phone number"

            # Numeric bounds
            if isinstance(val, (int, float)):
                if "min" in rule and val < rule["min"]:
                    errors[field] = f"Field '{field}' must be >= {rule['min']}"
                if "max" in rule and val > rule["max"]:
                    errors[field] = f"Field '{field}' must be <= {rule['max']}"

            # Choices enum validation
            if "choices" in rule and val not in rule["choices"]:
                errors[field] = f"Field '{field}' must be one of: {', '.join(map(str, rule['choices']))}"

            cleaned_data[field] = val

        return len(errors) == 0, errors, cleaned_data
