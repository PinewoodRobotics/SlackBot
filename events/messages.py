"""Single listener for message events.

Bolt stops at the first listener whose matcher accepts an event, so two
@app.event("message") handlers would shadow each other. Fan out from here instead.
"""

from events import keyword_reactions, poll

HANDLERS = (poll.handle_message, keyword_reactions.handle_message)


def register(app):
    @app.event("message")
    def handle_message(event, client):
        for handler in HANDLERS:
            handler(event, client)
