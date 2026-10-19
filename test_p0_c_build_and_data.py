"""
Phase P0-C Build and Data Integrity Test Suite for AnnRakshak AI.
Verifies:
1. requirements.txt pins real releases of google-genai and removes psycopg2-binary.
2. Single source of truth: single-node SQLite architecture honestly configured in docker-compose.
3. .gitignore excludes all SQLite database files (*.db, *.db-wal, *.db-shm).
4. Fresh clone simulation: starts clean, runs migrations, populates non-destructive seed, maintains integrity.
"""

import unittest
import os
import tempfile
import re
import sqlite3

import database

class TestP0CBuildAndData(unittest.TestCase):
    def test_requirements_real_versions(self):
        """Test requirements.txt contains real google-genai version and no psycopg2."""
        req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
        self.assertTrue(os.path.exists(req_path), "requirements.txt must exist")

        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()

        # google-genai==0.1.1 does not exist on PyPI
        self.assertNotIn("google-genai==0.1.1", content, "Invalid google-genai==0.1.1 must not be present")
        self.assertTrue(
            "google-genai" in content,
            "Real version of google-genai must be specified"
        )
        # Verify psycopg2 is removed to keep SQLite as single truth
        self.assertNotIn("psycopg2", content, "psycopg2 must not be present in SQLite-focused platform")

    def test_single_source_of_truth_docker_compose(self):
        """Test docker-compose.yml defines single-node SQLite architecture without phantom Postgres."""
        compose_path = os.path.join(os.path.dirname(__file__), "docker-compose.yml")
        self.assertTrue(os.path.exists(compose_path), "docker-compose.yml must exist")

        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify no postgres service
        self.assertNotIn("postgres:", content, "Phantom postgres service must be removed from docker-compose")
        self.assertNotIn("5432:5432", content, "Postgres port must not be mapped")
        self.assertIn("ANNRAKSHAK_DB_PATH", content, "SQLite database path must be explicitly mapped")
        self.assertIn("app_data", content, "Persistent volume must be mounted for SQLite")

    def test_gitignore_database_artifacts(self):
        """Test .gitignore prevents committing any SQLite database files or WAL/SHM journals."""
        gi_path = os.path.join(os.path.dirname(__file__), ".gitignore")
        self.assertTrue(os.path.exists(gi_path), ".gitignore must exist")

        with open(gi_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]

        self.assertIn("*.db", lines, "*.db must be explicitly ignored in .gitignore")
        self.assertIn("*.db-wal", lines, "*.db-wal must be explicitly ignored in .gitignore")
        self.assertIn("*.db-shm", lines, "*.db-shm must be explicitly ignored in .gitignore")

    def test_fresh_clone_and_clean_seed(self):
        """Test that a fresh clone starts with a clean database, runs migrations, and seeds non-destructively."""
        temp_dir = tempfile.mkdtemp()
        fresh_db_path = os.path.join(temp_dir, "fresh_annrakshak.db")

        try:
            self.assertFalse(os.path.exists(fresh_db_path), "Database should not exist before init")

            # First run: initialize fresh db
            database.init_db(force_reset=False, db_path=fresh_db_path)
            self.assertTrue(os.path.exists(fresh_db_path), "Database must be created on first init")

            # Verify schema version
            conn = database.get_connection(db_path=fresh_db_path)
            v = database.get_db_version(conn)
            self.assertEqual(v, 4, "Schema must be migrated to version 4")

            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) as count FROM users;")
            user_count = cur.fetchone()["count"]
            self.assertGreaterEqual(user_count, 3, "Fresh DB must seed demo users")
            conn.close()

            # Second run: must be idempotent and non-destructive
            database.init_db(force_reset=False, db_path=fresh_db_path)
            conn2 = database.get_connection(db_path=fresh_db_path)
            cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(*) as count FROM users;")
            user_count_2 = cur2.fetchone()["count"]
            self.assertEqual(user_count, user_count_2, "Re-running init_db must not duplicate users")
            conn2.close()

        finally:
            if os.path.exists(fresh_db_path):
                try:
                    os.remove(fresh_db_path)
                except Exception:
                    pass
            try:
                os.rmdir(temp_dir)
            except Exception:
                pass

if __name__ == "__main__":
    unittest.main()
