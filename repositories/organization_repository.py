"""
Organization, User, Audit, and Waste Repository for AnnRakshak AI.
Encapsulates all SQL persistence for Donors, NGOs, Users, Status History, and Food Waste logs.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from .base import BaseRepository

class OrganizationRepository(BaseRepository):
    # Donors
    def get_donor_by_id(self, donor_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT id, name, contact, location, lat, lng, created_at FROM donors WHERE id = ?;"
        return self.execute_one(query, (donor_id,), conn=conn)

    def get_donor_by_name(self, name: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT id, name, contact, location, lat, lng, created_at FROM donors WHERE LOWER(name) = LOWER(?) OR id = ?;"
        return self.execute_one(query, (name.strip(), name.strip()), conn=conn)

    def list_donors(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = "SELECT id, name, contact, location, lat, lng, created_at FROM donors ORDER BY name ASC;"
        return self.execute_query(query, conn=conn)

    def insert_donor(self, donor_id: str, name: str, contact: str, location: str, lat: float = 25.4358, lng: float = 81.8463, created_at: str = "", conn: Optional[sqlite3.Connection] = None) -> None:
        query = """
            INSERT OR REPLACE INTO donors (id, name, contact, location, lat, lng, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        self.execute_non_query(query, (donor_id, name, contact, location, lat, lng, created_at), conn=conn)

    # NGOs
    def get_ngo_by_id(self, ngo_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT id, name, contact, location, lat, lng, is_verified, approved_by, capacity_portions, created_at FROM ngos WHERE id = ?;"
        return self.execute_one(query, (ngo_id,), conn=conn)

    def get_ngo_by_name(self, name: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT id, name, contact, location, lat, lng, is_verified, approved_by, capacity_portions, created_at FROM ngos WHERE LOWER(name) = LOWER(?) OR id = ?;"
        return self.execute_one(query, (name.strip(), name.strip()), conn=conn)

    def is_ngo_verified(self, ngo_id_or_name: str, conn: Optional[sqlite3.Connection] = None) -> bool:
        if not ngo_id_or_name:
            return False
        clean = ngo_id_or_name.strip()
        query = "SELECT is_verified FROM ngos WHERE id = ? OR LOWER(name) = LOWER(?);"
        row = self.execute_one(query, (clean, clean), conn=conn)
        if row:
            return bool(row["is_verified"])
        return False

    def list_ngos(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = "SELECT id, name, contact, location, lat, lng, is_verified, approved_by, capacity_portions, created_at FROM ngos ORDER BY created_at DESC;"
        return self.execute_query(query, conn=conn)

    def approve_ngo(self, ngo_id: str, approved_by: str, conn: Optional[sqlite3.Connection] = None) -> int:
        query = "UPDATE ngos SET is_verified = 1, approved_by = ? WHERE id = ?;"
        return self.execute_non_query(query, (approved_by, ngo_id), conn=conn)

    def insert_ngo(self, ngo_id: str, name: str, contact: str, location: str, lat: float = 25.4358, lng: float = 81.8463, is_verified: int = 0, approved_by: Optional[str] = None, capacity_portions: int = 100, created_at: str = "", conn: Optional[sqlite3.Connection] = None) -> None:
        query = """
            INSERT OR REPLACE INTO ngos (id, name, contact, location, lat, lng, is_verified, approved_by, capacity_portions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.execute_non_query(query, (ngo_id, name, contact, location, lat, lng, is_verified, approved_by, capacity_portions, created_at), conn=conn)

    # Users
    def get_user_by_username(self, username: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT id, username, password_hash, role, org_id, is_active, created_at FROM users WHERE username = ?;"
        return self.execute_one(query, (username.strip(),), conn=conn)

    def get_user_by_id(self, user_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = "SELECT id, username, password_hash, role, org_id, is_active, created_at FROM users WHERE id = ?;"
        return self.execute_one(query, (user_id,), conn=conn)

    def insert_user(self, user_id: str, username: str, password_hash: str, role: str, org_id: Optional[str] = None, is_active: int = 1, created_at: str = "", conn: Optional[sqlite3.Connection] = None) -> None:
        query = """
            INSERT OR REPLACE INTO users (id, username, password_hash, role, org_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        self.execute_non_query(query, (user_id, username, password_hash, role, org_id, is_active, created_at), conn=conn)

    # Status History
    def record_status_change(self, entity_type: str, entity_id: str, previous_status: Optional[str], new_status: str, changed_by: str, timestamp: str, remarks: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            INSERT INTO status_history (entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        return self.execute_non_query(query, (entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks), conn=conn)

    def get_history_for_entity(self, entity_type: str, entity_id: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT id, entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks
            FROM status_history
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY id ASC;
        """
        return self.execute_query(query, (entity_type, entity_id), conn=conn)

    # Food Waste Records
    def log_waste_record(self, record: Dict[str, Any], conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            INSERT INTO food_waste_records (
                id, provider_name, date, meal_type, menu_items, portions_prepared,
                portions_consumed, edible_surplus, discarded_waste, cost_per_meal,
                financial_loss, notes, is_demo_seed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            record["id"], record["provider_name"], record["date"], record["meal_type"],
            record["menu_items"], record["portions_prepared"], record["portions_consumed"],
            record["edible_surplus"], record["discarded_waste"], record["cost_per_meal"],
            record["financial_loss"], record.get("notes", ""), record.get("is_demo_seed", 0),
            record["created_at"]
        )
        return self.execute_non_query(query, params, conn=conn)

    def list_waste_records(self, provider_name: Optional[str] = None, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        if provider_name:
            query = "SELECT * FROM food_waste_records WHERE provider_name = ? ORDER BY date DESC;"
            return self.execute_query(query, (provider_name,), conn=conn)
        query = "SELECT * FROM food_waste_records ORDER BY date DESC;"
        return self.execute_query(query, conn=conn)
