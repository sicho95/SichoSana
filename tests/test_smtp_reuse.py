"""Tests sans secrets de la reprise SMTP locale SichoBooks → SichoSana."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "adopt-sichobooks-smtp.py"
spec = importlib.util.spec_from_file_location("adopt_sichobooks_smtp", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class SMTPReuseTests(unittest.TestCase):
    def _payload(self):
        return [{
            "Name": "/sichobooks-worker-1",
            "Config": {"Env": [
                "SICHOBOOKS_SMTP_HOST=smtp.gmail.com",
                "SICHOBOOKS_SMTP_PORT=465",
                "SICHOBOOKS_SMTP_USER=example@gmail.com",
                "SICHOBOOKS_SMTP_PASSWORD=not-a-real-secret",
                "SICHOBOOKS_SMTP_FROM=example@gmail.com",
                "SICHOBOOKS_SMTP_MAX_BOOKS=50"
            ]}
        }]

    def test_maps_actual_prefixed_worker_variables(self):
        conf = module.configuration_from_inspect(self._payload())
        self.assertEqual(conf["SICHOSANA_SMTP_HOST"], "smtp.gmail.com")
        self.assertEqual(conf["SICHOSANA_SMTP_PORT"], "465")
        self.assertEqual(conf["SICHOSANA_SMTP_SECURITY"], "ssl")
        self.assertEqual(conf["SICHOSANA_SMTP_USER"], "example@gmail.com")
        self.assertEqual(conf["SICHOSANA_SMTP_FROM"], "example@gmail.com")
        self.assertEqual(conf["SICHOSANA_SMTP_PASSWORD"], "not-a-real-secret")

    def test_587_is_starttls(self):
        raw = self._payload()
        raw[0]["Config"]["Env"][1] = "SICHOBOOKS_SMTP_PORT=587"
        self.assertEqual(module.configuration_from_inspect(raw)["SICHOSANA_SMTP_SECURITY"], "starttls")

    def test_unrelated_container_refused(self):
        raw = self._payload()
        raw[0]["Name"] = "/sichobooks-web-1"
        with self.assertRaises(ValueError):
            module.configuration_from_inspect(raw)

    def test_non_gmail_refused(self):
        raw = self._payload()
        raw[0]["Config"]["Env"][0] = "SICHOBOOKS_SMTP_HOST=untrusted.example"
        with self.assertRaises(ValueError):
            module.configuration_from_inspect(raw)

if __name__ == "__main__":
    unittest.main()
