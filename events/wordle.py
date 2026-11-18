"""React to WordleBot shares in #wordle that score 99/99 on Skill or Luck, or solve in 1 or 2."""

import logging
import re

import config
from events.keyword_reactions import add_reactions
from events.poll import is_user_message

log = logging.getLogger(__name__)

_PERFECT_SKILL = re.compile(r"\bskill\s*99\s*/\s*99\b", re.IGNORECASE)
_PERFECT_LUCK = re.compile(r"\bluck\s*99\s*/\s*99\b", re.IGNORECASE)
_QUICK_SOLVE = re.compile(r"\bwordle\s+[\d,]+\s+[12]\s*/\s*6\b", re.IGNORECASE)


def perfect_score_reactions(text):
    names = []
    if _PERFECT_SKILL.search(text):
        names.append(config.PERFECT_SKILL_EMOJI)
    if _PERFECT_LUCK.search(text) or _QUICK_SOLVE.search(text):
        names.append(config.PERFECT_LUCK_EMOJI)
    return names


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
