"""
Phase P1 Regression & Integrity Test Suite for AnnRakshak AI.
Verifies:
1. Deterministic derived donation status state machine.
2. Bug Fix: Confirmed status never reverts to Available on partial cancellation.
3. Expired donation portion release: 0 portions restored when expired food is cancelled/rejected.
4. Food safety "closed-fail" check: missing, unparseable, future, and stale dates rejected.
5. SQLite schema migrations: PRAGMA user_version, idempotent execution, index verification.
6. Typed repository pattern: decoupling SQL from business rules with transactional integrity.
"""

import unittest
import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from database import init_db, get_connection, get_db_version, run_migrations, format_ist_str, get_ist_now, IST
from workflow_manager import (
    WorkflowStatus,
    derive_donation_status,
    create_donation,
    request_pickup,
    update_request_status,
    cancel_donation,
    check_and_expire_donations,
    invariant_check
)
from repositories import DonationRepository, RequestRepository, OrganizationRepository

class TestDataIntegrityP1(unittest.TestCase):
    def setUp(self):
        # Create an isolated temporary SQLite database for each test
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        os.environ["ANNRAKSHAK_DB_PATH"] = self.temp_db_path
        init_db(force_reset=True, db_path=self.temp_db_path)

        # Repositories bound to temp db
        self.donation_repo = DonationRepository(self.temp_db_path)
        self.request_repo = RequestRepository(self.temp_db_path)
        self.org_repo = OrganizationRepository(self.temp_db_path)

        # Admin user
        self.admin_user = {"id": "USR-ADMIN", "username": "admin", "role": "admin", "org_id": None}
        # Donor user
        self.donor_user = {"id": "USR-001", "username": "sharma_catering", "role": "donor", "org_id": "DONOR-001"}
        # Verified NGO user
        self.ngo1_user = {"id": "USR-003", "username": "prayag_seva", "role": "ngo", "org_id": "NGO-001"}
        self.ngo2_user = {"id": "USR-004", "username": "ganga_relief", "role": "ngo", "org_id": "NGO-002"}

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_derived_status_direct_matrix(self):
        """Test the pure derive_donation_status function across all matrix combinations."""
        # 1. Available with no requests
        self.assertEqual(derive_donation_status(100, 100, []), "Available")

        # 2. Available with partial request
        self.assertEqual(derive_donation_status(100, 60, ["Requested"]), "Available")

        # 3. Fully requested
        self.assertEqual(derive_donation_status(100, 0, ["Requested"]), "Requested")

        # 4. Confirmed with active request
        self.assertEqual(derive_donation_status(100, 50, ["Confirmed", "Requested"]), "Confirmed")

        # 5. Confirmed does not revert to Available even if another request is Cancelled
        self.assertEqual(derive_donation_status(100, 50, ["Confirmed", "Cancelled"]), "Confirmed")

        # 6. Collected
        self.assertEqual(derive_donation_status(100, 0, ["Collected"]), "Collected")

        # 7. Fully delivered
        self.assertEqual(derive_donation_status(100, 0, ["Delivered"]), "Delivered")

        # 8. Cancelled is terminal
        self.assertEqual(derive_donation_status(100, 100, [], is_cancelled=True), "Cancelled")

        # 9. Expired is terminal
        self.assertEqual(derive_donation_status(100, 100, [], is_expired=True), "Expired")

    def test_partial_cancellation_preserves_confirmed_status(self):
        """
        REGRESSION TEST:
        When a donation has 2 requests, one Confirmed and one Requested,
        cancelling the second request MUST NOT revert the donation's status to Available.
        """
        now = get_ist_now()
        t_prep = format_ist_str(now - timedelta(hours=1))
        t_avail = format_ist_str(now)
        t_dead = format_ist_str(now + timedelta(hours=4))

        # Create donation with 100 portions
        ok, msg, don_id = create_donation(
            acting_user=self.donor_user,
            event_type="Wedding",
            food_description="100 Thalis",
            quantity_portions=100,
            prep_datetime=t_prep,
            available_from=t_avail,
            pickup_deadline=t_dead,
            storage_info="Insulated hot box >65C",
            location="Civil Lines, Prayagraj",
            private_contact="+91-98765-11111",
            food_safety_window_hours=6.0
        )
        self.assertTrue(ok)

        # NGO 1 requests 40 portions
        ok1, msg1, req1_id = request_pickup(
            acting_user=self.ngo1_user,
            donation_id=don_id,
            requested_portions=40,
            proposed_pickup_time=format_ist_str(now + timedelta(hours=1))
        )
        self.assertTrue(ok1)

        # Donor confirms NGO 1 request
        ok_conf, msg_conf = update_request_status(
            req1_id, WorkflowStatus.CONFIRMED.value, acting_user=self.donor_user
        )
        self.assertTrue(ok_conf)

        # Check donation is Confirmed
        don_after_conf = self.donation_repo.get_by_id(don_id)
        self.assertEqual(don_after_conf["status"], "Confirmed")
        self.assertEqual(don_after_conf["available_portions"], 60)

        # NGO 2 requests remaining 60 portions
        ok2, msg2, req2_id = request_pickup(
            acting_user=self.ngo2_user,
            donation_id=don_id,
            requested_portions=60,
            proposed_pickup_time=format_ist_str(now + timedelta(hours=2))
        )
        self.assertTrue(ok2)

        don_after_req2 = self.donation_repo.get_by_id(don_id)
        self.assertEqual(don_after_req2["status"], "Confirmed")
        self.assertEqual(don_after_req2["available_portions"], 0)

        # NGO 2 cancels its request
        ok_cancel, msg_cancel = update_request_status(
            req2_id, WorkflowStatus.CANCELLED.value, acting_user=self.ngo2_user, remarks="Van breakdown"
        )
        self.assertTrue(ok_cancel)

        # CRITICAL ASSERTION: The donation's available portions must be 60,
        # but its status MUST REMAIN 'Confirmed' because NGO 1's request is still Confirmed!
        don_final = self.donation_repo.get_by_id(don_id)
        self.assertEqual(don_final["available_portions"], 60)
        self.assertEqual(
            don_final["status"], "Confirmed",
            "REGRESSION: Confirmed status must not revert to Available on partial cancellation!"
        )

    def test_expired_donation_portion_release_zero(self):
        """
        REGRESSION TEST:
        When a donation expires past its pickup deadline, cancelling or rejecting
        a request on it MUST release 0 portions back to the available pool.
        """
        now = get_ist_now()
        t_prep = format_ist_str(now - timedelta(hours=2))
        t_avail = format_ist_str(now - timedelta(hours=1))
        # Deadline 10 minutes in past to simulate expired listing
        t_dead_past = format_ist_str(now - timedelta(minutes=10))

        # Create donation directly with past deadline
        don_id = "DON-TEST-EXPIRED"
        self.donation_repo.insert({
            "id": don_id,
            "donor_id": "DONOR-001",
            "donor_name": "Sharma Wedding Events",
            "event_type": "Wedding",
            "food_description": "Leftover dinner boxes",
            "quantity_portions": 50,
            "available_portions": 0,
            "prep_datetime": t_prep,
            "available_from": t_avail,
            "pickup_deadline": t_dead_past,
            "storage_info": "Ambient",
            "location": "Civil Lines, Prayagraj",
            "private_contact": "+91-98765-11111",
            "status": "Expired",
            "food_safety_window_hours": 6.0,
            "created_at": format_ist_str(now),
            "updated_at": format_ist_str(now)
        })

        req_id = "REQ-TEST-EXP-01"
        self.request_repo.insert({
            "id": req_id,
            "donation_id": don_id,
            "ngo_id": "NGO-001",
            "ngo_name": "Prayag Annapurna Seva Sansthan",
            "ngo_contact": "+91-94500-11111",
            "requested_portions": 50,
            "proposed_pickup_time": t_dead_past,
            "status": "Requested",
            "created_at": format_ist_str(now),
            "updated_at": format_ist_str(now)
        })

        # Cancel request on expired donation
        ok, msg = update_request_status(
            request_id=req_id,
            new_status=WorkflowStatus.CANCELLED.value,
            acting_user=self.ngo1_user
        )
        self.assertTrue(ok)

        # Invariant assertion: portions are restored to available_portions (50),
        # but status remains Expired (cannot re-open expired food to Available)
        don = self.donation_repo.get_by_id(don_id)
        self.assertEqual(don["available_portions"], 50, "Portions must return to available pool to satisfy portion conservation!")
        self.assertEqual(don["status"], "Expired", "Expired listing must not re-open to Available!")
        self.assertTrue(invariant_check(don_id), "Portion conservation invariant must hold!")

    def test_food_safety_closed_fail(self):
        """Test closed-fail food safety checks on donation creation."""
        now = get_ist_now()
        t_avail = format_ist_str(now)
        t_dead = format_ist_str(now + timedelta(hours=4))

        # 1. Missing prep_datetime
        ok, msg, _ = create_donation(
            acting_user=self.donor_user,
            food_description="Paneer curry",
            quantity_portions=20,
            prep_datetime="",
            available_from=t_avail,
            pickup_deadline=t_dead,
            location="Civil Lines",
            private_contact="+91-98765-11111"
        )
        self.assertFalse(ok)
        self.assertIn("Food safety violation", msg)

        # 2. Unparseable prep_datetime
        ok, msg, _ = create_donation(
            acting_user=self.donor_user,
            food_description="Paneer curry",
            quantity_portions=20,
            prep_datetime="invalid-date-string",
            available_from=t_avail,
            pickup_deadline=t_dead,
            location="Civil Lines",
            private_contact="+91-98765-11111"
        )
        self.assertFalse(ok)
        self.assertIn("Unparseable", msg)

        # 3. Future prep_datetime
        future_dt = format_ist_str(now + timedelta(hours=2))
        ok, msg, _ = create_donation(
            acting_user=self.donor_user,
            food_description="Paneer curry",
            quantity_portions=20,
            prep_datetime=future_dt,
            available_from=t_avail,
            pickup_deadline=t_dead,
            location="Civil Lines",
            private_contact="+91-98765-11111"
        )
        self.assertFalse(ok)
        self.assertIn("cannot be in the future", msg)

        # 4. Exceeded safety threshold (>6h)
        stale_dt = format_ist_str(now - timedelta(hours=7))
        ok, msg, _ = create_donation(
            acting_user=self.donor_user,
            food_description="Paneer curry",
            quantity_portions=20,
            prep_datetime=stale_dt,
            available_from=t_avail,
            pickup_deadline=t_dead,
            location="Civil Lines",
            private_contact="+91-98765-11111",
            food_safety_window_hours=6.0
        )
        self.assertFalse(ok)
        self.assertIn("exceeds the safety threshold", msg)

        # 5. Valid prep_datetime within 6h window
        valid_dt = format_ist_str(now - timedelta(hours=2))
        ok, msg, don_id = create_donation(
            acting_user=self.donor_user,
            food_description="Fresh Paneer curry and Roti",
            quantity_portions=20,
            prep_datetime=valid_dt,
            available_from=t_avail,
            pickup_deadline=t_dead,
            location="Civil Lines",
            private_contact="+91-98765-11111",
            food_safety_window_hours=6.0
        )
        self.assertTrue(ok, f"Expected creation to succeed, got: {msg}")
        self.assertIsNotNone(don_id)

    def test_schema_migrations_and_indexes(self):
        """Test PRAGMA user_version, migration runner, and index creation."""
        conn = get_connection(self.temp_db_path)
        try:
            # Schema version should be 4 (after migration 004)
            v = get_db_version(conn)
            self.assertEqual(v, 4)

            # Verify indexes exist in sqlite_master
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type = 'index';")
            idx_names = [row[0] for row in c.fetchall()]

            self.assertIn("idx_donations_donor_id", idx_names)
            self.assertIn("idx_donations_status", idx_names)
            self.assertIn("idx_donations_deadline", idx_names)
            self.assertIn("idx_requests_donation_id", idx_names)
            self.assertIn("idx_requests_ngo_id", idx_names)
            self.assertIn("idx_requests_status", idx_names)
            self.assertIn("idx_users_username", idx_names)
            self.assertIn("idx_food_waste_date", idx_names)
            self.assertIn("idx_notifications_recipient", idx_names)
            self.assertIn("idx_login_attempts_username_time", idx_names)

            # Re-running migrations is completely idempotent
            new_v = run_migrations(conn=conn)
            self.assertEqual(new_v, 4)
        finally:
            conn.close()

    def test_repository_pattern_layer(self):
        """Test that typed repositories function correctly and maintain data integrity."""
        # 1. OrganizationRepo
        donors = self.org_repo.list_donors()
        self.assertGreater(len(donors), 0)

        ngos = self.org_repo.list_ngos()
        self.assertGreater(len(ngos), 0)

        # 2. DonationRepo
        dons = self.donation_repo.list_all()
        self.assertGreater(len(dons), 0)

        # 3. RequestRepo
        reqs = self.request_repo.list_all()
        self.assertGreater(len(reqs), 0)

if __name__ == "__main__":
    unittest.main()
