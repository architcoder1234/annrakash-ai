"""
Business Logic & Workflow Manager for AnnRakshak AI.
Implements canonical workflow statuses, partial pickup requests, portion release,
food safety windows, IST timezone awareness, BEGIN IMMEDIATE transactions,
backend user authorization checks, verified NGO gates, contact privacy unmasking,
CSV formula injection escaping, deterministic derived status transitions,
and repository pattern persistence decoupling SQL from business rules.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import uuid
import html
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from zoneinfo import ZoneInfo

from database import get_connection, _db_lock, get_ist_now, format_ist_str, IST
from repositories import DonationRepository, RequestRepository, OrganizationRepository
from notifications import emit_workflow_notification

donation_repo = DonationRepository()
request_repo = RequestRepository()
org_repo = OrganizationRepository()

# Environmental and Scientific Calculation Constants (UNEP / FAO Standard Assumptions)
PORTION_TO_KG = 0.35      # UNEP Food Waste Index: ~0.35 kg per cooked meal portion
KG_TO_CO2E = 2.5          # FAO / UNEP GHG benchmark: ~2.5 kg CO2e emissions avoided per kg surplus food rescued
KG_TO_WATER_L = 1000.0    # FAO Water Footprint benchmark: ~1000 liters embedded agricultural water saved per kg food

def calculate_impact_metrics(portions_delivered: int, avg_kg_per_portion: float = PORTION_TO_KG) -> Dict[str, float]:
    """Pure helper calculating factual impact metrics based on UNEP/FAO benchmark assumptions."""
    kg_saved = round(portions_delivered * avg_kg_per_portion, 2)
    co2_avoided_kg = round(kg_saved * KG_TO_CO2E, 2)
    water_saved_l = round(kg_saved * KG_TO_WATER_L, 1)
    return {
        "kg_saved": kg_saved,
        "co2_avoided_kg": co2_avoided_kg,
        "water_saved_l": water_saved_l,
        "meals_served": portions_delivered
    }

# Canonical Status Enum
class WorkflowStatus(str, Enum):
    AVAILABLE = "Available"
    REQUESTED = "Requested"
    CONFIRMED = "Confirmed"
    COLLECTED = "Collected"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"
    EXPIRED = "Expired"

    def __str__(self):
        return self.value

VALID_STATUSES = [s.value for s in WorkflowStatus]
VALID_DONATION_STATUSES = VALID_STATUSES
VALID_REQUEST_STATUSES = VALID_STATUSES

# Allowed state transitions for pickup requests
ALLOWED_REQUEST_TRANSITIONS = {
    WorkflowStatus.REQUESTED.value: [
        WorkflowStatus.CONFIRMED.value,
        WorkflowStatus.REJECTED.value,
        WorkflowStatus.CANCELLED.value,
        WorkflowStatus.EXPIRED.value
    ],
    WorkflowStatus.CONFIRMED.value: [
        WorkflowStatus.COLLECTED.value,
        WorkflowStatus.CANCELLED.value,
        WorkflowStatus.EXPIRED.value
    ],
    WorkflowStatus.COLLECTED.value: [
        WorkflowStatus.DELIVERED.value
    ],
    WorkflowStatus.DELIVERED.value: [],
    WorkflowStatus.REJECTED.value: [],
    WorkflowStatus.CANCELLED.value: [],
    WorkflowStatus.EXPIRED.value: []
}

def derive_donation_status(
    quantity_portions: int,
    available_portions: int,
    request_statuses: List[str],
    current_status: Optional[str] = None,
    is_expired: bool = False,
    is_cancelled: bool = False
) -> str:
    """
    Computes the canonical donation status derived from portion counts, active requests, and terminal conditions.
    Enforces monotonic progression (status never moves backwards):
    - Cancelled is terminal.
    - Expired is terminal (unless already collected/delivered before expiry).
    - If any request is Confirmed, status remains at least Confirmed; does not revert to Available on partial cancellation.
    - If all active portions are Delivered and 0 portions remaining -> Delivered.
    - If any request is Collected -> Collected.
    - If any request is Confirmed -> Confirmed.
    - If any request is Requested and available == 0 -> Requested.
    - If available > 0 and no requests are Confirmed/Collected/Delivered -> Available.
    - A donation must NEVER be Available with 0 portions unless fully delivered/cancelled/expired.
    """
    if is_cancelled or current_status == WorkflowStatus.CANCELLED.value:
        return WorkflowStatus.CANCELLED.value

    if current_status in (WorkflowStatus.DELIVERED.value, WorkflowStatus.COLLECTED.value):
        if is_expired:
            return current_status

    if is_expired or current_status == WorkflowStatus.EXPIRED.value:
        return WorkflowStatus.EXPIRED.value

    active_statuses = [
        s for s in request_statuses
        if s not in (WorkflowStatus.CANCELLED.value, WorkflowStatus.REJECTED.value, WorkflowStatus.EXPIRED.value)
    ]

    # Check if completely delivered
    if len(active_statuses) > 0 and all(s == WorkflowStatus.DELIVERED.value for s in active_statuses) and available_portions == 0:
        return WorkflowStatus.DELIVERED.value

    # Check collected (or partial delivery where other parts are collected/active)
    if any(s == WorkflowStatus.COLLECTED.value for s in active_statuses):
        return WorkflowStatus.COLLECTED.value
    if any(s == WorkflowStatus.DELIVERED.value for s in active_statuses):
        return WorkflowStatus.COLLECTED.value

    # Check confirmed: if any request is Confirmed, donation status stays Confirmed
    if any(s == WorkflowStatus.CONFIRMED.value for s in active_statuses):
        return WorkflowStatus.CONFIRMED.value

    # Monotonicity check: If current_status was Confirmed and there are still active requests, do not revert to Available
    if current_status == WorkflowStatus.CONFIRMED.value and len(active_statuses) > 0:
        return WorkflowStatus.CONFIRMED.value

    # Check requested: if all portions are requested
    if any(s == WorkflowStatus.REQUESTED.value for s in active_statuses):
        if available_portions == 0:
            return WorkflowStatus.REQUESTED.value
        return WorkflowStatus.AVAILABLE.value

    # Invariant: A donation must never be Available with 0 portions unless fully delivered/cancelled/expired
    if available_portions == 0:
        if any(s == WorkflowStatus.DELIVERED.value for s in request_statuses):
            return WorkflowStatus.DELIVERED.value
        return WorkflowStatus.EXPIRED.value

    return WorkflowStatus.AVAILABLE.value

def invariant_check(donation_id: str, conn: Optional[sqlite3.Connection] = None, return_details: bool = False) -> Any:
    """
    Validates portion conservation and status invariants for a donation:
    1. available + sum(active request portions) + delivered portions == quantity
       where active requests are in ('Requested', 'Confirmed', 'Collected').
    2. available_portions >= 0
    3. A donation must never have status 'Available' if available_portions == 0
       (unless fully delivered/cancelled/expired).
    """
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True
    try:
        cur = conn.cursor()
        cur.execute("SELECT quantity_portions, available_portions, status FROM donations WHERE id = ?;", (donation_id,))
        don = cur.fetchone()
        if not don:
            return (False, {"error": f"Donation {donation_id} not found"}) if return_details else False

        quantity = don["quantity_portions"]
        available = don["available_portions"]
        status = don["status"]

        cur.execute("""
            SELECT status, COALESCE(SUM(requested_portions), 0) as portions
            FROM pickup_requests
            WHERE donation_id = ?
            GROUP BY status;
        """, (donation_id,))
        rows = cur.fetchall()
        p_map = {r["status"]: r["portions"] for r in rows}

        active_sum = sum(p_map.get(s, 0) for s in (WorkflowStatus.REQUESTED.value, WorkflowStatus.CONFIRMED.value, WorkflowStatus.COLLECTED.value))
        delivered_sum = p_map.get(WorkflowStatus.DELIVERED.value, 0)

        total_accounted = available + active_sum + delivered_sum
        portions_ok = (total_accounted == quantity) and (available >= 0)

        if available == 0 and status == WorkflowStatus.AVAILABLE.value:
            status_ok = False
        else:
            status_ok = True

        valid = bool(portions_ok and status_ok)
        details = {
            "donation_id": donation_id,
            "quantity": quantity,
            "available": available,
            "active_sum": active_sum,
            "delivered_sum": delivered_sum,
            "total_accounted": total_accounted,
            "status": status,
            "portions_ok": portions_ok,
            "status_ok": status_ok,
            "valid": valid
        }
        return (valid, details) if return_details else valid
    finally:
        if close_conn:
            conn.close()

def mask_contact_max_2_digits(phone: str) -> str:
    """Masks contact number showing at most the last 2 digits."""
    if not phone or len(str(phone).strip()) < 2:
        return "[MASKED]"
    clean = str(phone).strip()
    digits = [c for c in clean if c.isdigit()]
    if len(digits) >= 2:
        last2 = "".join(digits[-2:])
        return f"+XX-XXXXX-XX{last2}"
    return "[MASKED]"

def sanitize_cell_for_csv(val: Any) -> Any:
    """Escapes strings starting with =, +, -, @, \\t, \\r to prevent CSV formula injection."""
    if isinstance(val, str) and len(val) > 0:
        if val[0] in ('=', '+', '-', '@', '\t', '\r'):
            return "'" + val
    return val

def sanitize_dataframe_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Returns a copy of the dataframe with all string columns sanitized for CSV export."""
    clean_df = df.copy()
    for col in clean_df.columns:
        clean_df[col] = clean_df[col].apply(sanitize_cell_for_csv)
    return clean_df

