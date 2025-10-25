#!/usr/bin/env python3
"""
Simple Slack Bot with Bolt for Python
Handles:
- /ping slash command -> responds with "Pong!"
- Messages containing "hello" (case-insensitive) -> responds with "Hey there!"
"""

import os
import re
import sys
import threading
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Force unbuffered output for logging
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Load environment variables from .env file
load_dotenv()

# Initialize the Slack app
# For production (HTTP mode), remove socket_mode lines and use signing_secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Join all public channels (runs in background)
def join_all_public_channels_async():
    def _worker():
        try:
            cursor = None
            joined = 0
            while True:
                resp = app.client.conversations_list(types="public_channel", limit=200, cursor=cursor)
                channels = resp.get("channels", [])
                for ch in channels:
                    if ch.get("is_member") or ch.get("is_archived"):
                        continue
                    cid = ch.get("id")
                    try:
                        app.client.conversations_join(channel=cid)
                        joined += 1
                        print(f"[auto-join] Joined public channel {cid}")
                    except Exception as e:
                        # Ignore if already in channel or cannot join
                        print(f"[auto-join] Could not join {cid}: {e}")
                cursor = resp.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            print(f"[auto-join] Completed joining public channels. Joined: {joined}")
        except Exception as e:
            print(f"[auto-join] Error: {e}")
    t = threading.Thread(target=_worker, daemon=True)
    t.start()



# Slash command: /ping
@app.command("/ping")
def handle_ping_command(ack, respond, command):
    """Handle the /ping slash command"""
    print(f"[DEBUG /ping] Command received from user {command['user_id']} in channel {command['channel_id']}")
    # Acknowledge the command request
    ack()
    # Respond with "Pong!"
    respond("Pong!")
    print(f"[DEBUG /ping] Response sent")


# Message listener: detects "hello" (case-insensitive)
@app.message(re.compile("hello", re.IGNORECASE))
def handle_hello_message(message, say):
    """Handle messages containing 'hello' (case-insensitive)"""
    user_id = message.get("user")
    print(f"[DEBUG hello] Message detected from user {user_id} in channel {message.get('channel')}")
    say(f"Hey there <@{user_id}>!")
    print(f"[DEBUG hello] Response sent")


# Slash command: /add-all
@app.command("/add-all")
def handle_add_all_command(ack, command, client, respond):
    """Handle the /add-all slash command - adds all workspace members to channel"""
    print(f"[DEBUG /add-all] Command received from user {command['user_id']} in channel {command['channel_id']}")
    ack()

    channel_id = command["channel_id"]
    user_id = command["user_id"]

    try:
        # Get all workspace members
        users_response = client.users_list()
        all_users = users_response["members"]

        # Filter out bots and deactivated users
        active_users = [
            u for u in all_users
            if not u.get("is_bot", False)
            and not u.get("deleted", False)
            and u["id"] != "USLACKBOT"
        ]

        # Get current channel members
        channel_members_response = client.conversations_members(channel=channel_id)
        current_members = set(channel_members_response["members"])

        # Find users not in channel
        users_to_add = [u for u in active_users if u["id"] not in current_members]

        if not users_to_add:
            respond(text="✅ All workspace members are already in this channel!", replace_original=False)
            return

        # Create user mention list
        user_mentions = " ".join([f"<@{u['id']}>" for u in users_to_add])

        # Send confirmation message (ephemeral via response_url)
        respond(
            text=f"⚠️ You're about to add {len(users_to_add)} members to this channel:\n\n{user_mentions}",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Add {len(users_to_add)} members to this channel?*\n\n{user_mentions}"
                    }
                },
                {
                    "type": "actions",
                    "block_id": "add_all_confirmation",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Confirm"
                            },
                            "style": "primary",
                            "action_id": "confirm_add_all",
                            "value": channel_id
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Cancel"
                            },
                            "style": "danger",
                            "action_id": "cancel_add_all"
                        }
                    ]
                }
            ]
        )

        print(f"[/add-all] Confirmation sent to user {user_id} for channel {channel_id}")

    except Exception as e:
        print(f"[/add-all] Error: {e}")
        respond(text="❌ Something went wrong. Most likely, you need to invite the Pinewood Robot to your channel first (especially if its a private channel).")


