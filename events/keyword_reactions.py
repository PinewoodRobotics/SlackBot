"""React with an emoji when a message contains a trigger word.

Stands in for Slack's built-in "automated messages", which post the emoji as a
reply from Slackbot instead of reacting to the original message.

Text is normalized (lowercased, diacritics stripped, keycap/emoji digits mapped
to ASCII, repeated letters collapsed) so triggers match the idea rather than a
list of spellings: "SIIIX SEVVEN", "6️⃣7️⃣" and "sixty-seven" all count as 67.
"""

import logging
import re
import unicodedata

from slack_sdk.errors import SlackApiError

import config
from events.poll import _slack_error, is_user_message

log = logging.getLogger(__name__)

_DIGIT_EMOJI = {
    ":zero:": "0", ":one:": "1", ":two:": "2", ":three:": "3", ":four:": "4",
    ":five:": "5", ":six:": "6", ":seven:": "7", ":eight:": "8", ":nine:": "9",
}
_ZERO_WIDTH = re.compile(r"[​-‍⁠️⃣]")
_REPEATED_LETTER = re.compile(r"([a-z])\1+")

# Kept out of the repeated-letter collapse because the count of o's is the trigger.
_NOOO = re.compile(r"(?<![a-z0-9])no{2,}(?![a-z0-9])")

_NUMBER_WORDS = {"six": "6", "sixty": "60", "seven": "7", "sixseven": "6 7"}
# Words allowed between the six and the seven. "6.7", "6/7" and "6:7" are
# deliberately not here; they read as a decimal, fraction or time.
_FILLERS = {"and", "or", "to", "&", "-", "–", "—", "n"}
_TOKEN = re.compile(r"[a-z]+|\d+|[&\-–—]")
_NUMERIC_SEPARATOR = re.compile(r"(?<=\d)[./:](?=\d)")
_SIX_SEVEN = re.compile(r"(?<![a-z0-9])(?:67|(?:6|60) (?:(?:and|or|to|&|-|–|—|n) )?7)(?![a-z0-9])")


def normalize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = _ZERO_WIDTH.sub("", text)
    for shortcode, digit in _DIGIT_EMOJI.items():
        text = text.replace(shortcode, digit)
    return text


def canonical_tokens(text):
    """Collapse repeated letters and spell number words as digits."""
    tokens = []
    for token in _TOKEN.findall(_NUMERIC_SEPARATOR.sub(" x ", text)):
        if token.isalpha():
            token = _REPEATED_LETTER.sub(r"\1", token)
            token = _NUMBER_WORDS.get(token, token)
        tokens.append(token)
    return " ".join(tokens)


def matching_reactions(text):
    normalized = normalize(text)
    names = []
    if _NOOO.search(normalized):
        names.append(config.NOOO_EMOJI)
    if _SIX_SEVEN.search(canonical_tokens(normalized)):
        names.append(config.SIX_SEVEN_EMOJI)
    return names


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
