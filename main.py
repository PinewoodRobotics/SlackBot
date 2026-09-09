#!/usr/bin/env python3
"""Local development entrypoint. Production is served by wsgi.py under gunicorn."""

import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from commands import add_all, ping
from events import channels, mentions, poll
from utils.autojoin import join_all_public_channels_async

REGISTRARS = (ping, add_all, channels, mentions, poll)

log = logging.getLogger(__name__)


def build_app():
    app = App(
        token=config.BOT_TOKEN,
        signing_secret=config.SIGNING_SECRET,
        # Handlers keep making blocking Slack API calls after ack(); bolt's
        # default pool of 5 starves once an /add-all invite loop takes a thread.
        listener_executor=ThreadPoolExecutor(max_workers=10),
    )
    for module in REGISTRARS:
        module.register(app)
    return app


def configure_logging():
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )


def main():
    configure_logging()

    app = build_app()
    if config.AUTOJOIN_ON_BOOT:
        join_all_public_channels_async(app.client)

    if config.APP_TOKEN:
        log.info("Starting in Socket Mode")
        SocketModeHandler(app, config.APP_TOKEN).start()
    else:
        log.info("Starting HTTP server on port %d", config.PORT)
        app.start(port=config.PORT)


if __name__ == "__main__":
    main()
