import logging

log = logging.getLogger(__name__)


def register(app):
    @app.event("app_mention")
    def handle_app_mention(event, say):
        user = event.get("user")
        log.info("Mentioned by %s in %s", user, event.get("channel"))
        say(f"Hey there <@{user}>!")
