"""Seed Quick Poll-style reactions on messages containing -poll.

Quick Poll already does this in a few channels (see QUICK_POLL_CHANNEL_IDS);
those rooms are skipped so we don't double-react.
"""

import logging

from slack_sdk.errors import SlackApiError

import config

log = logging.getLogger(__name__)

# User-authored posts Slack tags with a subtype. Everything else (edits, joins,
# deletes, bot_message, …) is ignored so we don't loop or react to system events.
_ALLOWED_SUBTYPES = frozenset({"file_share", "thread_broadcast"})


def should_seed_poll_reactions(event):
    if event.get("bot_id"):
        return False

    subtype = event.get("subtype")
    if subtype and subtype not in _ALLOWED_SUBTYPES:
        return False

    if event.get("channel") in config.QUICK_POLL_CHANNEL_IDS:
        return False

    text = event.get("text") or ""
    return config.POLL_TRIGGER in text


def seed_poll_reactions(client, channel, ts):
    for name in config.POLL_REACTION_EMOJIS:
        try:
            client.reactions_add(channel=channel, timestamp=ts, name=name)
        except SlackApiError as e:
            error = _slack_error(e)
            if error == "already_reacted":
                continue
            log.warning(
                "Failed to add reaction %s to %s in %s: %s",
                name,
                ts,
                channel,
                error,
            )


def register(app):
    @app.event("message")
    def handle_message(event, client):
        if not should_seed_poll_reactions(event):
            return

        channel = event.get("channel")
        ts = event.get("ts")
        if not channel or not ts:
            return

        log.info("Seeding -poll reactions on %s in %s", ts, channel)
        seed_poll_reactions(client, channel, ts)


def _slack_error(exc):
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc)
    try:
        return response.get("error") or str(exc)
    except Exception:
        return str(exc)
