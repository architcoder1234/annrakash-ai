"""
Phase P0-B Fail-Closed Backend and Invariant Verification Test Suite for AnnRakshak AI.
Verifies:
1. Fail-closed backend authorization:
   - acting_user is strictly REQUIRED for: create_donation, request_pickup, update_request_status,
     cancel_donation, approve_ngo, get_contact_for, log_food_waste.
   - Missing, None, or inactive (is_active=0/False) user immediately returns (False, "Unauthorized").
   - Negative tests: no user, wrong role, wrong organization, inactive user, unverified NGO.
2. Portion conservation and state invariants:
   - Invariant: available + sum(active request portions) + delivered portions == quantity.
   - Transitioning a request to Expired releases its reserved portions.
   - A donation is NEVER Available with 0 portions.
3. 500-iteration randomized state machine testing asserting invariant_check after every step.
"""

import unittest
import os
import random
import tempfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import database
import workflow_manager as wm
from repositories import DonationRepository, RequestRepository, OrganizationRepository

IST = ZoneInfo("Asia/Kolkata")

class TestP0BBackendFailClosedAndInvariants(unittest.TestCase):
    temp_db_file = None

    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = cls.temp_db.name
        cls.temp_db.close()
        os.environ["ANNRAKSHAK_DB_PATH"] = cls.temp_db_path
        database.init_db(force_reset=True, db_path=cls.temp_db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except Exception:
                pass
        if "ANNRAKSHAK_DB_PATH" in os.environ:
            del os.environ["ANNRAKSHAK_DB_PATH"]

    def setUp(self):
        database.init_db(force_reset=True, db_path=self.temp_db_path)
        self.donor1 = {"id": "USR-001", "username": "sharma_catering", "role": "donor", "org_id": "DONOR-001", "is_active": True}
        self.donor2 = {"id": "USR-002", "username": "verma_events", "role": "donor", "org_id": "DONOR-002", "is_active": True}
        self.ngo1 = {"id": "USR-003", "username": "prayag_seva", "role": "ngo", "org_id": "NGO-001", "is_active": True}
        self.ngo2 = {"id": "USR-004", "username": "ganga_relief", "role": "ngo", "org_id": "NGO-002", "is_active": True}
        self.ngo_unverified = {"id": "USR-005", "username": "new_hope", "role": "ngo", "org_id": "NGO-003", "is_active": True}
        self.admin = {"id": "USR-ADMIN", "username": "admin", "role": "admin", "org_id": None, "is_active": True}
        self.inactive_user = {"id": "USR-INACT", "username": "inactive_donor", "role": "donor", "org_id": "DONOR-001", "is_active": False}

    # =========================================================================
    # NEGATIVE TESTS FOR ALL 7 FUNCTIONS
    # =========================================================================
    def test_negative_create_donation(self):
        """Negative tests for create_donation."""
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        # 1. No user
        ok, msg, _ = wm.create_donation(acting_user=None, food_description="Curry", quantity_portions=50, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 2. Inactive user
        ok, msg, _ = wm.create_donation(acting_user=self.inactive_user, food_description="Curry", quantity_portions=50, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 3. Wrong role (NGO cannot publish donor listing)
        ok, msg, _ = wm.create_donation(acting_user=self.ngo1, food_description="Curry", quantity_portions=50, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 4. Donor user with no org_id
        bad_donor = {"id": "USR-999", "username": "no_org", "role": "donor", "org_id": None, "is_active": True}
        ok, msg, _ = wm.create_donation(acting_user=bad_donor, food_description="Curry", quantity_portions=50, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

    def test_negative_request_pickup(self):
        """Negative tests for request_pickup."""
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(acting_user=self.donor1, food_description="Pulao", quantity_portions=50, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")

        # 1. No user
        ok, msg, _ = wm.request_pickup(acting_user=None, donation_id=don_id, requested_portions=20)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 2. Inactive user
        inact_ngo = {"id": "USR-INACT-NGO", "username": "inact_ngo", "role": "ngo", "org_id": "NGO-001", "is_active": False}
        ok, msg, _ = wm.request_pickup(acting_user=inact_ngo, donation_id=don_id, requested_portions=20)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 3. Wrong role (Donor cannot claim pickup)
        ok, msg, _ = wm.request_pickup(acting_user=self.donor1, donation_id=don_id, requested_portions=20)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 4. Unverified NGO
        ok, msg, _ = wm.request_pickup(acting_user=self.ngo_unverified, donation_id=don_id, requested_portions=20)
        self.assertFalse(ok)
        self.assertIn("verification is required", msg)

    def test_negative_update_request_status(self):
        """Negative tests for update_request_status."""
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(acting_user=self.donor1, food_description="Biryani", quantity_portions=50, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        _, _, req_id = wm.request_pickup(acting_user=self.ngo1, donation_id=don_id, requested_portions=25)

        # 1. No user
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=None)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 2. Inactive user
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=self.inactive_user)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 3. Wrong role / Wrong org: NGO cannot Confirm
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=self.ngo1)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 4. Wrong donor org: Donor 2 cannot confirm Donor 1's listing
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=self.donor2)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # Legitimate confirm
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=self.donor1)
        self.assertTrue(ok)

        # 5. Wrong role / Wrong org: Donor cannot mark Collected
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Collected", acting_user=self.donor1)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 6. Wrong NGO: NGO 2 cannot mark NGO 1's request as Collected
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Collected", acting_user=self.ngo2)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

    def test_negative_cancel_donation(self):
        """Negative tests for cancel_donation."""
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(acting_user=self.donor1, food_description="Dessert", quantity_portions=30, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")

        # 1. No user
        ok, msg = wm.cancel_donation(donation_id=don_id, acting_user=None)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 2. Inactive user
        ok, msg = wm.cancel_donation(donation_id=don_id, acting_user=self.inactive_user)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 3. Wrong role (NGO cannot cancel donation)
        ok, msg = wm.cancel_donation(donation_id=don_id, acting_user=self.ngo1)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 4. Wrong donor (Donor 2 cannot cancel Donor 1's donation)
        ok, msg = wm.cancel_donation(donation_id=don_id, acting_user=self.donor2)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

    def test_negative_approve_ngo(self):
        """Negative tests for approve_ngo."""
        # 1. No user
        ok, msg = wm.approve_ngo(acting_user=None, ngo_id="NGO-003")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 2. Inactive admin
        inact_admin = {"id": "USR-INACT-ADM", "username": "inact_adm", "role": "admin", "org_id": None, "is_active": False}
        ok, msg = wm.approve_ngo(acting_user=inact_admin, ngo_id="NGO-003")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 3. Wrong role (Donor cannot approve NGO)
        ok, msg = wm.approve_ngo(acting_user=self.donor1, ngo_id="NGO-003")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 4. Wrong role (NGO cannot approve itself)
        ok, msg = wm.approve_ngo(acting_user=self.ngo1, ngo_id="NGO-003")
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

    def test_negative_get_contact_for(self):
        """Negative privacy tests for get_contact_for."""
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(acting_user=self.donor1, food_description="Thali", quantity_portions=40, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        _, _, req_id = wm.request_pickup(acting_user=self.ngo1, donation_id=don_id, requested_portions=20)

        # 1. No user -> [MASKED]
        self.assertEqual(wm.get_contact_for(request_id=req_id, acting_user=None), "[MASKED]")

        # 2. Inactive user -> [MASKED]
        self.assertEqual(wm.get_contact_for(request_id=req_id, acting_user=self.inactive_user), "[MASKED]")

        # 3. Requesting NGO while status is Requested (not Confirmed) -> Masked
        contact = wm.get_contact_for(request_id=req_id, acting_user=self.ngo1)
        self.assertTrue(contact.startswith("+XX-XXXXX-XX") or contact == "[MASKED]")

        # 4. Third-party NGO (NGO 2) -> Masked even if confirmed
        wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=self.donor1)
        contact_other = wm.get_contact_for(request_id=req_id, acting_user=self.ngo2)
        self.assertTrue(contact_other.startswith("+XX-XXXXX-XX") or contact_other == "[MASKED]")

    def test_negative_log_food_waste(self):
        """Negative tests for log_food_waste."""
        # 1. No user
        ok, msg, _ = wm.log_food_waste(acting_user=None, provider_name="Kitchen", date="2026-10-19", meal_type="Lunch", menu_items="Rice", portions_prepared=100, portions_consumed=80, edible_surplus=10, discarded_waste=10, cost_per_meal=100.0)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 2. Inactive user
        ok, msg, _ = wm.log_food_waste(acting_user=self.inactive_user, provider_name="Kitchen", date="2026-10-19", meal_type="Lunch", menu_items="Rice", portions_prepared=100, portions_consumed=80, edible_surplus=10, discarded_waste=10, cost_per_meal=100.0)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

        # 3. Wrong role (NGO cannot log kitchen waste audit)
        ok, msg, _ = wm.log_food_waste(acting_user=self.ngo1, provider_name="Kitchen", date="2026-10-19", meal_type="Lunch", menu_items="Rice", portions_prepared=100, portions_consumed=80, edible_surplus=10, discarded_waste=10, cost_per_meal=100.0)
        self.assertFalse(ok)
        self.assertIn("Unauthorized", msg)

    # =========================================================================
    # EXPIRY PORTION RELEASE & STATUS INVARIANT TESTS
    # =========================================================================
    def test_request_transition_to_expired_releases_portions(self):
        """Transitioning a request to Expired must release portions and assert invariant."""
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(acting_user=self.donor1, food_description="Banquet", quantity_portions=100, prep_datetime=prep, available_from=avail, pickup_deadline=dead, location="Civil Lines", private_contact="+91-98765-11111")
        _, _, req_id = wm.request_pickup(acting_user=self.ngo1, donation_id=don_id, requested_portions=40)

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT available_portions FROM donations WHERE id = ?;", (don_id,))
        self.assertEqual(cur.fetchone()["available_portions"], 60)
        conn.close()
        self.assertTrue(wm.invariant_check(don_id))

        # Admin or donor owner marks request Expired
        ok, msg = wm.update_request_status(request_id=req_id, new_status="Expired", acting_user=self.donor1)
        self.assertTrue(ok)

        # Portions must be released back to 100
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT available_portions, status FROM donations WHERE id = ?;", (don_id,))
        don_row = cur.fetchone()
        self.assertEqual(don_row["available_portions"], 100)
        self.assertEqual(don_row["status"], "Available")
        conn.close()
        self.assertTrue(wm.invariant_check(don_id))

    def test_donation_never_available_with_zero_portions(self):
        """A donation must never have status 'Available' if available_portions == 0."""
        # Test the pure derive_donation_status function directly
        status = wm.derive_donation_status(
            quantity_portions=100,
            available_portions=0,
            request_statuses=["Requested"]
        )
        self.assertEqual(status, "Requested")

        status_delivered = wm.derive_donation_status(
            quantity_portions=100,
            available_portions=0,
            request_statuses=["Delivered"]
        )
        self.assertEqual(status_delivered, "Delivered")

        status_no_active = wm.derive_donation_status(
            quantity_portions=100,
            available_portions=0,
            request_statuses=[]
        )
        self.assertNotEqual(status_no_active, "Available")

    # =========================================================================
    # 500-ITERATION RANDOMIZED STATE MACHINE INVARIANT TEST
    # =========================================================================
    def test_500_randomized_state_machine_invariants(self):
        """
        Runs 500 randomized lifecycle transitions across multiple donations,
        asserting invariant_check(donation_id) after EVERY single transition.
        """
        random.seed(42)
        now = datetime.now(IST)

        active_donations = []
        # Create 5 baseline donations
        for i in range(5):
            qty = random.randint(50, 200)
            prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            avail = now.strftime("%Y-%m-%d %H:%M:%S")
            dead = (now + timedelta(hours=random.randint(2, 6))).strftime("%Y-%m-%d %H:%M:%S")
            donor = random.choice([self.donor1, self.donor2])
            ok, _, don_id = wm.create_donation(
                acting_user=donor,
                food_description=f"Batch {i}",
                quantity_portions=qty,
                prep_datetime=prep,
                available_from=avail,
                pickup_deadline=dead,
                location="Civil Lines",
                private_contact="+91-98765-11111"
            )
            self.assertTrue(ok)
            self.assertTrue(wm.invariant_check(don_id))
            active_donations.append({"id": don_id, "donor": donor, "quantity": qty})

        # Run 500 randomized operations
        operations_executed = 0
        conn = database.get_connection()

        for step in range(500):
            don_entry = random.choice(active_donations)
            don_id = don_entry["id"]
            donor = don_entry["donor"]

            # Query current donation state
            cur = conn.cursor()
            cur.execute("SELECT available_portions, status FROM donations WHERE id = ?;", (don_id,))
            don_state = cur.fetchone()
            cur_avail = don_state["available_portions"]
            cur_status = don_state["status"]

            # Query existing requests
            cur.execute("SELECT id, status, requested_portions, ngo_id FROM pickup_requests WHERE donation_id = ?;", (don_id,))
            req_rows = cur.fetchall()

            action = random.choice(["request", "confirm", "reject", "collect", "deliver", "cancel_req", "expire_req", "cancel_don"])

            if action == "request" and cur_avail > 0 and cur_status not in ("Cancelled", "Delivered", "Expired"):
                claim_qty = random.randint(1, min(cur_avail, 40))
                ngo = random.choice([self.ngo1, self.ngo2])
                ok, _, _ = wm.request_pickup(
                    acting_user=ngo,
                    donation_id=don_id,
                    requested_portions=claim_qty,
                    proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                )
                if ok:
                    operations_executed += 1
                self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after request at step {step}")

            elif action == "confirm":
                requested = [r for r in req_rows if r["status"] == "Requested"]
                if requested:
                    target = random.choice(requested)
                    ok, _ = wm.update_request_status(request_id=target["id"], new_status="Confirmed", acting_user=donor)
                    if ok:
                        operations_executed += 1
                    self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after confirm at step {step}")

            elif action == "reject":
                requested = [r for r in req_rows if r["status"] == "Requested"]
                if requested:
                    target = random.choice(requested)
                    ok, _ = wm.update_request_status(request_id=target["id"], new_status="Rejected", acting_user=donor)
                    if ok:
                        operations_executed += 1
                    self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after reject at step {step}")

            elif action == "collect":
                confirmed = [r for r in req_rows if r["status"] == "Confirmed"]
                if confirmed:
                    target = random.choice(confirmed)
                    ngo = self.ngo1 if target["ngo_id"] == "NGO-001" else self.ngo2
                    ok, _ = wm.update_request_status(request_id=target["id"], new_status="Collected", acting_user=ngo)
                    if ok:
                        operations_executed += 1
                    self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after collect at step {step}")

            elif action == "deliver":
                collected = [r for r in req_rows if r["status"] == "Collected"]
                if collected:
                    target = random.choice(collected)
                    ngo = self.ngo1 if target["ngo_id"] == "NGO-001" else self.ngo2
                    ok, _ = wm.update_request_status(request_id=target["id"], new_status="Delivered", acting_user=ngo)
                    if ok:
                        operations_executed += 1
                    self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after deliver at step {step}")

            elif action == "cancel_req":
                cancellable = [r for r in req_rows if r["status"] in ("Requested", "Confirmed")]
                if cancellable:
                    target = random.choice(cancellable)
                    ngo = self.ngo1 if target["ngo_id"] == "NGO-001" else self.ngo2
                    ok, _ = wm.update_request_status(request_id=target["id"], new_status="Cancelled", acting_user=ngo)
                    if ok:
                        operations_executed += 1
                    self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after cancel_req at step {step}")

            elif action == "expire_req":
                expirable = [r for r in req_rows if r["status"] in ("Requested", "Confirmed")]
                if expirable:
                    target = random.choice(expirable)
                    ok, _ = wm.update_request_status(request_id=target["id"], new_status="Expired", acting_user=donor)
                    if ok:
                        operations_executed += 1
                    self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after expire_req at step {step}")

            elif action == "cancel_don" and cur_status not in ("Collected", "Delivered", "Cancelled"):
                ok, _ = wm.cancel_donation(donation_id=don_id, acting_user=donor, reason="Randomized test cancel")
                if ok:
                    operations_executed += 1
                self.assertTrue(wm.invariant_check(don_id), f"Invariant violated after cancel_don at step {step}")

        conn.close()
        print(f"\n[PASS] Completed 500-step randomized state machine test with {operations_executed} successful operations. All invariants verified!")

if __name__ == "__main__":
    unittest.main()
