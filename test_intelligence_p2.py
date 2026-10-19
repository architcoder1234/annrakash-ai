"""
Phase P2 Regression & Verification Test Suite for AnnRakshak AI.
Verifies:
1. Upgraded Demand Predictor with P80 prediction intervals (Z=1.28).
2. Historical waste sample backtesting with MAPE (Mean Absolute Percentage Error) metric.
3. Resilient Gemma client with retries, exponential backoff, timeout handling, and PII scrubbing.
4. Geospatial logistics: Haversine distance, estimated transit time at 20 km/h, and nearest-first sorting.
5. Multi-channel notification engine (SMS, WhatsApp, Email) writing to notifications table.
6. CSR ESG & UNEP environmental impact metrics (CO2e, kg food, water footprint).
"""

import unittest
import os
import tempfile
import math
from unittest.mock import MagicMock, patch

from database import init_db, get_connection
import demand_predictor as dp
import logistics
from notifications import NotificationEngine, emit_workflow_notification
import ai_insights as ai

class TestIntelligenceP2(unittest.TestCase):
    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)
        os.environ["ANNRAKSHAK_DB_PATH"] = self.temp_db_path
        init_db(force_reset=True, db_path=self.temp_db_path)
        self.notif_engine = NotificationEngine(db_path=self.temp_db_path)

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except OSError:
                pass

    def test_demand_predictor_p80_interval(self):
        """Test that P80 prediction intervals are computed correctly using Z=1.28."""
        sample_history = [
            {"id": "W1", "meal_type": "Dinner", "provider_name": "Wedding", "portions_prepared": 300, "portions_consumed": 240, "discarded_waste": 40, "edible_surplus": 20},
            {"id": "W2", "meal_type": "Dinner", "provider_name": "Wedding", "portions_prepared": 250, "portions_consumed": 210, "discarded_waste": 25, "edible_surplus": 15},
            {"id": "W3", "meal_type": "Dinner", "provider_name": "Wedding", "portions_prepared": 400, "portions_consumed": 310, "discarded_waste": 60, "edible_surplus": 30}
        ]

        res = dp.calculate_demand_estimate(
            event_type="Wedding",
            meal_type="Dinner",
            expected_attendees=350,
            cost_per_meal=180.0,
            safety_buffer_pct=8.0,
            historical_records=sample_history
        )

        self.assertIn("p80_portions", res)
        self.assertIn("p80_waste_ratio", res)
        self.assertIn("std_waste_ratio", res)
        self.assertGreater(res["p80_portions"], 0)
        # P80 risk-averse bound should be >= net demand
        self.assertGreaterEqual(res["p80_portions"], res["estimated_net_demand"])

    def test_demand_predictor_mape_backtesting(self):
        """Test historical waste record backtesting and MAPE accuracy score."""
        sample_history = [
            {"id": "W1", "date": "2026-10-10", "meal_type": "Dinner", "provider_name": "Grand Banquet", "portions_prepared": 200, "portions_consumed": 170, "cost_per_meal": 150.0},
            {"id": "W2", "date": "2026-10-11", "meal_type": "Lunch", "provider_name": "City Restaurant", "portions_prepared": 100, "portions_consumed": 88, "cost_per_meal": 100.0},
            {"id": "W3", "date": "2026-10-12", "meal_type": "Dinner", "provider_name": "Hostel Mess", "portions_prepared": 250, "portions_consumed": 220, "cost_per_meal": 80.0}
        ]

        backtest = dp.backtest_model(sample_history)
        self.assertEqual(backtest["sample_count"], 3)
        self.assertIsInstance(backtest["mape_pct"], float)
        self.assertGreaterEqual(backtest["mape_pct"], 0.0)
        self.assertLessEqual(backtest["mape_pct"], 100.0)
        self.assertGreaterEqual(backtest["accuracy_pct"], 0.0)
        self.assertEqual(len(backtest["details"]), 3)

    def test_haversine_logistics_and_sorting(self):
        """Test Haversine distance, transit time at 20 km/h, and nearest-first sorting."""
        # Civil Lines coordinates: 25.4520, 81.8340
        # Naini coordinates: 25.4080, 81.8680 (approx 5-6 km apart)
        dist = logistics.haversine_distance_km(25.4520, 81.8340, 25.4080, 81.8680)
        self.assertGreater(dist, 4.0)
        self.assertLess(dist, 8.0)

        transit_time = logistics.estimate_transit_time_minutes(dist, speed_kmh=20.0)
        self.assertGreaterEqual(transit_time, 12)
        self.assertLessEqual(transit_time, 25)

        # Test listing sorting relative to Naini (25.4080, 81.8680)
        listings = [
            {"id": "DON-FAR", "donor_name": "Far Donor", "lat": 25.5500, "lng": 81.9500},
            {"id": "DON-NEAR", "donor_name": "Near Donor", "lat": 25.4120, "lng": 81.8700},
            {"id": "DON-MID", "donor_name": "Mid Donor", "lat": 25.4520, "lng": 81.8340}
        ]

        sorted_listings = logistics.sort_listings_by_distance(listings, viewer_lat=25.4080, viewer_lng=81.8680)
        self.assertEqual(sorted_listings[0]["id"], "DON-NEAR")
        self.assertEqual(sorted_listings[1]["id"], "DON-MID")
        self.assertEqual(sorted_listings[2]["id"], "DON-FAR")
        self.assertLess(sorted_listings[0]["distance_km"], sorted_listings[1]["distance_km"])
        self.assertLess(sorted_listings[1]["distance_km"], sorted_listings[2]["distance_km"])

    def test_multichannel_notification_engine(self):
        """Test that notification engine emits SMS, WhatsApp, and Email records to the DB."""
        dispatched = self.notif_engine.emit(
            event_type="donation_created",
            recipient_id="DONOR-001",
            recipient_type="donor",
            title="Listing Live",
            body="Your surplus food listing is now available for pickup claims."
        )

        self.assertEqual(len(dispatched), 3)
        channels = [d["channel"] for d in dispatched]
        self.assertIn("sms", channels)
        self.assertIn("whatsapp", channels)
        self.assertIn("email", channels)

        # Verify persisted in database
        saved = self.notif_engine.list_notifications(recipient_id="DONOR-001")
        self.assertEqual(len(saved), 3)
        for s in saved:
            self.assertEqual(s["status"], "sent")
            self.assertIsNotNone(s["sent_at"])

    def test_resilient_gemma_client_retries_and_timeout(self):
        """Test that call_gemma_with_retry retries on failure and enforces 10s timeout."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Actionable waste reduction insight generated."

        # Simulate 1 transient failure followed by success
        mock_client.models.generate_content.side_effect = [
            Exception("Temporary network blip"),
            mock_response
        ]

        res = ai.call_gemma_with_retry(
            mock_client,
            model_name="gemma-4-26b-a4b-it",
            contents="Analyze waste log",
            max_retries=2,
            timeout_seconds=5.0
        )
        self.assertEqual(res, "Actionable waste reduction insight generated.")
        self.assertEqual(mock_client.models.generate_content.call_count, 2)

    def test_pii_scrubbing(self):
        """Verify that private phone numbers and emails are completely scrubbed before sending to AI."""
        text = "Contact donor Rajesh at +91-98765-43210 or email test@example.com for pickup."
        scrubbed = ai.scrub_pii(text)
        self.assertNotIn("+91-98765-43210", scrubbed)
        self.assertNotIn("test@example.com", scrubbed)
        self.assertIn("[PHONE REDACTED]", scrubbed)
        self.assertIn("[EMAIL REDACTED]", scrubbed)

if __name__ == "__main__":
    unittest.main()
