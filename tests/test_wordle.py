import unittest
from unittest.mock import Mock

import config
from events.wordle import handle_message, perfect_score_reactions

SHARE = "Wordle 1,977 {guesses}/6\n\n:large_green_square:\n\nWordleBot\nSkill {skill}/99\nLuck {luck}/99"


class WordleTest(unittest.TestCase):
    def test_perfect_scores(self):
        cases = {
            (99, 76): ["woooo"],
            (62, 99): ["skelly-dance-rainbow"],
            (99, 99): ["woooo", "skelly-dance-rainbow"],
            (89, 78): [],
            (9, 199): [],
        }
        for (skill, luck), expected in cases.items():
            self.assertEqual(perfect_score_reactions(SHARE.format(guesses=3, skill=skill, luck=luck)), expected)
        self.assertEqual(perfect_score_reactions("skill 99 / 99"), ["woooo"])

    def test_one_or_two_guess_solves_get_skelly(self):
        for guesses in (1, 2):
            text = SHARE.format(guesses=guesses, skill=99, luck=99)
            self.assertEqual(perfect_score_reactions(text), ["woooo", "skelly-dance-rainbow"])
            text = SHARE.format(guesses=guesses, skill=80, luck=50)
            self.assertEqual(perfect_score_reactions(text), ["skelly-dance-rainbow"])
        self.assertEqual(perfect_score_reactions("Wordle 1,977 2/6*"), ["skelly-dance-rainbow"])
        for guesses in (3, 6, "X"):
            self.assertEqual(perfect_score_reactions(SHARE.format(guesses=guesses, skill=80, luck=50)), [])

    def test_reacts_in_wordle_channel(self):
        client = Mock()
        event = {"channel": config.WORDLE_CHANNEL_ID, "ts": "1.2", "text": SHARE.format(guesses=3, skill=99, luck=50)}
        handle_message(event, client)
        client.reactions_add.assert_called_once_with(
            channel=config.WORDLE_CHANNEL_ID, timestamp="1.2", name="woooo"
        )

    def test_ignores_other_channels(self):
        client = Mock()
        handle_message({"channel": "C1", "ts": "1.2", "text": SHARE.format(guesses=3, skill=99, luck=99)}, client)
        client.reactions_add.assert_not_called()