# Handle confirmation button click
@app.action("confirm_add_all")
def handle_confirm_add_all(ack, body, client):
    """Handle the confirm button click"""
    print(f"[DEBUG confirm_add_all] Button clicked by user {body['user']['id']}")
    ack()

    channel_id = body["actions"][0]["value"]
    response_url = body["response_url"]

    try:
        # Ensure bot is in the channel (auto-join for public channels)
        try:
            client.conversations_join(channel=channel_id)
        except Exception as _:
            pass

        # Get all workspace members again (in case it changed)
        users_response = client.users_list()
        all_users = users_response["members"]

        # Filter out bots and deactivated users
        active_users = [
            u for u in all_users
            if not u.get("is_bot", False)
            and not u.get("deleted", False)
            and u["id"] != "USLACKBOT"
        ]

        # Get current channel members
        channel_members_response = client.conversations_members(channel=channel_id)
        current_members = set(channel_members_response["members"])

        # Find users not in channel
        users_to_add = [u for u in active_users if u["id"] not in current_members]

        if not users_to_add:
            # Delete the original message
            import requests
            requests.post(response_url, json={"delete_original": True})
            client.chat_postMessage(channel=channel_id, text="✅ Everyone is already here.")
            return

        # Add users to channel
        added_count = 0
        failed_users = []

        for user in users_to_add:
            try:
                client.conversations_invite(channel=channel_id, users=user["id"])
                added_count += 1
            except Exception as e:
                failed_users.append(user["id"])
                print(f"[/add-all] Failed to add user {user['id']}: {e}")

        success_msg = f"✅ Successfully added {added_count} members to this channel!"
        if failed_users:
            success_msg += f"\n⚠️ Failed to add {len(failed_users)} users."

        # Delete the confirmation message and post success in channel
        import requests
        requests.post(response_url, json={"delete_original": True})
        client.chat_postMessage(channel=channel_id, text=success_msg)

        print(f"[/add-all] Added {added_count} users to channel {channel_id}")

    except Exception as e:
        print(f"[/add-all] Error during confirmation: {e}")
        import requests
        requests.post(response_url, json={
            "replace_original": True,
            "text": "❌ Error: I may not be in this channel. Please add me first and try again."
        })


# Handle cancel button click
@app.action("cancel_add_all")
def handle_cancel_add_all(ack, body):
    """Handle the cancel button click"""
    print(f"[DEBUG cancel_add_all] Button clicked by user {body['user']['id']}")
    ack()

    response_url = body["response_url"]

    # Delete the original message
    import requests
    requests.post(response_url, json={"delete_original": True})

    print(f"[DEBUG cancel_add_all] Message deleted")


# Auto-join new public channels when they're created
@app.event("channel_created")
def handle_channel_created(event, client):
    print(f"[DEBUG channel_created] Event received: {event}")
    try:
        cid = event.get("channel", {}).get("id")
        if cid:
            client.conversations_join(channel=cid)
            print(f"[DEBUG channel_created] Joined newly created channel {cid}")
    except Exception as e:
        print(f"[DEBUG channel_created] Failed to join newly created channel: {e}")


# Health check endpoint (useful for monitoring)
@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle when the bot is mentioned"""
    print(f"[DEBUG app_mention] Event received from user {event.get('user')} in channel {event.get('channel')}")
    say("👋 I'm alive! Try `/ping` or say 'hello'!")
    print(f"[DEBUG app_mention] Response sent")



if __name__ == "__main__":
    # Start the app on port 3000
    # The app will listen for incoming requests from Slack
    port = int(os.environ.get("PORT", 3000))
    print(f"⚡️ Slack bot is starting on port {port}...")
    # Kick off background auto-join on startup
    join_all_public_channels_async()
    app.start(port=port)

