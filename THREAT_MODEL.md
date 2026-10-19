# 🛡️ AnnRakshak AI — Threat Model & Security Architecture

> **Document Version:** 2.0 (Post-Audit Round 2)  
> **Target Scope:** AnnRakshak AI Surplus Food Rescue Logistics System (Prayagraj Pilot)  
> **Application Architecture:** Python 3.11, Streamlit, SQLite 3 (WAL Mode), Google GenAI Gemma 4  
> **Security Standard:** OWASP Top 10 (2021), STRIDE Threat Modeling Methodology  

---

## 1. System Scope & Trust Boundaries

AnnRakshak AI operates across four distinct trust domains:

```
[ Unstrusted Zone: Public Internet & Web Browsers ]
                         │
                         ▼ HTTPS / TLS 1.3
[ Perimeter Zone: Reverse Proxy / Streamlit Server ]
    ├── auth.py (Bcrypt Verification, Login Throttling)
    ├── app.py (Session Router, Session Inactivity Guard)
    └── ui_styles.py (XSS Defense via html.escape)
                         │
                         ▼ Process-Level Function Invocations
[ Core Application Zone: Business Logic & Repositories ]
    ├── workflow_manager.py (Fail-Closed RBAC & Invariant Enforcement)
    ├── repositories/ (Parameterized SQL Queries & BEGIN IMMEDIATE locks)
    └── ai_insights.py (PII Scrubbing & Outbound Sanitization)
           │                                 │
           ▼ Local Disk                      ▼ External TLS API
[ Data Persistence ]              [ Third-Party AI Services ]
SQLite (annrakshak.db + WAL)      Google GenAI (Gemma 4 API)
```

### Trust Boundary Definitions:
1. **Boundary A (Client ↔ Streamlit Server):** Untrusted web clients submit HTTP requests and WebSocket packets. All user input must be sanitized and validated server-side.
2. **Boundary B (Streamlit UI ↔ Domain Logic):** Presentation components must pass the validated `acting_user` object. Domain methods fail closed if `acting_user` is missing, inactive, or unauthorized.
3. **Boundary C (Domain Logic ↔ SQLite Database):** All SQL execution utilizes parameterized queries (`?` placeholders). No user-controlled strings are ever interpolated into SQL statements.
4. **Boundary D (Domain Logic ↔ External AI):** Donor private phone numbers and personal contact details are redacted prior to payload dispatch to Google GenAI APIs.

---

## 2. Actors, Personas, and Authorization Model

| Persona | Identity Verification | Org Association | Authorized Operations |
| :--- | :--- | :--- | :--- |
| **Anonymous Visitor** | None | None | View login portal; review fictional demo notice and public health guidance. Cannot view or reserve surplus listings. |
| **Food Donor** (`donor`) | Bcrypt hash comparison (`verify_password`) | `donors` table (`donor_id`) | Create food donation listings; accept/reject pickup claims on owned donations; cancel owned donations; log kitchen audits. Cannot claim food or approve NGOs. |
| **NGO Recovery Team** (`ngo`) | Bcrypt hash comparison (`verify_password`) | `ngos` table (`ngo_id`) | Browse available listings (with masked contacts); claim portions (only if `is_verified == 1`); progress claimed requests (`Collected` → `Delivered`); cancel own pending requests. Cannot create donor listings or approve NGOs. |
| **System Administrator** (`admin`) | Bcrypt hash comparison (`verify_password`) | Global admin | Verify and approve NGOs; view platform audit logs; monitor system health, portion conservation invariants, and ESG metrics; emergency cancellation. |

---

## 3. STRIDE Threat Analysis & Implemented Countermeasures

### 3.1 Spoofing (Identity Deception)
* **Threat:** An attacker attempts credential stuffing, brute-force guessing of demo passwords, or session hijacking.
* **Countermeasures:**
  * **Strict Bcrypt Password Hashing:** Demo match bypasses have been removed. Passwords must match the stored bcrypt hash (`auth.py:verify_password`).
  * **Constant-Time Comparison Defense:** When an invalid or nonexistent username is entered, `auth.authenticate_user` executes a dummy bcrypt comparison against a pre-computed hash, preventing timing attacks.
  * **Rate Limiting & Account Lockout:** 5 failed authentication attempts for any username within a 5-minute window results in an automatic 5-minute lockout (`auth.is_account_locked`).
  * **Session Inactivity Timeout:** Active sessions automatically expire after 30 minutes of client inactivity (`app.py:last_activity`).

