import threading
import time

import requests

SLACKBOT_USER_ID = "USLACKBOT"

# Slack applies a much stricter, unpublished limit to users.list when it is
# called without pagination, and /add-all hits it twice per run (prompt, then
# confirm). Paginate, and reuse the roster across those two calls.
MEMBER_CACHE_TTL = 60

_member_cache = {"fetched_at": 0.0, "members": []}
_member_cache_lock = threading.Lock()


def _all_users(client):
    users = []
    cursor = None
    while True:
        resp = client.users_list(limit=200, cursor=cursor)
        users.extend(resp["members"])
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return users


def is_full_member(user):
    """Active, non-guest human who has actually joined the workspace."""
    return not (
        user["id"] == SLACKBOT_USER_ID
        or user.get("is_bot")
        or user.get("is_app_user")
        or user.get("deleted")
        or user.get("is_restricted")
        or user.get("is_ultra_restricted")
        or user.get("is_invited_user")
    )


def active_members(client):
    with _member_cache_lock:
        if time.monotonic() - _member_cache["fetched_at"] < MEMBER_CACHE_TTL:
            return list(_member_cache["members"])

        members = [u for u in _all_users(client) if is_full_member(u)]
        _member_cache["members"] = members
        _member_cache["fetched_at"] = time.monotonic()
        return list(members)


def channel_members(client, channel_id):
    members = set()
    cursor = None
    while True:
        resp = client.conversations_members(channel=channel_id, limit=200, cursor=cursor)
        members.update(resp["members"])
        cursor = resp.get("response_metadata", {}).get("next_cursor")
        if not cursor:
            return members


def members_missing_from(client, channel_id):
    current = channel_members(client, channel_id)
    return [u for u in active_members(client) if u["id"] not in current]


def mention_list(users):
    return " ".join(f"<@{u['id']}>" for u in users)


def join_quietly(client, channel_id):
    try:
        client.conversations_join(channel=channel_id)
        return True
    except Exception:
        return False


def delete_original(response_url):
    requests.post(response_url, json={"delete_original": True})


def replace_original(response_url, text):
    requests.post(response_url, json={"replace_original": True, "text": text})
