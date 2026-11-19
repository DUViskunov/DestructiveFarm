import unittest
from collections import namedtuple

from server.flag_utils import deduplicate_flags


class DeduplicateFlagsTest(unittest.TestCase):
    def test_removes_repeats_and_keeps_first_occurrence_order(self):
        flags = [
            {'flag': 'FLAG_A=', 'source': 'first'},
            {'flag': 'FLAG_B=', 'source': 'second'},
            {'flag': 'FLAG_A=', 'source': 'duplicate'},
            {'flag': 'FLAG_C=', 'source': 'third'},
            {'flag': 'FLAG_B=', 'source': 'duplicate'},
        ]

        unique, removed = deduplicate_flags(flags, lambda item: item['flag'])

        self.assertEqual([item['flag'] for item in unique],
                         ['FLAG_A=', 'FLAG_B=', 'FLAG_C='])
        self.assertEqual(unique[0]['source'], 'first')
        self.assertEqual(unique[1]['source'], 'second')
        self.assertEqual(removed, 2)
        self.assertEqual(len(flags), 5)

    def test_supports_flag_objects(self):
        Flag = namedtuple('Flag', ['flag', 'team'])
        flags = [Flag('FLAG_A=', 'team1'), Flag('FLAG_A=', 'team2')]

        unique, removed = deduplicate_flags(flags, lambda item: item.flag)

        self.assertEqual(unique, [flags[0]])
        self.assertEqual(removed, 1)

    def test_empty_input(self):
        unique, removed = deduplicate_flags([], lambda item: item['flag'])

        self.assertEqual(unique, [])
        self.assertEqual(removed, 0)

    def test_does_not_merge_different_flags(self):
        flags = [{'flag': 'FLAG_A='}, {'flag': 'flag_a='}, {'flag': 'FLAG_A ='}]

        unique, removed = deduplicate_flags(flags, lambda item: item['flag'])

        self.assertEqual(unique, flags)
        self.assertEqual(removed, 0)


if __name__ == '__main__':
    unittest.main()
