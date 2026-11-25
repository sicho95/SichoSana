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

    def test_voice_script_has_distinct_title_and_hold(self):
        import importlib.util,json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('voice',root/'scripts/generate-voice-pack.py')
        mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        data=root/'static/data'
        args=[json.loads((data/n).read_text()) for n in ('meditations.json','yoga.json','pose-guidance.json','salutations.json','transitions.json')]
        clips={k:t for k,t,_ in mod.clips(*args)}
        self.assertEqual(len(clips),260)
        self.assertIn('Adho Mukha Svanasana, le chien tête en bas',clips['transition_tadasana_adho-mukha_easy'])
        self.assertIn('Savasana, la relaxation allongée',clips['easy_savasana'])
        for pose in args[2]['poses']:
            for variant in ('easy','full'):
                hold=clips['hold_'+pose+'_'+variant]
                self.assertNotIn('Nous allons pratiquer',hold)
                self.assertNotEqual(hold,args[2]['poses'][pose]['facile'])

    def test_downward_dog_wall_alignment(self):
        import json
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'static/data'
        g=json.loads((root/'pose-guidance.json').read_text())['poses']['adho-mukha']
        t=json.loads((root/'transitions.json').read_text())['routes']
        m=json.loads((root/'variant-art.json').read_text())
        self.assertIn('mur',g['facile'])
        self.assertIn('mur',t['tadasana>adho-mukha']['easy'])
        self.assertIn('mur',t['adho-mukha>anjaneyasana']['full'])
        self.assertEqual(m['easy']['adho-mukha'],'adho-mukha-easy')
        self.assertEqual(m['alternatives']['adho-mukha'][0]['image'],'adho-mukha-floor')
        self.assertIn('au sol',m['alternatives']['adho-mukha'][0]['text'])

    def test_horoscope_full_and_canonical(self):
        import json,os
        from unittest.mock import patch,MagicMock
        from server import astrology
        payload={"items":[{"text":"Première phrase. Deuxième phrase. Troisième phrase entière.\n\nDernier paragraphe complet."}],"attribution":{"localizedHref":"https://sigastra.com/fr/horoscope-du-jour","canonicalTag":'<link rel="canonical" href="https://sigastra.com/fr/horoscope-du-jour">' }}
        response=MagicMock()
        response.status=200
        response.read.return_value=json.dumps(payload).encode()
        response.__enter__.return_value=response
        astrology.CACHE.clear()
        try:
            with patch.dict(os.environ,{"SICHOSANA_ASTRO_ENABLED":"1"}),patch.object(astrology,"urlopen",return_value=response) as request:
                for period in ("daily","weekly","monthly"):
                    result=astrology.daily("Verseau",period)
                    self.assertTrue(result["full"])
                    self.assertIn("full=1",request.call_args.args[0].full_url)
                    self.assertEqual(result["text"],payload["items"][0]["text"])
                    self.assertEqual(result["preview"],"Première phrase.")
                    self.assertIn('<link rel="canonical" href="https://sigastra.com/fr/horoscope-du-jour">',astrology.public_reading("Verseau",period,result))
                    self.assertIn("Dernier paragraphe complet.",astrology.public_reading("Verseau",period,result))
        finally:
            astrology.CACHE.clear()
        with self.assertRaises(ValueError):
            astrology.source_canonical('<link rel="canonical" href="https://example.com/">')
