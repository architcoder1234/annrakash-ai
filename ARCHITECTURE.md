# 🏛️ AnnRakshak AI — Enterprise Architecture & System Design Document

> **System:** AnnRakshak AI (अन्न बचाओ, बर्बादी घटाओ)  
> **Deployment Target:** Prayagraj Municipal Surplus Food Logistics Pilot  
> **Core Stack:** Python 3.11, Streamlit, SQLite 3 (WAL mode, `user_version = 4`), Google GenAI (Gemma 4), Playwright  

---

## 1. System Overview & Layered Architecture

AnnRakshak AI is engineered with strict separation of concerns, decoupling presentation controllers from transactional business logic and relational database persistence via the Repository Pattern.

```mermaid
graph TD
    subgraph UI_Presentation ["Presentation Layer (Streamlit UI)"]
        APP["app.py (Controller & Session Router)"]
        DONOR_UI["components/donor.py (Donor Portal)"]
        NGO_UI["components/ngo.py (NGO Recovery Portal)"]
        ADMIN_UI["components/admin.py (Admin & Audit Portal)"]
        THEME["ui_styles.py (Dynamic WCAG AA Themes)"]
        I18N["i18n.py (Bilingual Translation Engine)"]
    end

    subgraph Service_Logic ["Business Logic & Intelligence Services"]
        AUTH["auth.py (Bcrypt RBAC, Lockout Throttling)"]
        WM["workflow_manager.py (State Machine & Atomic Transactions)"]
        DP["demand_predictor.py (P80 Interval & MAPE Backtesting)"]
        GEO["logistics.py (Haversine Routing & Urban Transit)"]
        NOTIF["notifications.py (Multi-Channel Event Dispatcher)"]
        AI["ai_insights.py (Gemma 4 Client & PII Redactor)"]
    end

    subgraph Data_Access ["Repository Pattern Data Access Layer"]
        DONOR_REPO["repositories/donation_repository.py"]
        REQ_REPO["repositories/request_repository.py"]
        ORG_REPO["repositories/organization_repository.py"]
        BASE_REPO["repositories/base.py (Transaction Context Manager)"]
    end

    subgraph Storage ["Persistence & External Services"]
        SQLITE[("SQLite 3 (annrakshak.db: WAL Mode, user_version 4)")]
        GEMMA_API["Google Gemma 4 API (Official google-genai SDK)"]
    end

    APP --> DONOR_UI & NGO_UI & ADMIN_UI
    APP --> THEME & I18N
    DONOR_UI & NGO_UI & ADMIN_UI --> WM & AUTH & DP & GEO & AI
    WM --> DONOR_REPO & REQ_REPO & ORG_REPO
    DONOR_REPO & REQ_REPO & ORG_REPO --> BASE_REPO
    BASE_REPO --> SQLITE
    WM --> NOTIF
    AI --> GEMMA_API
```

---

## 2. Monotonic State Transition Machine & Invariants

Donation state is deterministically derived from portion balances, pickup deadlines, and active request states (`derive_donation_status()`). Once a milestone is reached, status cannot move backward.

```mermaid
stateDiagram-v2
    [*] --> Available: Donor creates listing (Portions > 0)
    Available --> Requested: NGO submits pickup request (Portions reserved)
    Available --> Available: NGO submits partial request (Portions remain)
    
    Requested --> Confirmed: Donor approves request
    Requested --> Rejected: Donor rejects request (Portions released back)
    Requested --> Cancelled: NGO cancels pending claim (Portions released back)
    
    Confirmed --> Collected: NGO recovery team collects food
    Confirmed --> Cancelled: Exceptional cancellation (Portions released back)
    
    Collected --> Delivered: NGO delivers food to shelter/community
    
    Available --> Expired: Pickup deadline passes (Auto-expiry scanner)
    Requested --> Expired: Pickup deadline passes (Requests closed, portions released)
    
    Rejected --> [*]
    Cancelled --> [*]
    Delivered --> [*]
    Expired --> [*]
```

### Invariant Rules:
1. **Portion Conservation Invariant:**
   $$\text{available\_portions} + \sum(\text{portions of active requests}) + \text{delivered\_portions} = \text{quantity\_portions}$$
   where active requests are those in `Requested`, `Confirmed`, or `Collected` state.
2. **Atomic Restoration:** On request rejection, cancellation, or expiry, reserved portions return to `available_portions` if the pickup deadline has not elapsed. If the deadline has passed, the donation transitions to `Expired` and food cannot be claimed.
3. **No Availability with Zero Balance:** A donation is never marked `Available` if `available_portions == 0`.
4. **State Machine Verification:** Validated by `test_p0_b_backend.py` using a 500-step randomized state machine test that asserts `invariant_check(donation_id)` after every transition.

---

## 3. High-Concurrency Transaction Isolation

To prevent double-booking when multiple NGOs claim overlapping portions simultaneously, the database repository enforces SQLite `BEGIN IMMEDIATE` transactions:

```mermaid
sequenceDiagram
    autonumber
    actor NGO_A as NGO Alfa (Van 1)
    actor NGO_B as NGO Bravo (Van 2)
    participant WM as Workflow Manager
    participant DB as SQLite WAL Database

    NGO_A->>WM: request_pickup(don_1, 50 portions)
    NGO_B->>WM: request_pickup(don_1, 50 portions)
    
    Note over WM,DB: Transaction A acquires BEGIN IMMEDIATE lock
    WM->>DB: Check available portions (100 >= 50)
    DB-->>WM: OK (Available: 100)
    WM->>DB: UPDATE available_portions = 50, INSERT request A
    DB-->>WM: Commit A Success
    
    Note over WM,DB: Transaction B executes sequentially
    WM->>DB: Check available portions (50 >= 50)
    DB-->>WM: OK (Available: 50)
    WM->>DB: UPDATE available_portions = 0, INSERT request B
    DB-->>WM: Commit B Success
    
    Note over NGO_A,NGO_B: Both claims safely fulfilled without over-booking
```

---

## 4. Threat Model & Security Posture

A comprehensive threat analysis is documented in [`THREAT_MODEL.md`](THREAT_MODEL.md). Key defenses include:
- **Mandatory `acting_user` Authorization:** Checked at the service layer on all 7 workflow functions. Missing or unverified sessions fail closed.
- **Bcrypt Password Storage:** Eliminates plaintext or hardcoded credentials.
- **Constant-Time Timing Defense:** Nonexistent accounts trigger a dummy bcrypt comparison to thwart username enumeration.
- **Login Throttling:** 5 failed attempts in 5 minutes locks the account for 5 minutes.
- **PII Redaction:** Donor telephone numbers are masked by default (`+XX-XXXXX-XX87`) and omitted from CSV exports and AI prompts.

---

## 5. Known Operational Limitations

1. **Single-Host SQLite Architecture:** WAL mode enables concurrent readers with serialized writers on a single node. It does not provide multi-node clustering or cross-region failover.
2. **No Automatic High Availability:** If the server hardware fails, manual restart or container recreation is required.
3. **Streamlit Session State Volatility:** Streamlit holds user session states in server memory. Client browser reloads reset transient form fields.
4. **AI Safety Classifiers:** Gemma 4 uses regex-based PII scrubbing and prompt sanitization; it does not currently employ automated adversarial prompt injection classifiers.
