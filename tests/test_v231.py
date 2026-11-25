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

    def test_transition_catalog_coverage(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'static/data'
        yoga=json.loads((root/'yoga.json').read_text())
        transitions=json.loads((root/'transitions.json').read_text())['routes']
        expected={a+'>'+b for r in yoga['routines'] for a,b in zip(r['poseIds'],r['poseIds'][1:])}
        self.assertEqual(set(transitions),expected)
        self.assertEqual(len(expected),19)
        for route in transitions.values():
            self.assertEqual(set(route),{'full','easy'})
            self.assertNotEqual(route['full'],route['easy'])
            self.assertTrue(all(len(t)>20 for t in route.values()))

    def test_salutation_variant_cues(self):
        import json
        from pathlib import Path
        data=json.loads((Path(__file__).resolve().parents[1]/'static/data/salutations.json').read_text())
        variants=[s for r in data['routines'] for s in r['steps'] if s.get('easyPoseId',s['poseId'])!=s['poseId']]
        self.assertEqual(len(variants),2)
        for s in variants:
            self.assertNotEqual(s['fullCue'],s['easyCue'])
