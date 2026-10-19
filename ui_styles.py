"""
UI Styling, Themes, and Component Helpers for AnnRakshak AI.
WCAG 2.1 AA Compliant (>= 4.5:1 contrast for normal body text).
Supports multiple high-contrast UI setups:
- Nature Theme (Warm Forest & Cream)
- Midnight Pro (Dark Obsidian & Emerald Glow)
- High-Contrast Daylight (Executive Royal Navy & Gold)
Fully integrated with canonical workflow statuses and i18n translation system.
"""

from i18n import t
import html

THEMES = {
    "nature": {
        "name": "🌿 AnnRakshak Nature (Warm Forest)",
        "label": "🌿 AnnRakshak Nature (Warm Forest)",
        "plotly_template": "plotly_white",
        "bg_paper": "#FFFFFF",
        "bg_plot": "#FFFFFF",
        "font_color": "#0F172A",
        "grid_color": "#F1F5F9"
    },
    "dark": {
        "name": "🌙 Midnight Pro (Dark Obsidian)",
        "label": "🌙 Midnight Pro (Dark Obsidian)",
        "plotly_template": "plotly_dark",
        "bg_paper": "#151E2E",
        "bg_plot": "#151E2E",
        "font_color": "#F8FAFC",
        "grid_color": "#1E293B"
    },
    "navy": {
        "name": "🏛️ High-Contrast Daylight (Navy & Gold)",
        "label": "🏛️ High-Contrast Daylight (Navy & Gold)",
        "plotly_template": "plotly_white",
        "bg_paper": "#FFFFFF",
        "bg_plot": "#FFFFFF",
        "font_color": "#020617",
        "grid_color": "#E2E8F0"
    }
}