def export_dataframe_to_csv_string(df: pd.DataFrame) -> str:
    """Sanitizes and exports dataframe to CSV string, strictly stripping private contacts."""
    clean_df = sanitize_dataframe_for_csv(df)
    # Ensure no raw contact numbers leak into CSV exports
    for col in ["private_contact", "raw_donor_contact", "contact", "donor_contact", "ngo_contact"]:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].apply(lambda x: mask_contact_max_2_digits(str(x)) if pd.notna(x) else "[MASKED]")
    return clean_df.to_csv(index=False)

def check_and_expire_donations() -> int:
    """
    Checks active listings past their pickup deadline and auto-marks them as Expired.
    Atomically updates both donations and unconfirmed requests under BEGIN IMMEDIATE,
    releasing reserved portions back to available pool to maintain portion conservation.
    """
    now_ist_str = format_ist_str(get_ist_now())
    expired_count = 0

    with donation_repo.transaction() as conn:
        expired_dons = donation_repo.get_expired_candidates(now_ist_str, conn=conn)
        for don in expired_dons:
            don_id = don["id"]
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(requested_portions), 0) as released
                FROM pickup_requests
                WHERE donation_id = ? AND status IN ('Requested', 'Confirmed');
            """, (don_id,))
            released = cursor.fetchone()["released"]
            new_avail = don["available_portions"] + released

            # Expire active requests
            cursor.execute("""
                UPDATE pickup_requests
                SET status = 'Expired', updated_at = ?
                WHERE donation_id = ? AND status IN ('Requested', 'Confirmed');
            """, (now_ist_str, don_id))

            # Re-derive donation status
            all_req_statuses = request_repo.get_statuses_for_donation(don_id, conn=conn)
            new_don_status = derive_donation_status(
                quantity_portions=don["quantity_portions"],
                available_portions=new_avail,
                request_statuses=all_req_statuses,
                current_status=don["status"],
                is_expired=True
            )

            donation_repo.update_portions_and_status(don_id, new_avail, new_don_status, now_ist_str, conn=conn)

            org_repo.record_status_change(
                "donation", don_id, don["status"], new_don_status,
                "System Auto-Expiry", now_ist_str, "Pickup deadline elapsed", conn=conn
            )
            expired_count += 1

    return expired_count

def is_ngo_verified(ngo_id_or_name: str) -> bool:
    """Checks if an NGO has verified standing by ID or exact name."""
    return org_repo.is_ngo_verified(ngo_id_or_name)

def get_ngos_df() -> pd.DataFrame:
    """Returns all registered NGOs without leaking raw private phones."""
    rows = org_repo.list_ngos()
    return pd.DataFrame(rows)

def approve_ngo(
    acting_user: Optional[Dict[str, Any]] = None,
    ngo_id: Optional[str] = None,
    admin_name: str = "System Admin"
) -> Tuple[bool, str]:
    """Backend authorization check: only active System Administrators can verify NGOs."""
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True):
        return False, "Unauthorized: Valid active acting_user is required."

    if acting_user.get("role") != "admin":
        return False, "Unauthorized: Only system administrators can verify NGOs."

    if not ngo_id:
        return False, "NGO ID is required."

    resolved_admin = acting_user.get("username", admin_name)

    try:
        with org_repo.transaction() as conn:
            org_repo.approve_ngo(ngo_id, resolved_admin, conn=conn)
        return True, f"NGO {ngo_id} successfully verified by {resolved_admin}."
    except Exception as e:
        return False, f"Failed to approve NGO: {str(e)}"

def create_donation(
    acting_user: Optional[Dict[str, Any]] = None,
    donor_name: Optional[str] = None,
    event_type: str = "Other",
    food_description: str = "",
    quantity_portions: int = 0,
    prep_datetime: str = "",
    available_from: str = "",
    pickup_deadline: str = "",
    storage_info: str = "",
    location: str = "",
    private_contact: str = "",
    notes: str = "",
    food_safety_window_hours: float = 6.0,
    donor_id: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Creates a new food donation listing with closed-fail food safety checks.
    Strict backend authorization: acting_user must be an active donor or admin.
    """
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True):
        return False, "Unauthorized: Valid active acting_user is required.", None

    if acting_user.get("role") not in ("donor", "admin"):
        return False, "Unauthorized: Only authenticated food donors can publish donation listings.", None

    if acting_user.get("role") == "donor":
        donor_id = acting_user.get("org_id")
        if not donor_id:
            return False, "Unauthorized: Donor user has no associated organization.", None
    else:  # admin
        donor_id = donor_id or acting_user.get("org_id")
        if not donor_id:
            return False, "Donor ID is required when admin creates a donation.", None

    if not food_description or not food_description.strip():
        return False, "Food items and description are required.", None
    if quantity_portions <= 0:
        return False, "Donation quantity must be greater than 0 meal portions.", None
    if not location or not location.strip():
        return False, "Pickup location is required.", None
    if not private_contact or not private_contact.strip():
        return False, "Private contact details are required for coordination.", None

    now_ist = get_ist_now()
    now_ist_str = format_ist_str(now_ist)

    # Food safety: "closed-fail" validation check
    if not prep_datetime or not str(prep_datetime).strip():
        return False, "Food safety violation: Preparation datetime is required.", None

    try:
        prep_clean = str(prep_datetime).replace("T", " ")[:19].strip()
        prep_dt = datetime.strptime(prep_clean, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
    except (ValueError, TypeError):
        return False, f"Food safety violation: Unparseable preparation datetime '{prep_datetime}'. Format must be YYYY-MM-DD HH:MM:SS.", None

    if prep_dt > (now_ist + timedelta(minutes=5)):
        return False, "Food safety violation: Preparation datetime cannot be in the future.", None

    try:
        window_hours = float(food_safety_window_hours)
    except (ValueError, TypeError):
        window_hours = 6.0
    window_hours = max(2.0, min(8.0, window_hours))

    hours_since_prep = (now_ist - prep_dt).total_seconds() / 3600.0
    if hours_since_prep > window_hours:
        return False, (
            f"Food Safety Policy Violation: Food was prepared {hours_since_prep:.1f} hours ago, "
            f"which exceeds the safety threshold ({window_hours:.1f} hours). Cannot list expired food."
        ), None

    donation_id = f"DON-{now_ist.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        with donation_repo.transaction() as conn:
            d_row = org_repo.get_donor_by_id(donor_id, conn=conn)
            if not d_row:
                return False, f"Donor organization '{donor_id}' not found.", None
            resolved_donor_name = d_row["name"]
            d_lat = d_row["lat"]
            d_lng = d_row["lng"]

            don_dict = {
                "id": donation_id,
                "donor_id": donor_id,
                "donor_name": resolved_donor_name,
                "event_type": event_type,
                "food_description": food_description.strip(),
                "quantity_portions": quantity_portions,
                "available_portions": quantity_portions,
                "prep_datetime": prep_datetime,
                "available_from": available_from,
                "pickup_deadline": pickup_deadline,
                "storage_info": storage_info.strip(),
                "location": location.strip(),
                "lat": d_lat,
                "lng": d_lng,
                "private_contact": private_contact.strip(),
                "notes": notes.strip() if notes else "",
                "status": WorkflowStatus.AVAILABLE.value,
                "food_safety_window_hours": window_hours,
                "is_demo_seed": 0,
                "created_at": now_ist_str,
                "updated_at": now_ist_str
            }
            donation_repo.insert(don_dict, conn=conn)

            changed_by_name = acting_user.get("username", resolved_donor_name)
            org_repo.record_status_change(
                "donation", donation_id, None, WorkflowStatus.AVAILABLE.value,
                changed_by_name, now_ist_str, "Listing published", conn=conn
            )

        try:
            emit_workflow_notification(
                "donation_created",
                donation_id=donation_id,
                donor_id=donor_id,
                portions=quantity_portions,
                food_name=food_description.strip()
            )
        except Exception:
            pass

        return True, f"Donation listing {donation_id} created successfully!", donation_id
    except Exception as e:
        return False, f"Database error creating donation: {str(e)}", None

def request_pickup(
    acting_user: Optional[Dict[str, Any]] = None,
    donation_id: Optional[str] = None,
    requested_portions: int = 0,
    proposed_pickup_time: str = "",
    notes: str = "",
    ngo_contact: Optional[str] = None,
    ngo_id: Optional[str] = None,
    ngo_name: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    Submits an NGO pickup request with atomic portion reservation under BEGIN IMMEDIATE.
    Backend Authorization: Checks active acting user is NGO/Admin and verifies NGO verification status.
    """
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True):
        return False, "Unauthorized: Valid active acting_user is required.", None

    if acting_user.get("role") not in ("ngo", "admin"):
        return False, "Unauthorized: Only authenticated NGO recovery personnel can request pickups.", None

    if acting_user.get("role") == "ngo":
        ngo_id = acting_user.get("org_id")
        if not ngo_id:
            return False, "Unauthorized: NGO user has no associated organization.", None
    else:  # admin
        ngo_id = ngo_id or acting_user.get("org_id")
        if not ngo_id:
            return False, "NGO ID is required when admin creates a pickup request.", None

    # Strict NGO Verification Check inside backend logic
    if not is_ngo_verified(ngo_id):
        return False, "Permission denied: System Admin verification is required before placing food recovery requests.", None

    if not donation_id:
        return False, "Donation ID is required.", None

    if requested_portions <= 0:
        return False, "Requested portions must be greater than 0.", None

    now_ist = get_ist_now()
    now_ist_str = format_ist_str(now_ist)
    request_id = f"REQ-{now_ist.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        with donation_repo.transaction() as conn:
            ngo_row = org_repo.get_ngo_by_id(ngo_id, conn=conn)
            if not ngo_row:
                return False, f"NGO organization '{ngo_id}' not found.", None
            resolved_ngo_name = ngo_row["name"]
            resolved_ngo_contact = ngo_contact or ngo_row["contact"] or "Verified App Channel"

            don = donation_repo.get_by_id(donation_id, conn=conn)
            if not don:
                return False, f"Donation {donation_id} not found.", None

            if don["status"] == WorkflowStatus.EXPIRED.value or don["pickup_deadline"] < now_ist_str:
                return False, f"Donation {donation_id} has expired and cannot accept requests.", None

            if don["status"] in (WorkflowStatus.CANCELLED.value, WorkflowStatus.DELIVERED.value):
                return False, f"Donation {donation_id} is in '{don['status']}' state and cannot accept requests.", None

            if don["available_portions"] < requested_portions:
                return False, f"Insufficient available portions ({don['available_portions']} left, requested {requested_portions}).", None

            new_avail = don["available_portions"] - requested_portions

            req_dict = {
                "id": request_id,
                "donation_id": donation_id,
                "ngo_id": ngo_id,
                "ngo_name": resolved_ngo_name,
                "ngo_contact": resolved_ngo_contact,
                "requested_portions": requested_portions,
                "proposed_pickup_time": proposed_pickup_time,
                "notes": notes.strip() if notes else "",
                "status": WorkflowStatus.REQUESTED.value,
                "is_demo_seed": 0,
                "created_at": now_ist_str,
                "updated_at": now_ist_str
            }
            request_repo.insert(req_dict, conn=conn)

            # Derive new donation status
            all_req_statuses = request_repo.get_statuses_for_donation(donation_id, conn=conn)
            new_don_status = derive_donation_status(
                quantity_portions=don["quantity_portions"],
                available_portions=new_avail,
                request_statuses=all_req_statuses,
                current_status=don["status"]
            )

            donation_repo.update_portions_and_status(donation_id, new_avail, new_don_status, now_ist_str, conn=conn)

            changed_by = acting_user.get("username", resolved_ngo_name)
            org_repo.record_status_change(
                "request", request_id, None, WorkflowStatus.REQUESTED.value,
                changed_by, now_ist_str, "Pickup requested by verified NGO", conn=conn
            )

        try:
            emit_workflow_notification(
                "request_submitted",
                donation_id=donation_id,
                request_id=request_id,
                donor_id=don["donor_id"],
                ngo_id=ngo_id,
                portions=requested_portions,
                food_name=don["food_description"],
                donor_name=don["donor_name"],
                ngo_name=resolved_ngo_name
            )
        except Exception:
            pass

        return True, f"Pickup request {request_id} submitted successfully! Awaiting donor confirmation.", request_id
    except Exception as e:
        return False, f"Failed to submit pickup request: {str(e)}", None

def update_request_status(
    request_id: Optional[str] = None,
    new_status: Optional[str] = None,
    acting_user: Optional[Dict[str, Any]] = None,
    remarks: str = "",
    changed_by: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Updates request status and manages atomic portion releases on Reject/Cancel/Expire under BEGIN IMMEDIATE.
    Backend Authorization:
    - Only the linked donation owner (or admin) can Confirm or Reject.
    - Only the linked requesting NGO (or admin) can mark Collected or Delivered.
    - Only the linked donation owner, requesting NGO, or admin can Cancel.
    - Only the linked donation owner or admin can mark Expired.
    - Portion release logic releases reserved portions on Reject, Cancel, or Expire,
      and re-derives canonical donation status through derive_donation_status.
    """
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True):
        return False, "Unauthorized: Valid active acting_user is required."

    if not request_id or not new_status:
        return False, "Request ID and target status are required."

    if new_status not in VALID_REQUEST_STATUSES:
        return False, f"Invalid request status: {new_status}"

    now_ist_str = format_ist_str(get_ist_now())

    try:
        with request_repo.transaction() as conn:
            row = request_repo.get_by_id(request_id, conn=conn)
            if not row:
                return False, f"Request {request_id} not found."

            user_role = acting_user.get("role")
            user_org = acting_user.get("org_id")

            if new_status in (WorkflowStatus.CONFIRMED.value, WorkflowStatus.REJECTED.value):
                if user_role != "admin" and (user_role != "donor" or not user_org or user_org != row["donor_id"]):
                    return False, "Unauthorized: Only the food donor who published this listing can confirm or reject pickup requests."

            elif new_status in (WorkflowStatus.COLLECTED.value, WorkflowStatus.DELIVERED.value):
                if user_role != "admin" and (user_role != "ngo" or not user_org or user_org != row["ngo_id"]):
                    return False, "Unauthorized: Only the assigned requesting NGO can update collection and delivery milestones."

            elif new_status == WorkflowStatus.CANCELLED.value:
                can_cancel = (user_role == "admin") or (user_org and user_org in (row["donor_id"], row["ngo_id"]))
                if not can_cancel:
                    return False, "Unauthorized: You do not have permission to cancel this pickup request."

            elif new_status == WorkflowStatus.EXPIRED.value:
                can_expire = (user_role == "admin") or (user_role == "donor" and user_org == row["donor_id"])
                if not can_expire:
                    return False, "Unauthorized: Only administrators or the listing owner can mark requests expired."

            current_status = row["status"]
            allowed = ALLOWED_REQUEST_TRANSITIONS.get(current_status, [])
            if new_status not in allowed:
                return False, f"Invalid status transition from '{current_status}' to '{new_status}'."

            donation_id = row["donation_id"]
            req_portions = row["requested_portions"]
            cur_avail = row["available_portions"]
            don_status = row["donation_status"]

            # Update the pickup request status
            request_repo.update_status(request_id, new_status, now_ist_str, conn=conn)

            # Portion release logic: If Rejected, Cancelled, or Expired, release reserved portions back to available
            if new_status in (WorkflowStatus.REJECTED.value, WorkflowStatus.CANCELLED.value, WorkflowStatus.EXPIRED.value):
                restored_avail = cur_avail + req_portions
            else:
                restored_avail = cur_avail

            # Check if donation is expired past deadline or marked Expired
            don_detail = donation_repo.get_by_id(donation_id, conn=conn)
            is_don_expired = (
                don_status == WorkflowStatus.EXPIRED.value or
                (don_detail and don_detail["pickup_deadline"] < now_ist_str)
            )

            # Fetch all request statuses for this donation
            all_req_statuses = request_repo.get_statuses_for_donation(donation_id, conn=conn)

            # Derive canonical donation status deterministically
            new_don_status = derive_donation_status(
                quantity_portions=row["quantity_portions"],
                available_portions=restored_avail,
                request_statuses=all_req_statuses,
                current_status=don_status,
                is_expired=is_don_expired
            )

            donation_repo.update_portions_and_status(donation_id, restored_avail, new_don_status, now_ist_str, conn=conn)

            actor = changed_by or acting_user.get("username", "User")
            org_repo.record_status_change(
                "request", request_id, current_status, new_status,
                actor, now_ist_str, remarks, conn=conn
            )

        try:
            emit_workflow_notification(
                f"request_{new_status.lower()}",
                donation_id=donation_id,
                request_id=request_id,
                donor_id=row["donor_id"],
                ngo_id=row["ngo_id"],
                portions=req_portions,
                food_name=row["food_description"],
                donor_name=row["donor_name"],
                ngo_name=row["ngo_name"]
            )
        except Exception:
            pass

        return True, f"Request {request_id} updated to '{new_status}'."
    except Exception as e:
        return False, f"Status update failed: {str(e)}"

def cancel_donation(
    donation_id: Optional[str] = None,
    acting_user: Optional[Dict[str, Any]] = None,
    reason: str = "",
    donor_name: Optional[str] = None
) -> Tuple[bool, str]:
    """Allows donor owner (or admin) to cancel an active donation listing."""
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True):
        return False, "Unauthorized: Valid active acting_user is required."

    if not donation_id:
        return False, "Donation ID is required."

    now_ist_str = format_ist_str(get_ist_now())

    try:
        with donation_repo.transaction() as conn:
            row = donation_repo.get_by_id(donation_id, conn=conn)
            if not row:
                return False, f"Donation {donation_id} not found."

            if acting_user.get("role") != "admin" and acting_user.get("org_id") != row["donor_id"]:
                return False, "Unauthorized: You can only cancel your own donation listings."

            if row["status"] in (WorkflowStatus.COLLECTED.value, WorkflowStatus.DELIVERED.value):
                return False, f"Cannot cancel donation in '{row['status']}' state."

            cursor = conn.cursor()
            cursor.execute("""
                SELECT COALESCE(SUM(requested_portions), 0) as released
                FROM pickup_requests
                WHERE donation_id = ? AND status IN ('Requested', 'Confirmed');
            """, (donation_id,))
            released = cursor.fetchone()["released"]
            new_avail = row["available_portions"] + released

            cursor.execute("""
                UPDATE pickup_requests SET status = 'Cancelled', updated_at = ?
                WHERE donation_id = ? AND status IN ('Requested', 'Confirmed');
            """, (now_ist_str, donation_id))

            donation_repo.update_portions_and_status(donation_id, new_avail, WorkflowStatus.CANCELLED.value, now_ist_str, conn=conn)

            actor = acting_user.get("username", donor_name or "Donor")
            org_repo.record_status_change(
                "donation", donation_id, row["status"], WorkflowStatus.CANCELLED.value,
                actor, now_ist_str, f"Cancelled by donor: {reason}", conn=conn
            )

        return True, f"Donation {donation_id} cancelled."
    except Exception as e:
        return False, f"Cancellation failed: {str(e)}"

