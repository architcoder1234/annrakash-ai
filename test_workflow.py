"""
End-to-End Automated Verification Test Suite for AnnRakshak AI.
Runs completely isolated against a temporary SQLite database (never touches annrakshak.db).

Tests all 12 audited dimensions:
- Test A: Wedding donation creation with IST time & food safety window check.
- Test B: Partial pickup requests (multiple requests per donation) & donor confirmation.
- Test C: Milestone transitions (Collected -> Delivered) & Environmental Impact KPIs (kg, CO2).
- Test D: Atomic portion release upon Request Rejection and Cancellation.
- Test E: Auto-expiry past deadline & food safety window enforcement (>6h blocked).
- Test F: Concurrency & Threaded contention test proving BEGIN IMMEDIATE prevents double-booking.
- Test G: Demand predictor edge cases (0/negative attendees, buffer clamping 0-50%, cold start).
- Test H: Gemma 4 mocked client test (with PII phone redaction & Hindi) + deterministic fallback.
- Test I: CSV injection protection (formula escaping for =, +, -, @).
"""

import sys
import os
import unittest
import tempfile
import threading
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

# Ensure current directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database
import workflow_manager as wm
import demand_predictor as dp
import ai_insights as ai

IST = ZoneInfo("Asia/Kolkata")

