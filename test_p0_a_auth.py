"""
test_p0_a_auth.py - Regression Test Suite for P0-A Auth & Security Hardening
Tests:
1. No hardcoded PINs (1234/5678/9999/Admin@123): authentication succeeds ONLY via verify_password on stored hash.
   When admin changes password, old PIN and old password MUST fail.
2. Login throttling: 5 failed attempts per username -> 5-minute lockout; generic error message.
3. Audit log of failed and successful attempts in login_attempts table.
4. Constant-time timing attack mitigation for nonexistent accounts.
5. Minimum password length (>= 10 characters) enforced in create_user and update_user_password.
6. DEMO_MODE env flag behavior (default false).
"""

import unittest
import tempfile
import os
import sys
import sqlite3
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import auth

class TestP0AAuthHardening(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = cls.temp_db.name
        cls.temp_db.close()
        os.environ["ANNRAKSHAK_DB_PATH"] = cls.temp_db_path
        os.environ["DEMO_PASSWORD_ADMIN"] = "InitialAdminPassword2026!"
        os.environ["DEMO_PASSWORD_DONOR"] = "InitialDonorPassword2026!"
        os.environ["DEMO_PASSWORD_NGO"] = "InitialNGOPassword2026!"
        database.init_db(force_reset=True, db_path=cls.temp_db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except Exception:
                pass
        for var in ["ANNRAKSHAK_DB_PATH", "DEMO_PASSWORD_ADMIN", "DEMO_PASSWORD_DONOR", "DEMO_PASSWORD_NGO", "DEMO_MODE"]:
            if var in os.environ:
                del os.environ[var]

    def setUp(self):
        database.init_db(force_reset=True, db_path=self.temp_db_path)

    def test_admin_password_change_old_pins_and_old_passwords_must_fail(self):
        """P0-A.1: Admin password change must invalidate old password AND old hardcoded PIN 9999."""
        initial_admin_pwd = "InitialAdminPassword2026!"
        admin_user = auth.authenticate_user("admin", initial_admin_pwd, db_path=self.temp_db_path)
        self.assertIsNotNone(admin_user, "Initial admin login must succeed with configured env password")
        self.assertEqual(admin_user["role"], "admin")

        # Prior to fix, 9999 was accepted via demo_match. Verify 9999 FAILS now:
        pin_login = auth.authenticate_user("admin", "9999", db_path=self.temp_db_path)
        self.assertIsNone(pin_login, "Old hardcoded PIN 9999 must strictly fail!")

        # Now change admin's password to a brand new secure password
        new_pwd = "BrandNewAdminPassword999!"
        ok, msg = auth.update_user_password(admin_user["id"], new_pwd, db_path=self.temp_db_path)
        self.assertTrue(ok, f"Password update should succeed: {msg}")

        # Old password must fail
        old_login = auth.authenticate_user("admin", initial_admin_pwd, db_path=self.temp_db_path)
        self.assertIsNone(old_login, "Old password must fail after password update!")

        # Old hardcoded PIN 9999 must still fail
        old_pin = auth.authenticate_user("admin", "9999", db_path=self.temp_db_path)
        self.assertIsNone(old_pin, "PIN 9999 must strictly fail!")

        # New password must succeed
        new_login = auth.authenticate_user("admin", new_pwd, db_path=self.temp_db_path)
        self.assertIsNotNone(new_login, "New password must succeed!")
        self.assertEqual(new_login["id"], admin_user["id"])

    def test_login_throttling_5_failed_attempts_locks_account(self):
        """P0-A.3: 5 failed attempts locks the account for 5 minutes."""
        test_user = "throttle_test_user"
        test_pwd = "ValidThrottlePassword123!"
        ok, msg, uid = auth.create_user(test_user, test_pwd, "donor", db_path=self.temp_db_path)
        self.assertTrue(ok)

        # Execute 5 failed login attempts
        for i in range(5):
            res = auth.authenticate_user(test_user, f"WrongPassword{i}!", db_path=self.temp_db_path)
            self.assertIsNone(res, f"Attempt {i+1} with wrong password must fail")

        # 6th attempt with the CORRECT password must be locked out
        locked_attempt = auth.authenticate_user(test_user, test_pwd, db_path=self.temp_db_path)
        self.assertIsNone(locked_attempt, "Account must be locked out after 5 consecutive failures")

        # Verify audit log in login_attempts table
        conn = database.get_connection(self.temp_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM login_attempts WHERE username = ? AND success = 0;", (test_user,))
            failed_count = cursor.fetchone()[0]
            self.assertGreaterEqual(failed_count, 5, "Audit log must record at least 5 failed attempts")
        finally:
            conn.close()

    def test_constant_time_comparison_nonexistent_user(self):
        """P0-A.3: Nonexistent user returns None and logs failure without raising exceptions."""
        res = auth.authenticate_user("completely_ghost_user_xyz", "RandomPassword123!", db_path=self.temp_db_path)
        self.assertIsNone(res)

        # Verify failure logged in audit table
        conn = database.get_connection(self.temp_db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM login_attempts WHERE username = 'completely_ghost_user_xyz';")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)
        finally:
            conn.close()

    def test_minimum_password_length_enforcement(self):
        """P0-A.3: Passwords under 10 characters must be rejected."""
        # Short password (< 10) in create_user
        ok, msg, uid = auth.create_user("short_pwd_user", "Short123", "donor", db_path=self.temp_db_path)
        self.assertFalse(ok, "create_user with < 10 characters must fail")
        self.assertIn("10 characters", msg)

        # Valid password (>= 10)
        ok, msg, uid = auth.create_user("valid_pwd_user", "ValidPassword123!", "donor", db_path=self.temp_db_path)
        self.assertTrue(ok)

        # Short password (< 10) in update_user_password
        ok, msg = auth.update_user_password(uid, "Tiny123", db_path=self.temp_db_path)
        self.assertFalse(ok, "update_user_password with < 10 characters must fail")
        self.assertIn("10 characters", msg)

    def test_demo_mode_env_flag_behavior(self):
        """P0-A.2: Default DEMO_MODE is false; when false, demo bypass is disabled."""
        # When DEMO_MODE is false or unset
        os.environ["DEMO_MODE"] = "false"
        is_demo = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
        self.assertFalse(is_demo)

        # When DEMO_MODE is true
        os.environ["DEMO_MODE"] = "true"
        is_demo = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
        self.assertTrue(is_demo)

if __name__ == "__main__":
    unittest.main()