def get_contact_for(
    request_id: Optional[str] = None,
    acting_user: Optional[Dict[str, Any]] = None
) -> str:
    """
    Strict contact privacy unmasking:
    - Never unmasks to unauthenticated or inactive viewers.
    - Full contact revealed ONLY to:
      1. The listing's donor owner.
      2. The requesting NGO once the request is Confirmed, Collected, or Delivered.
      3. System Administrator.
    - In all other cases, masks phone with at most the last 2 digits visible.
    - No substring matching or None bypass.
    """
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True) or not request_id:
        return "[MASKED]"

    row = request_repo.get_by_id(request_id)
    if not row:
        return "[NOT FOUND]"

    raw_contact = row["donor_private_contact"]
    u_role = acting_user.get("role")
    u_org = acting_user.get("org_id")

    # 1. Admin
    if u_role == "admin":
        return raw_contact

    # 2. Donor owner
    if u_role == "donor" and u_org and u_org == row["donor_id"]:
        return raw_contact

    # 3. Requesting NGO once Confirmed/Collected/Delivered
    if u_role == "ngo" and u_org and u_org == row["ngo_id"]:
        if row["status"] in ("Confirmed", "Collected", "Delivered"):
            return raw_contact

    # Fallback masked
    return mask_contact_max_2_digits(raw_contact)

