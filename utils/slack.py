import requests

SLACKBOT_USER_ID = "USLACKBOT"


def active_members(client):
    members = client.users_list()["members"]
    return [
        u
        for u in members
        if not u.get("is_bot", False)
        and not u.get("deleted", False)
        and u["id"] != SLACKBOT_USER_ID
    ]


def members_missing_from(client, channel_id):
    current = set(client.conversations_members(channel=channel_id)["members"])
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
