import unittest
from unittest.mock import Mock

from slack_sdk.errors import SlackApiError

from events.keyword_reactions import add_reactions, matching_reactions


class MatchingReactionsTest(unittest.TestCase):
    def test_nooo_variants(self):
        for text in ("nooo", "NOOOO", "well noooooooooooo way", "nooooooooooooo"):
            self.assertEqual(matching_reactions(text), ["nooo"], text)

    def test_no_and_noo_do_not_match(self):
        self.assertEqual(matching_reactions("no"), [])
        self.assertEqual(matching_reactions("noo"), [])
        self.assertEqual(matching_reactions("snooooze"), [])

    def test_67_variants(self):
        for text in (
            "67",
            "six seven",
            "six-seven",
            "6-7",
            "6 7",
            "sixty seven",
            "sixty-seven",
            "six or seven",
            "6 to 7",
            "six to seven",
            "6 or 7",
            "6 and 7",
            "6&7",
            "6 & 7",
            "six and seven",
            "six & seven",
            "SIX SEVEN!!",
            "it's 67 o'clock",
        ):
            self.assertEqual(matching_reactions(text), ["67"], text)

    def test_67_inside_other_numbers_does_not_match(self):
        for text in ("1670", "670", "167", "$6.7", "six sevens"):
            self.assertEqual(matching_reactions(text), [], text)

    def test_multiple_triggers_react_with_each(self):
        self.assertEqual(matching_reactions("noooo not 67"), ["nooo", "67"])


class AddReactionsTest(unittest.TestCase):
    def test_already_reacted_is_ignored(self):
        client = Mock()
        client.reactions_add.side_effect = SlackApiError(
            "already_reacted", {"error": "already_reacted"}
        )
        add_reactions(client, "C1", "1.2", ["nooo", "67"])
        self.assertEqual(client.reactions_add.call_count, 2)

    def test_errors_do_not_stop_later_reactions(self):
        client = Mock()
        client.reactions_add.side_effect = [
            SlackApiError("invalid_name", {"error": "invalid_name"}),
            None,
        ]
        add_reactions(client, "C1", "1.2", ["nooo", "67"])
        self.assertEqual(client.reactions_add.call_count, 2)


if __name__ == "__main__":
    unittest.main()
