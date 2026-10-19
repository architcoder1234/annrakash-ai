-- Migration 001: Initial schema for AnnRakshak AI
-- Sets up metadata, donors, ngos, users, donations, pickup_requests, food_waste_records, status_history

CREATE TABLE IF NOT EXISTS app_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS donors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    location TEXT NOT NULL,
    lat REAL DEFAULT 25.4358,
    lng REAL DEFAULT 81.8463,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ngos (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    contact TEXT NOT NULL,
    location TEXT NOT NULL,
    lat REAL DEFAULT 25.4358,
    lng REAL DEFAULT 81.8463,
    is_verified INTEGER DEFAULT 0,
    approved_by TEXT,
    capacity_portions INTEGER DEFAULT 100,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('donor', 'ngo', 'admin')),
    org_id TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS donations (
    id TEXT PRIMARY KEY,
    donor_id TEXT NOT NULL,
    donor_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    food_description TEXT NOT NULL,
    quantity_portions INTEGER NOT NULL CHECK (quantity_portions > 0),
    available_portions INTEGER NOT NULL CHECK (available_portions >= 0),
    prep_datetime TEXT NOT NULL,
    available_from TEXT NOT NULL,
    pickup_deadline TEXT NOT NULL,
    storage_info TEXT NOT NULL,
    location TEXT NOT NULL,
    lat REAL DEFAULT 25.4358,
    lng REAL DEFAULT 81.8463,
    private_contact TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL CHECK (status IN ('Available', 'Requested', 'Confirmed', 'Collected', 'Delivered', 'Cancelled', 'Rejected', 'Expired')),
    food_safety_window_hours REAL DEFAULT 6.0,
    is_demo_seed INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES donors (id) ON DELETE RESTRICT,
    CHECK (available_portions <= quantity_portions)
);

CREATE TABLE IF NOT EXISTS pickup_requests (
    id TEXT PRIMARY KEY,
    donation_id TEXT NOT NULL,
    ngo_id TEXT NOT NULL,
    ngo_name TEXT NOT NULL,
    ngo_contact TEXT NOT NULL,
    requested_portions INTEGER NOT NULL CHECK (requested_portions > 0),
    proposed_pickup_time TEXT NOT NULL,
    notes TEXT,
    status TEXT NOT NULL CHECK (status IN ('Available', 'Requested', 'Confirmed', 'Collected', 'Delivered', 'Cancelled', 'Rejected', 'Expired')),
    is_demo_seed INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (donation_id) REFERENCES donations (id) ON DELETE RESTRICT,
    FOREIGN KEY (ngo_id) REFERENCES ngos (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS food_waste_records (
    id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    date TEXT NOT NULL,
    meal_type TEXT NOT NULL,
    menu_items TEXT NOT NULL,
    portions_prepared INTEGER NOT NULL CHECK (portions_prepared >= 0),
    portions_consumed INTEGER NOT NULL CHECK (portions_consumed >= 0),
    edible_surplus INTEGER NOT NULL CHECK (edible_surplus >= 0),
    discarded_waste INTEGER NOT NULL CHECK (discarded_waste >= 0),
    cost_per_meal REAL NOT NULL CHECK (cost_per_meal >= 0),
    financial_loss REAL NOT NULL CHECK (financial_loss >= 0),
    notes TEXT,
    is_demo_seed INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    remarks TEXT
);
