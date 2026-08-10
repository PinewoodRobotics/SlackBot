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
