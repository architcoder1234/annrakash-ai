-- Migration 002: Performance and query optimization indexes

CREATE INDEX IF NOT EXISTS idx_donations_donor_id ON donations(donor_id);
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_deadline ON donations(pickup_deadline);

CREATE INDEX IF NOT EXISTS idx_requests_donation_id ON pickup_requests(donation_id);
CREATE INDEX IF NOT EXISTS idx_requests_ngo_id ON pickup_requests(ngo_id);
CREATE INDEX IF NOT EXISTS idx_requests_status ON pickup_requests(status);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);

CREATE INDEX IF NOT EXISTS idx_food_waste_date ON food_waste_records(date);
CREATE INDEX IF NOT EXISTS idx_food_waste_provider ON food_waste_records(provider_name);

CREATE INDEX IF NOT EXISTS idx_history_entity ON status_history(entity_type, entity_id);
