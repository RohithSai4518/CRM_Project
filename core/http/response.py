"""
CRM System - Custom HTTP Response Builder
Zero external HTTP framework dependencies
"""

import json
from typing import Dict, Any, Optional, Union, List


class Response:
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: Union[bytes, str, Dict[str, Any], List[Any]] = b"",
        content_type: str = "text/plain; charset=utf-8"
    ):
        self.status_code = status_code
        self.headers: Dict[str, str] = headers if headers is not None else {}
        self.content_type = content_type
        
        if "Content-Type" not in self.headers and "content-type" not in self.headers:
            self.headers["Content-Type"] = self.content_type
            
        self.body_bytes: bytes = b""
        self.set_body(body)

    def set_body(self, body: Union[bytes, str, Dict[str, Any], List[Any]]):
        """Set response body and automatically handle encoding."""
        if isinstance(body, bytes):
            self.body_bytes = body
        elif isinstance(body, str):
            self.body_bytes = body.encode('utf-8')
        elif isinstance(body, (dict, list)):
            self.headers["Content-Type"] = "application/json; charset=utf-8"
            self.body_bytes = json.dumps(body, default=str).encode('utf-8')
        else:
            self.body_bytes = str(body).encode('utf-8')

    def set_header(self, key: str, value: str) -> "Response":
        """Set a header on the response."""
        self.headers[key] = value
        return self

    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: int = 86400,
        path: str = "/",
        http_only: bool = True,
        same_site: str = "Lax",
        secure: bool = False
    ) -> "Response":
        """Set a Set-Cookie header."""
        cookie_parts = [
            f"{name}={value}",
            f"Path={path}",
            f"Max-Age={max_age}",
            f"SameSite={same_site}"
        ]
        if http_only:
            cookie_parts.append("HttpOnly")
        if secure:
            cookie_parts.append("Secure")
            
        self.set_header("Set-Cookie", "; ".join(cookie_parts))
        return self

    @classmethod
    def json(cls, data: Any, status_code: int = 200) -> "Response":
        """Factory for JSON responses."""
        payload = json.dumps(data, default=str).encode('utf-8')
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(payload))
        }
        return cls(status_code=status_code, headers=headers, body=payload)

    @classmethod
    def html(cls, html_content: str, status_code: int = 200) -> "Response":
        """Factory for HTML responses."""
        payload = html_content.encode('utf-8')
        headers = {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Length": str(len(payload))
        }
        return cls(status_code=status_code, headers=headers, body=payload)

    @classmethod
    def ok(cls, data: Any = None, message: str = "Success") -> "Response":
        """Standard Success JSON envelope."""
        return cls.json({
            "success": True,
            "message": message,
            "data": data
        }, status_code=200)

    @classmethod
    def created(cls, data: Any = None, message: str = "Resource created successfully") -> "Response":
        """Standard Created JSON envelope."""
        return cls.json({
            "success": True,
            "message": message,
            "data": data
        }, status_code=201)

    @classmethod
    def bad_request(cls, message: str = "Bad Request", errors: Any = None) -> "Response":
        """Standard 400 Bad Request envelope."""
        return cls.json({
            "success": False,
            "message": message,
            "errors": errors or []
        }, status_code=400)

    @classmethod
    def unauthorized(cls, message: str = "Unauthorized: Access token missing or invalid") -> "Response":
        """Standard 401 Unauthorized envelope."""
        return cls.json({
            "success": False,
            "message": message
        }, status_code=401)

    @classmethod
    def forbidden(cls, message: str = "Forbidden: Insufficient privileges for this action") -> "Response":
        """Standard 403 Forbidden envelope."""
        return cls.json({
            "success": False,
            "message": message
        }, status_code=403)

    @classmethod
    def not_found(cls, message: str = "Resource not found") -> "Response":
        """Standard 404 Not Found envelope."""
        return cls.json({
            "success": False,
            "message": message
        }, status_code=404)

    @classmethod
    def internal_error(cls, message: str = "Internal server error") -> "Response":
        """Standard 500 Internal Error envelope."""
        return cls.json({
            "success": False,
            "message": message
        }, status_code=500)
