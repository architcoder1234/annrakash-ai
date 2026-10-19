"""
AnnRakshak AI - Enterprise Surplus Food Logistics, Waste Audit & Demand Prediction System
Built for Prayagraj pilot deployment.
Pairing food donors (banquets, caterers, restaurants) with verified NGO recovery teams.
Bilingual English/Hindi, WCAG AA accessible, with WAL SQLite, bcrypt RBAC,
deterministic P80 demand prediction, Haversine geospatial logistics, and Gemma 4 insights.
"""

import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import html

import auth
from database import init_db, get_connection, get_ist_now, format_ist_str, IST
import workflow_manager as wm
import demand_predictor as dp
import ai_insights as ai
from i18n import t

from ui_styles import (
    THEMES,
    get_theme_css,
    apply_plot_theme,
    render_brand_header,
    get_status_badge_html,
    render_workflow_stepper,
    get_urgency_badge_html,
    render_metric_box
)

from components import (
    render_donor_dashboard,
    render_ngo_dashboard,
    render_admin_dashboard
)

# Page Configuration
st.set_page_config(
    page_title="AnnRakshak AI | अन्न बचाओ, बर्बादी घटाओ",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema and verify non-destructive seeds
init_db()

# Auto-expire donations past pickup deadline on each app refresh
expired_count = wm.check_and_expire_donations()

# Session State Initialization
if "lang" not in st.session_state:
    st.session_state["lang"] = "en"

if "theme" not in st.session_state:
    st.session_state["theme"] = "nature"

if "auth_user" not in st.session_state:
    st.session_state["auth_user"] = None

lang = st.session_state["lang"]
current_theme = st.session_state["theme"]

# Inject WCAG 2.1 AA Dynamic Theme CSS
theme_css = get_theme_css(current_theme)
st.markdown(f"<style>{theme_css}</style>", unsafe_allow_html=True)

# Session Idle Timeout & Auth Gate
if st.session_state.get("auth_user"):
    now_dt = datetime.now()
    last_active = st.session_state.get("last_activity")
    if last_active and (now_dt - last_active) > timedelta(minutes=30):
        st.session_state["auth_user"] = None
        st.session_state["last_activity"] = None
        st.warning("⚠️ Session expired due to 30 minutes of inactivity. Please sign in again.")
        st.rerun()
    else:
        st.session_state["last_activity"] = now_dt

if not st.session_state["auth_user"]:
    st.markdown(render_brand_header(role_name=t("auth_title", lang), lang=lang), unsafe_allow_html=True)
    auth_col1, auth_col2, auth_col3 = st.columns([1, 2, 1])
    with auth_col2:
        st.markdown('<div class="fictional-notice-bar">📌 <strong>Secure Pilot Environment:</strong> Please authenticate with your organization credentials. Role permissions and data access are strictly verified on the backend.</div>', unsafe_allow_html=True)
        st.subheader(t("auth_title", lang))

        is_demo_mode = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")
        demo_donor_pwd = os.getenv("DEMO_PASSWORD_DONOR", "")
        demo_ngo_pwd = os.getenv("DEMO_PASSWORD_NGO", "")
        demo_admin_pwd = os.getenv("DEMO_PASSWORD_ADMIN", "")

        if is_demo_mode:
            st.markdown("##### ⚡ 1-Click Quick Sign In (DEMO_MODE Active):")
            q1, q2, q3 = st.columns(3)
            with q1:
                if st.button("🌾 1-Click: Donor", use_container_width=True, type="primary"):
                    user = auth.authenticate_user("sharma_catering", demo_donor_pwd) if demo_donor_pwd else auth.get_user_by_username("sharma_catering")
                    if user:
                        st.session_state["auth_user"] = user
                        st.session_state["last_activity"] = datetime.now()
                        st.rerun()
            with q2:
                if st.button("🤝 1-Click: NGO", use_container_width=True):
                    user = auth.authenticate_user("prayag_seva", demo_ngo_pwd) if demo_ngo_pwd else auth.get_user_by_username("prayag_seva")
                    if user:
                        st.session_state["auth_user"] = user
                        st.session_state["last_activity"] = datetime.now()
                        st.rerun()
            with q3:
                if st.button("🛡️ 1-Click: Admin", use_container_width=True):
                    user = auth.authenticate_user("admin", demo_admin_pwd) if demo_admin_pwd else auth.get_user_by_username("admin")
                    if user:
                        st.session_state["auth_user"] = user
                        st.session_state["last_activity"] = datetime.now()
                        st.rerun()
            st.markdown("<div style='text-align: center; margin: 12px 0 8px 0; color: #94A3B8; font-size: 0.85rem;'>— OR SIGN IN WITH CREDENTIALS —</div>", unsafe_allow_html=True)

        with st.form("login_form"):
            initial_user = "sharma_catering" if is_demo_mode else ""
            initial_pwd = demo_donor_pwd if is_demo_mode else ""
            username = st.text_input("Username *", value=initial_user)
            password = st.text_input("Password *", type="password", value=initial_pwd)
            submit_login = st.form_submit_button(t("auth_login_btn", lang), use_container_width=True, type="primary")

            if submit_login:
                user = auth.authenticate_user(username, password)
                if user:
                    st.session_state["auth_user"] = user
                    st.session_state["last_activity"] = datetime.now()
                    st.success(f"✅ Welcome, {user['username']}! ({user['role'].upper()})")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials or account locked.")

    # Stop rendering remainder of app until authenticated
    st.stop()

# Authenticated user object
user = st.session_state["auth_user"]
is_donor = (user["role"] == "donor")
is_ngo = (user["role"] == "ngo")
is_admin = (user["role"] == "admin")

# =========================================================
# SIDEBAR CONTROLS & NAVIGATION
# =========================================================
with st.sidebar:
    st.title("🌾 AnnRakshak AI")
    st.caption("अन्न बचाओ, बर्बादी घटाओ।")

    # User Profile Card
    st.markdown(
        f"""
        <div style="background: rgba(255,255,255,0.06); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.12); margin-bottom: 15px;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: #94A3B8; font-weight: 700;">Authenticated Session</div>
            <div style="font-size: 1.05rem; font-weight: 700; color: #FFFFFF; margin: 2px 0;">{html.escape(user['org_name'])}</div>
            <div style="font-size: 0.82rem; color: #38BDF8;">Role: <code>{user['role'].upper()}</code> | User: {html.escape(user['username'])}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🚪 " + t("auth_logout_btn", lang), use_container_width=True):
        st.session_state["auth_user"] = None
        st.rerun()

    st.markdown("---")

    # UI Setup & Theme Selection
    st.markdown(f"### {t('ui_settings', lang)}")
    lang_choice = st.selectbox(
        t("select_lang", lang),
        options=["English", "हिंदी (Hindi)"],
        index=0 if lang == "en" else 1
    )
    new_lang = "en" if lang_choice == "English" else "hi"
    if new_lang != st.session_state["lang"]:
        st.session_state["lang"] = new_lang
        st.rerun()

    theme_keys = list(THEMES.keys())
    theme_labels = [THEMES[k].get("label", THEMES[k].get("name", k)) for k in theme_keys]
    curr_theme_idx = theme_keys.index(current_theme) if current_theme in theme_keys else 0

    chosen_label = st.selectbox(
        t("select_theme", lang),
        options=theme_labels,
        index=curr_theme_idx
    )
    new_theme_key = theme_keys[theme_labels.index(chosen_label)]
    if new_theme_key != st.session_state["theme"]:
        st.session_state["theme"] = new_theme_key
        st.rerun()

    st.markdown("---")
    st.markdown(f"### {t('sidebar_sections', lang)}")

    if is_donor:
        donor_sections = [
            t("sec_donor_overview", lang),
            t("sec_donor_donate", lang),
            t("sec_donor_my_donations", lang),
            t("sec_donor_ngo_requests", lang),
            t("sec_donor_waste_tracker", lang),
            t("sec_donor_demand_pred", lang),
            t("sec_donor_ai_insights", lang),
            t("sec_donor_impact", lang)
        ]
        active_section = st.radio(t("sidebar_navigate_donor", lang), donor_sections, index=0)
    elif is_admin:
        admin_sections = [
            t("sec_admin_approvals", lang),
            t("sec_admin_audit", lang),
            t("sec_admin_reset", lang)
        ]
        active_section = st.radio(t("sidebar_navigate_admin", lang), admin_sections, index=0)
    else:
        ngo_sections = [
            t("sec_ngo_overview", lang),
            t("sec_ngo_available", lang),
            t("sec_ngo_search", lang),
            t("sec_ngo_request_pickup", lang),
            t("sec_ngo_my_requests", lang),
            t("sec_ngo_milestones", lang),
            t("sec_ngo_impact", lang)
        ]
        active_section = st.radio(t("sidebar_navigate_ngo", lang), ngo_sections, index=0)

# =========================================================
# ROLE-BASED DASHBOARD ROUTING (MODULAR ARCHITECTURE)
# =========================================================
if is_donor:
    st.markdown(render_brand_header(role_name=t("donor_portal_title", lang), lang=lang), unsafe_allow_html=True)
    render_donor_dashboard(user, lang, active_section, current_theme)
elif is_admin:
    st.markdown(render_brand_header(role_name=t("admin_portal_title", lang), lang=lang), unsafe_allow_html=True)
    render_admin_dashboard(user, lang, active_section, current_theme)
else:
    st.markdown(render_brand_header(role_name=t("ngo_portal_title", lang), lang=lang), unsafe_allow_html=True)
    render_ngo_dashboard(user, lang, active_section, current_theme)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown('<div style="text-align: center; color: #64748B; font-size: 0.85rem; padding: 10px 0;">🌾 <strong>AnnRakshak AI</strong> &bull; अन्न बचाओ, बर्बादी घटाओ। &bull; Predict demand. Prevent waste. Rescue surplus.<br>Built with Streamlit, SQLite (WAL & BEGIN IMMEDIATE), Plotly & Gemma 4 on Google Gen AI SDK.</div>', unsafe_allow_html=True)
