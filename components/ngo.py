"""
NGO & Food Recovery Portal UI Component for AnnRakshak AI.
Encapsulates all view sections for NGOs and Surplus Recovery Teams:
1. Dispatch Overview & Active Claims
2. Available Food Donations (geospatially sorted nearest-first via Haversine)
3. Search & Locality Filters
4. Submit Food Pickup Request Form (with atomic reservation and verification check)
5. My Pickup Requests (with contact unmasking for confirmed claims)
6. Collection & Delivery Status Milestones (per-request stepper)
7. NGO Recovery & Social Impact Summary
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import html

import workflow_manager as wm
import logistics
from i18n import t
from database import get_ist_now, IST
from ui_styles import (
    apply_plot_theme,
    render_metric_box,
    render_ngo_available_card,
    render_ngo_my_request_card,
    render_actionable_milestone_card
)

def render_ngo_dashboard(user: dict, lang: str, active_section: str, current_theme: str):
    # Active Organization Banner
    st.markdown(
        f"<div style='background: #1B4332; color: #FFFFFF; padding: 8px 18px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; display: inline-block;'>"
        f"🏢 {html.escape(user['org_name'])} &nbsp;|&nbsp; 🚚 {t('current_view_ngo', lang)}</div>",
        unsafe_allow_html=True
    )
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 1. NGO: OVERVIEW
    if active_section.startswith("1."):
        st.subheader("📊 " + ("NGO Food Rescue Dispatch Overview" if lang == "en" else "खाद्य राहत प्रेषण अवलोकन"))

        impact = wm.get_impact_summary()
        donations_df = wm.get_donations_df()
        all_requests_df = wm.get_pickup_requests_df()
        requests_df = all_requests_df[all_requests_df['ngo_id'] == user['org_id']] if not all_requests_df.empty else pd.DataFrame()

        # Top Metric Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(render_metric_box(t("m_avail_lots", lang), len(donations_df[donations_df['status'] == 'Available']), t("m_avail_lots_sub", lang)), unsafe_allow_html=True)
        with c2:
            avail_portions = int(donations_df[donations_df['status'] == 'Available']['available_portions'].sum()) if not donations_df.empty else 0
            st.markdown(render_metric_box(t("m_awaiting_rescue", lang), f"{avail_portions:,}", t("m_awaiting_rescue_sub", lang), "orange"), unsafe_allow_html=True)
        with c3:
            active_claims_count = len(requests_df[requests_df['request_status'].isin(['Requested', 'Confirmed'])]) if not requests_df.empty else 0
            st.markdown(render_metric_box(t("m_active_claims", lang), active_claims_count, t("m_active_claims_sub", lang), "blue"), unsafe_allow_html=True)
        with c4:
            st.markdown(render_metric_box(t("m_rescued_delivered", lang), f"{impact['portions_delivered']:,}", t("m_rescued_delivered_sub", lang)), unsafe_allow_html=True)

        st.markdown("---")

        # Visual Analytics
        c_ch1, c_ch2 = st.columns(2)
        with c_ch1:
            st.markdown("##### 📍 Available Portions by Locality")
            if not donations_df.empty and avail_portions > 0:
                loc_df = donations_df[donations_df['status'] == 'Available'].groupby('location')['available_portions'].sum().reset_index()
                fig_loc = px.bar(loc_df, x='location', y='available_portions', labels={'available_portions': 'Portions', 'location': 'Location'}, title="Surplus Meal Portions by Area")
                apply_plot_theme(fig_loc, current_theme).update_layout(margin=dict(t=30, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_loc, use_container_width=True)
            else:
                st.info("No active available portions to chart.")

        with c_ch2:
            st.markdown("##### 📦 Request Status Breakdown")
            if not requests_df.empty:
                r_counts = requests_df['request_status'].value_counts().reset_index()
                r_counts.columns = ['Status', 'Count']
                fig_r = px.pie(r_counts, names='Status', values='Count', hole=0.4)
                apply_plot_theme(fig_r, current_theme).update_layout(margin=dict(t=30, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_r, use_container_width=True)
            else:
                st.info("No pickup requests recorded.")

    # 2. NGO: AVAILABLE FOOD DONATIONS (Geospatially Optimized)
    elif active_section.startswith("2."):
        st.subheader("🍲 " + ("Available Food Donations for Rescue" if lang == "en" else "उपलब्ध भोजन सूचियां"))
        donations_df = wm.get_donations_df()

        avail_df = donations_df[(donations_df['status'] == 'Available') & (donations_df['available_portions'] > 0)]
        if avail_df.empty:
            st.info("No surplus food donations currently available. Check back soon!")
        else:
            user_ngo = wm.org_repo.get_ngo_by_id(user.get("org_id", "NGO-001"))
            ngo_lat = float(user_ngo["lat"]) if user_ngo and user_ngo.get("lat") else 25.4080
            ngo_lng = float(user_ngo["lng"]) if user_ngo and user_ngo.get("lng") else 81.8680

            st.caption(f"📍 Route optimization relative to your base: **{user.get('org_name', 'NGO')}** ({ngo_lat:.4f}°N, {ngo_lng:.4f}°E) | Average urban speed: 20 km/h")

            avail_records = avail_df.to_dict(orient="records")
            sorted_avail = logistics.sort_listings_by_distance(avail_records, viewer_lat=ngo_lat, viewer_lng=ngo_lng)

            for don in sorted_avail:
                try:
                    dead_str = don["pickup_deadline"].replace("T", " ")[:19]
                    dead_dt = datetime.strptime(dead_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
                    hrs_left = round(max(0.1, (dead_dt - get_ist_now()).total_seconds() / 3600.0), 1)
                except Exception:
                    hrs_left = 4.0
                st.markdown(render_ngo_available_card(don, hrs_left=hrs_left, lang=lang), unsafe_allow_html=True)

    # 3. NGO: SEARCH & FILTERS
    elif active_section.startswith("3."):
        st.subheader("🔍 Search & Filter Surplus Listings")
        donations_df = wm.get_donations_df()
        search_query = st.text_input("Search by meal name, event, or locality:", placeholder="e.g. Biryani, Civil Lines, Wedding")
        if search_query:
            matched = donations_df[
                donations_df['food_description'].str.contains(search_query, case=False, na=False) |
                donations_df['location'].str.contains(search_query, case=False, na=False) |
                donations_df['event_type'].str.contains(search_query, case=False, na=False)
            ]
            st.write(f"Found {len(matched)} matching listing(s):")
            st.dataframe(matched[['id', 'donor_name', 'event_type', 'food_description', 'available_portions', 'location', 'pickup_deadline', 'status']], use_container_width=True)
        else:
            st.dataframe(donations_df[['id', 'donor_name', 'event_type', 'food_description', 'available_portions', 'location', 'pickup_deadline', 'status']], use_container_width=True)

    # 4. NGO: REQUEST PICKUP FORM
    elif active_section.startswith("4."):
        st.subheader("🚀 " + ("Submit Food Pickup Request" if lang == "en" else "पिकअप का अनुरोध करें"))
        donations_df = wm.get_donations_df()
        avail_options = donations_df[(donations_df['status'] == 'Available') & (donations_df['available_portions'] > 0)]

        if avail_options.empty:
            st.warning("No listings currently have available portions to claim.")
        else:
            listing_choices = {f"{r['donor_name']} ({r['id']}) - {r['available_portions']} portions available": r['id'] for _, r in avail_options.iterrows()}
            selected_label = st.selectbox("Select Target Donation Listing *", options=list(listing_choices.keys()))
            chosen_don_id = listing_choices[selected_label]
            chosen_row = avail_options[avail_options['id'] == chosen_don_id].iloc[0]

            with st.form("request_form"):
                st.info(f"Submitting surplus recovery claim as: **{user['org_name']}** (ID: `{user['org_id']}`)")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    ngo_contact = st.text_input("Driver / Coordinator Contact *", value="+91-94500-11111 (seva@prayagdemo.org)")
                    portions_to_claim = st.number_input("Portions to Recover (Supports Partial Requests) *", min_value=1, max_value=int(chosen_row['available_portions']), value=min(30, int(chosen_row['available_portions'])))

                with col_r2:
                    proposed_time = st.text_input("Proposed Pickup Time (IST) *", value=(get_ist_now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))
                    req_notes = st.text_area("Transport & Logistics Notes", value="Electric van equipped with insulated crates ready for immediate dispatch.")

                req_submit = st.form_submit_button("Submit Pickup Request", use_container_width=True, type="primary")
                if req_submit:
                    ok, msg, req_id = wm.request_pickup(
                        donation_id=chosen_don_id,
                        ngo_contact=ngo_contact,
                        requested_portions=portions_to_claim,
                        proposed_pickup_time=proposed_time,
                        notes=req_notes,
                        acting_user=user
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # 5. NGO: MY PICKUP REQUESTS
    elif active_section.startswith("5."):
        st.subheader("📋 " + ("My Pickup Requests & Tracking" if lang == "en" else "मेरे पिकअप अनुरोध"))
        all_requests_df = wm.get_pickup_requests_df()
        my_requests = all_requests_df[all_requests_df['ngo_id'] == user['org_id']] if not all_requests_df.empty else pd.DataFrame()

        if my_requests.empty:
            st.info("No pickup requests submitted under this profile.")
        else:
            for _, req in my_requests.iterrows():
                req_dict = dict(req)
                req_dict['donor_contact'] = wm.get_contact_for(request_id=req['request_id'], acting_user=user)
                st.markdown(render_ngo_my_request_card(req_dict, lang=lang), unsafe_allow_html=True)

    # 6. NGO: COLLECTION & DELIVERY STATUS
    elif active_section.startswith("6."):
        st.subheader("🚚 " + ("Collection & Delivery Milestone Progress" if lang == "en" else "संग्रहण एवं वितरण स्थिति"))
        st.write("Progress confirmed pickup requests through the collection and safe delivery milestones.")

        all_requests_df = wm.get_pickup_requests_df()
        actionable_reqs = all_requests_df[
            (all_requests_df['ngo_id'] == user['org_id']) & 
            (all_requests_df['request_status'].isin(['Confirmed', 'Collected']))
        ] if not all_requests_df.empty else pd.DataFrame()

        if actionable_reqs.empty:
            st.info("No confirmed requests are currently pending collection or delivery for your organization.")
        else:
            for _, req in actionable_reqs.iterrows():
                with st.container():
                    req_dict = dict(req)
                    req_dict['donor_contact'] = wm.get_contact_for(request_id=req['request_id'], acting_user=user)
                    st.markdown(render_actionable_milestone_card(req_dict, lang=lang), unsafe_allow_html=True)
                    c_m1, c_m2 = st.columns(2)
                    if req['request_status'] == "Confirmed":
                        with c_m1:
                            if st.button(t("mark_collected_btn", lang), key=f"col_{req['request_id']}", use_container_width=True):
                                ok, msg = wm.update_request_status(request_id=req['request_id'], new_status="Collected", acting_user=user, remarks="Loaded onto NGO van")
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)
                    elif req['request_status'] == "Collected":
                        with c_m2:
                            if st.button(t("mark_delivered_btn", lang), key=f"del_{req['request_id']}", use_container_width=True):
                                ok, msg = wm.update_request_status(request_id=req['request_id'], new_status="Delivered", acting_user=user, remarks="Safely distributed to beneficiaries")
                                if ok:
                                    st.success(msg)
                                    st.rerun()
                                else:
                                    st.error(msg)

    # 7. NGO: IMPACT SUMMARY
    elif active_section.startswith("7."):
        st.subheader("🏅 NGO Recovery & Social Impact")
        impact = wm.get_impact_summary()
        donations_df = wm.get_donations_df()
        requests_df = wm.get_pickup_requests_df()
        history_df = wm.get_status_history_df()

        col_n1, col_n2, col_n3 = st.columns(3)
        with col_n1:
            st.metric("Total Requests Placed", f"{impact['total_requests']}")
            st.metric("Requests Confirmed", f"{impact['requests_confirmed']}")
        with col_n2:
            st.metric("Portions Rescued & Delivered", f"{impact['portions_delivered']:,}")
            st.metric("Food Rescued (kg)", f"{impact['kg_food_saved']:,} kg")
        with col_n3:
            st.metric("Estimated CO₂ Avoided", f"{impact['co2_avoided_kg']:,} kg CO₂")
            st.metric("Active Network Donors", f"{donations_df['donor_name'].nunique()}")

        st.markdown("---")
        st.markdown("#### 📥 NGO Operations Data Export (CSV Protected)")
        c_exp_n1, c_exp_n2 = st.columns(2)
        with c_exp_n1:
            st.download_button(
                "Export Requests CSV",
                data=wm.export_dataframe_to_csv_string(requests_df),
                file_name=f"ngo_recovery_log_{get_ist_now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c_exp_n2:
            st.download_button(
                "Export Full Audit History CSV",
                data=wm.export_dataframe_to_csv_string(history_df),
                file_name=f"ngo_audit_history_{get_ist_now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