def get_donations_df() -> pd.DataFrame:
    """Fetch donations DataFrame. Strictly NEVER selects private contact into DataFrame!"""
    rows = donation_repo.list_all()
    return pd.DataFrame(rows)

def get_pickup_requests_df() -> pd.DataFrame:
    """Fetch pickup requests DataFrame. Strictly NEVER selects raw private contact into DataFrame!"""
    rows = request_repo.list_all()
    return pd.DataFrame(rows)

def get_food_waste_df() -> pd.DataFrame:
    """Fetch food waste records as a pandas DataFrame."""
    rows = org_repo.list_waste_records()
    return pd.DataFrame(rows)

def log_food_waste(
    acting_user: Optional[Dict[str, Any]] = None,
    provider_name: str = "",
    date: str = "",
    meal_type: str = "",
    menu_items: str = "",
    portions_prepared: int = 0,
    portions_consumed: int = 0,
    edible_surplus: int = 0,
    discarded_waste: int = 0,
    cost_per_meal: float = 0.0,
    notes: str = ""
) -> Tuple[bool, str, Optional[str]]:
    """Logs kitchen food waste with mass-balance validation."""
    if not acting_user or not isinstance(acting_user, dict) or not acting_user.get("is_active", True):
        return False, "Unauthorized: Valid active acting_user is required.", None

    if acting_user.get("role") not in ("donor", "admin"):
        return False, "Unauthorized: Only food donors and admins can record kitchen waste audits.", None

    if not provider_name or not provider_name.strip():
        return False, "Provider or event name is required.", None
    if not menu_items or not menu_items.strip():
        return False, "Menu items are required.", None
    if portions_prepared <= 0:
        return False, "Portions prepared must be greater than 0.", None
    if portions_consumed < 0:
        return False, "Portions consumed cannot be negative.", None
    if edible_surplus < 0 or discarded_waste < 0:
        return False, "Surplus and discarded waste quantities cannot be negative.", None
    if cost_per_meal < 0:
        return False, "Cost per meal cannot be negative.", None

    if portions_consumed > portions_prepared:
        return False, f"Inconsistent quantities: Consumed ({portions_consumed}) exceeds prepared ({portions_prepared}). Please correct.", None

    total_leftover = portions_prepared - portions_consumed
    recorded_breakdown = edible_surplus + discarded_waste

    if recorded_breakdown > total_leftover:
        return False, (
            f"Quantity mismatch: Edible surplus ({edible_surplus}) + Discarded waste ({discarded_waste}) = {recorded_breakdown}, "
            f"which exceeds total unconsumed leftovers ({total_leftover} = {portions_prepared} prepared - {portions_consumed} consumed)."
        ), None

    financial_loss = discarded_waste * cost_per_meal
    now_ist = get_ist_now()
    now_ist_str = format_ist_str(now_ist)
    waste_id = f"WST-{now_ist.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    try:
        waste_record = {
            "id": waste_id,
            "provider_name": provider_name.strip(),
            "date": date,
            "meal_type": meal_type,
            "menu_items": menu_items.strip(),
            "portions_prepared": portions_prepared,
            "portions_consumed": portions_consumed,
            "edible_surplus": edible_surplus,
            "discarded_waste": discarded_waste,
            "cost_per_meal": cost_per_meal,
            "financial_loss": financial_loss,
            "notes": notes.strip() if notes else "",
            "is_demo_seed": 0,
            "created_at": now_ist_str
        }
        with org_repo.transaction() as conn:
            org_repo.log_waste_record(waste_record, conn=conn)

        return True, f"Food waste record {waste_id} saved successfully! Measured direct loss: ₹{financial_loss:,.2f}.", waste_id
    except Exception as e:
        return False, f"Failed to record waste: {str(e)}", None