### 3.2 Tampering (Data Manipulation)
* **Threat:** An unauthorized user modifies listing status, inflates available portions, claims unverified quantities, or injects malicious SQL.
* **Countermeasures:**
  * **Fail-Closed Backend Authorization:** All 7 critical workflow functions (`create_donation`, `request_pickup`, `update_request_status`, `cancel_donation`, `approve_ngo`, `get_contact_for`, `log_food_waste`) explicitly require an active `acting_user` dictionary. Inactive or missing users immediately fail closed (`False, "Unauthorized"`).
  * **Portion Conservation Invariant:** Database transitions enforce `available_portions + sum(active requests) + delivered_portions == quantity_portions`. Any request cancellation or expiry atomically returns portions to the available pool.
  * **100% Parameterized SQL:** All SQL queries in `repositories/` use parameterized binding, eliminating SQL injection vulnerabilities.
  * **BEGIN IMMEDIATE Concurrency Isolation:** SQLite transactions take an exclusive reservation lock to prevent race conditions and double-booking during simultaneous NGO claims.

### 3.3 Repudiation (Denial of Action)
* **Threat:** A user claims they never approved, rejected, or modified a surplus food pickup.
* **Countermeasures:**
  * **Audit Logging:** Every login attempt (successful or failed) is recorded in `login_attempts` with UTC timestamp, username, and IP/session context.
  * **Transition History:** Every request status transition records timestamp, previous state, new state, and triggering organization ID.

### 3.4 Information Disclosure (Data Leakage)
* **Threat:** Competitors, scraped bots, or unverified NGOs harvest donor personal phone numbers; CSV export injection; reflected XSS.
* **Countermeasures:**
  * **Zero-Contact Leakage in UI & AI:** Phone numbers are masked by default (`+XX-XXXXX-XX87`). Unmasking is restricted strictly to the listing donor owner and the requesting NGO *only after* the pickup request is `Confirmed` (`workflow_manager.get_contact_for`).
  * **Raw Contact Redaction:** Database queries in `workflow_manager.py` explicitly exclude raw contact numbers from general listing DataFrames used by Streamlit tables and CSV exports.
  * **HTML XSS Sanitization:** All user-supplied inputs (donor names, food menus, storage notes, locations) are escaped using `html.escape()` prior to rendering in HTML cards.
  * **CSV Formula Injection Mitigation:** Exported CSV cells starting with `=`, `+`, `-`, or `@` are sanitized with single-quote escaping.

### 3.5 Denial of Service (Service Disruption)
* **Threat:** An attacker floods the login portal or exhausts SQLite write locks.
* **Countermeasures:**
  * **WAL Mode & Busy Timeout:** SQLite is configured with Write-Ahead Logging (`PRAGMA journal_mode = WAL;`) and `PRAGMA busy_timeout = 10000;`, enabling concurrent reads while serializing atomic writes safely without deadlocks.
  * **Login Lockout:** Limits abusive authentication attempts to 5 per 5 minutes per user.

### 3.6 Elevation of Privilege (Unauthorized Access)
* **Threat:** An NGO user approves their own verification status or a donor confirms a pickup on another caterer's listing.
* **Countermeasures:**
  * **Ownership Assertion:** `workflow_manager.py` validates that `acting_user['org_id'] == row['donor_id']` for confirmation/rejection, and `acting_user['role'] == 'admin'` for NGO verification.
  * **Verified NGO Enforcement:** `workflow_manager.request_pickup()` checks `is_verified == 1` inside the transactional backend, rejecting unverified organizations regardless of UI state.

---

## 4. Residual Risks & Production Hardening Roadmap

While AnnRakshak AI incorporates robust defenses suitable for municipal pilot trials, the following residual risks are acknowledged:

1. **Single-Node Availability:** SQLite does not support distributed active-active replication. For multi-datacenter high availability, the repository layer should be pointed to a managed PostgreSQL cluster.
2. **Streamlit Session Persistence:** Streamlit stores session states in server RAM. Browser refreshes re-trigger script execution; long-term mobile deployments benefit from dedicated REST API endpoints (e.g., FastAPI) paired with a lightweight PWA.
3. **AI Guardrails:** Current LLM integration scrubs PII and applies a 10-second timeout with deterministic fallback. Production deployments with live user-generated LLM interactions should introduce automated content safety classifiers (e.g., Google Cloud Content Safety or Llama Guard).
4. **Transport Layer Security:** The prototype is configured for local and containerized HTTP; production deployments must terminate TLS 1.3 at a reverse proxy (e.g., Caddy, Nginx, or AWS ALB) with HSTS headers enabled.
