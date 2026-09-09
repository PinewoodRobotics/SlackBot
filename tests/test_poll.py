import unittest
from unittest.mock import Mock

from slack_sdk.errors import SlackApiError

import config
from events.poll import seed_poll_reactions, should_seed_poll_reactions


def _event(**overrides):
    event = {
        "type": "message",
        "text": "lunch? -poll",
        "channel": "C00GENERAL",
        "ts": "123.456",
        "user": "U123",
    }
    event.update(overrides)
    return event


class ShouldSeedPollReactionsTest(unittest.TestCase):
    def test_user_message_with_poll_trigger(self):
        self.assertTrue(should_seed_poll_reactions(_event()))

    def test_trigger_is_substring(self):
        self.assertTrue(should_seed_poll_reactions(_event(text="please -poll now")))

    def test_no_trigger(self):
        self.assertFalse(should_seed_poll_reactions(_event(text="just chatting")))

    def test_skips_bots(self):
        self.assertFalse(should_seed_poll_reactions(_event(bot_id="B123")))

    def test_skips_edits_and_joins(self):
        self.assertFalse(
            should_seed_poll_reactions(_event(subtype="message_changed"))
        )
        self.assertFalse(should_seed_poll_reactions(_event(subtype="channel_join")))
        self.assertFalse(should_seed_poll_reactions(_event(subtype="bot_message")))

    def test_allows_file_share_and_thread_broadcast(self):
        self.assertTrue(should_seed_poll_reactions(_event(subtype="file_share")))
        self.assertTrue(should_seed_poll_reactions(_event(subtype="thread_broadcast")))

    def test_file_share_without_trigger(self):
        self.assertFalse(
            should_seed_poll_reactions(_event(subtype="file_share", text="photo"))
        )

    def test_skips_quick_poll_channels(self):
        for channel_id in config.QUICK_POLL_CHANNEL_IDS:
            self.assertFalse(
                should_seed_poll_reactions(_event(channel=channel_id)),
                channel_id,
            )

    def test_missing_text(self):
        self.assertFalse(should_seed_poll_reactions(_event(text=None)))

    def test_thread_reply_still_seeds(self):
        self.assertTrue(should_seed_poll_reactions(_event(thread_ts="111.222")))


class SeedPollReactionsTest(unittest.TestCase):
    def test_adds_both_quick_poll_emojis(self):
        client = Mock()
        seed_poll_reactions(client, "C00GENERAL", "123.456")
        names = [c.kwargs["name"] for c in client.reactions_add.call_args_list]
        self.assertEqual(list(config.POLL_REACTION_EMOJIS), names)

    def test_already_reacted_is_success(self):
        client = Mock()
        client.reactions_add.side_effect = SlackApiError(
            "already_reacted", {"error": "already_reacted"}
        )
        seed_poll_reactions(client, "C00GENERAL", "123.456")
        self.assertEqual(client.reactions_add.call_count, 2)

    def test_other_errors_do_not_stop_second_emoji(self):
        client = Mock()
        client.reactions_add.side_effect = [
            SlackApiError("missing_scope", {"error": "missing_scope"}),
            None,
        ]
        seed_poll_reactions(client, "C00GENERAL", "123.456")
        self.assertEqual(client.reactions_add.call_count, 2)


if __name__ == "__main__":
    unittest.main()
