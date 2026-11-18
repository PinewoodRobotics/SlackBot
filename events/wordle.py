"""React to WordleBot shares in #wordle that score Skill 99/99."""

import logging
import random
import re

import config
from events.keyword_reactions import add_reactions
from events.poll import is_user_message

log = logging.getLogger(__name__)

_PERFECT_SKILL = re.compile(r"\bskill\s*99\s*/\s*99\b", re.IGNORECASE)


def is_perfect_skill(text):
    return bool(_PERFECT_SKILL.search(text))


def handle_message(event, client):
    if not is_user_message(event):
        return
    if event.get("channel") != config.WORDLE_CHANNEL_ID:
        return
    ts = event.get("ts")
    if not ts or not is_perfect_skill(event.get("text") or ""):
        return

    log.info("Perfect Wordle skill on %s", ts)
    add_reactions(client, config.WORDLE_CHANNEL_ID, ts, [random.choice(config.PERFECT_SKILL_EMOJIS)])
