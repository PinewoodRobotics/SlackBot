import logging

log = logging.getLogger(__name__)


def register(app):
    @app.event("channel_created")
    def handle_channel_created(event, client):
        channel_id = event.get("channel", {}).get("id")
        if not channel_id:
            return
        try:
            client.conversations_join(channel=channel_id)
            log.info("Joined newly created channel %s", channel_id)
        except Exception:
            log.exception("Failed to join newly created channel %s", channel_id)
