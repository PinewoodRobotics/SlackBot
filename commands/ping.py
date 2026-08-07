import logging

log = logging.getLogger(__name__)


def register(app):
    @app.command("/ping")
    def handle_ping(ack, respond, command):
        ack()
        log.info("/ping from %s in %s", command["user_id"], command["channel_id"])
        respond("Pong!")
