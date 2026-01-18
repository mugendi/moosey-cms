"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

from pathlib import Path
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class ScriptInjectorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, script: str):
        super().__init__(app)
        self.script = script

    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        response = await call_next(request)

        # We only want to touch HTML pages, not JSON APIs or Images
        content_type = response.headers.get("content-type", "")
        # get content length
        content_length = response.headers.get("content-length")

        # Skip if not HTML
        if "text/html" not in content_type:
            return response

        # Skip if too big (e.g. > 20KB) to prevent Memory DoS
        if content_length and int(content_length) > 20 * 1024 :
            return response


        # Read the response body
        # Note: Response body is a stream, we must consume it to modify it
        response_body = [section async for section in response.body_iterator]
        full_body = b"".join(response_body)

        # Prepare the injection
        # Encode the script to bytes
        injection = self.script.encode("utf-8")

        # Inject the script
        # We look for the closing body tag
        if b"</body>" in full_body:
            full_body = full_body.replace(b"</body>", injection + b"</body>")
        else:
            # Fallback: Just append if no body tag found
            full_body += injection

        # Create a NEW Response object
        # We cannot modify the existing response easily because Content-Length
        # would be wrong. Creating a new one recalculates headers.
        new_response = Response(
            content=full_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

        # Remove Content-Length so Starlette recalculates it automatically
        if "content-length" in new_response.headers:
            del new_response.headers["content-length"]

        return new_response


def inject_script_middleware(app, host, port):
    # Your custom script to inject
    package_root = Path(__file__).resolve().parent
    javascript_file = package_root / "static" / "js" / "reload-script.js"

    if not javascript_file.exists():
        print(f"⚠️  CMS Error: Hot reload script not found at: {js_file}")
        return

    with open(javascript_file, encoding="utf-8") as f:
        content = f.read()

    script_data = content.replace(
        "{{host}}",
        f"{host}:{port}",
    )

    # Add the middleware
    app.add_middleware(
        ScriptInjectorMiddleware, script=f"<script>{script_data}</script>"
    )
