"""Tests des comptes SichoSana V2 ; aucun email réel n'est envoyé."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server import accounts, app


class TestAccounts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        app.DATA_DIR = Path(self.temp.name)
        app.DB_PATH = app.DATA_DIR / "sichosana.sqlite3"
        app.initialize()
        self.environment = patch.dict(os.environ, {
            "SICHOSANA_TEST_MODE": "1", "SICHOSANA_HOST": "127.0.0.1",
            "SICHOSANA_PUBLIC_URL": "https://yoga.sicho.cc.cd",
        })
        self.environment.start()
        with app.connection() as conn:
            self.admin = accounts.create_admin(conn, "Sicho", "admin@example.test", "1234")

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def test_bootstrap_password_is_forced_and_single_admin(self):
        with app.connection() as conn:
            admin = accounts.get_account(conn, self.admin)
            self.assertTrue(admin["must_change"])
            self.assertEqual(admin["role"], "admin")
            with self.assertRaises(accounts.AccountError):
                accounts.create_admin(conn, "AnotherAdmin", "other@example.test", "1234")
            logged = accounts.login(conn, {"pseudo": "sIcHo", "password": "1234"})
            self.assertTrue(logged["user"]["mustChangePassword"])
            with self.assertRaises(accounts.AccountError):
                accounts.bearer_user(conn, {"Authorization": "Bearer " + logged["token"]})
            actor = accounts.bearer_user(conn, {"Authorization": "Bearer " + logged["token"]},
                                          allow_forced_change=True)
            accounts.new_password(conn, actor, {"currentPassword": "1234",
                                                "newPassword": "UniqueNewPassword2026!"})
            logged = accounts.login(conn, {"pseudo": "SICHO",
                                           "password": "UniqueNewPassword2026!"})
            self.assertFalse(logged["user"]["mustChangePassword"])

    def test_registration_casefold_admin_approval_and_suspension(self):
        with app.connection() as conn:
            result = accounts.new_account(conn, {"pseudo": "Léna", "email": "lena@example.test",
                                                 "password": "SecurePassword2026!"})
            self.assertEqual(result["status"], "pending")
            with self.assertRaises(accounts.AccountError):
                accounts.new_account(conn, {"pseudo": "LÉNA", "email": "different@example.test",
                                            "password": "SecurePassword2026!"})
            with self.assertRaises(accounts.AccountError):
                accounts.login(conn, {"pseudo": "léna", "password": "SecurePassword2026!"})
            user = conn.execute("SELECT id FROM accounts WHERE handle_key=?", ("léna",)).fetchone()["id"]
            admin = accounts.get_account(conn, self.admin)
            approved = accounts.manage(conn, admin, user, "approve")
            self.assertEqual(approved["status"], "active")
            logged = accounts.login(conn, {"pseudo": "LÉNA", "password": "SecurePassword2026!"})
            self.assertEqual(logged["user"]["pseudo"], "Léna")
            self.assertGreaterEqual(conn.execute("SELECT count(*) FROM email_outbox").fetchone()[0], 3)
            accounts.manage(conn, admin, user, "suspend")
            with self.assertRaises(accounts.AccountError):
                accounts.bearer_user(conn, {"Authorization": "Bearer " + logged["token"]})
            accounts.manage(conn, admin, user, "restore")
            self.assertEqual(accounts.get_account(conn, user)["status"], "active")
            accounts.manage(conn, admin, user, "promote")
            self.assertEqual(accounts.get_account(conn, user)["role"], "admin")
            accounts.manage(conn, admin, user, "demote")
            accounts.manage(conn, admin, user, "delete")
            self.assertIsNone(accounts.get_account(conn, user))

    def test_password_reset_and_snapshot_conflicts(self):
        with app.connection() as conn:
            admin = accounts.get_account(conn, self.admin)
            accounts.request_reset(conn, {"pseudoOrEmail": "SICHO"})
            # Compte provisoire : réinitialisation permise ; le lien reste secret côté client.
            self.assertEqual(conn.execute("SELECT count(*) FROM password_resets").fetchone()[0], 1)
            with self.assertRaises(accounts.AccountError):
                accounts.reset_password(conn, {"token": "invalid", "newPassword": "SecureNewPassword2026!"})
            sample = {"schemaVersion": 1, "profiles": [{"id": "one", "name": "Test", "history": []}],
                      "activeProfileId": "one"}
            result = accounts.save_snapshot(conn, admin["id"], 0, sample)
            self.assertEqual(result["revision"], 1)
            self.assertEqual(accounts.snapshot(conn, admin["id"])["data"]["profiles"][0]["name"], "Test")
            with self.assertRaises(accounts.AccountError) as issue:
                accounts.save_snapshot(conn, admin["id"], 0, sample)
            self.assertEqual(issue.exception.status, 409)
            self.assertEqual(conn.execute("SELECT count(*) FROM account_snapshots").fetchone()[0], 1)

    def test_admin_cannot_self_delete(self):
        with app.connection() as conn:
            admin = accounts.get_account(conn, self.admin)
            with self.assertRaises(accounts.AccountError):
                accounts.manage(conn, admin, self.admin, "delete")


if __name__ == "__main__":
    unittest.main()
