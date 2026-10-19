# 🌾 AnnRakshak AI (अन्न बचाओ, बर्बादी घटाओ)

> **Hindi Tagline:** अन्न बचाओ, बर्बादी घटाओ।  
> **English Tagline:** Predict demand. Prevent waste. Rescue surplus.  
> **System Architecture:** Pilot-Ready Modular Clean Architecture (Streamlit + SQLite WAL + Google GenAI Gemma 4)  
> **Target Deployment:** Municipal Surplus Food Rescue Network (Prayagraj Pilot)

---

## 1. Executive Summary

**AnnRakshak AI** is a surplus food rescue and waste reduction system engineered for banquets, wedding halls, caterers, restaurants, and canteens in Prayagraj. It connects surplus food donors with verified non-governmental organizations (NGOs) to prevent edible food from reaching landfills while preserving food safety.

Key architectural features include:
- **Clean Repository Architecture:** Modular separation between Streamlit UI views (`components/`), domain workflow services (`workflow_manager.py`), data access repositories (`repositories/`), and storage.
- **Fail-Closed Backend RBAC:** Server-side authorization verifying `acting_user` identity, active status, role, and organization ownership on all workflow functions.
- **Portion Conservation Invariant:** Strict mathematical conservation enforcing $\text{Available} + \sum(\text{Active Claims}) + \text{Delivered} = \text{Total Quantity}$. Expired or cancelled requests atomically release portions back to the pool.
- **Concurrency Isolation:** SQLite Write-Ahead Logging (`WAL`) with `BEGIN IMMEDIATE` transaction locks and a 10-second busy timeout to prevent double-booking during simultaneous NGO claims.
- **Closed-Fail Food Safety Window:** Enforces FSSAI 4–6 hour ambient temperature guidelines; food past its safety window is blocked from dispatch and automatically marked `Expired`.
- **Contact Privacy:** Masked phone numbers (`+XX-XXXXX-XX87`) by default; raw donor phone numbers are unmasked only to the assigned NGO after donation confirmation, and are omitted from CSV exports and AI prompts.
- **P80 Demand Planning:** Gaussian normal distribution 80th percentile ($Z = 1.28$) planning buffer with historical Mean Absolute Percentage Error (MAPE) backtesting.
- **Geospatial Dispatch:** Great-circle Haversine distance calculations and a calibrated 20 km/h urban transit model.
- **Resilient AI Dispatch Insights:** Google Gemma 4 client with 3-attempt exponential backoff, 10s timeout, PII redaction, and deterministic rule-based fallback.
- **Automated Contrast Verification:** 636 DOM nodes evaluated across 18 matrix configurations (3 themes x 2 languages x 3 roles) with $\ge 4.5:1$ contrast ratio ($\ge 3.0:1$ for large text), verified by `test_playwright_contrast.py`.
- **Bilingual Interface:** 133 English and Hindi localized keys verified by `test_engineering_p3.py`.

---

## 2. Authentication & Demo Access

AnnRakshak AI enforces server-side authentication using `bcrypt` password hashing. Demo user sessions are tied directly to relational database IDs:

| Portal | Demo Username | Credentials | Role Permissions |
| :--- | :--- | :--- | :--- |
| **🌾 Donor Portal** | `sharma_catering` | Randomly generated on seed (or set via `DEMO_PASSWORD_DONOR`) | Create listings, accept/reject pickup claims, log kitchen audits, view P80 predictions & AI insights |
| **🤝 NGO Portal** | `prayag_seva` | Randomly generated on seed (or set via `DEMO_PASSWORD_NGO`) | Browse listings with masked contacts, submit atomic portion claims, update transit milestones (`Collected` → `Delivered`) |
| **🛡️ Admin Portal** | `admin` | Randomly generated on seed (or set via `DEMO_PASSWORD_ADMIN`) | Verify/approve NGOs, view platform audit logs, monitor system health, portion conservation invariants, and ESG metrics |

> [!NOTE]
> When `DEMO_MODE=true` is set in the environment, convenient 1-click authentication buttons appear on the login screen for testing. In standard operation (`DEMO_MODE=false`), credentials must be entered manually, and 5 failed attempts within 5 minutes trigger a 5-minute lockout.

---

## 3. Technology Stack & Enterprise Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Streamlit Presentation                          │
│  ┌───────────────────────┐┌──────────────────────┐┌──────────────────┐ │
│  │  components/donor.py  ││  components/ngo.py   ││components/admin  │ │
│  └───────────┬───────────┘└──────────┬───────────┘└─────────┬────────┘ │
└──────────────┼───────────────────────┼──────────────────────┼──────────┘
               │                       │                      │
┌──────────────▼───────────────────────▼──────────────────────▼──────────┐
│                      Business Logic & Domain Layer                     │
│  • workflow_manager.py : Monotonic state machine & portion release     │
│  • auth.py             : Bcrypt hashing, lockout throttling & RBAC     │
│  • demand_predictor.py : P80 prediction interval & MAPE backtesting    │
│  • logistics.py        : Haversine distance & 20 km/h transit model    │
│  • notifications.py    : Multi-channel event emitter (SMS/WA/Email)    │
│  • ai_insights.py      : Gemma 4 client with retry, timeout & PII scrub│
│  • ui_styles.py        : WCAG AA color tokens, high-contrast themes    │
│  • i18n.py             : Bilingual English/Hindi localization engine   │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼─────────────────────────────────┐
│                     Repository Data Access Layer                       │
│  • repositories/donation_repository.py                                 │
│  • repositories/request_repository.py                                  │
│  • repositories/organization_repository.py                             │
│  • repositories/base.py (Thread-safe transaction context manager)      │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼─────────────────────────────────┐
│                      Persistent Relational Storage                     │
│  • SQLite 3 (annrakshak.db: WAL mode, PRAGMA user_version = 4)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Scientific ESG & Environmental Citations