def get_impact_summary(avg_kg_per_portion: float = 0.35) -> Dict[str, Any]:
    """Calculates factual aggregate impact metrics strictly from recorded database values."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(quantity_portions), 0) FROM donations;")
        don_count, total_portions_offered = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM donations WHERE status = 'Delivered';")
        completed_donations = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(requested_portions), 0) FROM pickup_requests WHERE status IN ('Collected', 'Delivered');")
        portions_collected = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(requested_portions), 0) FROM pickup_requests WHERE status = 'Delivered';")
        portions_delivered = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pickup_requests;")
        total_requests = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pickup_requests WHERE status IN ('Confirmed', 'Collected', 'Delivered');")
        requests_confirmed = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pickup_requests WHERE status = 'Requested';")
        requests_pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*), COALESCE(SUM(discarded_waste), 0), COALESCE(SUM(financial_loss), 0), COALESCE(SUM(edible_surplus), 0) FROM food_waste_records;")
        waste_records_count, total_discarded, total_financial_loss, total_edible_surplus = cursor.fetchone()

        kg_food_saved = round(portions_delivered * avg_kg_per_portion, 2)
        co2_avoided_kg = round(kg_food_saved * 2.5, 2)
        water_saved_liters = round(kg_food_saved * 1000.0, 1)
        meals_served = portions_delivered

        return {
            "donations_listed": don_count,
            "portions_offered": total_portions_offered,
            "portions_collected": portions_collected,
            "portions_delivered": portions_delivered,
            "completed_donations": completed_donations,
            "total_requests": total_requests,
            "requests_confirmed": requests_confirmed,
            "requests_pending": requests_pending,
            "waste_records_count": waste_records_count,
            "total_discarded_portions": total_discarded,
            "total_financial_loss": total_financial_loss,
            "total_edible_surplus": total_edible_surplus,
            "kg_food_saved": kg_food_saved,
            "co2_avoided_kg": co2_avoided_kg,
            "water_saved_liters": water_saved_liters,
            "meals_served": meals_served,
            "avg_kg_per_portion": avg_kg_per_portion
        }
    finally:
        conn.close()

def get_status_history_df(entity_id: Optional[str] = None) -> pd.DataFrame:
    """Fetch immutable status history audit log."""
    conn = get_connection()
    try:
        if entity_id:
            query = "SELECT * FROM status_history WHERE entity_id = ? ORDER BY timestamp DESC;"
            df = pd.read_sql_query(query, conn, params=(entity_id,))
        else:
            query = "SELECT * FROM status_history ORDER BY timestamp DESC;"
            df = pd.read_sql_query(query, conn)
        return df
    finally:
        conn.close()