def get_theme_css(theme_key: str = "nature") -> str:
    """Returns dynamic CSS matching the requested theme setup with strict contrast compliance."""
    if theme_key == "dark":
        # Midnight Pro Theme (Dark Mode)
        return """
<style>
/* ========================================================= */
/* THEME: MIDNIGHT PRO (DARK OBSIDIAN / HIGH-CONTRAST OLED) */
/* ========================================================= */
:root {
    --bg-canvas: #0B0F19;
    --bg-card: #151E2E;
    --border-color: #334155;
    --text-primary: #F8FAFC;
    --text-secondary: #CBD5E1;
    --text-muted: #CBD5E1;
    --primary-color: #10B981;
    --primary-hover: #059669;
    --accent-color: #38BDF8;
    --accent-amber: #F59E0B;
}

/* Hide deploy toolbar and prevent overlap */
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

.stApp {
    background-color: #0B0F19 !important;
    color: #F8FAFC !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.stApp p, .stApp span, .stApp div, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span {
    color: #F1F5F9;
}

h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithAnchor"] h1,
[data-testid="stHeadingWithAnchor"] h2,
[data-testid="stHeadingWithAnchor"] h3,
[data-testid="stHeadingWithAnchor"] h4 {
    color: #F8FAFC !important;
    font-weight: 700 !important;
}

label, 
[data-testid="stWidgetLabel"], 
[data-testid="stWidgetLabel"] p, 
[data-testid="stWidgetLabel"] span {
    color: #F8FAFC !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}

code {
    color: #67E8F9 !important;
    background-color: #1E293B !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
}

input, textarea, select {
    color: #FFFFFF !important;
    background-color: #1E293B !important;
    border: 1.5px solid #475569 !important;
    border-radius: 8px !important;
}

[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #1E293B !important;
    border: 1.5px solid #475569 !important;
    border-radius: 8px !important;
}

[data-baseweb="input"] input, [data-baseweb="base-input"] input {
    background-color: #1E293B !important;
    color: #FFFFFF !important;
}

div[data-baseweb="select"] > div {
    background-color: #1E293B !important;
    color: #FFFFFF !important;
    border: 1.5px solid #475569 !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] * {
    color: #FFFFFF !important;
}

.brand-header-box {
    background-color: #064E3B !important;
    background-image: linear-gradient(135deg, #064E3B 0%, #065F46 100%) !important;
    border-radius: 12px !important;
    padding: 22px 28px !important;
    margin-bottom: 18px !important;
    border: 1px solid #10B981 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
}
.brand-title { color: #FFFFFF !important; font-size: 1.85rem !important; font-weight: 800 !important; }
.brand-title * { color: #FFFFFF !important; }
.brand-tagline-hi { color: #A7F3D0 !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.brand-tagline-en { color: #D1FAE5 !important; font-size: 0.92rem !important; }

.demo-mode-pill {
    background: #F59E0B !important;
    color: #000000 !important;
    font-weight: 800 !important;
    padding: 5px 14px !important;
    border-radius: 20px !important;
    font-size: 0.78rem !important;
    display: inline-block !important;
}

.fictional-notice-bar {
    background-color: #1E293B !important;
    border-left: 4px solid #F59E0B !important;
    color: #F1F5F9 !important;
    padding: 10px 16px !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    margin-bottom: 20px !important;
}

.metric-box {
    background: #151E2E !important;
    border-radius: 10px !important;
    padding: 16px !important;
    border: 1px solid #334155 !important;
    border-top: 4px solid #10B981 !important;
    margin-bottom: 12px !important;
}
.metric-box-blue { border-top-color: #38BDF8 !important; }
.metric-box-orange { border-top-color: #F59E0B !important; }
.metric-box-purple { border-top-color: #A855F7 !important; }
.metric-label { font-size: 0.78rem !important; text-transform: uppercase !important; font-weight: 700 !important; color: #CBD5E1 !important; }
.metric-value { font-size: 1.75rem !important; font-weight: 800 !important; color: #F8FAFC !important; margin: 4px 0 !important; }
.metric-sub { font-size: 0.8rem !important; color: #E2E8F0 !important; }

.ann-card {
    background-color: #151E2E !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    padding: 18px !important;
    margin-bottom: 16px !important;
}
.ann-card-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-bottom: 1px solid #334155 !important;
    padding-bottom: 10px !important;
    margin-bottom: 12px !important;
}
.ann-card-title { font-size: 1.15rem !important; font-weight: 700 !important; color: #F8FAFC !important; }
.ann-card-id { font-size: 0.82rem !important; color: #CBD5E1 !important; margin-left: 8px !important; }
.ann-card-body { font-size: 0.95rem !important; color: #F1F5F9 !important; line-height: 1.5 !important; margin-bottom: 12px !important; }

.ann-pills-row { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; margin-bottom: 12px !important; }
.ann-meta-pill {
    background-color: #1E293B !important;
    color: #F1F5F9 !important;
    padding: 4px 10px !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    border: 1px solid #334155 !important;
}
.ann-meta-pill-success { background-color: #064E3B !important; color: #A7F3D0 !important; border-color: #059669 !important; }
.ann-meta-pill-warning { background-color: #78350F !important; color: #FDE68A !important; border-color: #D97706 !important; }

.ann-footer-box {
    background-color: #0B0F19 !important;
    border: 1px solid #1E293B !important;
    padding: 10px 14px !important;
    border-radius: 6px !important;
    font-size: 0.84rem !important;
    color: #E2E8F0 !important;
}
.ann-footer-box * {
    color: #E2E8F0 !important;
}

.stepper-container { margin: 14px 0 16px 0 !important; }
.step-item { display: flex !important; flex-direction: column !important; align-items: center !important; font-size: 0.75rem !important; font-weight: 600 !important; color: #CBD5E1 !important; }
.step-item.active { color: #38BDF8 !important; }
.step-item.completed { color: #10B981 !important; }
.step-circle {
    width: 26px !important;
    height: 26px !important;
    border-radius: 50% !important;
    background-color: #1E293B !important;
    border: 2px solid #475569 !important;
    color: #CBD5E1 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
}
.step-item.active .step-circle { background-color: #0284C7 !important; border-color: #38BDF8 !important; color: #FFFFFF !important; }
.step-item.completed .step-circle { background-color: #059669 !important; border-color: #10B981 !important; color: #FFFFFF !important; }
.step-divider { flex: 1 !important; height: 2px !important; background-color: #334155 !important; margin: 0 6px 16px 6px !important; }
.step-divider.completed { background-color: #10B981 !important; }

/* Status Badges */
.badge-available { background-color: #064E3B; color: #A7F3D0; border: 1px solid #059669; }
.badge-requested { background-color: #78350F; color: #FDE68A; border: 1px solid #D97706; }
.badge-confirmed { background-color: #1E3A8A; color: #BFDBFE; border: 1px solid #3B82F6; }
.badge-collected { background-color: #312E81; color: #C7D2FE; border: 1px solid #6366F1; }
.badge-delivered { background-color: #064E3B; color: #6EE7B7; border: 1px solid #10B981; }
.badge-cancelled { background-color: #334155; color: #CBD5E1; border: 1px solid #475569; }
.badge-rejected { background-color: #7F1D1D; color: #FECACA; border: 1px solid #EF4444; }
.badge-expired { background-color: #1F2937; color: #E2E8F0; border: 1px solid #4B5563; }

div.stButton > button, .stFormSubmitButton > button {
    background-color: #059669 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 10px 18px !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    min-width: 140px !important;
    line-height: 1.35 !important;
    text-align: center !important;
}
div.stButton > button *, .stFormSubmitButton > button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}
div.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #10B981 !important;
}
div.stButton > button[kind="secondary"], .stFormSubmitButton > button[kind="secondary"] {
    background-color: #1E293B !important;
    border: 1px solid #475569 !important;
}
div.stButton > button[kind="secondary"] *, .stFormSubmitButton > button[kind="secondary"] * {
    color: #F8FAFC !important;
    fill: #F8FAFC !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarNav"] {
    background-color: #070A10 !important;
    border-right: 1px solid #1E293B !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] caption,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #1E293B !important;
    color: #FFFFFF !important;
    border: 1.5px solid #475569 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #FFFFFF !important;
}
</style>
"""

    elif theme_key == "navy":
        # High-Contrast Daylight (Navy & Gold / Executive High Contrast)
        return """
<style>
/* ========================================================= */
/* THEME: HIGH-CONTRAST DAYLIGHT (NAVY & GOLD / WCAG AA)    */
/* ========================================================= */
:root {
    --bg-canvas: #FFFFFF;
    --bg-card: #FFFFFF;
    --border-color: #CBD5E1;
    --text-primary: #020617;
    --text-secondary: #1E293B;
    --text-muted: #475569;
    --primary-color: #0A192F;
    --primary-hover: #1E3A8A;
    --accent-color: #854D0E; /* Darkened Gold for 6.8:1 contrast */
}

/* Hide deploy toolbar and prevent overlap */
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

.stApp {
    background-color: #FFFFFF !important;
    color: #020617 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.stApp p, .stApp span, .stApp div, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span {
    color: #0F172A;
}

h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithAnchor"] h1,
[data-testid="stHeadingWithAnchor"] h2,
[data-testid="stHeadingWithAnchor"] h3,
[data-testid="stHeadingWithAnchor"] h4 {
    color: #0A192F !important;
    font-weight: 800 !important;
}

label, 
[data-testid="stWidgetLabel"], 
[data-testid="stWidgetLabel"] p, 
[data-testid="stWidgetLabel"] span {
    color: #0A192F !important;
    font-weight: 800 !important;
    font-size: 0.94rem !important;
}

code {
    color: #0A192F !important;
    background-color: #F1F5F9 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border: 1px solid #CBD5E1 !important;
    font-weight: 700 !important;
}

input, textarea, select {
    color: #000000 !important;
    background-color: #FFFFFF !important;
    border: 2px solid #0A192F !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #FFFFFF !important;
    border: 2px solid #0A192F !important;
    border-radius: 6px !important;
}

[data-baseweb="input"] input, [data-baseweb="base-input"] input {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    font-weight: 600 !important;
}

div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #000000 !important;
    border: 2px solid #0A192F !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
}

div[data-baseweb="select"] * {
    color: #000000 !important;
}

.brand-header-box {
    background: #0A192F !important;
    border-radius: 8px !important;
    padding: 22px 28px !important;
    margin-bottom: 18px !important;
    border: 2px solid #020617 !important;
}
.brand-title { color: #FFFFFF !important; font-size: 1.85rem !important; font-weight: 900 !important; }
.brand-title * { color: #FFFFFF !important; }
.brand-tagline-hi { color: #FEF08A !important; font-size: 1.05rem !important; font-weight: 700 !important; }
.brand-tagline-en { color: #E2E8F0 !important; font-size: 0.92rem !important; font-weight: 600 !important; }

.demo-mode-pill {
    background: #FEF08A !important;
    color: #000000 !important;
    font-weight: 900 !important;
    padding: 5px 14px !important;
    border-radius: 4px !important;
    font-size: 0.8rem !important;
    border: 2px solid #854D0E !important;
    display: inline-block !important;
}

.fictional-notice-bar {
    background-color: #F8FAFC !important;
    border-left: 6px solid #854D0E !important;
    border: 1px solid #CBD5E1 !important;
    border-left-width: 6px !important;
    color: #020617 !important;
    padding: 10px 16px !important;
    border-radius: 4px !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    margin-bottom: 20px !important;
}

.metric-box {
    background: #FFFFFF !important;
    border-radius: 6px !important;
    padding: 16px !important;
    border: 2px solid #0A192F !important;
    margin-bottom: 12px !important;
}
.metric-box-blue { border-top: 5px solid #0A192F !important; }
.metric-box-orange { border-top: 5px solid #854D0E !important; }
.metric-box-purple { border-top: 5px solid #4338CA !important; }
.metric-label { font-size: 0.8rem !important; text-transform: uppercase !important; font-weight: 800 !important; color: #0A192F !important; }
.metric-value { font-size: 1.85rem !important; font-weight: 900 !important; color: #000000 !important; margin: 4px 0 !important; }
.metric-sub { font-size: 0.82rem !important; color: #1E293B !important; font-weight: 600 !important; }

.ann-card {
    background-color: #FFFFFF !important;
    border: 2px solid #0A192F !important;
    border-radius: 6px !important;
    padding: 18px !important;
    margin-bottom: 16px !important;
}
.ann-card-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-bottom: 2px solid #CBD5E1 !important;
    padding-bottom: 10px !important;
    margin-bottom: 12px !important;
}
.ann-card-title { font-size: 1.2rem !important; font-weight: 800 !important; color: #0A192F !important; }
.ann-card-id { font-size: 0.84rem !important; color: #1E293B !important; font-weight: 600 !important; margin-left: 8px !important; }
.ann-card-body { font-size: 0.95rem !important; color: #000000 !important; line-height: 1.5 !important; font-weight: 500 !important; margin-bottom: 12px !important; }

.ann-pills-row { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; margin-bottom: 12px !important; }
.ann-meta-pill {
    background-color: #F8FAFC !important;
    color: #020617 !important;
    padding: 4px 10px !important;
    border-radius: 4px !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    border: 1.5px solid #0A192F !important;
}
.ann-meta-pill-success { background-color: #DCFCE7 !important; color: #064E3B !important; border-color: #047857 !important; }
.ann-meta-pill-warning { background-color: #FEF3C7 !important; color: #78350F !important; border-color: #854D0E !important; }

.ann-footer-box {
    background-color: #F1F5F9 !important;
    border: 1px solid #CBD5E1 !important;
    padding: 10px 14px !important;
    border-radius: 4px !important;
    font-size: 0.86rem !important;
    color: #0F172A !important;
    font-weight: 600 !important;
}
.ann-footer-box * {
    color: #0F172A !important;
}

.stepper-container { margin: 14px 0 16px 0 !important; }
.step-item { display: flex !important; flex-direction: column !important; align-items: center !important; font-size: 0.78rem !important; font-weight: 700 !important; color: #334155 !important; }
.step-item.active { color: #0A192F !important; }
.step-item.completed { color: #064E3B !important; }
.step-circle {
    width: 28px !important;
    height: 28px !important;
    border-radius: 50% !important;
    background-color: #F8FAFC !important;
    border: 2px solid #0A192F !important;
    color: #0A192F !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: 800 !important;
    margin-bottom: 4px !important;
}
.step-item.active .step-circle { background-color: #0A192F !important; color: #FFFFFF !important; }
.step-item.completed .step-circle { background-color: #047857 !important; color: #FFFFFF !important; border-color: #047857 !important; }
.step-divider { flex: 1 !important; height: 3px !important; background-color: #CBD5E1 !important; margin: 0 6px 16px 6px !important; }
.step-divider.completed { background-color: #047857 !important; }

/* Status Badges */
.badge-available { background-color: #DCFCE7; color: #064E3B; border: 2px solid #047857; }
.badge-requested { background-color: #FEF3C7; color: #78350F; border: 2px solid #854D0E; }
.badge-confirmed { background-color: #DBEAFE; color: #1E3A8A; border: 2px solid #1D4ED8; }
.badge-collected { background-color: #E0E7FF; color: #3730A3; border: 2px solid #4338CA; }
.badge-delivered { background-color: #D1FAE5; color: #064E3B; border: 2px solid #059669; }
.badge-cancelled { background-color: #F1F5F9; color: #1E293B; border: 2px solid #64748B; }
.badge-rejected { background-color: #FEE2E2; color: #991B1B; border: 2px solid #DC2626; }
.badge-expired { background-color: #E2E8F0; color: #1E293B; border: 2px solid #475569; }

div.stButton > button, .stFormSubmitButton > button {
    background-color: #0A192F !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    border-radius: 6px !important;
    border: none !important;
    padding: 10px 18px !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    min-width: 140px !important;
    line-height: 1.35 !important;
    text-align: center !important;
}
div.stButton > button *, .stFormSubmitButton > button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}
div.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #1E3A8A !important;
}
div.stButton > button[kind="secondary"], .stFormSubmitButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 2px solid #0A192F !important;
}
div.stButton > button[kind="secondary"] *, .stFormSubmitButton > button[kind="secondary"] * {
    color: #0A192F !important;
    fill: #0A192F !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarNav"] {
    background-color: #0A192F !important;
    border-right: 2px solid #020617 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] caption,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #FFFFFF !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #FFFFFF !important;
    font-weight: 800 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #1E3A8A !important;
    color: #FFFFFF !important;
    border: 1.5px solid #60A5FA !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #FFFFFF !important;
}
</style>
"""

    else:
        # Default: AnnRakshak Nature (Warm Forest & Cream)
        return """
<style>
/* ========================================================= */
/* THEME: ANNRAKSHAK NATURE (WARM FOREST & CREAM / WCAG AA) */
/* ========================================================= */
:root {
    --bg-canvas: #FBF9F4;
    --bg-card: #FFFFFF;
    --border-color: #E2E8F0;
    --text-primary: #0F172A;
    --text-secondary: #334155;
    --text-muted: #475569;
    --primary-color: #1B4332;
    --primary-hover: #2D6A4F;
    --accent-color: #A23B20; /* Darkened Terracotta for 6.6:1 contrast */
}

/* Hide deploy toolbar and prevent overlap */
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

.stApp {
    background-color: #FBF9F4 !important;
    color: #0F172A !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.stApp p, .stApp span, .stApp div, [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span {
    color: #0F172A;
}

h1, h2, h3, h4, h5, h6,
[data-testid="stHeadingWithAnchor"] h1,
[data-testid="stHeadingWithAnchor"] h2,
[data-testid="stHeadingWithAnchor"] h3,
[data-testid="stHeadingWithAnchor"] h4 {
    color: #1B4332 !important;
    font-weight: 800 !important;
}

label, 
[data-testid="stWidgetLabel"], 
[data-testid="stWidgetLabel"] p, 
[data-testid="stWidgetLabel"] span {
    color: #1B4332 !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
}

code {
    color: #1B4332 !important;
    background-color: #F1F5F9 !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
    border: 1px solid #CBD5E1 !important;
    font-weight: 700 !important;
}

input, textarea, select {
    color: #0F172A !important;
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
}

[data-baseweb="input"], [data-baseweb="base-input"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
}

[data-baseweb="input"] input, [data-baseweb="base-input"] input {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
}

div[data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #0F172A !important;
    border: 1.5px solid #CBD5E1 !important;
    border-radius: 8px !important;
}

div[data-baseweb="select"] * {
    color: #0F172A !important;
}

.brand-header-box {
    background-color: #1B4332 !important;
    background-image: linear-gradient(135deg, #1B4332 0%, #2D6A4F 100%) !important;
    border-radius: 12px !important;
    padding: 22px 28px !important;
    margin-bottom: 18px !important;
    border: 1px solid #1B4332 !important;
    box-shadow: 0 4px 14px rgba(27, 67, 50, 0.15) !important;
}
.brand-title { color: #FFFFFF !important; font-size: 1.85rem !important; font-weight: 800 !important; }
.brand-title * { color: #FFFFFF !important; }
.brand-tagline-hi { color: #D8F3DC !important; font-size: 1.05rem !important; font-weight: 600 !important; }
.brand-tagline-en { color: #F1FAEE !important; font-size: 0.92rem !important; }

.demo-mode-pill {
    background: #FEF3C7 !important;
    color: #78350F !important;
    font-weight: 800 !important;
    padding: 5px 14px !important;
    border-radius: 20px !important;
    font-size: 0.78rem !important;
    border: 1px solid #FCD34D !important;
    display: inline-block !important;
}

.fictional-notice-bar {
    background-color: #FFFBEB !important;
    border-left: 5px solid #D97706 !important;
    color: #78350F !important;
    padding: 10px 16px !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
    margin-bottom: 20px !important;
    border: 1px solid #FDE68A !important;
    border-left-width: 5px !important;
}

.metric-box {
    background: #FFFFFF !important;
    border-radius: 10px !important;
    padding: 16px !important;
    border: 1px solid #E2E8F0 !important;
    border-top: 4px solid #1B4332 !important;
    margin-bottom: 12px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
}
.metric-box-blue { border-top-color: #2563EB !important; }
.metric-box-orange { border-top-color: #D97706 !important; }
.metric-box-purple { border-top-color: #7C3AED !important; }
.metric-label { font-size: 0.78rem !important; text-transform: uppercase !important; font-weight: 700 !important; color: #475569 !important; }
.metric-value { font-size: 1.75rem !important; font-weight: 800 !important; color: #0F172A !important; margin: 4px 0 !important; }
.metric-sub { font-size: 0.8rem !important; color: #334155 !important; }

.ann-card {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    padding: 18px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
}
.ann-card-header {
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-bottom: 1px solid #F1F5F9 !important;
    padding-bottom: 10px !important;
    margin-bottom: 12px !important;
}
.ann-card-title { font-size: 1.15rem !important; font-weight: 700 !important; color: #0F172A !important; }
.ann-card-id { font-size: 0.82rem !important; color: #334155 !important; margin-left: 8px !important; }
.ann-card-body { font-size: 0.95rem !important; color: #1E293B !important; line-height: 1.5 !important; margin-bottom: 12px !important; }

.ann-pills-row { display: flex !important; flex-wrap: wrap !important; gap: 8px !important; margin-bottom: 12px !important; }
.ann-meta-pill {
    background-color: #F8FAFC !important;
    color: #1E293B !important;
    padding: 4px 10px !important;
    border-radius: 6px !important;
    font-size: 0.82rem !important;
    border: 1px solid #CBD5E1 !important;
}
.ann-meta-pill-success { background-color: #ECFDF5 !important; color: #065F46 !important; border-color: #A7F3D0 !important; }
.ann-meta-pill-warning { background-color: #FFFBEB !important; color: #92400E !important; border-color: #FDE68A !important; }

.ann-footer-box {
    background-color: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    padding: 10px 14px !important;
    border-radius: 6px !important;
    font-size: 0.84rem !important;
    color: #1E293B !important;
}
.ann-footer-box * {
    color: #1E293B !important;
}

.stepper-container { margin: 14px 0 16px 0 !important; }
.step-item { display: flex !important; flex-direction: column !important; align-items: center !important; font-size: 0.75rem !important; font-weight: 600 !important; color: #475569 !important; }
.step-item.active { color: #1B4332 !important; font-weight: 700 !important; }
.step-item.completed { color: #059669 !important; }
.step-circle {
    width: 26px !important;
    height: 26px !important;
    border-radius: 50% !important;
    background-color: #FFFFFF !important;
    border: 2px solid #CBD5E1 !important;
    color: #334155 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
}
.step-item.active .step-circle { background-color: #1B4332 !important; border-color: #1B4332 !important; color: #FFFFFF !important; }
.step-item.completed .step-circle { background-color: #059669 !important; border-color: #059669 !important; color: #FFFFFF !important; }
.step-divider { flex: 1 !important; height: 2px !important; background-color: #CBD5E1 !important; margin: 0 6px 16px 6px !important; }
.step-divider.completed { background-color: #059669 !important; }

/* Status Badges */
.badge-available { background-color: #D1FAE5; color: #065F46; border: 1px solid #6EE7B7; }
.badge-requested { background-color: #FEF3C7; color: #92400E; border: 1px solid #FCD34D; }
.badge-confirmed { background-color: #DBEAFE; color: #1E40AF; border: 1px solid #93C5FD; }
.badge-collected { background-color: #EDE9FE; color: #5B21B6; border: 1px solid #C4B5FD; }
.badge-delivered { background-color: #ECFDF5; color: #064E3B; border: 1px solid #34D399; }
.badge-cancelled { background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; }
.badge-rejected { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5; }
.badge-expired { background-color: #F3F4F6; color: #1F2937; border: 1px solid #D1D5DB; }

div.stButton > button, .stFormSubmitButton > button {
    background-color: #1B4332 !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 10px 18px !important;
    box-shadow: 0 2px 6px rgba(27, 67, 50, 0.2) !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    min-width: 140px !important;
    line-height: 1.35 !important;
    text-align: center !important;
}
div.stButton > button *, .stFormSubmitButton > button * {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}
div.stButton > button:hover, .stFormSubmitButton > button:hover {
    background-color: #2D6A4F !important;
}
div.stButton > button[kind="secondary"], .stFormSubmitButton > button[kind="secondary"] {
    background-color: #FFFFFF !important;
    border: 1.5px solid #CBD5E1 !important;
}
div.stButton > button[kind="secondary"] *, .stFormSubmitButton > button[kind="secondary"] * {
    color: #1B4332 !important;
    fill: #1B4332 !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebar"] > div:first-child,
[data-testid="stSidebarNav"] {
    background-color: #111827 !important;
    border-right: 1px solid #1F2937 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] caption,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
    color: #F8FAFC !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #FFFFFF !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #1E293B !important;
    color: #FFFFFF !important;
    border: 1.5px solid #475569 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * {
    color: #FFFFFF !important;
}
</style>
"""

