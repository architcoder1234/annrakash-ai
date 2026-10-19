"""
Donation repository for AnnRakshak AI.
Encapsulates all SQL persistence for food donation listings.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from .base import BaseRepository

class DonationRepository(BaseRepository):
    def get_by_id(self, donation_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = """
            SELECT id, donor_id, donor_name, event_type, food_description,
                   quantity_portions, available_portions, prep_datetime, available_from,
                   pickup_deadline, storage_info, location, lat, lng, private_contact,
                   notes, status, food_safety_window_hours, is_demo_seed, created_at, updated_at
            FROM donations
            WHERE id = ?;
        """
        return self.execute_one(query, (donation_id,), conn=conn)

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT id, donor_id, donor_name, event_type, food_description,
                   quantity_portions, available_portions, prep_datetime, available_from,
                   pickup_deadline, storage_info, location, lat, lng, notes, status,
                   food_safety_window_hours, created_at, updated_at
            FROM donations
            ORDER BY created_at DESC;
        """
        return self.execute_query(query, conn=conn)

    def get_expired_candidates(self, now_str: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT id, status, quantity_portions, available_portions, pickup_deadline
            FROM donations
            WHERE status IN ('Available', 'Requested') AND pickup_deadline < ?;
        """
        return self.execute_query(query, (now_str,), conn=conn)

    def insert(self, don: Dict[str, Any], conn: Optional[sqlite3.Connection] = None) -> None:
        query = """
            INSERT INTO donations (
                id, donor_id, donor_name, event_type, food_description, quantity_portions,
                available_portions, prep_datetime, available_from, pickup_deadline,
                storage_info, location, lat, lng, private_contact, notes, status, food_safety_window_hours,
                is_demo_seed, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            don["id"], don["donor_id"], don["donor_name"], don["event_type"], don["food_description"],
            don["quantity_portions"], don["available_portions"], don["prep_datetime"], don["available_from"],
            don["pickup_deadline"], don["storage_info"], don["location"], don.get("lat", 25.4520), don.get("lng", 81.8340),
            don["private_contact"], don.get("notes", ""), don.get("status", "Available"),
            don.get("food_safety_window_hours", 6.0), don.get("is_demo_seed", 0),
            don["created_at"], don["updated_at"]
        )
        self.execute_non_query(query, params, conn=conn)

    def update_portions_and_status(self, donation_id: str, available_portions: int, status: str, updated_at: str, conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            UPDATE donations
            SET available_portions = ?, status = ?, updated_at = ?
            WHERE id = ?;
        """
        return self.execute_non_query(query, (available_portions, status, updated_at, donation_id), conn=conn)

    def update_status(self, donation_id: str, status: str, updated_at: str, conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            UPDATE donations
            SET status = ?, updated_at = ?
            WHERE id = ?;
        """
        return self.execute_non_query(query, (status, updated_at, donation_id), conn=conn)
