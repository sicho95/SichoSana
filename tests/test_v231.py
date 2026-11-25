import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from server.astrology import period_key
class PeriodTests(unittest.TestCase):
    def test_calendar_periods(self):
        now=datetime(2026,11,25,20,0,tzinfo=ZoneInfo('Europe/Paris'))
        self.assertEqual(period_key('daily', now),'2026-11-25')
        self.assertEqual(period_key('weekly', now),'2026-11-23')
        self.assertEqual(period_key('monthly', now),'2026-11')
