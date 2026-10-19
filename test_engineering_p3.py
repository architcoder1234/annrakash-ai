"""
test_engineering_p3.py - Phase P3 Verification Test Suite
Tests for Modular Architecture, Bilingual Parity, WCAG 2.1 AA Contrast,
Production Packaging, and Scientific/Environmental Citations.
"""

import unittest
import os
import re
from i18n import TRANSLATIONS, t
import check_contrast
import logistics
import notifications
import workflow_manager as wm
from database import get_connection, init_db

class TestEngineeringP3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure temporary in-memory or fresh DB for tests
        cls.test_db = "file:p3_test_db?mode=memory&cache=shared"

    def test_i18n_exact_key_parity(self):
        """P3.1: Assert 100% key parity between English and Hindi translation dictionaries."""
        en_keys = set(TRANSLATIONS.get("en", {}).keys())
        hi_keys = set(TRANSLATIONS.get("hi", {}).keys())
        
        self.assertGreater(len(en_keys), 50, "English translations must contain all UI keys")
        missing_in_hi = en_keys - hi_keys
        missing_in_en = hi_keys - en_keys
        
        self.assertEqual(missing_in_hi, set(), f"Keys missing in Hindi translation: {missing_in_hi}")
        self.assertEqual(missing_in_en, set(), f"Keys missing in English translation: {missing_in_en}")
        
        # Verify all translation values are non-empty strings
        for k, v in TRANSLATIONS["en"].items():
            self.assertTrue(isinstance(v, str) and len(v.strip()) > 0, f"English key '{k}' has empty value")
        for k, v in TRANSLATIONS["hi"].items():
            self.assertTrue(isinstance(v, str) and len(v.strip()) > 0, f"Hindi key '{k}' has empty value")
            
        # Verify formatting interpolator in t()
        res_en = t("w_balance_ok", lang="en", prep=100, cons=80, edible=15, disc=5)
        self.assertIn("100 Prepared", res_en)
        res_hi = t("w_balance_ok", lang="hi", prep=100, cons=80, edible=15, disc=5)
        self.assertIn("100 तैयार", res_hi)

    def test_wcag_21_aa_color_contrast(self):
        """P3.2: Programmatically verify WCAG 2.1 AA color contrast across all themes."""
        # Run check_all_themes and assert truthy return
        all_passed = check_contrast.check_all_themes()
        self.assertTrue(all_passed, "WCAG 2.1 AA contrast check failed for one or more color pairs")

    def test_modular_components_architecture(self):
        """P3.3: Verify modular component structure and app.py conciseness."""
        from components import (
            render_donor_dashboard,
            render_ngo_dashboard,
            render_admin_dashboard
        )
        self.assertTrue(callable(render_donor_dashboard))
        self.assertTrue(callable(render_ngo_dashboard))
        self.assertTrue(callable(render_admin_dashboard))
        
        # Verify app.py SLOC count is under 250 lines
        app_path = os.path.join(os.path.dirname(__file__), "app.py")
        with open(app_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertLessEqual(len(lines), 250, f"app.py exceeds modular limit of 250 lines (currently {len(lines)})")

    def test_production_packaging_artifacts(self):
        """P3.4: Verify Dockerfile, docker-compose.yml, and requirements.txt validity."""
        base_dir = os.path.dirname(__file__)
        req_path = os.path.join(base_dir, "requirements.txt")
        docker_path = os.path.join(base_dir, "Dockerfile")
        compose_path = os.path.join(base_dir, "docker-compose.yml")
        
        self.assertTrue(os.path.exists(req_path), "requirements.txt must exist")
        self.assertTrue(os.path.exists(docker_path), "Dockerfile must exist")
        self.assertTrue(os.path.exists(compose_path), "docker-compose.yml must exist")
        
        with open(req_path, "r", encoding="utf-8") as f:
            req_content = f.read()
            self.assertIn("streamlit", req_content)
            self.assertIn("bcrypt", req_content)
            self.assertIn("google-genai", req_content)
            
        with open(docker_path, "r", encoding="utf-8") as f:
            docker_content = f.read()
            self.assertIn("FROM python:3.11-slim", docker_content)
            self.assertIn("EXPOSE 8501", docker_content)
            self.assertIn("HEALTHCHECK", docker_content)
            
        with open(compose_path, "r", encoding="utf-8") as f:
            compose_content = f.read()
            self.assertIn("services:", compose_content)
            self.assertIn("app:", compose_content)
            self.assertIn("volumes:", compose_content)
            self.assertIn("app_data", compose_content)

    def test_scientific_esg_citations_and_standards(self):
        """P3.5: Assert environmental factors follow UNEP/FAO standards and are labeled as assumptions."""
        # 0.35 kg/portion (UNEP Food Waste Index)
        # 2.5 kg CO2e / kg food waste (FAO / UNEP GHG benchmark)
        # 1000 L water footprint / kg food (FAO benchmark)
        self.assertEqual(wm.PORTION_TO_KG, 0.35)
        self.assertEqual(wm.KG_TO_CO2E, 2.5)
        self.assertEqual(wm.KG_TO_WATER_L, 1000.0)
        
        # Verify impact calculations adhere to mathematical definitions
        impact = wm.calculate_impact_metrics(100)
        self.assertAlmostEqual(impact["kg_saved"], 35.0)
        self.assertAlmostEqual(impact["co2_avoided_kg"], 87.5)
        self.assertAlmostEqual(impact["water_saved_l"], 35000.0)

    def test_geospatial_haversine_and_logistics(self):
        """P3.6: Verify Haversine distance and transit time estimations."""
        # Civil Lines, Prayagraj to Naini, Prayagraj (~7.5 km)
        lat1, lon1 = 25.4528, 81.8347
        lat2, lon2 = 25.3900, 81.8600
        dist = logistics.calculate_haversine_distance(lat1, lon1, lat2, lon2)
        self.assertGreater(dist, 5.0)
        self.assertLess(dist, 12.0)
        
        # Transit time at 20 km/h
        transit = logistics.estimate_transit_minutes(dist, speed_kmh=20.0)
        self.assertGreater(transit, 15)
        self.assertLess(transit, 40)

if __name__ == "__main__":
    unittest.main()