AnnRakshak AI references established public health and environmental benchmarks as configurable baseline assumptions:

| Metric | Baseline Value | Standard / Public Benchmark | Formula Applied |
| :--- | :--- | :--- | :--- |
| **Portion Mass** | $0.35\text{ kg / portion}$ | **UNEP Food Waste Index Report (2021/2024)** | $\text{kg Saved} = \text{Portions Delivered} \times 0.35$ |
| **Emissions Avoided** | $2.5\text{ kg CO}_2\text{e / kg food}$ | **FAO / UNEP GHG Food Waste Life-Cycle Benchmark** | $\text{CO}_2\text{e Avoided} = \text{kg Saved} \times 2.5$ |
| **Water Footprint** | $1,000\text{ Liters / kg food}$ | **FAO Agricultural Water Footprint Benchmark** | $\text{Water Saved (L)} = \text{kg Saved} \times 1,000$ |
| **Safety Window** | $4\text{ to }6\text{ Hours}$ | **FSSAI Food Safety & Standards Guidelines** (Ambient Holding) | $\text{Prep Time} + \text{Window} \ge \text{Pickup Deadline}$ |
| **P80 Confidence** | $Z = 1.28$ | **Gaussian Normal Distribution (80th Percentile)** | $\text{Target} = \mu + 1.28 \cdot \sigma$ |

---

## 5. Quickstart & Deployment

### Option A: Local Python Environment

1. **Clone or Navigate to the Workspace:**
   ```bash
   cd c:\Users\Dell\Desktop\annrakash-ai
   ```

2. **Install Required Packages:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Configure Environment Variables:**
   ```bash
   cp .env.example .env
   ```
   *Note:* Set `GEMINI_API_KEY` for live Gemma 4 insights. If omitted, the platform automatically activates its deterministic rule-based fallback engine.

4. **Launch Streamlit:**
   ```bash
   streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.

---

### Option B: Docker Container Deployment

AnnRakshak AI provides a lightweight, single-node container deployment:

1. **Build and Run with Docker Compose:**
   ```bash
   docker compose up -d --build
   ```

2. **Verify Service Health:**
   ```bash
   docker compose ps
   ```
   The stack provisions `annrakshak_ai_app` on Python 3.11-slim with an isolated volume mount at `/app/data/annrakshak.db`.

---

## 6. Known Limitations

While engineered to high reliability for pilot validation, AnnRakshak AI currently has the following known operational constraints:

1. **Single-Node SQLite Persistence:** Write-Ahead Logging (`WAL`) provides high read concurrency and safe write serialization on a single host. It does not provide distributed replication, multi-node clustering, or automatic failover.
2. **No High Availability / Failover:** If the host process terminates, the platform is offline until restarted.
3. **Demo-Grade AI Content Filtering:** The Gemma 4 integration includes heuristic PII scrubbing (phone numbers and names) and exponential backoff, but lacks advanced content-moderation safety classifiers or automated adversarial jailbreak detection.
4. **Streamlit Session State volatile to Reloads:** Streamlit stores session states in server memory. Full browser refreshes reset transient form buffers.
5. **Single Timezone:** The application is calibrated specifically for Indian Standard Time (`Asia/Kolkata`, IST). Cross-timezone deployments require configurable timezone contexts.

---

## 7. Verification & Automated Test Suite

AnnRakshak AI is validated by an automated regression test suite covering all tiers:

```bash
# Run Core Unit Test Suite
python -m unittest test_p0_a_auth.py test_p0_b_backend.py test_p0_c_build_and_data.py test_security_p0.py test_integrity_p1.py test_workflow.py test_intelligence_p2.py test_engineering_p3.py

# Run Playwright Automated Headless Browser Contrast Audit
python test_playwright_contrast.py
```

### Verified Test Suites:
- **`test_p0_a_auth.py` (5/5 Passed):** Password hashing, bypass removal, lockout throttling, constant-time compare, session idle timeout.
- **`test_p0_b_backend.py` (10/10 Passed):** Mandatory `acting_user` authorization on all 7 workflow methods, negative permission assertions, and 500-step randomized state machine invariant verification.
- **`test_p0_c_build_and_data.py` (4/4 Passed):** Package compatibility, single-node SQLite compose configuration, gitignore database hygiene, fresh seed simulation.
- **`test_security_p0.py` (6/6 Passed):** Bcrypt auth, foreign keys, unverified NGO gates, contact masking, XSS escaping, CSV formula sanitization.
- **`test_integrity_p1.py` (6/6 Passed):** Repository decoupling, `BEGIN IMMEDIATE` concurrency, deterministic status derivation, closed-fail food safety checks, schema migrations (version 4).
- **`test_workflow.py` (9/9 Passed):** Full lifecycle workflow, partial reservations, request cancellations, portion restorations, and invariant checks.
- **`test_intelligence_p2.py` (6/6 Passed):** P80 predictor with MAPE backtesting, Gemma 4 retry/timeout and rule fallback, Haversine geospatial calculations, notification queueing.
- **`test_engineering_p3.py` (6/6 Passed):** 133/133 English/Hindi key parity, dynamic color contrast, modular architecture (`app.py` $\le 250$ lines).
- **`test_playwright_contrast.py` (1/1 Passed):** Automated browser audit testing 636 DOM elements across 18 matrix configurations (3 themes x 2 languages x 3 roles), verifying WCAG AA contrast.

---

## 8. License

- **Application Codebase:** Licensed under the [Apache License, Version 2.0](LICENSE).
- **Gemma 4 Models:** Subject to the [Gemma Terms of Use](https://ai.google.dev/gemma/terms) and Prohibited Use Policy.
