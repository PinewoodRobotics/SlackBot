"""React to WordleBot shares in #wordle that score 99/99 on Skill or Luck."""

import logging
import re

import config
from events.keyword_reactions import add_reactions
from events.poll import is_user_message

log = logging.getLogger(__name__)

_PERFECT = {
    re.compile(r"\bskill\s*99\s*/\s*99\b", re.IGNORECASE): config.PERFECT_SKILL_EMOJI,
    re.compile(r"\bluck\s*99\s*/\s*99\b", re.IGNORECASE): config.PERFECT_LUCK_EMOJI,
}


def perfect_score_reactions(text):
    return [emoji for pattern, emoji in _PERFECT.items() if pattern.search(text)]


def handle_message(event, client):
    if not is_user_message(event):
        return
    if event.get("channel") != config.WORDLE_CHANNEL_ID:
        return
    ts = event.get("ts")
    names = perfect_score_reactions(event.get("text") or "")
    if not ts or not names:
        return

    log.info("Perfect Wordle score on %s: %s", ts, names)
    add_reactions(client, config.WORDLE_CHANNEL_ID, ts, names)
