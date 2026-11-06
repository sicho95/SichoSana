"""Contrôles de non-régression de la recette SichoSana V2.1."""
import io
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

class ReleaseValidation(unittest.TestCase):
    def test_lotus_and_five_mobile_items(self):
        app=(ROOT/'static/app.js').read_text(encoding='utf-8')
        auth=(ROOT/'static/auth.js').read_text(encoding='utf-8')
        css=(ROOT/'static/styles.css').read_text(encoding='utf-8')
        self.assertIn('nav.map(navButton)',app)
        self.assertIn('class="lotus-mark"',app)
        self.assertIn('src="/icon.svg"',auth)
        self.assertIn('.bottom-nav{display:grid;grid-template-columns:repeat(5,minmax(0,1fr))',css)
        self.assertIn('body:has(.auth-layout) .topbar',css)
        self.assertIn('admin-entry',app)

    def test_voice_manifest_references_real_mp3(self):
        folder=ROOT/'static/voice/vivienne-fr-v2'
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['voiceId'],'fr-FR-VivienneMultilingualNeural')
        self.assertGreaterEqual(len(manifest['files']),80)
        for key,entry in manifest['files'].items():
            file=folder/entry['src']
            self.assertTrue(file.is_file(),f'{key}: absent')
            self.assertGreater(file.stat().st_size,1500,key)
            with file.open('rb') as inp:
                first=inp.read(4)
            self.assertTrue(first.startswith(b'ID3') or first.startswith(b'\xff'),f'{key}: pas un MP3')

    def test_pose_credits_and_files(self):
        manifest=json.loads((ROOT/'static/data/pose-media.json').read_text(encoding='utf-8'))
        for row in manifest['photos']:
            self.assertTrue((ROOT/'static'/row['src'].lstrip('/')).is_file(),row['id'])
            self.assertTrue(row['source'].startswith('https://commons.wikimedia.org/'))
            self.assertTrue(row['licenseUrl'].startswith('https://creativecommons.org/'))

    def test_astrology_periods_and_attribution(self):
        from server import astrology
        self.assertEqual(astrology.PERIODS,{'daily','weekly','monthly'})
        response={'items':[{'text':'Un jour serein. Cultive le calme. Prends un instant.'}],
                  'attribution':{'localizedHref':'https://sigastra.com/fr/horoscope-du-jour'}}
        class R:
            status=200
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,size):return json.dumps(response).encode('utf-8')
        with patch.dict(os.environ,{'SICHOSANA_ASTRO_ENABLED':'1'}):
            with patch.object(astrology,'urlopen',return_value=R()) as fetch:
                astrology.CACHE.clear()
                data=astrology.daily('Lion','weekly')
        self.assertTrue(data['available'])
        self.assertEqual(data['period'],'weekly')
        self.assertEqual(data['source'],'Sigastra')
        self.assertIn('/weekly?',fetch.call_args.args[0].full_url)

if __name__=='__main__':
    unittest.main()
