"""Tests API et de synchronisation, avec base temporaire isolée."""
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import app

class TestSichoSana(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        app.DATA_DIR = Path(cls.tmp.name)
        app.DB_PATH = app.DATA_DIR / "sichosana.sqlite3"
        app.initialize()
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        cls.base = "http://127.0.0.1:" + str(cls.http.server_port)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(5)
        cls.tmp.cleanup()

    def request(self, path, method="GET", data=None, headers=None):
        raw = json.dumps(data).encode("utf-8") if data is not None else None
        h = headers or {}
        if data is not None:
            h["Content-Type"] = "application/json"
        request = Request(self.base + path, data=raw, headers=h, method=method)
        try:
            with urlopen(request, timeout=4) as r:
                content = r.read()
                return r.status, json.loads(content) if path.startswith("/api/") else content
        except HTTPError as e:
            return e.code, json.loads(e.read())

    def test_static_and_health(self):
        self.assertEqual(self.request("/api/health")[0], 200)
        status, html = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn(b'SichoSana', html)
        self.assertEqual(self.request("/styles.css")[0], 200)
        self.assertGreaterEqual(len(self.request("/api/v1/poses")[1]["poses"]), 10)

    def test_pair_sync_and_conflict(self):
        code, new = self.request("/api/v1/groups", "POST", {"password": "mon-tres-long-mot-de-passe", "deviceId": "ios-1"})
        self.assertEqual(code, 201)
        code2, paired = self.request("/api/v1/pair", "POST", {"code": new["code"], "password": "mon-tres-long-mot-de-passe", "deviceId": "ipad-2"})
        self.assertEqual(code2, 201)
        self.assertNotEqual(paired["token"], new["token"])
        head = {"Authorization": "Bearer " + new["token"], "If-Match": "0"}
        sample = {"schemaVersion": 1, "profiles": [{"id": "p1", "name": "Test", "history": []}], "activeProfileId": "p1"}
        status, updated = self.request("/api/v1/snapshot", "PUT", {"data": sample}, head)
        self.assertEqual(status, 200)
        self.assertEqual(updated["revision"], 1)
        status, other = self.request("/api/v1/snapshot", headers={"Authorization": "Bearer " + paired["token"]})
        self.assertEqual(status, 200)
        self.assertEqual(other["data"]["profiles"][0]["name"], "Test")
        status, conflict = self.request("/api/v1/snapshot", "PUT", {"data": sample}, head)
        self.assertEqual(status, 409)
        self.assertEqual(conflict["revision"], 1)
        self.assertEqual(self.request("/api/v1/snapshot")[0], 401)
        status, _ = self.request("/api/v1/pair", "POST", {"code": new["code"], "password": "wrong-wrong-wrong", "deviceId": "rogue"})
        self.assertEqual(status, 403)

    def test_reject_secret_in_snapshot(self):
        with self.assertRaises(ValueError):
            app.validate_snapshot({"schemaVersion": 1, "profiles": [{"id": "x", "name": "Test", "history": []}], "credentials": "DO_NOT_STORE"})

if __name__ == "__main__":
    unittest.main()
