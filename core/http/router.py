"""
CRM System - Fast Path Parameter HTTP Router
Zero external routing framework dependencies
"""

import re
from typing import Callable, Dict, List, Tuple, Optional, Any
from core.http.request import Request
from core.http.response import Response


HandlerFunc = Callable[[Request], Response]


class Route:
    def __init__(self, method: str, path_pattern: str, handler: HandlerFunc):
        self.method = method.upper()
        self.path_pattern = path_pattern
        self.handler = handler
        
        # Compile parameterized paths (e.g., /api/leads/:id -> regex with named group)
        self.regex, self.param_names = self._compile_pattern(path_pattern)

    def _compile_pattern(self, pattern: str) -> Tuple[re.Pattern, List[str]]:
        param_names: List[str] = []
        segments = pattern.strip("/").split("/")
        regex_parts = []
        
        for seg in segments:
            if not seg:
                continue
            if seg.startswith(":"):
                param_name = seg[1:]
                param_names.append(param_name)
                regex_parts.append(rf"(?P<{param_name}>[^/]+)")
            elif seg == "*":
                regex_parts.append(r"(?P<wildcard>.*)")
                param_names.append("wildcard")
            else:
                regex_parts.append(re.escape(seg))
                
        if not regex_parts:
            regex_str = r"^/?$"
        else:
            regex_str = r"^/" + r"/".join(regex_parts) + r"/?$"
            
        return re.compile(regex_str), param_names

    def match(self, path: str) -> Optional[Dict[str, str]]:
        match = self.regex.match(path)
        if match:
            return match.groupdict()
        return None


class Router:
    def __init__(self):
        self.routes: List[Route] = []

    def add_route(self, method: str, path: str, handler: HandlerFunc):
        self.routes.append(Route(method, path, handler))

    def get(self, path: str, handler: HandlerFunc):
        self.add_route("GET", path, handler)

    def post(self, path: str, handler: HandlerFunc):
        self.add_route("POST", path, handler)

    def put(self, path: str, handler: HandlerFunc):
        self.add_route("PUT", path, handler)

    def patch(self, path: str, handler: HandlerFunc):
        self.add_route("PATCH", path, handler)

    def delete(self, path: str, handler: HandlerFunc):
        self.add_route("DELETE", path, handler)

    def options(self, path: str, handler: HandlerFunc):
        self.add_route("OPTIONS", path, handler)

    def resolve(self, method: str, path: str) -> Tuple[Optional[HandlerFunc], Dict[str, str], bool]:
        """
        Find handler for method and path.
        Returns (Handler, PathParams, PathMatchedOtherMethod)
        """
        method = method.upper()
        path_matched_other_method = False
        
        for route in self.routes:
            params = route.match(path)
            if params is not None:
                if route.method == method:
                    return route.handler, params, False
                else:
                    path_matched_other_method = True
                    
        return None, {}, path_matched_other_method
