import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
PORT = int(os.environ.get("PORT", 3000))

# Presence of an app-level token is what selects Socket Mode over the HTTP server.
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")

EVENTS_PATH = "/slack/events"
HEALTH_PATH = "/health"

# The startup sweep walks every public channel; once the workspace is backfilled,
# events/channels.py keeps up with new ones and this can be turned off.
AUTOJOIN_ON_BOOT = os.environ.get("AUTOJOIN_ON_BOOT", "true").lower() not in (
    "0",
    "false",
    "no",
)

# Quick Poll (DashPoll, Slack user U0BJZVAPG5B) already seeds -poll reactions in
# these channels. This bot must no-op there so we don't duplicate emoji.
QUICK_POLL_CHANNEL_IDS = frozenset(
    {
        "C09EK4LP656",  # #transit
        "C09DBURED53",  # #announcements
        "C09DADRS73M",  # #food-orders
    }
)

POLL_TRIGGER = "-poll"
POLL_REACTION_EMOJIS = (
    "sf-symbols_checkmark-square-fill",
    "sf-symbols_xmark-square-fill",
)
