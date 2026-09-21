import unittest
from unittest.mock import Mock

from slack_sdk.errors import SlackApiError

from events.keyword_reactions import add_reactions, matching_reactions


class MatchingReactionsTest(unittest.TestCase):
    def test_nooo_variants(self):
        for text in ("noo", "nooo", "NOOOO", "well noooooooooooo way", "nöööö", "nooo!!!"):
            self.assertEqual(matching_reactions(text), ["nooo"], text)

    def test_nooo_non_matches(self):
        for text in ("no", "nook", "noon", "noodle", "nooooob", "snooooze", "noo7", "nooooo7"):
            self.assertEqual(matching_reactions(text), [], text)

    def test_67_listed_variants(self):
        for text in (
            "67", "six seven", "six-seven", "6-7", "6 7", "sixty seven",
            "sixty-seven", "six or seven", "6 to 7", "six to seven", "6 or 7",
            "6 and 7", "6&7", "6 & 7", "six and seven", "six & seven",
        ):
            self.assertEqual(matching_reactions(text), ["67"], text)

    def test_67_fuzzy_variants(self):
        for text in (
            "SIIIIX SEVVVEN", "siiix    seeeven", "6 seven", "six 7", "sixseven",
            "6️⃣7️⃣", ":six::seven:", "６７", "ｓｉｘ seven", "síx sevén", "six n seven",
            "SIXTY SEVEN!!", "it's 67 o'clock", "six...seven", "6—7",
        ):
            self.assertEqual(matching_reactions(text), ["67"], text)

    def test_67_non_matches(self):
        for text in ("1670", "670", "167", "6.7", "6/7", "6:7", "six sevens", "6 8 7", "seven six"):
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
