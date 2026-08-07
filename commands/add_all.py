import logging

from utils.slack import (
    delete_original,
    join_quietly,
    members_missing_from,
    mention_list,
    replace_original,
)

log = logging.getLogger(__name__)

NOT_IN_CHANNEL_HELP = (
    "❌ Something went wrong. Most likely, you need to invite the Pinewood Robot "
    "to your channel first (especially if its a private channel)."
)
CONFIRM_ACTION = "confirm_add_all"
CANCEL_ACTION = "cancel_add_all"


def register(app):
    @app.command("/add-all")
    def handle_add_all(ack, command, client, respond):
        ack()
        channel_id = command["channel_id"]
        user_id = command["user_id"]
        log.info("/add-all from %s in %s", user_id, channel_id)

        try:
            pending = members_missing_from(client, channel_id)

            if not pending:
                respond(
                    text="✅ All workspace members are already in this channel!",
                    replace_original=False,
                )
                return

            respond(**_confirmation_prompt(channel_id, pending))
            log.info("Confirmation sent to %s for %s", user_id, channel_id)
        except Exception:
            log.exception("/add-all failed for channel %s", channel_id)
            respond(text=NOT_IN_CHANNEL_HELP)

    @app.action(CONFIRM_ACTION)
    def handle_confirm(ack, body, client):
        ack()
        channel_id = body["actions"][0]["value"]
        response_url = body["response_url"]
        log.info("add-all confirmed by %s for %s", body["user"]["id"], channel_id)

        try:
            join_quietly(client, channel_id)

            # Re-read membership rather than trusting the list rendered in the prompt,
            # which may be minutes stale by the time someone clicks Confirm.
            pending = members_missing_from(client, channel_id)
            if not pending:
                delete_original(response_url)
                client.chat_postMessage(
                    channel=channel_id, text="✅ Everyone is already here."
                )
                return

            added, failed = _invite_all(client, channel_id, pending)

            summary = f"✅ Successfully added {added} members to this channel!"
            if failed:
                summary += f"\n⚠️ Failed to add {len(failed)} users."

            delete_original(response_url)
            client.chat_postMessage(channel=channel_id, text=summary)
            log.info("Added %d users to %s", added, channel_id)
        except Exception:
            log.exception("add-all confirmation failed for %s", channel_id)
            replace_original(
                response_url,
                "❌ Error: I may not be in this channel. Please add me first and try again.",
            )

    @app.action(CANCEL_ACTION)
    def handle_cancel(ack, body):
        ack()
        log.info("add-all cancelled by %s", body["user"]["id"])
        delete_original(body["response_url"])


def _invite_all(client, channel_id, users):
    added = 0
    failed = []
    for user in users:
        try:
            client.conversations_invite(channel=channel_id, users=user["id"])
            added += 1
        except Exception as e:
            failed.append(user["id"])
            log.warning("Failed to add %s to %s: %s", user["id"], channel_id, e)
    return added, failed


def _confirmation_prompt(channel_id, users):
    mentions = mention_list(users)
    return {
        "text": f"⚠️ You're about to add {len(users)} members to this channel:\n\n{mentions}",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"⚠️ *Add {len(users)} members to this channel?*\n\n{mentions}",
                },
            },
            {
                "type": "actions",
                "block_id": "add_all_confirmation",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Confirm"},
                        "style": "primary",
                        "action_id": CONFIRM_ACTION,
                        "value": channel_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Cancel"},
                        "style": "danger",
                        "action_id": CANCEL_ACTION,
                    },
                ],
            },
        ],
    }
