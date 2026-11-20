import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from server.models import FlagStatus
from server.protocols.forcad_http import classify_message, parse_retry_after


class ForcadHttpHelpersTest(unittest.TestCase):
    def test_known_accepted_message(self):
        self.assertEqual(classify_message('Accepted'), FlagStatus.ACCEPTED)

    def test_known_rejected_messages(self):
        for message in ('Wrong flag', 'Flag is your own', 'Flag is too old'):
            with self.subTest(message=message):
                self.assertEqual(classify_message(message), FlagStatus.REJECTED)

    def test_negative_message_is_not_misclassified_as_accepted(self):
        self.assertEqual(classify_message('Not accepted yet'), FlagStatus.QUEUED)

    def test_unknown_message_stays_queued(self):
        self.assertEqual(classify_message('temporary checksystem issue'),
                         FlagStatus.QUEUED)

    def test_retry_after_seconds(self):
        self.assertEqual(parse_retry_after('2.5'), 2.5)

    def test_retry_after_http_date(self):
        future = datetime.now(timezone.utc) + timedelta(seconds=30)
        delay = parse_retry_after(format_datetime(future, usegmt=True))
        self.assertGreater(delay, 0)
        self.assertLessEqual(delay, 31)

    def test_missing_retry_after_has_safe_default(self):
        self.assertEqual(parse_retry_after(None), 1.0)


if __name__ == '__main__':
    unittest.main()
