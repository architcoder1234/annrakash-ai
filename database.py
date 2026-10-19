"""
Database management module for AnnRakshak AI.
Uses SQLite for lightweight, transactional persistent storage with foreign keys enabled.
Supports WAL mode, busy_timeout, explicit IMMEDIATE transactions, IST timezone,
and relational integrity with donors, ngos, and users tables.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import threading
import uuid
from zoneinfo import ZoneInfo
from typing import Optional, List, Dict, Any, Tuple
import bcrypt

IST = ZoneInfo("Asia/Kolkata")

def get_ist_now() -> datetime:
    """Returns current datetime in IST (Asia/Kolkata)."""
    return datetime.now(IST)

def format_ist_str(dt: datetime) -> str:
    """Formats datetime to standard ISO-like string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")

__all__ = [
    "init_db",
    "get_connection",
    "get_ist_now",
    "format_ist_str",
    "run_migrations",
    "get_db_version",
    "set_db_version",
    "IST",
    "DB_FILE",
    "_db_lock"
]

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "annrakshak.db")
_db_lock = threading.Lock()

def get_connection(db_path=None):
    """
    Return a connection with WAL mode, busy_timeout, foreign keys enabled,
    and isolation_level=None to support explicit BEGIN IMMEDIATE transactions.
    """
    target = db_path or os.environ.get("ANNRAKSHAK_DB_PATH") or DB_FILE
    conn = sqlite3.connect(target, timeout=30.0, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "migrations")

def get_db_version(conn: sqlite3.Connection) -> int:
    """Read the current schema version from PRAGMA user_version."""
    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version;")
    row = cursor.fetchone()
    return int(row[0]) if row else 0

def set_db_version(conn: sqlite3.Connection, version: int) -> None:
    """Set the schema version in PRAGMA user_version."""
    conn.execute(f"PRAGMA user_version = {int(version)};")

