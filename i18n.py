"""
i18n.py - Internationalization & Translation Module for AnnRakshak AI.
Provides complete bilingual support (English and Hindi) for all UI components,
canonical workflow statuses, forms, metrics, and authentication controls.
"""

TRANSLATIONS = {
    "en": {
        # App Branding
        "app_name": "AnnRakshak AI",
        "tagline_hi": "अन्न बचाओ, बर्बादी घटाओ।",
        "tagline_en": "Predict demand. Prevent waste. Rescue surplus.",
        "demo_mode": "DEMO MODE • SAMPLE DATA",
        "demo_notice": "Demonstration Environment Notice: All organizations, donor events, phone numbers, and location addresses displayed in this system are fictional records seeded for hackathon demonstration.",
        "donor_portal_title": "Donor & Food Provider Portal",
        "ngo_portal_title": "NGO & Food Recovery Portal",
        "admin_portal_title": "System Administration Portal",
        "current_view_donor": "🌾 Current View: Donor Portal",
        "current_view_ngo": "🤝 Current View: NGO Recovery Portal",
        "current_view_admin": "🛡️ Current View: Admin Panel",
        "switch_to_ngo": "🤝 Switch to NGO Recovery View",
        "switch_to_donor": "🌾 Switch to Donor Portal",
        
        # Authentication & Role Access
        "auth_title": "🔐 Platform Authentication",
        "auth_select_role": "Select Login Persona:",
        "auth_pin_label": "Security PIN (Demo):",
        "auth_login_btn": "Sign In",
        "auth_logout_btn": "Sign Out",
        "auth_invalid_pin": "Invalid PIN. Demo credentials: Donor 1234 | NGO 5678 | Admin 9999",
        "auth_logged_in_as": "Signed in as: {role}",
        "donor_role_label": "🌾 Donor / Food Provider",
        "ngo_role_label": "🤝 NGO / Food Recovery",
        "admin_role_label": "🛡️ System Admin",

        # Sidebar & Navigation
        "sidebar_sections": "🧭 Dashboard Sections",
        "sidebar_navigate_donor": "Navigate Donor Portal:",
        "sidebar_navigate_ngo": "Navigate NGO Portal:",
        "sidebar_navigate_admin": "Navigate Admin Portal:",
        "ui_settings": "🎨 UI Setup & Language",
        "select_theme": "Choose Theme / UI Setup:",
        "select_lang": "Language / भाषा:",
        "theme_nature": "🌿 AnnRakshak Nature (Warm Forest)",
        "theme_dark": "🌙 Midnight Pro (Dark Obsidian)",
        "theme_navy": "🏛️ High-Contrast Daylight (Navy & Gold)",
        
        # Navigation Sections - Donor
        "sec_donor_overview": "1. Overview",
        "sec_donor_donate": "2. Donate Food",
        "sec_donor_my_donations": "3. My Donations",
        "sec_donor_ngo_requests": "4. NGO Pickup Requests",
        "sec_donor_waste_tracker": "5. Food Waste Tracker",
        "sec_donor_demand_pred": "6. Demand Prediction",
        "sec_donor_ai_insights": "7. Gemma 4 AI Insights",
        "sec_donor_impact": "8. Impact Summary",
        
        # Navigation Sections - NGO
        "sec_ngo_overview": "1. Overview",
        "sec_ngo_available": "2. Available Food Donations",
        "sec_ngo_search": "3. Search & Filters",
        "sec_ngo_request_pickup": "4. Request Pickup",
        "sec_ngo_my_requests": "5. My Pickup Requests",
        "sec_ngo_milestones": "6. Collection & Delivery Status",
        "sec_ngo_impact": "7. Impact Summary",

        # Navigation Sections - Admin
        "sec_admin_approvals": "1. NGO Verifications",
        "sec_admin_audit": "2. System Audit Trail",
        "sec_admin_reset": "3. Reset Database",
        
        # Canonical Workflow Statuses
        "status_available": "Available",
        "status_requested": "Requested",
        "status_confirmed": "Confirmed",
        "status_collected": "Collected",
        "status_delivered": "Delivered",
        "status_cancelled": "Cancelled",
        "status_rejected": "Rejected",
        "status_expired": "Expired",
        
        # Stepper Stages
        "step_1": "Available",
        "step_2": "Requested",
        "step_3": "Confirmed",
        "step_4": "Collected",
        "step_5": "Delivered",
        
        # Metrics - Donor
        "m_total_donations": "Total Donations Listed",
        "m_total_donations_sub": "Across all event categories",
        "m_portions_offered": "Portions Offered",
        "m_portions_offered_sub": "Standard meal portions",
        "m_pending_requests": "Active Requests",
        "m_pending_requests_sub": "Awaiting donor confirmation",
        "m_confirmed_pickups": "Confirmed Pickups",
        "m_confirmed_pickups_sub": "Coordinated with NGOs",
        "m_portions_collected": "Portions Collected",
        "m_portions_collected_sub": "Picked up by verified vans",
        "m_portions_delivered": "Portions Delivered",
        "m_portions_delivered_sub": "Distributed at shelters",
        "m_food_waste_rec": "Recorded Food Waste",
        "m_food_waste_sub": "Portions discarded",
        "m_discard_loss": "Estimated Discard Loss",
        "m_discard_loss_sub": "Direct ingredient cost",
        "m_kg_saved": "Food Rescued (kg)",
        "m_kg_saved_sub": "Based on 0.35 kg/portion avg",
        "m_co2_avoided": "Est. CO₂ Avoided (kg)",
        "m_co2_avoided_sub": "2.5 kg CO₂e per kg food saved",
        
        # Metrics - NGO
        "m_avail_lots": "Available Donation Lots",
        "m_avail_lots_sub": "Ready for immediate claim",
        "m_awaiting_rescue": "Meal Portions Awaiting Rescue",
        "m_awaiting_rescue_sub": "Portions ready for pickup",
        "m_active_claims": "My Active Pickup Requests",
        "m_active_claims_sub": "Submitted recovery requests",
        "m_rescued_delivered": "Portions Rescued & Delivered",
        "m_rescued_delivered_sub": "Verified at partner shelters",
        
        # Forms & Actions
        "load_wedding_demo": "✨ Load Wedding Demo (Sharma Wedding, 100 pax)",
        "load_bday_demo": "🎂 Load Birthday Demo (Verma Family, 30 pax)",
        "load_hotel_demo": "🏨 Hotel Buffet Surplus (50 pax)",
        "submit_donation_btn": "🚀 Submit Food Donation Listing",
        "save_waste_btn": "💾 Save Food Waste Record",
        "confirm_btn": "✅ Confirm Request",
        "reject_btn": "❌ Reject Request",
        "mark_collected_btn": "📦 Mark as Collected",
        "mark_delivered_btn": "🍲 Mark as Delivered",
        "run_ai_analysis_btn": "✨ Analyze Food Waste with Gemma 4",
        "run_prio_router_btn": "🚀 Run Priority Dispatch Router",
        
        # Card Labels
        "card_menu_items": "🍲 Menu Items:",
        "card_total": "Total:",
        "card_available": "Available Remaining:",
        "card_location": "Location:",
        "card_deadline": "Deadline:",
        "card_storage": "Storage:",
        "card_contact": "Contact:",
        "portions_unit": "portions",
        "hours_left": "h left",
        "window": "h window",
        "critical_pill": "🔥 CRITICAL",
        "urgent_pill": "⚡ URGENT",
        "normal_pill": "⏱️ NORMAL",
        "safety_window_label": "Food Safety Limit:",
        
        # Waste Tracker Form
        "w_header": "📉 Food Waste Tracker & Kitchen Audit",
        "w_sub": "Track prepared versus consumed quantities to calculate edible surplus, discarded waste, and direct financial loss.",
        "w_log_title": "➕ Log New Food Waste / Service Record",
        "w_provider": "Kitchen / Provider Name *",
        "w_date": "Audit Date *",
        "w_meal": "Meal Category *",
        "w_menu": "Menu Prepared *",
        "w_cost": "Cost Per Meal (₹) *",
        "w_prep": "Portions Prepared *",
        "w_cons": "Portions Consumed *",
        "w_edible": "Edible Surplus (Rescuable before spoilage) *",
        "w_disc": "Discarded Inedible Waste (Plate scraps / expired) *",
        "w_notes": "Operational Notes (Weather, RSVP drop, menu mismatch)",
        "w_balance_ok": "Audit Balance: {prep} Prepared = {cons} Consumed + {edible} Edible Surplus + {disc} Discarded Scraps",
        "w_mismatch": "Quantity Mismatch: Edible surplus ({edible}) + Discarded scraps ({disc}) = {sum_val}, which exceeds total unconsumed leftovers ({pool}). Reconcile before saving.",
        "w_unaccounted": "Unaccounted Leftovers: {diff} portions of {pool} unconsumed remain unaccounted for."
    },
    
    "hi": {
        # App Branding
        "app_name": "अन्नरक्षक AI",
        "tagline_hi": "अन्न बचाओ, बर्बादी घटाओ।",
        "tagline_en": "मांग का अनुमान लगाएं। बर्बादी रोकें। अधिशेष बचाएं।",
        "demo_mode": "डेमो मोड • नमूना डेटा",
        "demo_notice": "प्रदर्शन पर्यावरण सूचना: इस प्रणाली में प्रदर्शित सभी संगठन, दाता कार्यक्रम, फोन नंबर और स्थान पते हैकथॉन प्रदर्शन के लिए कल्पित रिकॉर्ड हैं।",
        "donor_portal_title": "भोजन प्रदाता एवं डोनर पोर्टल",
        "ngo_portal_title": "एनजीओ एवं खाद्य राहत पोर्टल",
        "admin_portal_title": "सिस्टम एडमिनिस्ट्रेशन पोर्टल",
        "current_view_donor": "🌾 वर्तमान दृश्य: डोनर पोर्टल",
        "current_view_ngo": "🤝 वर्तमान दृश्य: एनजीओ रिकवरी पोर्टल",
        "current_view_admin": "🛡️ वर्तमान दृश्य: एडमिन पैनल",
        "switch_to_ngo": "🤝 एनजीओ रिकवरी पोर्टल पर जाएं",
        "switch_to_donor": "🌾 डोनर पोर्टल पर जाएं",
        
        # Authentication & Role Access
        "auth_title": "🔐 प्लेटफॉर्म प्रमाणीकरण",
        "auth_select_role": "उपयोगकर्ता भूमिका चुनें:",
        "auth_pin_label": "सुरक्षा पिन (डेमो):",
        "auth_login_btn": "लॉग इन करें",
        "auth_logout_btn": "लॉग आउट करें",
        "auth_invalid_pin": "गलत पिन। डेमो क्रेडेंशियल्स: डोनर 1234 | एनजीओ 5678 | एडमिन 9999",
        "auth_logged_in_as": "लॉग इन: {role}",
        "donor_role_label": "🌾 भोजन प्रदाता / डोनर",
        "ngo_role_label": "🤝 एनजीओ / राहत संस्था",
        "admin_role_label": "🛡️ सिस्टम एडमिनिस्ट्रेटर",

        # Sidebar & Navigation
        "sidebar_sections": "🧭 डैशबोर्ड अनुभाग",
        "sidebar_navigate_donor": "डोनर पोर्टल नेविगेशन:",
        "sidebar_navigate_ngo": "एनजीओ पोर्टल नेविगेशन:",
        "sidebar_navigate_admin": "एडमिन पैनल नेविगेशन:",
        "ui_settings": "🎨 यूआई थीम एवं भाषा",
        "select_theme": "थीम / डिस्प्ले सेटअप चुनें:",
        "select_lang": "भाषा / Language:",
        "theme_nature": "🌿 अन्नरक्षक प्रकृति (वन हरा एवं क्रीम)",
        "theme_dark": "🌙 मिडनाइट प्रो (गहरा डार्क मोड)",
        "theme_navy": "🏛️ उच्च-कंट्रास्ट दिन (नेवी एवं केसरिया)",
        
        # Navigation Sections - Donor
        "sec_donor_overview": "1. डैशबोर्ड अवलोकन",
        "sec_donor_donate": "2. भोजन दान करें",
        "sec_donor_my_donations": "3. मेरी सूचियां व समन्वय",
        "sec_donor_ngo_requests": "4. एनजीओ पिकअप अनुरोध",
        "sec_donor_waste_tracker": "5. खाद्य बर्बादी ट्रैकर",
        "sec_donor_demand_pred": "6. मांग व तैयारी पूर्वानुमान",
        "sec_donor_ai_insights": "7. जेम्मा 4 एआई इनसाइट्स",
        "sec_donor_impact": "8. प्रभाव सारांश व रिपोर्ट",
        
        # Navigation Sections - NGO
        "sec_ngo_overview": "1. डैशबोर्ड अवलोकन",
        "sec_ngo_available": "2. उपलब्ध भोजन सूचियां",
        "sec_ngo_search": "3. खोज एवं फ़िल्टर",
        "sec_ngo_request_pickup": "4. पिकअप का अनुरोध करें",
        "sec_ngo_my_requests": "5. मेरे पिकअप अनुरोध",
        "sec_ngo_milestones": "6. संग्रहण एवं वितरण स्थिति",
        "sec_ngo_impact": "7. प्रभाव सारांश व रिपोर्ट",

        # Navigation Sections - Admin
        "sec_admin_approvals": "1. एनजीओ सत्यापन",
        "sec_admin_audit": "2. ऑडिट ट्रेल",
        "sec_admin_reset": "3. डेटाबेस रीसेट",
        
        # Canonical Workflow Statuses
        "status_available": "उपलब्ध",
        "status_requested": "अनुरोध प्राप्त",
        "status_confirmed": "स्वीकृत",
        "status_collected": "एकत्रित",
        "status_delivered": "सुरक्षित वितरित",
        "status_cancelled": "रद्द",
        "status_rejected": "अस्वीकृत",
        "status_expired": "समय समाप्त",
        
        # Stepper Stages
        "step_1": "उपलब्ध",
        "step_2": "अनुरोध प्राप्त",
        "step_3": "स्वीकृत",
        "step_4": "एकत्रित",
        "step_5": "वितरित",
        
        # Metrics - Donor
        "m_total_donations": "कुल सूचीबद्ध दान",
        "m_total_donations_sub": "सभी कार्यक्रम श्रेणियों में",
        "m_portions_offered": "प्रस्तावित भोजन हिस्से",
        "m_portions_offered_sub": "मानक भोजन थालियां",
        "m_pending_requests": "सक्रिय अनुरोध",
        "m_pending_requests_sub": "डोनर पुष्टि की प्रतीक्षा में",
        "m_confirmed_pickups": "पुष्ट किए गए पिकअप",
        "m_confirmed_pickups_sub": "एनजीओ के साथ समन्वित",
        "m_portions_collected": "एकत्रित भोजन हिस्से",
        "m_portions_collected_sub": "सत्यापित वाहनों द्वारा लोड",
        "m_portions_delivered": "वितरित भोजन हिस्से",
        "m_portions_delivered_sub": "आश्रयों व बस्तियों में वितरित",
        "m_food_waste_rec": "दर्ज खाद्य बर्बादी",
        "m_food_waste_sub": "फेंके गए भोजन हिस्से",
        "m_discard_loss": "अनुमानित वित्तीय नुकसान",
        "m_discard_loss_sub": "सीधी कच्ची सामग्री लागत",
        "m_kg_saved": "बचाया गया भोजन (किग्रा)",
        "m_kg_saved_sub": "औसत 0.35 किग्रा/थाली आधारित",
        "m_co2_avoided": "बचाया गया CO₂ (किग्रा)",
        "m_co2_avoided_sub": "2.5 किग्रा CO₂e प्रति किग्रा भोजन",
        
        # Metrics - NGO
        "m_avail_lots": "उपलब्ध दान लॉट",
        "m_avail_lots_sub": "तत्काल पिकअप हेतु तैयार",
        "m_awaiting_rescue": "बचाव हेतु भोजन हिस्से",
        "m_awaiting_rescue_sub": "पिकअप की प्रतीक्षा में हिस्से",
        "m_active_claims": "सक्रिय पिकअप अनुरोध",
        "m_active_claims_sub": "प्रस्तुत बचाव अनुरोध",
        "m_rescued_delivered": "बचाया व वितरित भोजन",
        "m_rescued_delivered_sub": "आश्रय स्थलों पर सत्यापित",
        
        # Forms & Actions
        "load_wedding_demo": "✨ विवाह डेमो भरें (शर्मा वेडिंग, 100 हिस्से)",
        "load_bday_demo": "🎂 जन्मदिन पार्टी डेमो (वर्मा परिवार, 30 हिस्से)",
        "load_hotel_demo": "🏨 होटल बुफे सरप्लस (50 हिस्से)",
        "submit_donation_btn": "🚀 भोजन दान सूची दर्ज करें",
        "save_waste_btn": "💾 खाद्य बर्बादी रिकॉर्ड सहेजें",
        "confirm_btn": "✅ अनुरोध स्वीकृत करें",
        "reject_btn": "❌ अनुरोध अस्वीकार करें",
        "mark_collected_btn": "📦 वाहन में लोड हुआ (Collected)",
        "mark_delivered_btn": "🍲 सुरक्षित वितरण संपन्न (Delivered)",
        "run_ai_analysis_btn": "✨ जेम्मा 4 द्वारा बर्बादी विश्लेषण करें",
        "run_prio_router_btn": "🚀 प्राथमिकता प्रेषण राउटर चलाएं",
        
        # Card Labels
        "card_menu_items": "🍲 मेनू व्यंजन:",
        "card_total": "कुल हिस्से:",
        "card_available": "शेष उपलब्ध:",
        "card_location": "स्थान / पता:",
        "card_deadline": "अंतिम समय:",
        "card_storage": "भंडारण विधि:",
        "card_contact": "संपर्क:",
        "portions_unit": "हिस्से",
        "hours_left": "घंटे शेष",
        "window": "घंटे की खिड़की",
        "critical_pill": "🔥 अति-महत्वपूर्ण (CRITICAL)",
        "urgent_pill": "⚡ जरूरी (URGENT)",
        "normal_pill": "⏱️ सामान्य (NORMAL)",
        "safety_window_label": "खाद्य सुरक्षा सीमा:",
        
        # Waste Tracker Form
        "w_header": "📉 खाद्य बर्बादी ट्रैकर एवं किचन ऑडिट",
        "w_sub": "तैयार और खपत किए गए भोजन की निगरानी करें, सरप्लस और वित्तीय नुकसान का सटीक हिसाब रखें।",
        "w_log_title": "➕ नया खाद्य बर्बादी / सेवा रिकॉर्ड दर्ज करें",
        "w_provider": "रसोई / प्रतिष्ठान का नाम *",
        "w_date": "ऑडिट तिथि *",
        "w_meal": "भोजन श्रेणी *",
        "w_menu": "तैयार किया गया मेनू *",
        "w_cost": "प्रति भोजन लागत (₹) *",
        "w_prep": "तैयार किए गए हिस्से (Portions) *",
        "w_cons": "खपत किए गए हिस्से (Portions) *",
        "w_edible": "बचा हुआ खाने योग्य भोजन (सरप्लस) *",
        "w_disc": "बर्बाद / अखाद्य कचरा (थाली का जूठन) *",
        "w_notes": "ऑपरेशनल नोट्स (मौसम, मेहमानों की संख्या में बदलाव, आदि)",
        "w_balance_ok": "लेखा संतुलन: {prep} तैयार = {cons} खपत + {edible} खाने योग्य सरप्लस + {disc} बर्बाद कचरा",
        "w_mismatch": "मात्रा असंतुलन: सरप्लस ({edible}) + कचरा ({disc}) = {sum_val}, जो कुल बचे हुए हिस्से ({pool}) से अधिक है। कृपया सही करें।",
        "w_unaccounted": "अनअकाउंटेड भोजन: कुल {pool} बचे हिस्सों में से {diff} का हिसाब दर्ज नहीं है।"
    }
}

def t(key: str, lang: str = "en", **kwargs) -> str:
    """Translates a string key into the specified language (default English)."""
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    text = lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
