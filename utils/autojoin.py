import logging
import threading

log = logging.getLogger(__name__)


def join_all_public_channels_async(client):
    threading.Thread(target=_join_all_public_channels, args=(client,), daemon=True).start()


def _join_all_public_channels(client):
    joined = 0
    cursor = None
    try:
        while True:
            resp = client.conversations_list(
                types="public_channel", limit=200, cursor=cursor
            )
            for channel in resp.get("channels", []):
                if channel.get("is_member") or channel.get("is_archived"):
                    continue
                channel_id = channel["id"]
                try:
                    client.conversations_join(channel=channel_id)
                    joined += 1
                    log.info("Joined public channel %s", channel_id)
                except Exception as e:
                    log.info("Could not join %s: %s", channel_id, e)

            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        log.info("Finished joining public channels. Joined: %d", joined)
    except Exception:
        log.exception("Auto-join failed")
