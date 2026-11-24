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
        (self.root/"data"/"original-art.json").write_text(json.dumps({"files":self.names,"aliases":dict(zip(self.names[:15],self.names[15:30])),"expectedPhysicalFiles":58}),encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_requires_58_assets_for_73_references(self):
        expected={"ready":False,"installed":0,"expected":58,"references":73,"shared":15}
        self.assertEqual(original_art_status(self.root),expected)
        physical=self.names[15:]
        # Use an actual valid PNG from the repository, not a fake x-filled file.
        png=(Path(__file__).resolve().parents[1]/"static/media/original/tadasana.png").read_bytes()
        for name in physical[:-1]:
            (self.root/"media"/"original"/(name+".png")).write_bytes(png)
        self.assertEqual(original_art_status(self.root)["installed"],57)
        self.assertFalse(original_art_status(self.root)["ready"])
        last=self.root/"media"/"original"/(physical[-1]+".png")
        last.write_bytes(b"x"*1500)
        self.assertFalse(original_art_status(self.root)["ready"])
        last.write_bytes(png)
        self.assertEqual(original_art_status(self.root),{**expected,"ready":True,"installed":58})

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
