"""
Pickup request repository for AnnRakshak AI.
Encapsulates all SQL persistence for NGO surplus food rescue claims.
"""

import sqlite3
from typing import Optional, List, Dict, Any, Tuple
from .base import BaseRepository

class RequestRepository(BaseRepository):
    def get_by_id(self, request_id: str, conn: Optional[sqlite3.Connection] = None) -> Optional[Dict[str, Any]]:
        query = """
            SELECT r.id, r.donation_id, r.ngo_id, r.ngo_name, r.ngo_contact,
                   r.requested_portions, r.proposed_pickup_time, r.notes, r.status,
                   r.is_demo_seed, r.created_at, r.updated_at,
                   d.donor_id, d.donor_name, d.food_description, d.location,
                   d.available_portions, d.quantity_portions, d.status as donation_status,
                   d.private_contact as donor_private_contact
            FROM pickup_requests r
            JOIN donations d ON r.donation_id = d.id
            WHERE r.id = ?;
        """
        return self.execute_one(query, (request_id,), conn=conn)

    def list_all(self, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT r.id as request_id, r.donation_id, r.ngo_id, r.ngo_name,
                   r.requested_portions, r.proposed_pickup_time, r.notes as request_notes,
                   r.status as request_status, r.created_at as requested_at,
                   d.donor_id, d.donor_name, d.event_type, d.food_description, d.location,
                   d.status as donation_status
            FROM pickup_requests r
            JOIN donations d ON r.donation_id = d.id
            ORDER BY r.created_at DESC;
        """
        return self.execute_query(query, conn=conn)

    def list_by_donation_id(self, donation_id: str, conn: Optional[sqlite3.Connection] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT id, donation_id, ngo_id, ngo_name, ngo_contact, requested_portions,
                   proposed_pickup_time, notes, status, created_at, updated_at
            FROM pickup_requests
            WHERE donation_id = ?
            ORDER BY created_at ASC;
        """
        return self.execute_query(query, (donation_id,), conn=conn)

    def get_statuses_for_donation(self, donation_id: str, conn: Optional[sqlite3.Connection] = None) -> List[str]:
        query = """
            SELECT status FROM pickup_requests
            WHERE donation_id = ?;
        """
        rows = self.execute_query(query, (donation_id,), conn=conn)
        return [r["status"] for r in rows]

    def insert(self, req: Dict[str, Any], conn: Optional[sqlite3.Connection] = None) -> None:
        query = """
            INSERT INTO pickup_requests (
                id, donation_id, ngo_id, ngo_name, ngo_contact, requested_portions,
                proposed_pickup_time, notes, status, is_demo_seed, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        params = (
            req["id"], req["donation_id"], req["ngo_id"], req["ngo_name"], req["ngo_contact"],
            req["requested_portions"], req["proposed_pickup_time"], req.get("notes", ""),
            req.get("status", "Requested"), req.get("is_demo_seed", 0),
            req["created_at"], req["updated_at"]
        )
        self.execute_non_query(query, params, conn=conn)

    def update_status(self, request_id: str, new_status: str, updated_at: str, conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            UPDATE pickup_requests
            SET status = ?, updated_at = ?
            WHERE id = ?;
        """
        return self.execute_non_query(query, (new_status, updated_at, request_id), conn=conn)

    def expire_active_for_donation(self, donation_id: str, updated_at: str, conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            UPDATE pickup_requests
            SET status = 'Expired', updated_at = ?
            WHERE donation_id = ? AND status = 'Requested';
        """
        return self.execute_non_query(query, (updated_at, donation_id), conn=conn)

    def count_other_active(self, donation_id: str, exclude_request_id: str, conn: Optional[sqlite3.Connection] = None) -> int:
        query = """
            SELECT COUNT(*) as count FROM pickup_requests
            WHERE donation_id = ? AND id != ? AND status NOT IN ('Cancelled', 'Rejected', 'Delivered');
        """
        row = self.execute_one(query, (donation_id, exclude_request_id), conn=conn)
        return row["count"] if row else 0
