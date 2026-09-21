"""React with an emoji when a message contains a trigger word.

Stands in for Slack's built-in "automated messages", which post the emoji as a
reply from Slackbot instead of reacting to the original message.
"""

import logging
import re

from slack_sdk.errors import SlackApiError

import config
from events.poll import _slack_error, is_user_message

log = logging.getLogger(__name__)

_MATCHERS = tuple(
    (emoji, re.compile(rf"(?<!\w)(?:{pattern})(?!\w)", re.IGNORECASE))
    for emoji, pattern in config.KEYWORD_REACTIONS
)


def matching_reactions(text):
    return [emoji for emoji, regex in _MATCHERS if regex.search(text)]


def add_reactions(client, channel, ts, names):
    for name in names:
        try:
            client.reactions_add(channel=channel, timestamp=ts, name=name)
        except SlackApiError as e:
            error = _slack_error(e)
            if error == "already_reacted":
                continue
            log.warning(
                "Failed to add reaction %s to %s in %s: %s", name, ts, channel, error
            )


def handle_message(event, client):
    if not is_user_message(event):
        return

    names = matching_reactions(event.get("text") or "")
    channel = event.get("channel")
    ts = event.get("ts")
    if not names or not channel or not ts:
        return

    log.info("Reacting %s to %s in %s", names, ts, channel)
    add_reactions(client, channel, ts, names)
