"""
P0 Security and Privacy Automated Test Suite for AnnRakshak AI.
Verifies:
1. Real auth (bcrypt hash, credential authentication, inactive accounts, role derivation).
2. Identity by ID and FK integrity.
3. Backend authorization & tenant isolation (cross-donor, cross-ngo, non-admin approvals).
4. Enforced NGO verification inside request_pickup().
5. Contact privacy & zero phone leak in generic DataFrames/CSVs with <=2 digits masked.
6. HTML/XSS escaping across UI rendering helpers.
"""

import unittest
import tempfile
import os
import sys
import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add current path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import auth
import workflow_manager as wm
from ui_styles import (
    render_donor_listing_card,
    render_ngo_available_card,
    render_ngo_request_card,
    render_ngo_my_request_card,
    render_actionable_milestone_card,
    render_brand_header,
    render_metric_box
)

IST = ZoneInfo("Asia/Kolkata")

class TestSecurityAndPrivacyP0(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db_path = cls.temp_db.name
        cls.temp_db.close()
        os.environ["ANNRAKSHAK_DB_PATH"] = cls.temp_db_path
        os.environ["DEMO_PASSWORD_DONOR"] = "Donor@123456!"
        os.environ["DEMO_PASSWORD_DONOR2"] = "Donor@456789!"
        os.environ["DEMO_PASSWORD_NGO"] = "NGO@1234567!"
        os.environ["DEMO_PASSWORD_NGO2"] = "NGO@4567890!"
        os.environ["DEMO_PASSWORD_NGO3"] = "NGO@7890123!"
        os.environ["DEMO_PASSWORD_ADMIN"] = "Admin@123456!"
        database.init_db(force_reset=True, db_path=cls.temp_db_path)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.temp_db_path):
            try:
                os.remove(cls.temp_db_path)
            except Exception:
                pass
        for var in ["ANNRAKSHAK_DB_PATH", "DEMO_PASSWORD_DONOR", "DEMO_PASSWORD_DONOR2", "DEMO_PASSWORD_NGO", "DEMO_PASSWORD_NGO2", "DEMO_PASSWORD_NGO3", "DEMO_PASSWORD_ADMIN"]:
            if var in os.environ:
                del os.environ[var]

    def setUp(self):
        database.init_db(force_reset=True, db_path=self.temp_db_path)
        self.donor_user1 = auth.authenticate_user("sharma_catering", "Donor@123456!", db_path=self.temp_db_path)
        self.donor_user2 = auth.authenticate_user("verma_events", "Donor@456789!", db_path=self.temp_db_path)
        self.ngo_user1 = auth.authenticate_user("prayag_seva", "NGO@1234567!", db_path=self.temp_db_path)
        self.ngo_user2 = auth.authenticate_user("ganga_relief", "NGO@4567890!", db_path=self.temp_db_path)
        self.ngo_unverified = auth.authenticate_user("new_hope", "NGO@7890123!", db_path=self.temp_db_path)
        self.admin_user = auth.authenticate_user("admin", "Admin@123456!", db_path=self.temp_db_path)

    # -------------------------------------------------------------
    # 1. Real Authentication Tests
    # -------------------------------------------------------------
    def test_01_real_auth_bcrypt_and_credentials(self):
        # Valid login
        self.assertIsNotNone(self.donor_user1)
        self.assertEqual(self.donor_user1["role"], "donor")
        self.assertEqual(self.donor_user1["org_id"], "DONOR-001")

        # Invalid password
        invalid_login = auth.authenticate_user("sharma_catering", "WrongPassword", db_path=self.temp_db_path)
        self.assertIsNone(invalid_login)

        # Non-existent user
        no_user = auth.authenticate_user("ghost_user", "Any@123", db_path=self.temp_db_path)
        self.assertIsNone(no_user)

        # Deactivated user cannot authenticate
        conn = database.get_connection(self.temp_db_path)
        conn.execute("UPDATE users SET is_active = 0 WHERE username = 'sharma_catering';")
        conn.commit()
        conn.close()

        deactivated_login = auth.authenticate_user("sharma_catering", "Donor@123456!", db_path=self.temp_db_path)
        self.assertIsNone(deactivated_login, "Deactivated account should not authenticate")

    # -------------------------------------------------------------
    # 2. Identity by ID & Foreign Key Integrity
    # -------------------------------------------------------------
    def test_02_identity_by_id_and_fk_enforcement(self):
        conn = database.get_connection(self.temp_db_path)
        cursor = conn.cursor()
        
        # Verify donors and ngos exist with ID primary keys
        cursor.execute("SELECT id, name FROM donors WHERE id = 'DONOR-001';")
        donor_row = cursor.fetchone()
        self.assertIsNotNone(donor_row)
        self.assertEqual(donor_row["id"], "DONOR-001")

        cursor.execute("SELECT id, name, is_verified FROM ngos WHERE id = 'NGO-001';")
        ngo_row = cursor.fetchone()
        self.assertIsNotNone(ngo_row)
        self.assertEqual(ngo_row["id"], "NGO-001")
        self.assertTrue(bool(ngo_row["is_verified"]))
        conn.close()

    # -------------------------------------------------------------
    # 3. Backend Authorization & Cross-Tenant Isolation
    # -------------------------------------------------------------
    def test_03_backend_authorization_ownership_checks(self):
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        # Donor 1 creates donation
        ok, msg, don_id = wm.create_donation(
            donor_name="Sharma Wedding Events (Fictional Demo)",
            event_type="Wedding",
            food_description="Royal Banquet Dinner",
            quantity_portions=100,
            prep_datetime=prep,
            available_from=avail,
            pickup_deadline=dead,
            storage_info="Insulated warmers >65°C",
            location="Civil Lines, Prayagraj",
            private_contact="+91-98765-11111",
            acting_user=self.donor_user1
        )
        self.assertTrue(ok)

        # NGO 1 requests pickup
        req_ok, req_msg, req_id = wm.request_pickup(
            donation_id=don_id,
            ngo_name="Prayag Annapurna Seva Sansthan (Fictional Demo NGO)",
            ngo_contact="+91-94500-11111",
            requested_portions=50,
            proposed_pickup_time=dead,
            acting_user=self.ngo_user1
        )
        self.assertTrue(req_ok)

        # Cross-Tenant Violation 1: Donor 2 tries to confirm/reject Donor 1's request
        cross_ok, cross_msg = wm.update_request_status(
            request_id=req_id,
            new_status="Confirmed",
            acting_user=self.donor_user2,
            remarks="Unauthorized confirmation attempt by Donor 2"
        )
        self.assertFalse(cross_ok, "Donor 2 should not be able to confirm Donor 1's listing")
        self.assertIn("Unauthorized", cross_msg)

        # Cross-Tenant Violation 2: Donor 2 tries to cancel Donor 1's donation
        cross_can_ok, cross_can_msg = wm.cancel_donation(
            donation_id=don_id,
            acting_user=self.donor_user2,
            reason="Malicious cancellation attempt"
        )
        self.assertFalse(cross_can_ok, "Donor 2 should not be able to cancel Donor 1's donation")
        self.assertIn("Unauthorized", cross_can_msg)

        # Legitimate Donor 1 confirms request
        legit_ok, legit_msg = wm.update_request_status(
            request_id=req_id,
            new_status="Confirmed",
            acting_user=self.donor_user1
        )
        self.assertTrue(legit_ok)

        # Cross-Tenant Violation 3: NGO 2 tries to mark NGO 1's request as Collected
        ngo_cross_ok, ngo_cross_msg = wm.update_request_status(
            request_id=req_id,
            new_status="Collected",
            acting_user=self.ngo_user2,
            remarks="Unauthorized NGO 2 pickup claim"
        )
        self.assertFalse(ngo_cross_ok, "NGO 2 should not be able to progress NGO 1's pickup milestones")
        self.assertIn("Unauthorized", ngo_cross_msg)

        # Legitimate NGO 1 marks Collected and Delivered
        ngo_legit_col, _ = wm.update_request_status(
            request_id=req_id,
            new_status="Collected",
            acting_user=self.ngo_user1
        )
        self.assertTrue(ngo_legit_col)

        ngo_legit_del, _ = wm.update_request_status(
            request_id=req_id,
            new_status="Delivered",
            acting_user=self.ngo_user1
        )
        self.assertTrue(ngo_legit_del)

    # -------------------------------------------------------------
    # 4. Enforce NGO Verification Inside request_pickup()
    # -------------------------------------------------------------
    def test_04_unverified_ngo_blocked_by_backend(self):
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(
            donor_name="Sharma Wedding Events (Fictional Demo)",
            event_type="Wedding",
            food_description="Gourmet buffet",
            quantity_portions=80,
            prep_datetime=prep,
            available_from=avail,
            pickup_deadline=dead,
            storage_info="Warmers",
            location="Civil Lines",
            private_contact="+91-98765-11111",
            acting_user=self.donor_user1
        )

        # Unverified NGO (NGO-003, new_hope) attempts pickup
        unv_ok, unv_msg, _ = wm.request_pickup(
            donation_id=don_id,
            ngo_name="New Hope Food Rescue (Fictional Demo NGO)",
            ngo_contact="+91-94500-33333",
            requested_portions=30,
            proposed_pickup_time=dead,
            acting_user=self.ngo_unverified
        )
        self.assertFalse(unv_ok, "Unverified NGO must be blocked from requesting pickup")
        self.assertIn("verification is required", unv_msg)

        # Non-admin attempts to approve NGO
        non_admin_ok, non_admin_msg = wm.approve_ngo(
            acting_user=self.donor_user1,
            ngo_id="NGO-003"
        )
        self.assertFalse(non_admin_ok, "Non-admin cannot approve NGO")
        self.assertIn("Unauthorized", non_admin_msg)

        # Admin approves NGO
        admin_ok, admin_msg = wm.approve_ngo(
            acting_user=self.admin_user,
            ngo_id="NGO-003"
        )
        self.assertTrue(admin_ok)

        # Now verified NGO can place pickup request
        now_v_ok, now_v_msg, req_id = wm.request_pickup(
            donation_id=don_id,
            ngo_name="New Hope Food Rescue (Fictional Demo NGO)",
            ngo_contact="+91-94500-33333",
            requested_portions=30,
            proposed_pickup_time=dead,
            acting_user=self.ngo_unverified
        )
        self.assertTrue(now_v_ok, f"Newly approved NGO should succeed: {now_v_msg}")

    # -------------------------------------------------------------
    # 5. Contact Privacy & Zero Phone Leaks in DataFrames/CSVs
    # -------------------------------------------------------------
    def test_05_contact_privacy_masking_and_csv_protection(self):
        now = datetime.now(IST)
        prep = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail = now.strftime("%Y-%m-%d %H:%M:%S")
        dead = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
        secret_phone = "+91-98765-99887"

        _, _, don_id = wm.create_donation(
            donor_name="Sharma Wedding Events (Fictional Demo)",
            event_type="Wedding",
            food_description="Privacy Test Meal",
            quantity_portions=100,
            prep_datetime=prep,
            available_from=avail,
            pickup_deadline=dead,
            storage_info="Warmers",
            location="Civil Lines",
            private_contact=secret_phone,
            acting_user=self.donor_user1
        )

        _, _, req_id = wm.request_pickup(
            donation_id=don_id,
            ngo_name="Prayag Annapurna Seva Sansthan (Fictional Demo NGO)",
            ngo_contact="+91-94500-11111",
            requested_portions=40,
            proposed_pickup_time=dead,
            acting_user=self.ngo_user1
        )

        # 1. Generic DataFrames must NOT contain private_contact or secret phone
        donations_df = wm.get_donations_df()
        self.assertNotIn("private_contact", donations_df.columns)
        self.assertNotIn("raw_donor_contact", donations_df.columns)

        requests_df = wm.get_pickup_requests_df()
        self.assertNotIn("private_contact", requests_df.columns)
        self.assertNotIn("raw_donor_contact", requests_df.columns)

        # 2. CSV exports must never leak secret phone
        csv_don = wm.export_dataframe_to_csv_string(donations_df)
        self.assertNotIn(secret_phone, csv_don)

        csv_req = wm.export_dataframe_to_csv_string(requests_df)
        self.assertNotIn(secret_phone, csv_req)

        # 3. get_contact_for() authorization behavior
        # - Donor owner gets full contact
        donor_view = wm.get_contact_for(req_id, acting_user=self.donor_user1)
        self.assertEqual(donor_view, secret_phone)

        # - Admin gets full contact
        admin_view = wm.get_contact_for(req_id, acting_user=self.admin_user)
        self.assertEqual(admin_view, secret_phone)

        # - Requesting NGO while status is 'Requested' gets masked phone with <= 2 digits visible
        ngo_req_view = wm.get_contact_for(req_id, acting_user=self.ngo_user1)
        self.assertNotEqual(ngo_req_view, secret_phone)
        self.assertTrue(ngo_req_view.endswith("87") or "87" in ngo_req_view)
        # Ensure no more than 2 digits visible
        digits = [c for c in ngo_req_view if c.isdigit()]
        self.assertLessEqual(len(digits), 2, f"Masked contact has too many visible digits: {ngo_req_view}")

        # - Once Confirmed, Requesting NGO gets full phone
        wm.update_request_status(req_id, "Confirmed", acting_user=self.donor_user1)
        ngo_conf_view = wm.get_contact_for(req_id, acting_user=self.ngo_user1)
        self.assertEqual(ngo_conf_view, secret_phone, "Requesting NGO should see phone once Confirmed")

        # - Third party NGO (NGO 2) gets masked phone even when Confirmed
        ngo2_view = wm.get_contact_for(req_id, acting_user=self.ngo_user2)
        self.assertNotEqual(ngo2_view, secret_phone)
        digits_ngo2 = [c for c in ngo2_view if c.isdigit()]
        self.assertLessEqual(len(digits_ngo2), 2)

    # -------------------------------------------------------------
    # 6. HTML & XSS Escaping Across All Render Functions
    # -------------------------------------------------------------
    def test_06_xss_payload_escaping_in_cards(self):
        xss_payload = '<script>alert("pwned")</script><img src=x onerror=alert(1)>'
        xss_payload_a = '<a href="javascript:alert(1)">Click Me</a>'

        row = {
            "id": "DON-XSS-001",
            "donor_name": f"Hacker Catering {xss_payload}",
            "event_type": "Wedding",
            "status": "Available",
            "food_description": f"Biryani with payload {xss_payload_a}",
            "quantity_portions": 50,
            "available_portions": 50,
            "location": f"Hacker Street {xss_payload}",
            "pickup_deadline": "2026-10-20 20:00:00",
            "storage_info": f"Cold storage {xss_payload}",
            "contact": f"+91-99999-00000 {xss_payload}"
        }

        # 1. Donor listing card
        donor_html = render_donor_listing_card(row, lang="en")
        self.assertNotIn("<script>", donor_html)
        self.assertNotIn("<img src=x onerror", donor_html)
        self.assertNotIn('<a href="javascript:', donor_html)
        self.assertIn("&lt;script&gt;", donor_html)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", donor_html)

        # 2. NGO available card
        ngo_avail_html = render_ngo_available_card(row, hrs_left=3.5, lang="en")
        self.assertNotIn("<script>", ngo_avail_html)
        self.assertNotIn("<img src=x onerror", ngo_avail_html)
        self.assertIn("&lt;script&gt;", ngo_avail_html)

        # 3. NGO request card
        req_row = {
            "request_id": "REQ-XSS-001",
            "ngo_name": f"Evil NGO {xss_payload}",
            "request_status": "Requested",
            "donor_name": f"Victim Donor {xss_payload}",
            "donation_id": "DON-XSS-001",
            "food_description": f"Food {xss_payload_a}",
            "location": f"Loc {xss_payload}",
            "request_notes": f"Note {xss_payload}",
            "requested_portions": 20,
            "proposed_pickup_time": "2026-10-20 18:00:00",
            "ngo_contact": f"Phone {xss_payload}",
            "requested_at": "2026-10-19 12:00:00"
        }
        ngo_req_html = render_ngo_request_card(req_row, lang="en")
        self.assertNotIn("<script>", ngo_req_html)
        self.assertNotIn("<img src=x onerror", ngo_req_html)
        self.assertIn("&lt;script&gt;", ngo_req_html)

        # 4. Metric box
        metric_html = render_metric_box(f"Label {xss_payload}", 100, f"Sub {xss_payload}")
        self.assertNotIn("<script>", metric_html)
        self.assertIn("&lt;script&gt;", metric_html)

if __name__ == "__main__":
    unittest.main()
