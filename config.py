import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")
PORT = int(os.environ.get("PORT", 3000))

# Presence of an app-level token is what selects Socket Mode over the HTTP server.
APP_TOKEN = os.environ.get("SLACK_APP_TOKEN")
