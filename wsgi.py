"""Production entrypoint: `gunicorn wsgi:application`."""

import io
import logging

from slack_bolt.adapter.wsgi import SlackRequestHandler

import config
from main import build_app, configure_logging
from utils.autojoin import join_all_public_channels_async

log = logging.getLogger(__name__)

HEALTH_BODY = b'{"status":"ok"}'


def _with_health_and_chunked_support(wsgi_app):
    def application(environ, start_response):
        if environ.get("PATH_INFO") == config.HEALTH_PATH:
            start_response(
                "200 OK",
                [
                    ("content-type", "application/json"),
                    ("content-length", str(len(HEALTH_BODY))),
                ],
            )
            return [HEALTH_BODY]

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
application = _with_health_and_chunked_support(
    SlackRequestHandler(bolt_app, path=config.EVENTS_PATH)
)

if config.AUTOJOIN_ON_BOOT:
    join_all_public_channels_async(bolt_app.client)
