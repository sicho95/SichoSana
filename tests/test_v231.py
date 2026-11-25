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

    def test_reflection_corpus(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).resolve().parents[1]/'static/data/reflections.json').read_text())
        phrases=data['reflections']
        self.assertEqual(len(phrases),400)
        self.assertEqual(len(set(phrases)),400)
        self.assertTrue(all(20<len(x)<160 for x in phrases))
