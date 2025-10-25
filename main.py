#!/usr/bin/env python3
"""
Simple Slack Bot with Bolt for Python
Handles:
- /ping slash command -> responds with "Pong!"
- Messages containing "hello" (case-insensitive) -> responds with "Hey there!"
"""

import os
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Initialize the Slack app
# For production (HTTP mode), remove socket_mode lines and use signing_secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)


# Slash command: /ping
@app.command("/ping")
def handle_ping_command(ack, respond, command):
    """Handle the /ping slash command"""
    # Acknowledge the command request
    ack()
    # Respond with "Pong!"
    respond("Pong!")
    print(f"[/ping] Command received from user {command['user_name']}")


# Message listener: detects "hello" (case-insensitive)
@app.message(re.compile("hello", re.IGNORECASE))
def handle_hello_message(message, say):
    """Handle messages containing 'hello' (case-insensitive)"""
    user_id = message.get("user")
    say(f"Hey there <@{user_id}>!")
    print(f"[hello] Message detected from user {user_id}")


# Health check endpoint (useful for monitoring)
@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle when the bot is mentioned"""
    say("👋 I'm alive! Try `/ping` or say 'hello'!")


if __name__ == "__main__":
    # Start the app on port 3000
    # The app will listen for incoming requests from Slack
    port = int(os.environ.get("PORT", 3000))
    print(f"⚡️ Slack bot is starting on port {port}...")
    app.start(port=port)

