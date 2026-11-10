"""Contrôles de présence des ressources originales SichoSana V2.3."""
import json
import tempfile
import unittest
from pathlib import Path

from server.app import original_art_status


class OriginalArtStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        (self.root/"data").mkdir()
        (self.root/"media"/"original").mkdir(parents=True)
        self.names=[f"yoga-api-{i}" for i in range(1,49)]+[f"essentielle-{i}" for i in range(25)]
        self.assertEqual(len(self.names),73)
        (self.root/"data"/"original-art.json").write_text(json.dumps({"files":self.names}),encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_requires_all_73(self):
        self.assertEqual(original_art_status(self.root),{"ready":False,"installed":0,"expected":73})
        for name in self.names[:-1]:
            (self.root/"media"/"original"/(name+".png")).write_bytes(b"x"*1500)
        partial=original_art_status(self.root)
        self.assertEqual(partial["installed"],72)
        self.assertFalse(partial["ready"])
        (self.root/"media"/"original"/(self.names[-1]+".png")).write_bytes(b"x"*1500)
        self.assertEqual(original_art_status(self.root),{"ready":True,"installed":73,"expected":73})

    def test_invalid_manifest_never_reports_ready(self):
        (self.root/"data"/"original-art.json").write_text('{"files":["../x"]}',encoding="utf-8")
        self.assertFalse(original_art_status(self.root)["ready"])


if __name__=="__main__":
    unittest.main()


class DonationDestinationTests(unittest.TestCase):
    def test_no_invented_destination(self):
        from unittest.mock import patch
        import os
        from server.app import donation_destination
        with patch.dict(os.environ,{"SICHOSANA_DONATION_URL":""}):
            self.assertIsNone(donation_destination())
        with patch.dict(os.environ,{"SICHOSANA_DONATION_URL":"https://paypal.me/EXAMPLE"}):
            self.assertEqual(donation_destination(),"https://paypal.me/EXAMPLE")
        with patch.dict(os.environ,{"SICHOSANA_DONATION_URL":"javascript:alert(1)"}):
            self.assertIsNone(donation_destination())
        with patch.dict(os.environ,{"SICHOSANA_DONATION_URL":"https://phishing.test/"}):
            self.assertIsNone(donation_destination())
