import unittest
from unittest.mock import Mock

import config
from events.wordle import handle_message, is_perfect_skill

SHARE = "Wordle 1,977 3/6\n\n:large_green_square:\n\nWordleBot\nSkill {skill}/99\nLuck 99/99"


class WordleTest(unittest.TestCase):
    def test_matches_only_skill_99(self):
        self.assertTrue(is_perfect_skill(SHARE.format(skill=99)))
        self.assertTrue(is_perfect_skill("skill 99 / 99"))
        for skill in (89, 9, 199):
            self.assertFalse(is_perfect_skill(SHARE.format(skill=skill)), skill)
        self.assertFalse(is_perfect_skill("Skill 62/99\nLuck 99/99"))

    def test_reacts_in_wordle_channel(self):
        client = Mock()
        event = {"channel": config.WORDLE_CHANNEL_ID, "ts": "1.2", "text": SHARE.format(skill=99)}
        handle_message(event, client)
        client.reactions_add.assert_called_once_with(
            channel=config.WORDLE_CHANNEL_ID, timestamp="1.2", name="woooo"
        )

    def test_ignores_other_channels(self):
        client = Mock()
        handle_message({"channel": "C1", "ts": "1.2", "text": SHARE.format(skill=99)}, client)
        client.reactions_add.assert_not_called()