CUSTOM_CSS = get_theme_css("nature")

def apply_plot_theme(fig, theme_key: str = "nature"):
    """Applies theme colors, backgrounds, and fonts to Plotly figures."""
    theme_cfg = THEMES.get(theme_key, THEMES["nature"])
    fig.update_layout(
        template=theme_cfg["plotly_template"],
        paper_bgcolor=theme_cfg["bg_paper"],
        plot_bgcolor=theme_cfg["bg_plot"],
        font=dict(color=theme_cfg["font_color"], family="Inter, sans-serif"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def get_status_border_color(status: str) -> str:
    """Returns matching accent border color for a canonical status."""
    color_map = {
        "Available": "#10B981",
        "Requested": "#F59E0B",
        "Confirmed": "#3B82F6",
        "Collected": "#6366F1",
        "Delivered": "#059669",
        "Cancelled": "#94A3B8",
        "Rejected": "#EF4444",
        "Expired": "#6B7280"
    }
    return color_map.get(status, "#1B4332")

def get_status_badge_html(status: str, lang: str = "en") -> str:
    """Return styled HTML badge for canonical status with bilingual support."""
    class_map = {
        "Available": "badge-available",
        "Requested": "badge-requested",
        "Confirmed": "badge-confirmed",
        "Collected": "badge-collected",
        "Delivered": "badge-delivered",
        "Cancelled": "badge-cancelled",
        "Rejected": "badge-rejected",
        "Expired": "badge-expired"
    }
    key_map = {
        "Available": "status_available",
        "Requested": "status_requested",
        "Confirmed": "status_confirmed",
        "Collected": "status_collected",
        "Delivered": "status_delivered",
        "Cancelled": "status_cancelled",
        "Rejected": "status_rejected",
        "Expired": "status_expired"
    }
    icons = {
        "Available": "🟢",
        "Requested": "⏳",
        "Confirmed": "🤝",
        "Collected": "🚚",
        "Delivered": "✅",
        "Cancelled": "❌",
        "Rejected": "🚫",
        "Expired": "⏱️"
    }
    css_class = class_map.get(status, "badge-cancelled")
    icon = icons.get(status, "📌")
    label = t(key_map.get(status, "status_requested"), lang=lang)
    return f'<span class="badge-status {css_class}" style="display: inline-flex; align-items: center; gap: 5px; padding: 5px 12px; border-radius: 8px; font-size: 0.82rem; font-weight: 700;">{icon} {label}</span>'

def get_urgency_badge_html(hours_remaining: float, lang: str = "en") -> str:
    """Return styled urgency pill based on remaining pickup hours."""
    if hours_remaining <= 2.0:
        return f'<span style="display: inline-flex; align-items: center; gap: 4px; padding: 5px 12px; border-radius: 20px; font-size: 0.76rem; font-weight: 700; background: #FEE2E2; color: #991B1B; border: 1px solid #FCA5A5;">{t("critical_pill", lang)} ({hours_remaining} {t("hours_left", lang)})</span>'
    elif hours_remaining <= 4.0:
        return f'<span style="display: inline-flex; align-items: center; gap: 4px; padding: 5px 12px; border-radius: 20px; font-size: 0.76rem; font-weight: 700; background: #FEF3C7; color: #92400E; border: 1px solid #FCD34D;">{t("urgent_pill", lang)} ({hours_remaining} {t("hours_left", lang)})</span>'
    else:
        return f'<span style="display: inline-flex; align-items: center; gap: 4px; padding: 5px 12px; border-radius: 20px; font-size: 0.76rem; font-weight: 700; background: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD;">⏱️ {hours_remaining} {t("window", lang)}</span>'

def render_workflow_stepper(current_status: str, lang: str = "en") -> str:
    """Renders canonical 5-step milestone stepper for a request or listing."""
    stages = ["Available", "Requested", "Confirmed", "Collected", "Delivered"]
    stage_keys = ["step_1", "step_2", "step_3", "step_4", "step_5"]
    
    if current_status in ["Cancelled", "Rejected", "Expired"]:
        term_label = t(f"status_{current_status.lower()}", lang=lang)
        icon = "❌" if current_status == "Cancelled" else ("🚫" if current_status == "Rejected" else "⏱️")
        return f'<div style="background: #FEE2E2; border: 1px solid #FECACA; border-radius: 8px; padding: 8px 14px; font-size: 0.85rem; color: #991B1B; margin: 8px 0;">{icon} <strong>Status:</strong> {term_label}</div>'

    curr_idx = stages.index(current_status) if current_status in stages else 0

    steps_html = []
    for idx, (name, skey) in enumerate(zip(stages, stage_keys)):
        is_completed = idx < curr_idx
        is_active = idx == curr_idx
        cls = "completed" if is_completed else ("active" if is_active else "")
        symbol = "✓" if is_completed else str(idx + 1)
        localized_name = t(skey, lang=lang)
        steps_html.append(f'<div class="step-item {cls}"><div class="step-circle">{symbol}</div><span>{localized_name}</span></div>')
        if idx < len(stages) - 1:
            div_cls = "completed" if idx < curr_idx else ""
            steps_html.append(f'<div class="step-divider {div_cls}"></div>')

    return f'<div class="stepper-container" style="display: flex; align-items: center; justify-content: space-between; overflow-x: auto;">{"".join(steps_html)}</div>'

def render_brand_header(role_name: str = "Donor", lang: str = "en") -> str:
    """Renders the top branding header with Hindi/English taglines and demo badge."""
    app_name = html.escape(str(t("app_name", lang=lang)))
    tagline_hi = html.escape(str(t("tagline_hi", lang=lang)))
    tagline_en = html.escape(str(t("tagline_en", lang=lang)))
    demo_mode = html.escape(str(t("demo_mode", lang=lang)))
    demo_notice = html.escape(str(t("demo_notice", lang=lang)))
    esc_role = html.escape(str(role_name))

    return f"""
<div class="brand-header-box">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <div class="brand-title">🌾 {app_name} <span style="font-size: 1.1rem; opacity: 0.88; font-weight: 500;">({esc_role})</span></div>
            <div class="brand-tagline-hi">{tagline_hi}</div>
            <div class="brand-tagline-en">{tagline_en}</div>
        </div>
        <div>
            <span class="demo-mode-pill">⚠️ {demo_mode}</span>
        </div>
    </div>
</div>
<div class="fictional-notice-bar">
    📌 <strong>{demo_notice}</strong>
</div>
"""

def render_metric_box(label: str, value: any, sub: str, variant: str = "") -> str:
    """Renders a styled metric card."""
    var_cls = f"metric-box-{variant}" if variant else ""
    esc_label = html.escape(str(label))
    esc_val = html.escape(str(value))
    esc_sub = html.escape(str(sub))
    return (
        f'<div class="metric-box {var_cls}">'
        f'<div class="metric-label">{esc_label}</div>'
        f'<div class="metric-value">{esc_val}</div>'
        f'<div class="metric-sub">{esc_sub}</div>'
        f'</div>'
    )

def render_donor_listing_card(row, lang: str = "en") -> str:
    """Renders styled card for donor listings with embedded stepper."""
    donor_name = html.escape(str(row.get('donor_name', '')))
    row_id = html.escape(str(row.get('id', '')))
    event_type = html.escape(str(row.get('event_type', '')))
    status = str(row.get('status', 'Available'))
    food_desc = html.escape(str(row.get('food_description', '')))
    total_qty = int(row.get('quantity_portions', 0))
    avail_qty = int(row.get('available_portions', 0))
    loc = html.escape(str(row.get('location', '')))
    deadline = html.escape(str(row.get('pickup_deadline', '')))
    storage = html.escape(str(row.get('storage_info', '')))
    contact = html.escape(str(row.get('contact', row.get('private_contact', '🔒 Masked'))))
    safety_window = row.get('food_safety_window_hours', 6.0)
    
    border_color = get_status_border_color(status)
    badge = get_status_badge_html(status, lang=lang)
    stepper = render_workflow_stepper(status, lang=lang)
    unit = html.escape(str(t("portions_unit", lang=lang)))
    
    return (
        f'<div class="ann-card" style="border-left: 5px solid {border_color};">'
        f'<div class="ann-card-header">'
        f'<div><span class="ann-card-title">{donor_name}</span>'
        f'<span class="ann-card-id">ID: <code>{row_id}</code> &bull; 🏷️ {event_type}</span></div>'
        f'<div>{badge}</div>'
        f'</div>'
        f'{stepper}'
        f'<div class="ann-card-body"><strong>{html.escape(str(t("card_menu_items", lang=lang)))}</strong> {food_desc}</div>'
        f'<div class="ann-pills-row">'
        f'<span class="ann-meta-pill">📦 <strong>{html.escape(str(t("card_total", lang=lang)))}</strong> {total_qty} {unit}</span>'
        f'<span class="ann-meta-pill ann-meta-pill-success">🟢 <strong>{html.escape(str(t("card_available", lang=lang)))}</strong> {avail_qty} {unit}</span>'
        f'<span class="ann-meta-pill">📍 <strong>{html.escape(str(t("card_location", lang=lang)))}</strong> {loc}</span>'
        f'<span class="ann-meta-pill ann-meta-pill-warning">⏰ <strong>{html.escape(str(t("card_deadline", lang=lang)))}</strong> {deadline}</span>'
        f'<span class="ann-meta-pill">🛡️ <strong>Safety Limit:</strong> {safety_window}h</span>'
        f'</div>'
        f'<div class="ann-footer-box">'
        f'🌡️ <strong>{html.escape(str(t("card_storage", lang=lang)))}</strong> {storage} &nbsp;|&nbsp; 📞 <strong>{html.escape(str(t("card_contact", lang=lang)))}</strong> {contact}'
        f'</div>'
        f'</div>'
    )

def render_ngo_available_card(don, hrs_left: float, lang: str = "en") -> str:
    """Renders card for available food donations in NGO discovery view with masked donor contact."""
    donor_name = html.escape(str(don.get('donor_name', '')))
    don_id = html.escape(str(don.get('id', '')))
    event_type = html.escape(str(don.get('event_type', '')))
    status = str(don.get('status', 'Available'))
    food_desc = html.escape(str(don.get('food_description', '')))
    total_qty = int(don.get('quantity_portions', 0))
    avail_qty = int(don.get('available_portions', 0))
    loc = html.escape(str(don.get('location', '')))
    deadline = html.escape(str(don.get('pickup_deadline', '')))
    storage = html.escape(str(don.get('storage_info', '')))
    safety_window = don.get('food_safety_window_hours', 6.0)
    
    border_color = get_status_border_color(status)
    badge = get_status_badge_html(status, lang=lang)
    urg_badge = get_urgency_badge_html(hrs_left, lang=lang)
    stepper = render_workflow_stepper(status, lang=lang)
    unit = html.escape(str(t("portions_unit", lang=lang)))
    
    return (
        f'<div class="ann-card" style="border-left: 5px solid {border_color};">'
        f'<div class="ann-card-header">'
        f'<div><span class="ann-card-title">{donor_name}</span>'
        f'<span class="ann-card-id">ID: <code>{don_id}</code> &bull; 🏷️ {event_type}</span></div>'
        f'<div style="display: flex; gap: 8px; align-items: center;">{badge}{urg_badge}</div>'
        f'</div>'
        f'{stepper}'
        f'<div class="ann-card-body"><strong>{html.escape(str(t("card_menu_items", lang=lang)))}</strong> {food_desc}</div>'
        f'<div class="ann-pills-row">'
        f'<span class="ann-meta-pill ann-meta-pill-success">📦 <strong>{html.escape(str(t("card_available", lang=lang)))}</strong> <strong>{avail_qty}</strong> of {total_qty} {unit}</span>'
        + (f'<span class="ann-meta-pill" style="border-color: #38BDF8; color: #38BDF8;">📍 <strong>Transit:</strong> {don["distance_km"]} km (~{don["transit_time_mins"]}m @ 20km/h)</span>' if "distance_km" in don else f'<span class="ann-meta-pill">📍 <strong>{html.escape(str(t("card_location", lang=lang)))}</strong> {loc}</span>') +
        f'<span class="ann-meta-pill ann-meta-pill-warning">⏰ <strong>{html.escape(str(t("card_deadline", lang=lang)))}</strong> {deadline}</span>'
        f'<span class="ann-meta-pill">🛡️ <strong>Safety Limit:</strong> {safety_window}h</span>'
        f'</div>'
        f'<div class="ann-footer-box">'
        f'🌡️ <strong>{html.escape(str(t("card_storage", lang=lang)))}</strong> {storage}<br>'
        f'🔒 <strong>{html.escape(str(t("card_contact", lang=lang)))}</strong> <em>Phone revealed to verified NGO upon Confirmed pickup request</em>'
        f'</div>'
        f'</div>'
    )

def render_ngo_request_card(req, lang: str = "en") -> str:
    """Renders card for incoming NGO pickup claims in Donor dashboard with stepper per request."""
    ngo_name = html.escape(str(req.get('ngo_name', '')))
    req_id = html.escape(str(req.get('request_id', '')))
    status = str(req.get('request_status', 'Requested'))
    donor_name = html.escape(str(req.get('donor_name', '')))
    don_id = html.escape(str(req.get('donation_id', '')))
    food_desc = html.escape(str(req.get('food_description', '')))
    loc = html.escape(str(req.get('location', '')))
    notes = html.escape(str(req.get('request_notes', '')))
    qty = int(req.get('requested_portions', 0))
    proposed = html.escape(str(req.get('proposed_pickup_time', '')))
    ngo_contact = html.escape(str(req.get('ngo_contact', '')))
    req_at = html.escape(str(req.get('requested_at', '')))
    unit = html.escape(str(t("portions_unit", lang=lang)))
    
    border_color = get_status_border_color(status)
    badge = get_status_badge_html(status, lang=lang)
    stepper = render_workflow_stepper(status, lang=lang)
    
    return (
        f'<div class="ann-card" style="border-left: 5px solid {border_color};">'
        f'<div class="ann-card-header">'
        f'<div><span class="ann-card-title">{ngo_name}</span>'
        f'<span class="ann-card-id">Request ID: <code>{req_id}</code></span></div>'
        f'<div>{badge}</div>'
        f'</div>'
        f'{stepper}'
        f'<div style="display: grid; grid-template-columns: 2fr 1fr; gap: 15px; margin-top: 10px;">'
        f'<div class="ann-card-body">'
        f'<p style="margin: 0 0 6px 0;"><strong>Donation Linked:</strong> {donor_name} (<code>{don_id}</code>)</p>'
        f'<p style="margin: 0 0 6px 0;"><strong>{html.escape(str(t("card_menu_items", lang=lang)))}</strong> {food_desc}</p>'
        f'<p style="margin: 0 0 6px 0;"><strong>{html.escape(str(t("card_location", lang=lang)))}</strong> {loc}</p>'
        f'<p style="margin: 0; font-size: 0.85rem;" class="ann-subtext"><strong>Logistics Notes:</strong> {notes}</p>'
        f'</div>'
        f'<div class="ann-footer-box" style="margin: 0;">'
        f'<div><strong>Requested:</strong> {qty} {unit}</div>'
        f'<div><strong>Proposed Time:</strong> {proposed}</div>'
        f'<div><strong>NGO Contact:</strong> {ngo_contact}</div>'
        f'<div style="font-size: 0.75rem; margin-top: 6px;" class="ann-subtext">Logged at: {req_at}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

def render_ngo_my_request_card(req, lang: str = "en") -> str:
    """Renders card for NGO\'s submitted requests with stepper per request and privacy-masked contact."""
    donor_name = html.escape(str(req.get('donor_name', '')))
    req_id = html.escape(str(req.get('request_id', '')))
    status = str(req.get('request_status', 'Requested'))
    food_desc = html.escape(str(req.get('food_description', '')))
    qty = int(req.get('requested_portions', 0))
    loc = html.escape(str(req.get('location', '')))
    proposed = html.escape(str(req.get('proposed_pickup_time', '')))
    donor_contact = html.escape(str(req.get('donor_contact', '🔒 Masked until Confirmed')))
    unit = html.escape(str(t("portions_unit", lang=lang)))
    
    border_color = get_status_border_color(status)
    badge = get_status_badge_html(status, lang=lang)
    stepper = render_workflow_stepper(status, lang=lang)
    
    return (
        f'<div class="ann-card" style="border-left: 5px solid {border_color};">'
        f'<div class="ann-card-header">'
        f'<div><span class="ann-card-title">{donor_name}</span>'
        f'<span class="ann-card-id">Request ID: <code>{req_id}</code></span></div>'
        f'<div>{badge}</div>'
        f'</div>'
        f'{stepper}'
        f'<div class="ann-card-body"><strong>{html.escape(str(t("card_menu_items", lang=lang)))}</strong> {food_desc}</div>'
        f'<div class="ann-pills-row">'
        f'<span class="ann-meta-pill">📦 <strong>Requested:</strong> {qty} {unit}</span>'
        f'<span class="ann-meta-pill">📍 <strong>{html.escape(str(t("card_location", lang=lang)))}</strong> {loc}</span>'
        f'<span class="ann-meta-pill ann-meta-pill-warning">⏰ <strong>Proposed:</strong> {proposed}</span>'
        f'</div>'
        f'<div class="ann-footer-box">'
        f'📞 <strong>{html.escape(str(t("card_contact", lang=lang)))}</strong> {donor_contact}'
        f'</div>'
        f'</div>'
    )

def render_actionable_milestone_card(req, lang: str = "en") -> str:
    """Renders card for actionable pickup requests awaiting milestone progression."""
    ngo_name = html.escape(str(req.get('ngo_name', '')))
    qty = int(req.get('requested_portions', 0))
    don_id = html.escape(str(req.get('donation_id', '')))
    status = str(req.get('request_status', 'Requested'))
    donor_name = html.escape(str(req.get('donor_name', '')))
    loc = html.escape(str(req.get('location', '')))
    donor_contact = html.escape(str(req.get('donor_contact', '🔒 Masked')))
    unit = html.escape(str(t("portions_unit", lang=lang)))
    
    border_color = get_status_border_color(status)
    badge = get_status_badge_html(status, lang=lang)
    stepper = render_workflow_stepper(status, lang=lang)
    
    return (
        f'<div class="ann-card" style="border-left: 5px solid {border_color};">'
        f'<div class="ann-card-header">'
        f'<div><span class="ann-card-title">{ngo_name} &bull; {qty} {unit}</span>'
        f'<span class="ann-card-id">Linked Donation: <code>{don_id}</code></span></div>'
        f'<div>{badge}</div>'
        f'</div>'
        f'{stepper}'
        f'<div class="ann-card-body" style="font-size: 0.92rem; margin: 10px 0 8px 0;">'
        f'<strong>Donor / Venue:</strong> {donor_name} &nbsp;|&nbsp; <strong>{html.escape(str(t("card_location", lang=lang)))}</strong> {loc}<br>'
        f'<strong>{html.escape(str(t("card_contact", lang=lang)))}</strong> {donor_contact}'
        f'</div>'
        f'</div>'
    )
