"""Production entrypoint: `gunicorn wsgi:application`."""

import io
import logging

from slack_bolt.adapter.wsgi import SlackRequestHandler

import config
from main import build_app, configure_logging
from utils.autojoin import join_all_public_channels_async

log = logging.getLogger(__name__)

WORKSPACE_URL = "https://pinewoodrobotics.slack.com"

INDEX_HTML = f"""<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pinewood Robotics Slack Bot</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{
    margin: 0;
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 1.5rem;
    font: 1rem/1.6 system-ui, -apple-system, "Segoe UI", sans-serif;
    background: Canvas;
    color: CanvasText;
  }}
  main {{ max-width: 32rem; text-align: center; }}
  p {{ margin: 0 0 0.75rem; }}
  p:last-child {{ margin-bottom: 0; }}
</style>
<main>
  <p>This is the Pinewood Robotics Slack bot.</p>
  <p>Looking for Slack? <a href="{WORKSPACE_URL}">Pinewood Robotics Slack Workspace</a></p>
</main>
</html>
"""

STATIC_ROUTES = {
    "/": ("text/html; charset=utf-8", INDEX_HTML.encode()),
    config.HEALTH_PATH: ("application/json", b'{"status":"ok"}'),
}


def _with_static_routes_and_chunked_support(wsgi_app):
    def application(environ, start_response):
        route = STATIC_ROUTES.get(environ.get("PATH_INFO"))
        if route is not None:
            content_type, body = route
            start_response(
                "200 OK",
                [("content-type", content_type), ("content-length", str(len(body)))],
            )
            return [] if environ.get("REQUEST_METHOD") == "HEAD" else [body]

        # Bolt's WSGI adapter reads exactly CONTENT_LENGTH bytes. A chunked
        # request would reach it as an empty body and fail signature
        # verification, which surfaces as a 401 that looks like a bad secret.
        if not environ.get("CONTENT_LENGTH") and environ.get("HTTP_TRANSFER_ENCODING"):
            body = environ["wsgi.input"].read()
            environ["wsgi.input"] = io.BytesIO(body)
            environ["CONTENT_LENGTH"] = str(len(body))

        return wsgi_app(environ, start_response)

    return application


configure_logging()

bolt_app = build_app()
application = _with_static_routes_and_chunked_support(
    SlackRequestHandler(bolt_app, path=config.EVENTS_PATH)
)

if config.AUTOJOIN_ON_BOOT:
    join_all_public_channels_async(bolt_app.client)
