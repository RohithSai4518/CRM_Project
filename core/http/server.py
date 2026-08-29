"""
CRM System - Multi-Threaded HTTP Server
Built using standard library socketserver/http.server
"""

import http.server
import socketserver
import urllib.parse
import traceback
import sys
from typing import Optional
from core.http.request import Request
from core.http.response import Response
from core.http.router import Router
from core.http.middleware import (
    MiddlewareStack,
    request_id_middleware,
    cors_middleware,
    security_headers_middleware,
    rate_limit_middleware,
    static_file_handler
)
from config.app_config import CONFIG


class CRMHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        if CONFIG.server.debug:
            sys.stdout.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")

    def do_GET(self):
        self._handle_request("GET")

    def do_POST(self):
        self._handle_request("POST")

    def do_PUT(self):
        self._handle_request("PUT")

    def do_PATCH(self):
        self._handle_request("PATCH")

    def do_DELETE(self):
        self._handle_request("DELETE")

    def do_OPTIONS(self):
        self._handle_request("OPTIONS")

    def _handle_request(self, method: str):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            raw_path = parsed_url.path
            query_params = urllib.parse.parse_qs(parsed_url.query)

            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length > 0 else b""

            headers_dict = {k: v for k, v in self.headers.items()}
            request = Request(
                method=method,
                path=raw_path,
                headers=headers_dict,
                query_params=query_params,
                body_bytes=body_bytes,
                client_address=self.client_address
            )

            # Retrieve parent CRMServer instance attached to httpd
            crm_app: CRMServer = self.server.crm_app  # type: ignore
            
            # 1. Check static file handler first
            static_res = static_file_handler(request)
            if static_res is not None:
                self._send_response(static_res)
                return

            # 2. Main route dispatch function
            def terminal_dispatch(req: Request) -> Response:
                handler, path_params, other_method = crm_app.router.resolve(req.method, req.path)
                if handler is not None:
                    req.path_params = path_params
                    try:
                        return handler(req)
                    except ValueError as ve:
                        return Response.bad_request(str(ve))
                    except PermissionError as pe:
                        return Response.forbidden(str(pe))
                    except Exception as e:
                        if CONFIG.server.debug:
                            traceback.print_exc()
                        return Response.internal_error(f"Internal processing error: {str(e)}")
                elif other_method:
                    res = Response.bad_request("HTTP Method not allowed for this route")
                    res.status_code = 405
                    return res
                else:
                    return Response.not_found(f"Route '{req.path}' not found on OmniFlow CRM")

            # 3. Pass through middleware stack
            final_response = crm_app.middleware_stack.execute(request, terminal_dispatch)
            self._send_response(final_response)

        except Exception as ex:
            traceback.print_exc()
            err_res = Response.internal_error("Fatal server exception")
            self._send_response(err_res)

    def _send_response(self, response: Response):
        self.send_response(response.status_code)
        for header_key, header_val in response.headers.items():
            self.send_header(header_key, header_val)
        
        if "Content-Length" not in response.headers:
            self.send_header("Content-Length", str(len(response.body_bytes)))
            
        self.end_headers()
        self.wfile.write(response.body_bytes)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    crm_app: Optional["CRMServer"] = None


class CRMServer:
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        self.host = host or CONFIG.server.host
        self.port = port or CONFIG.server.port
        self.router = Router()
        self.middleware_stack = MiddlewareStack()
        
        # Register default middlewares
        self.middleware_stack.use(request_id_middleware)
        self.middleware_stack.use(cors_middleware)
        self.middleware_stack.use(security_headers_middleware)
        self.middleware_stack.use(rate_limit_middleware)
        
        self.httpd: Optional[ThreadedHTTPServer] = None

    def start(self):
        self.httpd = ThreadedHTTPServer((self.host, self.port), CRMHTTPRequestHandler)
        self.httpd.crm_app = self
        print("================================================================")
        print(f"[*] {CONFIG.app_name} [v{CONFIG.app_version}]")
        print(f"[*] Server actively running on http://{self.host}:{self.port}")
        print("[*] Security: Active RBAC, Zero-GPL, Tamper-Evident Audit Active")
        print("================================================================")
        try:
            self.httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down OmniFlow CRM Server...")
            self.httpd.shutdown()
