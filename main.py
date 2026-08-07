#!/usr/bin/env python3
import logging
import sys

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

import config
from commands import add_all, ping
from events import channels, mentions
from utils.autojoin import join_all_public_channels_async

REGISTRARS = (ping, add_all, channels, mentions)

log = logging.getLogger(__name__)


def build_app():
    app = App(token=config.BOT_TOKEN, signing_secret=config.SIGNING_SECRET)
    for module in REGISTRARS:
        module.register(app)
    return app


def main():
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )

    app = build_app()
    join_all_public_channels_async(app.client)

    if config.APP_TOKEN:
        log.info("Starting in Socket Mode")
        SocketModeHandler(app, config.APP_TOKEN).start()
    else:
        log.info("Starting HTTP server on port %d", config.PORT)
        app.start(port=config.PORT)


if __name__ == "__main__":
    main()
