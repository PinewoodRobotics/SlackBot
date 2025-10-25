#!/usr/bin/env python3
"""
Simple Slack Bot with Bolt for Python
Handles:
- /ping slash command -> responds with "Pong!"
- Messages containing "hello" (case-insensitive) -> responds with "Hey there!"
"""

import os
import re
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Load environment variables from .env file
load_dotenv()

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


# Slash command: /add-all
@app.command("/add-all")
def handle_add_all_command(ack, command, client):
    """Handle the /add-all slash command - adds all workspace members to channel"""
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
            client.chat_postEphemeral(
                channel=channel_id,
                user=user_id,
                text="✅ All workspace members are already in this channel!"
            )
            return

        # Create user mention list
        user_mentions = " ".join([f"<@{u['id']}>" for u in users_to_add])

        # Send confirmation message (ephemeral - only visible to command user)
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
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
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=f"❌ Error: {str(e)}"
        )


# Handle confirmation button click
@app.action("confirm_add_all")
def handle_confirm_add_all(ack, body, client):
    """Handle the confirm button click"""
    ack()

    channel_id = body["actions"][0]["value"]
    user_id = body["user"]["id"]

    try:
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

        # Update the original message
        success_msg = f"✅ Successfully added {added_count} members to this channel!"
        if failed_users:
            success_msg += f"\n⚠️ Failed to add {len(failed_users)} users."

        client.chat_update(
            channel=channel_id,
            ts=body["message"]["ts"],
            text=success_msg,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": success_msg
                    }
                }
            ]
        )

        print(f"[/add-all] Added {added_count} users to channel {channel_id}")

    except Exception as e:
        print(f"[/add-all] Error during confirmation: {e}")
        client.chat_update(
            channel=channel_id,
            ts=body["message"]["ts"],
            text=f"❌ Error: {str(e)}",
            blocks=[]
        )


# Handle cancel button click
@app.action("cancel_add_all")
def handle_cancel_add_all(ack, body, client):
    """Handle the cancel button click"""
    ack()

    channel_id = body["channel"]["id"]

    # Update the original message
    client.chat_update(
        channel=channel_id,
        ts=body["message"]["ts"],
        text="❌ Cancelled. No users were added.",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "❌ Cancelled. No users were added."
                }
            }
        ]
    )

    print(f"[/add-all] Cancelled by user {body['user']['id']}")


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