class TestAnnRakshakAIAudit(unittest.TestCase):
    temp_db_file = None

    @classmethod
    def setUpClass(cls):
        # Create an isolated temporary SQLite database file for testing
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
        # Ensure fresh state in the temp db
        database.init_db(force_reset=True, db_path=self.temp_db_path)
        self.donor_user1 = {"id": "USR-001", "username": "sharma_catering", "role": "donor", "org_id": "DONOR-001", "is_active": True}
        self.donor_user2 = {"id": "USR-002", "username": "verma_events", "role": "donor", "org_id": "DONOR-002", "is_active": True}
        self.ngo_user1 = {"id": "USR-003", "username": "prayag_seva", "role": "ngo", "org_id": "NGO-001", "is_active": True}
        self.ngo_user2 = {"id": "USR-004", "username": "ganga_relief", "role": "ngo", "org_id": "NGO-002", "is_active": True}
        self.admin_user = {"id": "USR-ADMIN", "username": "admin", "role": "admin", "org_id": None, "is_active": True}

    def test_a_create_donation_and_food_safety_window(self):
        print("\n--- Test A: Create Donation & Food Safety Window ---")
        now = datetime.now(IST)
        prep_time = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        avail_time = now.strftime("%Y-%m-%d %H:%M:%S")
        dead_time = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        # 1. Valid donation
        ok, msg, don_id = wm.create_donation(
            acting_user=self.donor_user1,
            donor_name="Sharma Wedding Events (Fictional Demo)",
            event_type="Wedding",
            food_description="Vegetable pulao, dal makhani, paneer butter masala, chapati",
            quantity_portions=100,
            prep_datetime=prep_time,
            available_from=avail_time,
            pickup_deadline=dead_time,
            storage_info="Commercial insulated food warmers >65°C",
            location="Civil Lines Banquet Lawn (Fictional Demo Locality), Prayagraj",
            private_contact="+91-98765-11111",
            food_safety_window_hours=6.0
        )
        self.assertTrue(ok, f"Failed to create valid donation: {msg}")
        self.assertIsNotNone(don_id)
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after donation creation")

        # 2. Block food prepared > 6 hours ago
        too_old_prep = (now - timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
        old_ok, old_msg, _ = wm.create_donation(
            acting_user=self.donor_user1,
            donor_name="Old Food Donor",
            event_type="Wedding",
            food_description="Stale food",
            quantity_portions=50,
            prep_datetime=too_old_prep,
            available_from=avail_time,
            pickup_deadline=dead_time,
            storage_info="Room temp",
            location="Civil Lines",
            private_contact="+91-98765-11111",
            food_safety_window_hours=6.0
        )
        self.assertFalse(old_ok, "Food safety violation should have blocked food prepared 7 hours ago.")
        self.assertIn("Food Safety Policy Violation", old_msg)
        print("Test A PASSED: Valid donation created and food-safety threshold (>6h) enforced.")

    def test_b_partial_requests_and_confirm(self):
        print("\n--- Test B: Partial Pickup Requests & Confirmation ---")
        now = datetime.now(IST)
        prep_time = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail_time = now.strftime("%Y-%m-%d %H:%M:%S")
        dead_time = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(
            acting_user=self.donor_user1,
            donor_name="Grand Reception (Fictional Demo)",
            event_type="Wedding",
            food_description="North Indian Deluxe Buffet",
            quantity_portions=100,
            prep_datetime=prep_time,
            available_from=avail_time,
            pickup_deadline=dead_time,
            storage_info="Warmers",
            location="Civil Lines",
            private_contact="+91-98765-22222"
        )
        self.assertTrue(wm.invariant_check(don_id))

        # Partial Request 1: NGO 1 requests 40 portions
        ok1, msg1, req_id1 = wm.request_pickup(
            acting_user=self.ngo_user1,
            donation_id=don_id,
            requested_portions=40,
            proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.assertTrue(ok1, f"Partial request 1 failed: {msg1}")
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after partial request 1")

        # Check remaining portions: 100 - 40 = 60, donation status still Available!
        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT available_portions, status FROM donations WHERE id = ?;", (don_id,))
        don_row = cur.fetchone()
        self.assertEqual(don_row["available_portions"], 60)
        self.assertEqual(don_row["status"], "Available")

        # Partial Request 2: NGO 2 requests 30 portions
        ok2, msg2, req_id2 = wm.request_pickup(
            acting_user=self.ngo_user2,
            donation_id=don_id,
            requested_portions=30,
            proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.assertTrue(ok2, f"Partial request 2 failed: {msg2}")
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after partial request 2")
        cur.execute("SELECT available_portions FROM donations WHERE id = ?;", (don_id,))
        self.assertEqual(cur.fetchone()["available_portions"], 30)

        # Confirm Request 1
        conf_ok, conf_msg = wm.update_request_status(
            request_id=req_id1,
            new_status="Confirmed",
            acting_user=self.donor_user1,
            remarks="Confirmed by donor"
        )
        self.assertTrue(conf_ok, f"Confirm failed: {conf_msg}")
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after confirm request 1")

        cur.execute("SELECT status FROM pickup_requests WHERE id = ?;", (req_id1,))
        self.assertEqual(cur.fetchone()["status"], "Confirmed")
        conn.close()
        print("Test B PASSED: Partial requests handled cleanly; remaining portions stay Available.")

    def test_c_milestones_and_impact_metrics(self):
        print("\n--- Test C: Milestones & Environmental Impact Metrics ---")
        now = datetime.now(IST)
        prep_time = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail_time = now.strftime("%Y-%m-%d %H:%M:%S")
        dead_time = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(
            acting_user=self.donor_user1,
            donor_name="Catering Surplus",
            event_type="Corporate",
            food_description="Meal Boxes",
            quantity_portions=50,
            prep_datetime=prep_time,
            available_from=avail_time,
            pickup_deadline=dead_time,
            storage_info="Insulated",
            location="MG Marg",
            private_contact="+91-98765-33333"
        )
        self.assertTrue(wm.invariant_check(don_id))

        _, _, req_id = wm.request_pickup(
            acting_user=self.ngo_user1,
            donation_id=don_id,
            requested_portions=50,
            proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.assertTrue(wm.invariant_check(don_id))

        wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=self.donor_user1)
        self.assertTrue(wm.invariant_check(don_id))

        wm.update_request_status(request_id=req_id, new_status="Collected", acting_user=self.ngo_user1)
        self.assertTrue(wm.invariant_check(don_id))

        wm.update_request_status(request_id=req_id, new_status="Delivered", acting_user=self.ngo_user1)
        self.assertTrue(wm.invariant_check(don_id))

        impact = wm.get_impact_summary(avg_kg_per_portion=0.35)
        self.assertGreaterEqual(impact["portions_delivered"], 50)
        self.assertGreaterEqual(impact["kg_food_saved"], 17.5) # 50 * 0.35 = 17.5 kg
        self.assertGreaterEqual(impact["co2_avoided_kg"], 43.75) # 17.5 * 2.5 = 43.75 kg CO2
        self.assertEqual(impact["meals_served"], impact["portions_delivered"])
        print(f"Test C PASSED: Rescued {impact['kg_food_saved']} kg food; avoided {impact['co2_avoided_kg']} kg CO2.")

    def test_d_portion_release_on_rejection_and_cancellation(self):
        print("\n--- Test D: Portion Release on Rejection and Cancellation ---")
        now = datetime.now(IST)
        prep_time = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail_time = now.strftime("%Y-%m-%d %H:%M:%S")
        dead_time = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(
            acting_user=self.donor_user1,
            donor_name="Hotel Buffet",
            event_type="Restaurant",
            food_description="Buffet items",
            quantity_portions=80,
            prep_datetime=prep_time,
            available_from=avail_time,
            pickup_deadline=dead_time,
            storage_info="Warmers",
            location="Civil Lines",
            private_contact="+91-98765-44444"
        )
        self.assertTrue(wm.invariant_check(don_id))

        # Claim 50 portions -> available becomes 30
        _, _, req_id = wm.request_pickup(
            acting_user=self.ngo_user2,
            donation_id=don_id,
            requested_portions=50,
            proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.assertTrue(wm.invariant_check(don_id))

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT available_portions FROM donations WHERE id = ?;", (don_id,))
        self.assertEqual(cur.fetchone()["available_portions"], 30)

        # Reject the request -> portions should return to 80
        rej_ok, rej_msg = wm.update_request_status(
            request_id=req_id,
            new_status="Rejected",
            acting_user=self.donor_user1,
            remarks="Cannot coordinate time"
        )
        self.assertTrue(rej_ok, f"Reject failed: {rej_msg}")
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after rejection")

        cur.execute("SELECT available_portions, status FROM donations WHERE id = ?;", (don_id,))
        updated_don = cur.fetchone()
        self.assertEqual(updated_don["available_portions"], 80)
        self.assertEqual(updated_don["status"], "Available")

        # Claim 80 portions again, then Cancel
        _, _, req_id2 = wm.request_pickup(
            acting_user=self.ngo_user1,
            donation_id=don_id,
            requested_portions=80,
            proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        )
        self.assertTrue(wm.invariant_check(don_id))
        cur.execute("SELECT available_portions FROM donations WHERE id = ?;", (don_id,))
        self.assertEqual(cur.fetchone()["available_portions"], 0)

        canc_ok, canc_msg = wm.update_request_status(
            request_id=req_id2,
            new_status="Cancelled",
            acting_user=self.ngo_user1,
            remarks="Van breakdown"
        )
        self.assertTrue(canc_ok, f"Cancel failed: {canc_msg}")
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after cancellation")

        cur.execute("SELECT available_portions, status FROM donations WHERE id = ?;", (don_id,))
        restored_don = cur.fetchone()
        self.assertEqual(restored_don["available_portions"], 80)
        self.assertEqual(restored_don["status"], "Available")
        conn.close()
        print("Test D PASSED: Portions atomically returned to pool on Rejection and Cancellation.")

    def test_e_auto_expiry(self):
        print("\n--- Test E: Auto-Expiry Past Deadline ---")
        now = datetime.now(IST)
        prep_time = (now - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        avail_time = (now - timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
        past_deadline = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S") # 1 hour ago!

        # Insert directly to simulate past deadline
        conn = database.get_connection()
        cur = conn.cursor()
        don_id = "DON-PAST-EXP-001"
        cur.execute("""
            INSERT INTO donations (
                id, donor_id, donor_name, event_type, food_description, quantity_portions,
                available_portions, prep_datetime, available_from, pickup_deadline,
                storage_info, location, private_contact, notes, status, food_safety_window_hours,
                created_at, updated_at
            ) VALUES (?, 'DONOR-001', 'Expired Host', 'Wedding', 'Items', 40, 40, ?, ?, ?, 'Hot', 'Location', '+91-98765-55555', '', 'Available', 6.0, ?, ?);
        """, (don_id, prep_time, avail_time, past_deadline, now.isoformat(), now.isoformat()))
        conn.close()

        # Run auto-expiry check
        expired_count = wm.check_and_expire_donations()
        self.assertGreaterEqual(expired_count, 1)

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT status FROM donations WHERE id = ?;", (don_id,))
        self.assertEqual(cur.fetchone()["status"], "Expired")
        conn.close()
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after auto-expiry")
        print(f"Test E PASSED: Auto-expired {expired_count} donation(s) past pickup deadline.")

    def test_f_concurrency_no_double_booking(self):
        print("\n--- Test F: Concurrency & Double-Booking Thread Contention ---")
        now = datetime.now(IST)
        prep_time = (now - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        avail_time = now.strftime("%Y-%m-%d %H:%M:%S")
        dead_time = (now + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")

        _, _, don_id = wm.create_donation(
            acting_user=self.donor_user1,
            donor_name="Limited Food Donor",
            event_type="Wedding",
            food_description="Hot biryani",
            quantity_portions=50, # Exactly 50 portions available
            prep_datetime=prep_time,
            available_from=avail_time,
            pickup_deadline=dead_time,
            storage_info="Warmers",
            location="Civil Lines",
            private_contact="+91-98765-66666"
        )
        self.assertTrue(wm.invariant_check(don_id))

        success_count = 0
        failure_count = 0
        lock = threading.Lock()

        def try_claim(thread_idx):
            nonlocal success_count, failure_count
            ok, msg, req_id = wm.request_pickup(
                acting_user=self.ngo_user1,
                donation_id=don_id,
                requested_portions=40, # 40 portions requested each
                proposed_pickup_time=(now + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
            )
            with lock:
                if ok:
                    success_count += 1
                else:
                    failure_count += 1

        # Launch 10 concurrent threads attempting to claim 40 portions each
        threads = [threading.Thread(target=try_claim, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Since only 50 portions exist and each requests 40, strictly only 1 can succeed!
        self.assertEqual(success_count, 1, f"Expected exactly 1 claim to succeed, but got {success_count}.")
        self.assertEqual(failure_count, 9, f"Expected 9 claims to fail due to portion exhaustion, got {failure_count}.")

        conn = database.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT available_portions FROM donations WHERE id = ?;", (don_id,))
        self.assertEqual(cur.fetchone()["available_portions"], 10) # 50 - 40 = 10
        conn.close()
        self.assertTrue(wm.invariant_check(don_id), "Portion invariant failed after concurrent contention")
        print("Test F PASSED: BEGIN IMMEDIATE transaction lock serialized 10 threads; exactly 1 claimed, 9 safely rejected.")

    def test_g_demand_predictor_edge_cases(self):
        print("\n--- Test G: Demand Predictor Edge Cases & Clamping ---")
        # 1. Zero/Negative Attendees
        with self.assertRaises(ValueError):
            dp.calculate_demand_estimate("Wedding", "Dinner", expected_attendees=0, cost_per_meal=100.0)
        with self.assertRaises(ValueError):
            dp.calculate_demand_estimate("Wedding", "Dinner", expected_attendees=-25, cost_per_meal=100.0)

        # 2. Buffer clamping
        res_high_buf = dp.calculate_demand_estimate(
            "Wedding", "Dinner", expected_attendees=100, cost_per_meal=100.0, safety_buffer_pct=80.0
        )
        self.assertEqual(res_high_buf["safety_buffer_pct"], 50.0, "Buffer should be clamped to 50%.")

        res_neg_buf = dp.calculate_demand_estimate(
            "Wedding", "Dinner", expected_attendees=100, cost_per_meal=100.0, safety_buffer_pct=-15.0
        )
        self.assertEqual(res_neg_buf["safety_buffer_pct"], 0.0, "Buffer should be clamped to 0%.")

        # 3. Cold Start No-History Fallback
        res_fallback = dp.calculate_demand_estimate(
            "Conference", "Lunch", expected_attendees=100, cost_per_meal=150.0, safety_buffer_pct=10.0, historical_records=[]
        )
        self.assertTrue(res_fallback["is_fallback"])
        self.assertIn("formula_latex", res_fallback)
        print("Test G PASSED: Demand predictor properly handles 0/negative attendees, clamps buffers, and falls back.")

    def test_h_ai_insights_mock_and_fallback(self):
        print("\n--- Test H: AI Insights Mocking & Fallback ---")
        waste_records = wm.get_food_waste_df().to_dict(orient='records')

        # 1. Rule-based fallback when no API key
        with patch.object(ai, 'get_api_key', return_value=None):
            fb = ai.analyze_food_waste_with_gemma(waste_records, lang="hi")
            self.assertTrue(fb["success"])
            self.assertFalse(fb["is_live_gemma"])
            self.assertIn("Deterministic Rule-Based", fb["source"])
            self.assertIn("विश्लेषित", fb["observations"][0]) # Hindi output!

        # 2. Mock Gemma client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "### Observations\nMocked AI waste analysis.\n### Practical Recommendations\n1. Control prep."
        mock_client.models.generate_content.return_value = mock_response

        with patch.object(ai, 'get_api_key', return_value="mock-test-key"):
            with patch('google.genai.Client', return_value=mock_client):
                res = ai.analyze_food_waste_with_gemma(waste_records, model_name="gemma-4-26b-a4b-it", lang="en")
                self.assertTrue(res["success"])
                self.assertTrue(res["is_live_gemma"])
                self.assertIn("Mocked AI waste analysis", res["raw_text"])

        # 3. PII Scrubbing check
        test_text = "Call donor at +91-98765-43210 or email test@example.com for pickup."
        scrubbed = ai.scrub_pii(test_text)
        self.assertNotIn("+91-98765-43210", scrubbed)
        self.assertNotIn("test@example.com", scrubbed)
        self.assertIn("[PHONE REDACTED]", scrubbed)
        self.assertIn("[EMAIL REDACTED]", scrubbed)
        print("Test H PASSED: Gemma mocked and verified; PII scrubbed; rule-based Hindi fallback validated.")

    def test_i_csv_injection_escaping(self):
        print("\n--- Test I: CSV Injection Escaping ---")
        import pandas as pd
        evil_df = pd.DataFrame([
            {"name": "=1+2", "command": "-cmd|' /C calc'!A0", "at_sign": "@SUM(1,2)", "safe": "Normal Text"}
        ])
        csv_str = wm.export_dataframe_to_csv_string(evil_df)
        self.assertIn("'=1+2", csv_str)
        self.assertIn("'-cmd|", csv_str)
        self.assertIn("'@SUM", csv_str)
        self.assertIn("Normal Text", csv_str)
        print("Test I PASSED: All CSV formula injection triggers safely escaped with leading single-quote.")

if __name__ == "__main__":
    unittest.main()
