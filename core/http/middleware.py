"""
CRM System - HTTP Middleware Pipeline
Zero external middleware dependencies
"""

import time
import uuid
import os
import mimetypes
from typing import Callable, List, Dict, Tuple, Optional
from core.http.request import Request
from core.http.response import Response
from config.app_config import CONFIG


MiddlewareFunc = Callable[[Request, Callable[[Request], Response]], Response]


class MiddlewareStack:
    def __init__(self):
        self.middlewares: List[MiddlewareFunc] = []

    def use(self, middleware: MiddlewareFunc):
        self.middlewares.append(middleware)

    def execute(self, request: Request, terminal_handler: Callable[[Request], Response]) -> Response:
        """Execute chain of middlewares surrounding the terminal handler."""
        def create_next(index: int):
            if index < len(self.middlewares):
                current_mw = self.middlewares[index]
                return lambda req: current_mw(req, create_next(index + 1))
            else:
                return terminal_handler

        pipeline = create_next(0)
        return pipeline(request)


# -------------------------------------------------------------
# Standard Built-in Middlewares
# -------------------------------------------------------------

def request_id_middleware(request: Request, next_handler: Callable[[Request], Response]) -> Response:
    """Assigns unique UUID to every request for tracing and audit trails."""
    req_id = request.header("x-request-id") or str(uuid.uuid4())
    request.request_id = req_id
    response = next_handler(request)
    response.set_header("X-Request-ID", req_id)
    return response


def cors_middleware(request: Request, next_handler: Callable[[Request], Response]) -> Response:
    """Handles Cross-Origin Resource Sharing headers & Preflight requests."""
    if request.method == "OPTIONS":
        res = Response(status_code=204)
        res.set_header("Access-Control-Allow-Origin", "*")
        res.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        res.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With, X-Request-ID")
        res.set_header("Access-Control-Max-Age", "86400")
        return res

    response = next_handler(request)
    response.set_header("Access-Control-Allow-Origin", "*")
    response.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
    response.set_header("Access-Control-Allow-Headers", "Authorization, Content-Type, Accept, X-Requested-With, X-Request-ID")
    return response


def security_headers_middleware(request: Request, next_handler: Callable[[Request], Response]) -> Response:
    """Attaches standard enterprise security headers."""
    response = next_handler(request)
    response.set_header("X-Content-Type-Options", "nosniff")
    response.set_header("X-Frame-Options", "DENY")
    response.set_header("X-XSS-Protection", "1; mode=block")
    response.set_header("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


class RateLimiter:
    """Sliding-window IP rate limiter without external Redis."""
    def __init__(self, max_requests: int = 600, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.ip_records: Dict[str, List[float]] = {}

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        timestamps = self.ip_records.get(ip, [])
        # Filter old timestamps
        timestamps = [ts for ts in timestamps if ts > window_start]
        
        if len(timestamps) >= self.max_requests:
            self.ip_records[ip] = timestamps
            return False
            
        timestamps.append(now)
        self.ip_records[ip] = timestamps
        return True


GLOBAL_RATE_LIMITER = RateLimiter(CONFIG.security.rate_limit_requests_per_minute, 60)


def rate_limit_middleware(request: Request, next_handler: Callable[[Request], Response]) -> Response:
    client_ip = request.client_address[0] if request.client_address else "127.0.0.1"
    if not GLOBAL_RATE_LIMITER.is_allowed(client_ip):
        return Response.bad_request("Rate limit exceeded. Please throttle your requests.")
    return next_handler(request)


def static_file_handler(request: Request) -> Optional[Response]:
    """Serve static files from /static/ directory if path matches."""
    if not request.path.startswith("/static/"):
        return None

    rel_path = request.path[len("/static/"):].lstrip("/")
    base_dir = os.path.abspath(CONFIG.server.static_dir)
    target_path = os.path.abspath(os.path.join(base_dir, rel_path))

    # Security check: Prevent path traversal
    if not target_path.startswith(base_dir):
        return Response.forbidden("Access denied: Invalid file path")

    if os.path.isfile(target_path):
        mime_type, _ = mimetypes.guess_type(target_path)
        mime_type = mime_type or "application/octet-stream"
        
        try:
            with open(target_path, "rb") as f:
                content = f.read()
            return Response(status_code=200, headers={"Content-Type": mime_type, "Cache-Control": "public, max-age=3600"}, body=content)
        except Exception:
            return Response.internal_error("Failed to read static asset")

    return Response.not_found("Static asset not found")
