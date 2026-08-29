"""
CRM System - Custom HTTP Request Context & Parser
Zero external HTTP framework dependencies
"""

import json
import urllib.parse
from typing import Dict, Any, Optional, List


class Request:
    def __init__(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        query_params: Dict[str, List[str]],
        body_bytes: bytes,
        client_address: tuple,
    ):
        self.method = method.upper()
        self.path = path
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.query_params = query_params
        self.body_bytes = body_bytes
        self.client_address = client_address
        
        # Route matched parameters (e.g., /api/leads/:id -> {"id": "123"})
        self.path_params: Dict[str, str] = {}
        
        # Authentication & context state
        self.user: Optional[Dict[str, Any]] = None
        self.tenant_id: str = "default_tenant"
        self.request_id: str = ""
        self._parsed_json: Optional[Any] = None

    def query(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve single query parameter value."""
        values = self.query_params.get(key)
        if values and len(values) > 0:
            return values[0]
        return default

    def query_all(self, key: str) -> List[str]:
        """Retrieve list of all values for a query parameter."""
        return self.query_params.get(key, [])

    def header(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Retrieve header value in case-insensitive manner."""
        return self.headers.get(key.lower(), default)

    def json(self) -> Any:
        """Parse request body as JSON with caching."""
        if self._parsed_json is not None:
            return self._parsed_json
        
        if not self.body_bytes:
            self._parsed_json = {}
            return self._parsed_json
            
        try:
            text = self.body_bytes.decode('utf-8')
            self._parsed_json = json.loads(text)
            return self._parsed_json
        except Exception as ex:
            raise ValueError(f"Invalid JSON payload: {str(ex)}")

    def form_data(self) -> Dict[str, str]:
        """Parse URL-encoded form data."""
        try:
            text = self.body_bytes.decode('utf-8')
            parsed = urllib.parse.parse_qs(text)
            return {k: v[0] if v else "" for k, v in parsed.items()}
        except Exception:
            return {}

    @property
    def authorization_token(self) -> Optional[str]:
        """Extract Bearer token from Authorization header or Cookie."""
        auth = self.header("authorization")
        if auth and auth.startswith("Bearer "):
            return auth[7:].strip()
        
        cookie_header = self.header("cookie")
        if cookie_header:
            cookies = [c.strip() for c in cookie_header.split(";")]
            for c in cookies:
                if "=" in c:
                    k, v = c.split("=", 1)
                    if k.strip() == "CRM_SESSION_TOKEN":
                        return v.strip()
        return None
