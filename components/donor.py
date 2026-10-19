"""
Donor Portal UI Component for AnnRakshak AI.
Encapsulates all view sections for Food Providers & Donors:
1. Overview & Operational KPIs
2. Donate Food Form (with closed-fail food safety checks)
3. My Donation Listings & Stepper Progress
4. Incoming NGO Pickup Requests
5. Food Waste Tracker & Mass-Balance Kitchen Audit
6. Event Food Demand & Production Estimator (with P80 & MAPE backtesting)
7. Gemma 4 AI Waste Insights & Dispatch Prioritizer
8. Impact Summary & CSV Export Center
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import html

import workflow_manager as wm
import demand_predictor as dp
import ai_insights as ai
from i18n import t
from database import get_ist_now, format_ist_str, IST
from ui_styles import (
    apply_plot_theme,
    render_metric_box,
    render_donor_listing_card,
    render_ngo_request_card
)

def render_donor_dashboard(user: dict, lang: str, active_section: str, current_theme: str):
    # Active Organization Banner
    st.markdown(
        f"<div style='background: #1B4332; color: #FFFFFF; padding: 8px 18px; border-radius: 8px; font-size: 0.88rem; font-weight: 600; display: inline-block;'>"
        f"🏢 {html.escape(user['org_name'])} &nbsp;|&nbsp; 🌾 {t('current_view_donor', lang)}</div>",
        unsafe_allow_html=True
    )
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 1. DONOR: OVERVIEW
    if active_section.startswith("1."):
        st.subheader("📊 " + ("Donor Operations & Surplus Overview" if lang == "en" else "डोनर ऑपरेशंस एवं अधिशेष अवलोकन"))

        impact = wm.get_impact_summary()
        donations_df = wm.get_donations_df()
        requests_df = wm.get_pickup_requests_df()
        waste_df = wm.get_food_waste_df()

        # Top Metric Cards - 4 columns row 1
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(render_metric_box(t("m_total_donations", lang), impact['donations_listed'], t("m_total_donations_sub", lang)), unsafe_allow_html=True)
        with col2:
            st.markdown(render_metric_box(t("m_portions_offered", lang), f"{impact['portions_offered']:,}", t("m_portions_offered_sub", lang)), unsafe_allow_html=True)
        with col3:
            st.markdown(render_metric_box(t("m_pending_requests", lang), impact['requests_pending'], t("m_pending_requests_sub", lang), "orange"), unsafe_allow_html=True)
        with col4:
            st.markdown(render_metric_box(t("m_confirmed_pickups", lang), impact['requests_confirmed'], t("m_confirmed_pickups_sub", lang)), unsafe_allow_html=True)

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Environmental & Social Impact Metrics - Row 2
        col5, col6, col7, col8 = st.columns(4)
        with col5:
            st.markdown(render_metric_box(t("m_portions_delivered", lang), f"{impact['portions_delivered']:,}", t("m_portions_delivered_sub", lang)), unsafe_allow_html=True)
        with col6:
            st.markdown(render_metric_box(t("m_kg_saved", lang), f"{impact['kg_food_saved']:,} kg", t("m_kg_saved_sub", lang)), unsafe_allow_html=True)
        with col7:
            st.markdown(render_metric_box(t("m_co2_avoided", lang), f"{impact['co2_avoided_kg']:,} kg", t("m_co2_avoided_sub", lang)), unsafe_allow_html=True)
        with col8:
            st.markdown(render_metric_box("💧 Water Footprint Saved", f"{impact.get('water_saved_liters', 0):,} L", "FAO benchmark ~1000L/kg"), unsafe_allow_html=True)

        st.markdown("---")

        # Visual Analytics Charts
        st.markdown("#### 📈 Analytics & Trends" if lang == "en" else "#### 📈 रुझान एवं विश्लेषण")
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.markdown("##### 📌 Donation Status Distribution" if lang == "en" else "##### 📌 दान स्थिति वितरण")
            if not donations_df.empty:
                status_counts = donations_df['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                fig_status = px.pie(
                    status_counts,
                    names='Status',
                    values='Count',
                    color='Status',
                    color_discrete_map={
                        'Available': '#10B981',
                        'Requested': '#F59E0B',
                        'Confirmed': '#3B82F6',
                        'Collected': '#6366F1',
                        'Delivered': '#059669',
                        'Cancelled': '#94A3B8',
                        'Rejected': '#EF4444',
                        'Expired': '#6B7280'
                    },
                    hole=0.45
                )
                apply_plot_theme(fig_status, current_theme).update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No donation listings available yet.")

        with chart_col2:
            st.markdown("##### ⚖️ Portions Offered vs Collected vs Delivered" if lang == "en" else "##### ⚖️ प्रस्तावित vs लोड vs सुरक्षित वितरित भोजन")
            fig_bar = go.Figure(data=[
                go.Bar(name='Offered', x=['Donation Portions'], y=[impact['portions_offered']], marker_color='#1B4332'),
                go.Bar(name='Collected', x=['Donation Portions'], y=[impact['portions_collected']], marker_color='#3B82F6'),
                go.Bar(name='Delivered', x=['Donation Portions'], y=[impact['portions_delivered']], marker_color='#10B981')
            ])
            apply_plot_theme(fig_bar, current_theme).update_layout(barmode='group', margin=dict(t=30, b=10, l=10, r=10), height=300)
            st.plotly_chart(fig_bar, use_container_width=True)

    # 2. DONOR: DONATE FOOD FORM
    elif active_section.startswith("2."):
        st.subheader("🍲 " + ("Publish Surplus Food Donation" if lang == "en" else "अधिशेष भोजन दान सूची दर्ज करें"))
        st.write("List freshly prepared edible surplus food for verified NGO recovery within the safe distribution window.")

        # Preset Quick-Fill Demo Buttons
        st.markdown("##### ⚡ Quick-Fill Demonstration Presets:" if lang == "en" else "##### ⚡ त्वरित डेमो प्रीसेट:")
        p_c1, p_c2, p_c3 = st.columns(3)
        with p_c1:
            if st.button(t("load_wedding_demo", lang), use_container_width=True):
                st.session_state["d_name_val"] = "Sharma Wedding Events (Fictional Demo)"
                st.session_state["d_ev_val"] = "Wedding"
                st.session_state["d_desc_val"] = "Vegetable pulao, dal makhani, paneer butter masala, chapati and gulab jamun"
                st.session_state["d_qty_val"] = 120
                st.session_state["d_loc_val"] = "Civil Lines Banquet Lawn (Fictional Demo Locality), Prayagraj"
                st.session_state["d_stor_val"] = "Commercial insulated food warmers >65°C"
                st.session_state["d_cont_val"] = "+91-98765-11111"
        with p_c2:
            if st.button(t("load_bday_demo", lang), use_container_width=True):
                st.session_state["d_name_val"] = "Birthday Event Demo (Fictional Demo)"
                st.session_state["d_ev_val"] = "Birthday Party"
                st.session_state["d_desc_val"] = "Individual packed meal boxes (Veg fried rice, manchurian, fruit salad)"
                st.session_state["d_qty_val"] = 35
                st.session_state["d_loc_val"] = "Tagore Town Community Hall (Fictional Demo Locality), Prayagraj"
                st.session_state["d_stor_val"] = "Pre-sealed food-grade disposable containers"
                st.session_state["d_cont_val"] = "+91-98123-22222"
        with p_c3:
            if st.button(t("load_hotel_demo", lang), use_container_width=True):
                st.session_state["d_name_val"] = "Green Plate Demo Restaurant (Fictional Demo)"
                st.session_state["d_ev_val"] = "Restaurant"
                st.session_state["d_desc_val"] = "Prepared meal boxes (Jeera rice, yellow dal tadka, mix veg sabzi, phulkas)"
                st.session_state["d_qty_val"] = 40
                st.session_state["d_loc_val"] = "MG Marg Central Market (Fictional Demo Locality), Prayagraj"
                st.session_state["d_stor_val"] = "Hot holding food warmers in kitchen pantry"
                st.session_state["d_cont_val"] = "+91-97234-33333"

        with st.form("donation_entry_form"):
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                donor_name = st.text_input("Donor / Organization Name *", value=st.session_state.get("d_name_val", user.get("org_name", "Food Donor")))
                event_type = st.selectbox("Event Category *", ["Wedding", "Birthday Party", "Corporate Event", "Restaurant", "Hostel Mess", "Religious Gathering", "Other"])
                food_description = st.text_area("Food Items & Menu Description *", value=st.session_state.get("d_desc_val", "Vegetable Biryani, Dal Makhani, Paneer Butter Masala, Fresh Rotis"), height=80)
                quantity_portions = st.number_input("Estimated Quantity (Meal Portions) *", min_value=5, max_value=2000, value=st.session_state.get("d_qty_val", 80), step=10)
                safety_window = st.number_input("Food Safety Limit (Max hours since cooking) *", min_value=2.0, max_value=8.0, value=6.0, step=0.5, help="Standard FSSAI guideline for hot-held cooked food is 4 to 6 hours.")

            with col_d2:
                now_ist = get_ist_now()
                prep_datetime = st.text_input("Preparation Date & Time (IST) *", value=(now_ist - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))
                available_from = st.text_input("Available for Pickup From (IST) *", value=now_ist.strftime("%Y-%m-%d %H:%M:%S"))
                pickup_deadline = st.text_input("Strict Pickup Expiry Deadline (IST) *", value=(now_ist + timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S"))
                storage_info = st.text_input("Current Storage Condition *", value=st.session_state.get("d_stor_val", "Stored in commercial insulated warmers >65°C"))
                location = st.text_input("Pickup Address / Location *", value=st.session_state.get("d_loc_val", "Civil Lines Banquet Lawn (Fictional Demo Locality), Prayagraj"))
                private_contact = st.text_input("Private Donor Contact Phone *", value=st.session_state.get("d_cont_val", "+91-98765-11111"), help="🔒 Kept masked until an NGO request is Confirmed.")

            notes = st.text_area("Coordination Notes (Utensils, van access, parking instructions)", value="Please bring containers or crates for transfer.")

            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            submit_donation = st.form_submit_button(t("submit_donation_btn", lang), use_container_width=True)

            if submit_donation:
                ok, msg, don_id = wm.create_donation(
                    acting_user=user,
                    donor_name=donor_name,
                    event_type=event_type,
                    food_description=food_description,
                    quantity_portions=quantity_portions,
                    prep_datetime=prep_datetime,
                    available_from=available_from,
                    pickup_deadline=pickup_deadline,
                    storage_info=storage_info,
                    location=location,
                    private_contact=private_contact,
                    notes=notes,
                    food_safety_window_hours=safety_window
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # 3. DONOR: MY DONATIONS
    elif active_section.startswith("3."):
        st.subheader("📋 " + ("My Donation Listings & Coordination" if lang == "en" else "मेरी दान सूचियां एवं समन्वय"))
        st.write("Manage active listings, review real-time allocation status, and handle cancellation if needed.")

        donations_df = wm.get_donations_df()
        # Filter to donations belonging to logged in donor or show all if admin
        if user.get("role") == "donor" and user.get("org_id"):
            donations_df = donations_df[donations_df["donor_id"] == user["org_id"]]

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            all_statuses = list(donations_df['status'].unique()) if not donations_df.empty else []
            filter_status = st.multiselect("Filter by Status:", options=all_statuses, default=all_statuses)
        with col_f2:
            all_events = list(donations_df['event_type'].unique()) if not donations_df.empty else []
            filter_event = st.multiselect("Filter by Event Type:", options=all_events, default=all_events)

        filtered_df = donations_df
        if filter_status:
            filtered_df = filtered_df[filtered_df['status'].isin(filter_status)]
        if filter_event:
            filtered_df = filtered_df[filtered_df['event_type'].isin(filter_event)]

        st.markdown(f"**Showing {len(filtered_df)} listing(s):**")
        if filtered_df.empty:
            st.info("No donation listings match the selected filters.")
        else:
            for _, don in filtered_df.iterrows():
                st.markdown(render_donor_listing_card(don, lang=lang), unsafe_allow_html=True)
                
                # Associated pickup claims
                reqs = wm.request_repo.list_by_donation_id(don['id'])
                if reqs:
                    st.markdown(f"##### 🤝 Related NGO Pickup Requests ({len(reqs)})")
                    for req in reqs:
                        c_r1, c_r2 = st.columns([3, 1])
                        with c_r1:
                            st.write(f"**NGO:** {req['ngo_name']} | **Status:** `{req['status']}` | **Portions:** {req['requested_portions']} | **Time:** {req['proposed_pickup_time']}")
                        with c_r2:
                            if req['status'] == 'Requested':
                                if st.button(f"Confirm {req['id']}", key=f"conf_{req['id']}"):
                                    ok, m = wm.update_request_status(request_id=req['id'], new_status='Confirmed', acting_user=user)
                                    if ok: st.success(m); st.rerun()
                                    else: st.error(m)
                                if st.button(f"Reject {req['id']}", key=f"rej_{req['id']}"):
                                    ok, m = wm.update_request_status(request_id=req['id'], new_status='Rejected', acting_user=user)
                                    if ok: st.warning(m); st.rerun()
                                    else: st.error(m)

                # Cancellation option
                if don['status'] in ('Available', 'Requested', 'Confirmed'):
                    with st.expander(f"⚠️ Cancel Listing {don['id']}"):
                        reason = st.text_input(f"Cancellation Reason for {don['id']}:", key=f"cancel_reason_{don['id']}")
                        if st.button(f"Confirm Cancellation of {don['id']}", key=f"btn_cancel_{don['id']}", type="secondary"):
                            ok, msg = wm.cancel_donation(donation_id=don['id'], acting_user=user, reason=reason)
                            if ok:
                                st.warning(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                st.markdown("---")

    # 4. DONOR: NGO PICKUP REQUESTS
    elif active_section.startswith("4."):
        st.subheader("📬 " + ("NGO Pickup Requests & Claims" if lang == "en" else "एनजीओ पिकअप अनुरोध"))
        st.write("Review claims from verified non-profit partners and confirm food handover times.")

        requests_df = wm.get_pickup_requests_df()
        if user.get("role") == "donor" and user.get("org_id"):
            requests_df = requests_df[requests_df["donor_id"] == user["org_id"]]

        if requests_df.empty:
            st.info("No pickup requests currently pending for your listings.")
        else:
            for _, req in requests_df.iterrows():
                st.markdown(render_ngo_request_card(req, lang=lang), unsafe_allow_html=True)
                
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
                req_id = req["request_id"]
                req_status = req["request_status"]

                if req_status == "Requested":
                    with col_btn1:
                        if st.button("✅ " + t("btn_confirm_pickup", lang), key=f"btn_acc_{req_id}", type="primary"):
                            ok, msg = wm.update_request_status(request_id=req_id, new_status="Confirmed", acting_user=user, remarks="Donor confirmed handover schedule")
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    with col_btn2:
                        if st.button("❌ " + t("btn_reject", lang), key=f"btn_rej_{req_id}"):
                            ok, msg = wm.update_request_status(request_id=req_id, new_status="Rejected", acting_user=user, remarks="Portions allocated or kitchen unavailable")
                            if ok:
                                st.warning(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                elif req_status == "Confirmed":
                    st.info(f"Confirmed for pickup by {req['ngo_name']}. Awaiting NGO collection vehicle arrival.")
                st.markdown("---")

    # 5. DONOR: FOOD WASTE TRACKER & KITCHEN AUDIT
    elif active_section.startswith("5."):
        st.subheader("📉 " + ("Food Waste Tracker & Kitchen Audit" if lang == "en" else "खाद्य अपशिष्ट ट्रैकर एवं ऑडिट"))
        st.write("Track prepared versus consumed quantities to calculate edible surplus, discarded waste, and direct financial loss.")

        with st.expander("➕ Log New Food Waste / Service Record", expanded=False):
            with st.form("waste_log_form"):
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    w_provider = st.text_input("Kitchen / Provider Name *", value=user.get("org_name", "Banquet Kitchen"))
                    w_date = st.date_input("Audit Date *", value=datetime.today())
                    w_meal = st.selectbox("Meal Category *", ["Dinner", "Lunch", "Breakfast", "High Tea", "Buffet"])
                    w_items = st.text_input("Menu Prepared *", value="Dal Makhani, Pulao, Paneer, Naan")
                    w_cpm = st.number_input("Cost Per Meal (₹) *", min_value=10.0, value=150.0, step=10.0)

                with col_w2:
                    w_prep = st.number_input("Portions Prepared *", min_value=1, value=200, step=10)
                    w_cons = st.number_input("Portions Consumed *", min_value=0, value=170, step=10)
                    w_edible = st.number_input("Edible Surplus Portions (Salvageable) *", min_value=0, value=20, step=5)
                    w_disc = st.number_input("Discarded Waste Portions (Plate/Spoiled) *", min_value=0, value=10, step=5)
                    w_notes = st.text_input("Audit Notes", value="Rain impacted guest turnout")

                w_submit = st.form_submit_button("Record Kitchen Waste Audit", use_container_width=True)
                if w_submit:
                    ok, msg, _ = wm.log_food_waste(
                        acting_user=user,
                        provider_name=w_provider,
                        date=w_date.strftime("%Y-%m-%d"),
                        meal_type=w_meal,
                        menu_items=w_items,
                        portions_prepared=w_prep,
                        portions_consumed=w_cons,
                        edible_surplus=w_edible,
                        discarded_waste=w_disc,
                        cost_per_meal=w_cpm,
                        notes=w_notes
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

        waste_df = wm.get_food_waste_df()
        if not waste_df.empty:
            st.dataframe(waste_df[['date', 'provider_name', 'meal_type', 'portions_prepared', 'portions_consumed', 'edible_surplus', 'discarded_waste', 'cost_per_meal', 'financial_loss', 'notes']], use_container_width=True)
        else:
            st.info("No food waste records logged yet.")

    # 6. DONOR: DEMAND PREDICTION
    elif active_section.startswith("6."):
        st.subheader("🔮 " + ("Event Food Demand & Production Estimator" if lang == "en" else "मांग पूर्वानुमान एवं उत्पादन योजना"))
        st.write("Plan accurate food preparation based on historical consumption ratios, P80 confidence intervals, and configurable buffers.")

        # Formula Display
        st.markdown("##### 📐 Mathematical Formula:")
        st.latex(r"\text{Recommended Portions} = \left\lceil \text{Attendees} \times \text{Consumption Factor} \times \left(1 + \frac{\text{Clamped Buffer}\%}{100}\right) \right\rceil")
        st.caption("Buffer is strictly clamped between 0% and 50% to prevent reckless over-preparation.")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_event = st.selectbox("Event Category:", ["Wedding", "Birthday Party", "Corporate Event", "Restaurant", "Hostel Mess"])
            p_meal = st.selectbox("Target Meal Service:", ["Dinner", "Lunch", "Breakfast", "High Tea"])
            p_attendees = st.number_input("Expected Guest / Attendee Count *", min_value=1, max_value=5000, value=300, step=25)
            p_cost = st.number_input("Estimated Cost Per Meal (₹) *", min_value=10.0, value=220.0, step=10.0)
            p_buffer = st.slider("Safety Buffer Cushion (%):", min_value=0.0, max_value=50.0, value=8.0, step=1.0)

        with col_p2:
            waste_records = wm.get_food_waste_df().to_dict(orient='records')
            pred_res = dp.calculate_demand_estimate(
                event_type=p_event,
                meal_type=p_meal,
                expected_attendees=p_attendees,
                cost_per_meal=p_cost,
                safety_buffer_pct=p_buffer,
                historical_records=waste_records
            )

            rec_html = (
                f'<div class="ann-card" style="border: 1px solid #CBD5E1;">'
                f'<div class="ann-card-title">Recommended Preparation</div>'
                f'<div style="font-size: 2.5rem; font-weight: 800; color: #1B4332; margin: 10px 0;">'
                f'{pred_res["recommended_preparation"]} <span style="font-size: 1.2rem; font-weight: 400; color: #64748B;">meal portions</span></div>'
                f'<div style="font-size: 0.95rem; color: #334155; line-height: 1.6;">'
                f'&bull; <strong>Expected Attendance:</strong> {p_attendees} guests<br>'
                f'&bull; <strong>Estimated Net Demand:</strong> {pred_res["estimated_net_demand"]} portions<br>'
                f'&bull; <strong>Safety Buffer Reserve:</strong> {pred_res["safety_buffer_portions"]} portions ({pred_res["safety_buffer_pct"]}%)<br>'
                f'&bull; <strong>P80 Risk-Averse Bound (80th Percentile):</strong> {pred_res["p80_portions"]} portions (waste ratio: {pred_res["p80_waste_ratio"]*100:.1f}%)<br>'
                f'&bull; <strong>Expected Food Cost:</strong> ₹{pred_res["expected_total_cost"]:,.2f}<br>'
                f'&bull; <strong>Buffer Investment:</strong> ₹{pred_res["estimated_buffer_cost"]:,.2f}</div>'
                f'<div class="ann-footer-box" style="margin-top: 14px;">'
                f'ℹ️ <strong>Calculation Notes:</strong> {pred_res["methodology"]}</div>'
                f'</div>'
            )
            st.markdown(rec_html, unsafe_allow_html=True)

        st.caption(f"Calculated Formula: `{pred_res['formula_text']}`")

        # Backtest Validation Metric
        backtest_res = dp.backtest_model(waste_records)
        st.markdown(
            f"📈 **Historical Backtest Validation:** Mean Absolute Percentage Error (MAPE) = **{backtest_res['mape_pct']}%** "
            f"| Baseline Accuracy: **{backtest_res['accuracy_pct']}%** across {backtest_res['sample_count']} historical audit records."
        )

    # 7. DONOR: GEMMA 4 AI INSIGHTS
    elif active_section.startswith("7."):
        st.subheader("🧠 " + ("Gemma 4 AI Food Waste Insights & Intelligence" if lang == "en" else "जेम्मा 4 एआई खाद्य बर्बादी इनसाइट्स"))
        st.write("Leverage Google's open-weights Gemma 4 model via the official `google-genai` SDK to interpret kitchen logs, prioritize surplus collections, and formulate waste reduction strategies.")

        waste_records = wm.get_food_waste_df().to_dict(orient='records')
        
        tab_ai_waste, tab_ai_priority = st.tabs([
            "📊 Waste Trend Analysis & Recommendations" if lang == "en" else "📊 बर्बादी विश्लेषण एवं सिफारिशें",
            "🚨 Real-Time Surplus Dispatch Prioritizer" if lang == "en" else "🚨 प्राथमिकता प्रेषण राउटर"
        ])

        with tab_ai_waste:
            st.write("Synthesize kitchen logs across buffets, dinners, and events to isolate waste drivers.")
            if st.button("✨ " + t("run_ai_analysis_btn", lang), key="run_ai_btn_donor", type="primary"):
                with st.spinner("Analyzing historical records with Gemma 4..."):
                    report = ai.analyze_food_waste_with_gemma(
                        waste_records=waste_records,
                        model_name="gemma-4-26b-a4b-it",
                        lang=lang
                    )
                    st.session_state["cached_ai_report"] = report

            report = st.session_state.get("cached_ai_report")
            if report and report.get("success"):
                st.markdown(f'<div style="background: #ECFDF5; border: 1px solid #A7F3D0; padding: 12px 18px; border-radius: 8px; margin-bottom: 20px;"><strong>Engine Source:</strong> {report["source"]}<br><span style="font-size: 0.85rem; color: #065F46;">{report["food_safety_note"]}</span></div>', unsafe_allow_html=True)
                if report.get("is_live_gemma"):
                    st.markdown(report["raw_text"])
                else:
                    st.markdown("### 📋 Observations")
                    for obs in report["observations"]:
                        st.markdown(f"- {obs}")
                    st.markdown("### 💡 Practical Recommendations")
                    for rec in report["recommendations"]:
                        st.markdown(f"{rec}")

        with tab_ai_priority:
            st.write("Prioritize active surplus donations for vehicle routing.")
            donations = wm.get_donations_df().to_dict(orient='records')
            if st.button("🚀 " + t("run_prio_router_btn", lang), key="run_prio_btn_donor"):
                p_report = ai.prioritize_donations_with_gemma(donations, lang=lang)
                st.session_state["cached_prio_report"] = p_report

            p_report = st.session_state.get("cached_prio_report")
            if p_report and p_report.get("success"):
                st.info(p_report["dispatch_guidance"])
                for item in p_report["ranked_items"][:5]:
                    st.markdown(f"- **{item['donor_name']}**: {item.get('available_portions', 0)} portions | {item.get('hours_left', 0)}h remaining | Urgency Score: `{item.get('urgency_score', 0)}`")

    # 8. DONOR: IMPACT SUMMARY & CSV EXPORT
    elif active_section.startswith("8."):
        st.subheader("🏅 Donor Impact & Environmental Metrics")
        st.write("Measurable food recovery achievements recorded within the shared system.")

        impact = wm.get_impact_summary()
        donations_df = wm.get_donations_df()
        requests_df = wm.get_pickup_requests_df()
        waste_df = wm.get_food_waste_df()
        history_df = wm.get_status_history_df()

        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            st.metric("Total Food Portions Offered", f"{impact['portions_offered']:,}")
            st.metric("Food Rescued (kg)", f"{impact['kg_food_saved']:,} kg")
        with col_i2:
            st.metric("Portions Rescued & Delivered", f"{impact['portions_delivered']:,}")
            st.metric("Estimated CO₂ Avoided", f"{impact['co2_avoided_kg']:,} kg CO₂")
        with col_i3:
            st.metric("Kitchen Waste Portions Tracked", f"{impact['total_discarded_portions']:,}")
            st.metric("Estimated Water Saved", f"{impact.get('water_saved_liters', 0):,} Liters")

        st.caption("ℹ️ **Impact Criteria:** Standard 0.35 kg/portion avg and UNEP factor 2.5 kg CO₂e per kg food rescued; FAO benchmark 1000L water/kg food.")

        st.markdown("---")
        st.markdown("#### 📥 Data Export Center (CSV Injection Protected)")
        st.write("All cells starting with `=`, `+`, `-`, `@` are safely escaped.")

        col_exp1, col_exp2, col_exp3, col_exp4 = st.columns(4)
        with col_exp1:
            st.download_button(
                "Export Donations CSV",
                data=wm.export_dataframe_to_csv_string(donations_df),
                file_name=f"annrakshak_donations_{get_ist_now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp2:
            st.download_button(
                "Export Requests CSV",
                data=wm.export_dataframe_to_csv_string(requests_df),
                file_name=f"annrakshak_requests_{get_ist_now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp3:
            st.download_button(
                "Export Waste Logs CSV",
                data=wm.export_dataframe_to_csv_string(waste_df),
                file_name=f"annrakshak_waste_{get_ist_now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col_exp4:
            st.download_button(
                "Export Audit Trail CSV",
                data=wm.export_dataframe_to_csv_string(history_df),
                file_name=f"annrakshak_audit_{get_ist_now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
