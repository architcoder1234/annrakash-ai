"""
Admin Portal UI Component for AnnRakshak AI.
Encapsulates administrative controls:
1. NGO Partner Verification & Approvals
2. Immutable Audit Trail & Status History
3. Multi-Channel Notifications Stream (SMS, WhatsApp, Email logs)
4. Database Administration & Reset Utilities
"""

import streamlit as st
import pandas as pd
import workflow_manager as wm
from database import init_db
from notifications import notification_engine

def render_admin_dashboard(user: dict, lang: str, active_section: str, current_theme: str):
    # Active Organization Banner
    st.markdown(
        f"<div style='background: #1E293B; color: #FFFFFF; padding: 8px 18px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; display: inline-block;'>"
        f"🛡️ System Administrator Session &nbsp;|&nbsp; ⚙️ Admin Control Panel</div>",
        unsafe_allow_html=True
    )
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 1. ADMIN: NGO APPROVALS
    if active_section.startswith("1."):
        st.subheader("🛡️ NGO Verification & Approval Management")
        st.write("Review registered NGO partner credentials and grant verification for surplus food recovery.")

        ngos_df = wm.get_ngos_df()
        if not ngos_df.empty:
            for _, ngo in ngos_df.iterrows():
                with st.container():
                    c_n1, c_n2, c_n3 = st.columns([3, 2, 2])
                    with c_n1:
                        st.write(f"**{ngo['name']}**")
                        st.caption(f"Contact: {ngo.get('contact', 'N/A')} | Registered: {str(ngo['created_at'])[:10]}")
                    with c_n2:
                        is_v = bool(ngo['is_verified'])
                        v_badge = "<span class='badge-status badge-confirmed'>VERIFIED</span>" if is_v else "<span class='badge-status badge-requested'>PENDING APPROVAL</span>"
                        st.markdown(v_badge, unsafe_allow_html=True)
                    with c_n3:
                        if not is_v:
                            if st.button("✅ Approve NGO", key=f"app_{ngo['id']}", use_container_width=True):
                                ok, msg = wm.approve_ngo(acting_user=user, ngo_id=ngo['id'])
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                        else:
                            st.caption(f"Approved by: {ngo.get('approved_by', 'Admin')}")

                    st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
        else:
            st.info("No NGOs currently registered.")

    # 2. ADMIN: AUDIT TRAIL
    elif active_section.startswith("2."):
        st.subheader("📜 System Status History & Immutable Audit Trail")
        st.write("Tamper-proof event logs tracking every state transition across donations and requests.")
        history_df = wm.get_status_history_df()
        st.dataframe(history_df, use_container_width=True)

        st.markdown("---")
        st.subheader("📬 Multi-Channel Notification Dispatch Log")
        st.write("Records of all event notifications dispatched across SMS, WhatsApp, and Email channels.")
        notifs = notification_engine.list_notifications(limit=50)
        if notifs:
            notifs_df = pd.DataFrame(notifs)
            st.dataframe(notifs_df[['id', 'channel', 'event_type', 'recipient_id', 'title', 'status', 'created_at', 'sent_at']], use_container_width=True)
        else:
            st.info("No notifications dispatched yet.")

    # 3. ADMIN: RESET DATABASE
    elif active_section.startswith("3."):
        st.subheader("🔄 Database & Environment Administration")
        st.write("Reset database to clean seed state.")
        if st.button("Reset All Tables & Re-seed Fictional Data", type="primary"):
            init_db(force_reset=True)
            st.success("✅ Database reset complete.")
            st.rerun()