def run_migrations(conn: Optional[sqlite3.Connection] = None, db_path: Optional[str] = None) -> int:
    """
    Executes pending SQL migrations idempotently based on PRAGMA user_version.
    Returns the schema version after running migrations.
    """
    should_close = False
    if conn is None:
        conn = get_connection(db_path=db_path)
        should_close = True

    try:
        current_version = get_db_version(conn)

        # Migration 1: 001_initial_schema.sql
        if current_version < 1:
            m1_path = os.path.join(MIGRATIONS_DIR, "001_initial_schema.sql")
            if os.path.exists(m1_path):
                with open(m1_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            
            # Ensure backwards compatibility for legacy databases
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(donations);")
            don_cols = [r[1] for r in cursor.fetchall()]
            if don_cols:
                if "donor_id" not in don_cols:
                    cursor.execute("ALTER TABLE donations ADD COLUMN donor_id TEXT DEFAULT 'DONOR-001';")
                if "lat" not in don_cols:
                    cursor.execute("ALTER TABLE donations ADD COLUMN lat REAL DEFAULT 25.4358;")
                if "lng" not in don_cols:
                    cursor.execute("ALTER TABLE donations ADD COLUMN lng REAL DEFAULT 81.8463;")
                if "food_safety_window_hours" not in don_cols:
                    cursor.execute("ALTER TABLE donations ADD COLUMN food_safety_window_hours REAL DEFAULT 6.0;")

            cursor.execute("PRAGMA table_info(pickup_requests);")
            req_cols = [r[1] for r in cursor.fetchall()]
            if req_cols:
                if "ngo_id" not in req_cols:
                    cursor.execute("ALTER TABLE pickup_requests ADD COLUMN ngo_id TEXT DEFAULT 'NGO-001';")

            set_db_version(conn, 1)
            current_version = 1

        # Migration 2: 002_add_indexes.sql
        if current_version < 2:
            m2_path = os.path.join(MIGRATIONS_DIR, "002_add_indexes.sql")
            if os.path.exists(m2_path):
                with open(m2_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            set_db_version(conn, 2)
            current_version = 2

        # Migration 3: 003_notifications.sql
        if current_version < 3:
            m3_path = os.path.join(MIGRATIONS_DIR, "003_notifications.sql")
            if os.path.exists(m3_path):
                with open(m3_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            set_db_version(conn, 3)
            current_version = 3

        # Migration 4: 004_security_hardening.sql
        if current_version < 4:
            m4_path = os.path.join(MIGRATIONS_DIR, "004_security_hardening.sql")
            if os.path.exists(m4_path):
                with open(m4_path, "r", encoding="utf-8") as f:
                    conn.executescript(f.read())
            set_db_version(conn, 4)
            current_version = 4

        return current_version
    finally:
        if should_close:
            conn.close()

def ensure_schema_compatibility(cursor):
    """Ensures legacy SQLite databases have all required columns across all tables."""
    # 1. Donations
    cursor.execute("PRAGMA table_info(donations);")
    don_cols = [r[1] for r in cursor.fetchall()]
    if don_cols:
        if "donor_id" not in don_cols:
            cursor.execute("ALTER TABLE donations ADD COLUMN donor_id TEXT DEFAULT 'DONOR-001';")
        if "lat" not in don_cols:
            cursor.execute("ALTER TABLE donations ADD COLUMN lat REAL DEFAULT 25.4358;")
        if "lng" not in don_cols:
            cursor.execute("ALTER TABLE donations ADD COLUMN lng REAL DEFAULT 81.8463;")
        if "food_safety_window_hours" not in don_cols:
            cursor.execute("ALTER TABLE donations ADD COLUMN food_safety_window_hours REAL DEFAULT 6.0;")

    # 2. Pickup Requests
    cursor.execute("PRAGMA table_info(pickup_requests);")
    req_cols = [r[1] for r in cursor.fetchall()]
    if req_cols:
        if "ngo_id" not in req_cols:
            cursor.execute("ALTER TABLE pickup_requests ADD COLUMN ngo_id TEXT DEFAULT 'NGO-001';")

    # 3. NGOs
    cursor.execute("PRAGMA table_info(ngos);")
    ngo_cols = [r[1] for r in cursor.fetchall()]
    if ngo_cols:
        if "location" not in ngo_cols:
            cursor.execute("ALTER TABLE ngos ADD COLUMN location TEXT DEFAULT 'Naini Shelter Cluster, Prayagraj';")
        if "lat" not in ngo_cols:
            cursor.execute("ALTER TABLE ngos ADD COLUMN lat REAL DEFAULT 25.4080;")
        if "lng" not in ngo_cols:
            cursor.execute("ALTER TABLE ngos ADD COLUMN lng REAL DEFAULT 81.8680;")
        if "capacity_portions" not in ngo_cols:
            cursor.execute("ALTER TABLE ngos ADD COLUMN capacity_portions INTEGER DEFAULT 100;")

    # 4. Donors
    cursor.execute("PRAGMA table_info(donors);")
    donor_cols = [r[1] for r in cursor.fetchall()]
    if donor_cols:
        if "location" not in donor_cols:
            cursor.execute("ALTER TABLE donors ADD COLUMN location TEXT DEFAULT 'Prayagraj';")
        if "lat" not in donor_cols:
            cursor.execute("ALTER TABLE donors ADD COLUMN lat REAL DEFAULT 25.4520;")
        if "lng" not in donor_cols:
            cursor.execute("ALTER TABLE donors ADD COLUMN lng REAL DEFAULT 81.8340;")

def init_db(force_reset=False, db_path=None):
    """Initialize database tables via idempotent migrations and seed fictional demo data non-destructively."""
    with _db_lock:
        conn = get_connection(db_path=db_path)
        cursor = conn.cursor()

        if force_reset:
            cursor.execute("DROP TABLE IF EXISTS login_attempts;")
            cursor.execute("DROP TABLE IF EXISTS notifications;")
            cursor.execute("DROP TABLE IF EXISTS status_history;")
            cursor.execute("DROP TABLE IF EXISTS pickup_requests;")
            cursor.execute("DROP TABLE IF EXISTS food_waste_records;")
            cursor.execute("DROP TABLE IF EXISTS donations;")
            cursor.execute("DROP TABLE IF EXISTS users;")
            cursor.execute("DROP TABLE IF EXISTS ngos;")
            cursor.execute("DROP TABLE IF EXISTS donors;")
            cursor.execute("DROP TABLE IF EXISTS app_metadata;")
            set_db_version(conn, 0)

        run_migrations(conn=conn, db_path=db_path)
        ensure_schema_compatibility(cursor)

        # Non-destructive check: seed if donors, ngos, users, or donations table is empty
        cursor.execute("SELECT COUNT(*) FROM donors;")
        donors_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ngos;")
        ngos_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users;")
        users_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM donations;")
        don_count = cursor.fetchone()[0]

        if force_reset or donors_count == 0 or ngos_count == 0 or users_count == 0 or don_count == 0:
            seed_initial_demo_data(cursor)
            cursor.execute("""
                INSERT OR REPLACE INTO app_metadata (key, value, updated_at)
                VALUES ('demo_seeded', 'true', ?);
            """, (get_ist_now().isoformat(),))

        # Ensure existing legacy donations and requests have foreign keys populated
        cursor.execute("UPDATE donations SET donor_id = 'DONOR-001' WHERE donor_id IS NULL OR donor_id = '';")
        cursor.execute("UPDATE pickup_requests SET ngo_id = 'NGO-001' WHERE ngo_id IS NULL OR ngo_id = '';")

        conn.commit()
        conn.close()

def seed_initial_demo_data(cursor):
    """Seed realistic, clearly fictional demonstration records using relative offsets."""
    import secrets
    from auth import hash_password

    base_time = get_ist_now()
    demo_today = base_time.strftime("%Y-%m-%d")
    now_iso = format_ist_str(base_time)
    
    # Relative offsets (never fixed clock times)
    t_prep_a = format_ist_str(base_time - timedelta(hours=2))
    t_avail_a = format_ist_str(base_time - timedelta(minutes=30))
    t_dead_a = format_ist_str(base_time + timedelta(hours=4))

    t_prep_b = format_ist_str(base_time - timedelta(hours=1))
    t_avail_b = format_ist_str(base_time)
    t_dead_b = format_ist_str(base_time + timedelta(hours=3))

    t_prep_c = format_ist_str(base_time - timedelta(hours=3))
    t_avail_c = format_ist_str(base_time - timedelta(hours=1))
    t_dead_c = format_ist_str(base_time + timedelta(hours=3))

    # 1. Seed Donors
    donors_seed = [
        ("DONOR-001", "Sharma Wedding Events (Fictional Demo)", "+91-98765-11111", "Civil Lines Banquet Lawn (Fictional Demo Locality), Prayagraj", 25.4520, 81.8340),
        ("DONOR-002", "Birthday Event Demo (Fictional Demo)", "+91-98123-22222", "Tagore Town Community Hall (Fictional Demo Locality), Prayagraj", 25.4480, 81.8560),
        ("DONOR-003", "Green Plate Demo Restaurant (Fictional Demo)", "+91-97234-33333", "MG Marg Central Market (Fictional Demo Locality), Prayagraj", 25.4560, 81.8380)
    ]
    for d_id, name, contact, loc, lat, lng in donors_seed:
        cursor.execute("""
            INSERT OR REPLACE INTO donors (id, name, contact, location, lat, lng, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?);
        """, (d_id, name, contact, loc, lat, lng, now_iso))

    # 2. Seed NGOs
    ngos_seed = [
        ("NGO-001", "Prayag Annapurna Seva Sansthan (Fictional Demo NGO)", "+91-94500-11111", "Naini Shelter Cluster, Prayagraj", 25.4080, 81.8680, 1, "System Admin", 250),
        ("NGO-002", "Ganga Relief Foundation (Fictional Demo NGO)", "+91-94500-22222", "Katra Distribution Centre, Prayagraj", 25.4630, 81.8460, 1, "System Admin", 150),
        ("NGO-003", "New Hope Food Rescue (Fictional Demo NGO)", "+91-94500-33333", "Daraganj Community Depot, Prayagraj", 25.4320, 81.8750, 0, None, 100)
    ]
    for ngo_id, name, contact, loc, lat, lng, verified, app_by, cap in ngos_seed:
        cursor.execute("""
            INSERT OR REPLACE INTO ngos (id, name, contact, location, lat, lng, is_verified, approved_by, capacity_portions, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (ngo_id, name, contact, loc, lat, lng, verified, app_by, cap, now_iso))

    # 3. Seed Users with secure random or environment-configured passwords (never hardcoded)
    def get_seed_password(role: str, username: str) -> str:
        u_var = f"DEMO_PASSWORD_{username.upper()}"
        if os.getenv(u_var) and len(os.getenv(u_var)) >= 10:
            return os.getenv(u_var)
        if username == "verma_events" and os.getenv("DEMO_PASSWORD_DONOR2"):
            return os.getenv("DEMO_PASSWORD_DONOR2")
        if username == "ganga_relief" and os.getenv("DEMO_PASSWORD_NGO2"):
            return os.getenv("DEMO_PASSWORD_NGO2")
        if username == "new_hope" and os.getenv("DEMO_PASSWORD_NGO3"):
            return os.getenv("DEMO_PASSWORD_NGO3")
        r_var = f"DEMO_PASSWORD_{role.upper()}"
        if os.getenv(r_var) and len(os.getenv(r_var)) >= 10:
            return os.getenv(r_var)
        return secrets.token_urlsafe(12)

    pwd_donor1 = get_seed_password("donor", "sharma_catering")
    pwd_donor2 = get_seed_password("donor", "verma_events")
    pwd_ngo1 = get_seed_password("ngo", "prayag_seva")
    pwd_ngo2 = get_seed_password("ngo", "ganga_relief")
    pwd_ngo3 = get_seed_password("ngo", "new_hope")
    pwd_admin = get_seed_password("admin", "admin")

    users_seed = [
        ("USR-001", "sharma_catering", hash_password(pwd_donor1), "donor", "DONOR-001"),
        ("USR-002", "verma_events", hash_password(pwd_donor2), "donor", "DONOR-002"),
        ("USR-003", "prayag_seva", hash_password(pwd_ngo1), "ngo", "NGO-001"),
        ("USR-004", "ganga_relief", hash_password(pwd_ngo2), "ngo", "NGO-002"),
        ("USR-005", "new_hope", hash_password(pwd_ngo3), "ngo", "NGO-003"),
        ("USR-ADMIN", "admin", hash_password(pwd_admin), "admin", None)
    ]
    for u_id, uname, phash, role, org_id in users_seed:
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, username, password_hash, role, org_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?);
        """, (u_id, uname, phash, role, org_id, now_iso))

    if os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes"):
        print("[AnnRakshak Demo Seed] Generated random demo credentials (DEMO_MODE=true):")
        print(f"  Donor (sharma_catering): {pwd_donor1}")
        print(f"  NGO   (prayag_seva):     {pwd_ngo1}")
        print(f"  Admin (admin):           {pwd_admin}")

    # 4. Sample Donations with donor_id foreign key
    don_a_id = "DON-WED-001"
    cursor.execute("""
        INSERT OR IGNORE INTO donations (
            id, donor_id, donor_name, event_type, food_description, quantity_portions,
            available_portions, prep_datetime, available_from, pickup_deadline,
            storage_info, location, lat, lng, private_contact, notes, status, food_safety_window_hours,
            is_demo_seed, created_at, updated_at
        ) VALUES (?, 'DONOR-001', ?, 'Wedding', ?, 100, 100, ?, ?, ?, ?, ?, 25.4520, 81.8340, ?, ?, 'Available', 6.0, 1, ?, ?);
    """, (
        don_a_id,
        "Sharma Wedding Events (Fictional Demo)",
        "Vegetable pulao, dal makhani, paneer butter masala, chapati and gulab jamun",
        t_prep_a, t_avail_a, t_dead_a,
        "Stored in commercial insulated stainless containers at >65°C.",
        "Civil Lines Banquet Lawn (Fictional Demo Locality), Prayagraj",
        "+91-98765-11111",
        "Packed freshly right after banquet dinner concluded. Utensils or containers to be returned or brought by NGO.",
        now_iso, now_iso
    ))

    don_b_id = "DON-BDAY-002"
    cursor.execute("""
        INSERT OR IGNORE INTO donations (
            id, donor_id, donor_name, event_type, food_description, quantity_portions,
            available_portions, prep_datetime, available_from, pickup_deadline,
            storage_info, location, lat, lng, private_contact, notes, status, food_safety_window_hours,
            is_demo_seed, created_at, updated_at
        ) VALUES (?, 'DONOR-002', ?, 'Birthday Party', ?, 30, 30, ?, ?, ?, ?, ?, 25.4480, 81.8560, ?, ?, 'Available', 6.0, 1, ?, ?);
    """, (
        don_b_id,
        "Birthday Event Demo (Fictional Demo)",
        "Individual packed meal boxes (Veg fried rice, manchurian, fruit salad)",
        t_prep_b, t_avail_b, t_dead_b,
        "Pre-sealed food-grade disposable containers. Kept in cool, dry banquet holding area.",
        "Tagore Town Community Hall (Fictional Demo Locality), Prayagraj",
        "+91-98123-22222",
        "Surplus packaged boxes from children's evening birthday celebration.",
        now_iso, now_iso
    ))

    don_c_id = "DON-REST-003"
    cursor.execute("""
        INSERT OR IGNORE INTO donations (
            id, donor_id, donor_name, event_type, food_description, quantity_portions,
            available_portions, prep_datetime, available_from, pickup_deadline,
            storage_info, location, lat, lng, private_contact, notes, status, food_safety_window_hours,
            is_demo_seed, created_at, updated_at
        ) VALUES (?, 'DONOR-003', ?, 'Restaurant', ?, 25, 0, ?, ?, ?, ?, ?, 25.4560, 81.8380, ?, ?, 'Requested', 6.0, 1, ?, ?);
    """, (
        don_c_id,
        "Green Plate Demo Restaurant (Fictional Demo)",
        "Prepared meal boxes (Jeera rice, yellow dal tadka, mix veg sabzi, phulkas)",
        t_prep_c, t_avail_c, t_dead_c,
        "Hot holding food warmers in commercial kitchen pantry.",
        "MG Marg Central Market (Fictional Demo Locality), Prayagraj",
        "+91-97234-33333",
        "Fresh lunch buffet surplus packed immediately after 3:30 PM service cutoff.",
        now_iso, now_iso
    ))

    # 5. Sample Request for Donation C with ngo_id foreign key
    req_c_id = "REQ-DEMO-001"
    cursor.execute("""
        INSERT OR IGNORE INTO pickup_requests (
            id, donation_id, ngo_id, ngo_name, ngo_contact, requested_portions,
            proposed_pickup_time, notes, status, is_demo_seed, created_at, updated_at
        ) VALUES (?, ?, 'NGO-001', ?, ?, 25, ?, ?, 'Requested', 1, ?, ?);
    """, (
        req_c_id,
        don_c_id,
        "Prayag Annapurna Seva Sansthan (Fictional Demo NGO)",
        "Coordinator Manoj Gupta (+91-94500-11111, seva@prayagdemo.org)",
        format_ist_str(base_time + timedelta(hours=1)),
        "Electric van equipped with insulated crates ready for distribution at night shelter near Junction.",
        now_iso, now_iso
    ))

    # 6. Historical waste samples
    waste_samples = [
        ("Grand Heritage Banquet (Fictional Demo)", (base_time - timedelta(days=6)).strftime("%Y-%m-%d"), "Dinner", "North Indian Buffet, Naan, Paneer, Rice, Gulab Jamun", 250, 205, 30, 15, 180.0, 15 * 180.0, "Rain caused unexpected 18% attendance drop."),
        ("Green Plate Demo Restaurant (Fictional Demo)", (base_time - timedelta(days=5)).strftime("%Y-%m-%d"), "Lunch", "Thali menu, Rice, Roti, Dal, Seasonal Sabzi", 120, 108, 8, 4, 110.0, 4 * 110.0, "Standard weekday lunch service variance."),
        ("University Hostel Mess A (Fictional Demo)", (base_time - timedelta(days=4)).strftime("%Y-%m-%d"), "Dinner", "Chole Bhature, Pulao, Raita, Kheer", 320, 275, 35, 10, 85.0, 10 * 85.0, "Weekend exodus of students not accounted in prep."),
        ("Sharma Wedding Events (Fictional Demo)", (base_time - timedelta(days=3)).strftime("%Y-%m-%d"), "Dinner", "Deluxe Wedding Spread, Sweets, Live Counters", 400, 310, 70, 20, 250.0, 20 * 250.0, "Excess cooked at late night snack counters."),
        ("City Central Canteen (Fictional Demo)", (base_time - timedelta(days=2)).strftime("%Y-%m-%d"), "Lunch", "South Indian Combo, Dosa batter, Sambar, Idli", 150, 135, 10, 5, 75.0, 5 * 75.0, "Batter leftover discarded due to lack of cold storage capacity."),
        ("Grand Heritage Banquet (Fictional Demo)", (base_time - timedelta(days=1)).strftime("%Y-%m-%d"), "Dinner", "Corporate Annual Gala Dinner Buffet", 180, 160, 15, 5, 210.0, 5 * 210.0, "Better head count adherence; low discard rate."),
        ("Green Plate Demo Restaurant (Fictional Demo)", demo_today, "Lunch", "Executive Thali & Biryani special", 130, 115, 10, 5, 120.0, 5 * 120.0, "Edible surplus diverted for staff and potential listing.")
    ]

    for idx, (p_name, w_date, m_type, m_items, prep, cons, ed_surp, disc, cpm, fin_loss, notes) in enumerate(waste_samples, 1):
        w_id = f"WST-HIST-{idx:03d}"
        cursor.execute("""
            INSERT OR IGNORE INTO food_waste_records (
                id, provider_name, date, meal_type, menu_items, portions_prepared,
                portions_consumed, edible_surplus, discarded_waste, cost_per_meal,
                financial_loss, notes, is_demo_seed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?);
        """, (
            w_id, p_name, w_date, m_type, m_items, prep, cons, ed_surp, disc, cpm, fin_loss, notes, now_iso
        ))

    # Status history
    cursor.execute("""
        INSERT INTO status_history (entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks)
        VALUES ('donation', ?, NULL, 'Available', 'System Seed', ?, 'Initial demo listing creation');
    """, (don_a_id, now_iso))
    cursor.execute("""
        INSERT INTO status_history (entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks)
        VALUES ('donation', ?, NULL, 'Available', 'System Seed', ?, 'Initial demo listing creation');
    """, (don_b_id, now_iso))
    cursor.execute("""
        INSERT INTO status_history (entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks)
        VALUES ('donation', ?, 'Available', 'Requested', 'System Seed', ?, 'Demo NGO request placed');
    """, (don_c_id, now_iso))
    cursor.execute("""
        INSERT INTO status_history (entity_type, entity_id, previous_status, new_status, changed_by, timestamp, remarks)
        VALUES ('request', ?, NULL, 'Requested', 'System Seed', ?, 'Demo pickup request submitted');
    """, (req_c_id, now_iso))
