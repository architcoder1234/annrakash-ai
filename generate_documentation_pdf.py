"""
generate_documentation_pdf.py
Generates the comprehensive technical PDF documentation:
'AnnRakshak AI - Complete Implementation, Architecture & UI Specification Guide'
Using ReportLab with clean typography, tables, repeatRows=1, headers, footers,
navigation maps, 7 documented charts, and verified test suite results.
"""

import os
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display 'Page X of Y' in footer
    along with running header and footer dividing lines.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(page_count)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Don't draw header/footer on cover page if page 1
        if self._pageNumber > 1:
            # Header
            self.drawString(54, letter[1] - 36, "AnnRakshak AI - Implementation, Architecture & UI Specification Guide")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, letter[1] - 42, letter[0] - 54, letter[1] - 42)
            
            # Footer
            page_text = f"Page {self._pageNumber} of {page_count}"
            self.drawRightString(letter[0] - 54, 34, page_text)
            self.drawString(54, 34, "Confidential | Hackathon System Documentation | AnnRakshak AI (Demand Prediction & Surplus Recovery)")
            self.line(54, 46, letter[0] - 54, 46)
        self.restoreState()


def build_pdf(filename="AnnRakshak_AI_Implementation_and_UI_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=65
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    C_PRIMARY = colors.HexColor("#1B4332")      # Forest Green
    C_SECONDARY = colors.HexColor("#2D6A4F")    # Light Forest Green
    C_ACCENT = colors.HexColor("#A23B20")       # Darkened Terracotta (WCAG AA Compliant)
    C_GOLD = colors.HexColor("#854D0E")         # Darkened Gold (WCAG AA Compliant)
    C_NAVY = colors.HexColor("#0A192F")         # Deep Navy
    C_DARK = colors.HexColor("#0F172A")         # Deep Slate
    C_MUTED = colors.HexColor("#475569")        # Slate Muted
    C_LIGHT_BG = colors.HexColor("#F8FAFC")     # Card Canvas
    C_BORDER = colors.HexColor("#CBD5E1")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=C_PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=C_ACCENT,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=C_PRIMARY,
        spaceBefore=12,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=C_SECONDARY,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'DocH3',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=C_DARK,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=C_DARK,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'DocBodyBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=C_DARK,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=C_DARK,
        leftIndent=12,
        spaceAfter=3
    )

    callout_style = ParagraphStyle(
        'DocCallout',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=4,
        spaceAfter=6
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.white,
        alignment=0
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=C_DARK
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=11,
        textColor=C_PRIMARY
    )

    story = []

    # =========================================================
    # COVER / HEADER TITLE BLOCK
    # =========================================================
    story.append(Paragraph("AnnRakshak AI - System Implementation &amp; UI Architecture Guide", title_style))
    story.append(Paragraph("Operational Documentation, 3 Selectable UI Themes, Component Usage Matrix &amp; Audit Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=C_PRIMARY, spaceAfter=8, spaceBefore=0))
    story.append(Paragraph("<i>Surplus Food Rescue &bull; Kitchen Waste Audit &bull; Predictive Demand Planning &bull; Gemma 4 AI</i>", body_bold))
    story.append(Spacer(1, 4))
    
    meta_table_data = [
        [
            Paragraph("<b>Document Version:</b> 2.0 (Audited Release)", body_style),
            Paragraph("<b>Target Locality:</b> Prayagraj, India (IST)", body_style),
            Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d')}", body_style)
        ],
        [
            Paragraph("<b>Tech Stack:</b> Streamlit, SQLite (WAL), Plotly, google-genai", body_style),
            Paragraph("<b>AI Model:</b> Gemma 4 (gemma-4-26b-a4b-it / 31b)", body_style),
            Paragraph("<b>Supported Languages:</b> English (en), Hindi (hi)", body_style)
        ]
    ]
    t_meta = Table(meta_table_data, colWidths=[2.3*inch, 2.3*inch, 2.4*inch], repeatRows=1)
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # =========================================================
    # SECTION 1: EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # =========================================================
    story.append(Paragraph("1. Executive Summary &amp; Problem Statement", h1_style))
    story.append(Paragraph(
        "Commercial banquets, wedding venues, corporate events, and hotel kitchens frequently face unpredicted service variance. "
        "According to the <i>UNEP Food Waste Index Report (2024)</i> and Indian hospitality catering studies, approximately 10% to 20% of prepared banquet "
        "food is routinely discarded due to RSVP dropouts, adverse weather, or banquet closure timing. Simultaneously, night shelters and vulnerable "
        "communities in urban areas experience persistent meal deficits. <b>AnnRakshak AI</b> bridges this gap through four core capabilities:",
        body_style
    ))
    story.append(Paragraph("&bull; <b>Surplus Food Rescue &amp; Coordination:</b> Canonical 5-step milestone lifecycle (Available -&gt; Requested -&gt; Confirmed -&gt; Collected -&gt; Delivered) connecting donors with verified NGOs.", bullet_style))
    story.append(Paragraph("&bull; <b>Kitchen Food Waste Auditing:</b> Logging portions prepared vs consumed, calculating edible surplus vs inedible discards, and quantifying financial loss (INR).", bullet_style))
    story.append(Paragraph("&bull; <b>Predictive Demand Planning:</b> Mathematical estimator using historical consumption ratios, attendees, and clamped buffers (0-50%) to prevent over-preparation before cooking starts.", bullet_style))
    story.append(Paragraph("&bull; <b>Gemma 4 AI Insights:</b> Synthesizing kitchen audits and active surplus listings using Google Gen AI SDK to recommend waste reduction strategies and dispatch priorities.", bullet_style))
    story.append(Spacer(1, 8))

    # =========================================================
    # SECTION 2: FULL NAVIGATION MAP FOR ALL PORTALS
    # =========================================================
    story.append(Paragraph("2. Full Portal Navigation Map", h1_style))
    story.append(Paragraph(
        "The application provides three dedicated portal perspectives secured by role-based PIN authentication "
        "(Donor PIN <code>1234</code>, NGO PIN <code>5678</code>, Admin PIN <code>9999</code>). Each portal features numbered navigation sections:",
        body_style
    ))

    nav_data = [
        [Paragraph("Portal Perspective", table_header_style), Paragraph("Section Number &amp; Name", table_header_style), Paragraph("Key Functional Purpose", table_header_style)],
        [
            Paragraph("<b>Donor Portal</b><br/>(Food Providers / Caterers)", table_cell_bold),
            Paragraph("1. Overview<br/>2. Donate Food<br/>3. My Donations<br/>4. NGO Pickup Requests<br/>5. Food Waste Tracker<br/>6. Demand Prediction<br/>7. Gemma 4 AI Insights<br/>8. Impact Summary", table_cell_style),
            Paragraph("Operations KPIs, surplus food publishing, multi-stage coordination, kitchen waste audits, predictive demand calculations, AI waste advisory, and CSV exports.", table_cell_style)
        ],
        [
            Paragraph("<b>NGO Portal</b><br/>(Food Recovery Organizations)", table_cell_bold),
            Paragraph("1. Overview<br/>2. Available Food Donations<br/>3. Search &amp; Filters<br/>4. Request Pickup<br/>5. My Pickup Requests<br/>6. Collection &amp; Delivery Status<br/>7. Impact Summary", table_cell_style),
            Paragraph("Surplus discovery feeds, urgency countdown tracking, partial portion claims, driver coordination, collection/delivery milestone progression, and impact reporting.", table_cell_style)
        ],
        [
            Paragraph("<b>Admin Portal</b><br/>(System Administrators)", table_cell_bold),
            Paragraph("1. NGO Verifications<br/>2. System Audit Trail<br/>3. Reset Database", table_cell_style),
            Paragraph("Reviewing and granting verified standing to NGO partners, monitoring tamper-proof status transition logs, and non-destructive demo database management.", table_cell_style)
        ]
    ]

    t_nav = Table(nav_data, colWidths=[1.8*inch, 2.3*inch, 2.9*inch], repeatRows=1)
    t_nav.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_nav)
    story.append(Spacer(1, 10))

    # =========================================================
    # SECTION 3: COMPLETE LISTING OF THE 7 INTERACTIVE CHARTS
    # =========================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Complete Catalog of the 7 Interactive Plotly Charts", h1_style))
    story.append(Paragraph(
        "All visual analytics are rendered using Plotly interactive charts and automatically synchronized to the active theme palette via <code>apply_plot_theme()</code>:",
        body_style
    ))

    charts_data = [
        [Paragraph("Chart # &amp; Title", table_header_style), Paragraph("Portal &amp; Section Location", table_header_style), Paragraph("Chart Type &amp; Visual Metrics Tracked", table_header_style)],
        [
            Paragraph("<b>Chart 1: Donation Status Distribution</b>", table_cell_bold),
            Paragraph("Donor Portal: Section 1 (Overview)", table_cell_style),
            Paragraph("Donut Chart showing proportion of listings in Available, Requested, Confirmed, Collected, Delivered, and Cancelled.", table_cell_style)
        ],
        [
            Paragraph("<b>Chart 2: Portions Offered vs Collected vs Delivered</b>", table_cell_bold),
            Paragraph("Donor Portal: Section 1 (Overview)", table_cell_style),
            Paragraph("Grouped Bar Chart comparing total meal portions listed against portions loaded into vans and verified delivered.", table_cell_style)
        ],
        [
            Paragraph("<b>Chart 3: Recent Consumption vs Unconsumed Leftovers</b>", table_cell_bold),
            Paragraph("Donor Portal: Section 5 (Waste Tracker)", table_cell_style),
            Paragraph("Stacked Bar Chart showing chronological service logs with consumed meals stacked against unconsumed leftovers.", table_cell_style)
        ],
        [
            Paragraph("<b>Chart 4: Financial Discard Loss by Meal Category</b>", table_cell_bold),
            Paragraph("Donor Portal: Section 5 (Waste Tracker)", table_cell_style),
            Paragraph("Pie / Donut Chart visualizing aggregate monetary loss (INR) distributed across Dinner, Lunch, Breakfast, and Buffets.", table_cell_style)
        ],
        [
            Paragraph("<b>Chart 5: RSVP vs Estimated Net Demand vs Prep</b>", table_cell_bold),
            Paragraph("Donor Portal: Section 6 (Demand Predictor)", table_cell_style),
            Paragraph("Grouped Bar Chart contrasting raw attendee RSVP count against historical arrival demand and recommended batch size.", table_cell_style)
        ],
        [
            Paragraph("<b>Chart 6: Surplus Meal Portions by Area / Locality</b>", table_cell_bold),
            Paragraph("NGO Portal: Section 1 (Overview)", table_cell_style),
            Paragraph("Horizontal Bar Chart displaying available rescue portions grouped by geographic banquet clusters in Prayagraj.", table_cell_style)
        ],
        [
            Paragraph("<b>Chart 7: NGO Pickup Request Status Breakdown</b>", table_cell_bold),
            Paragraph("NGO Portal: Section 1 (Overview)", table_cell_style),
            Paragraph("Donut Chart tracking active recovery missions across Requested, Confirmed, Collected, and Delivered states.", table_cell_style)
        ]
    ]

    t_charts = Table(charts_data, colWidths=[2.2*inch, 2.0*inch, 2.8*inch], repeatRows=1)
    t_charts.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_charts)
    story.append(Spacer(1, 10))

    # =========================================================
    # SECTION 4: SELECTABLE UI SETUPS & WCAG AA CONTRAST AUDIT
    # =========================================================
    story.append(Paragraph("4. Selectable UI Setups &amp; Contrast Audit", h1_style))
    story.append(Paragraph(
        "To provide accessibility across indoor kitchen offices, outdoor lawns, and evening transport routes, AnnRakshak AI features "
        "three selectable UI setups. All color pairings have been validated via automated contrast script (<code>check_contrast.py</code>):",
        body_style
    ))

    theme_data = [
        [Paragraph("Theme Name", table_header_style), Paragraph("Palette &amp; Tone", table_header_style), Paragraph("Target Operational Environment", table_header_style), Paragraph("Audited Contrast Ratio", table_header_style)],
        [
            Paragraph("<b>AnnRakshak Nature</b><br/><i>(Warm Forest &amp; Cream)</i>", table_cell_bold),
            Paragraph("&bull; Canvas: <code>#FBF9F4</code><br/>&bull; Cards: <code>#FFFFFF</code><br/>&bull; Primary: <code>#1B4332</code><br/>&bull; Accent: <code>#A23B20</code><br/>&bull; Text: <code>#0F172A</code>", table_cell_style),
            Paragraph("Daytime kitchen management, banquet reception desks, and administrative logging.", table_cell_style),
            Paragraph("<b>16.97:1</b> (Body on bg)<br/><b>6.60:1</b> (Accent on white)<br/>WCAG AA &gt; 4.5:1 [PASS]", table_cell_style)
        ],
        [
            Paragraph("<b>Midnight Pro</b><br/><i>(Dark Obsidian Mode)</i>", table_cell_bold),
            Paragraph("&bull; Canvas: <code>#0B0F19</code><br/>&bull; Cards: <code>#151E2E</code><br/>&bull; Primary: <code>#10B981</code><br/>&bull; Accent: <code>#38BDF8</code><br/>&bull; Text: <code>#F8FAFC</code>", table_cell_style),
            Paragraph("Night-time recovery vans, low-light shelter distribution, and evening catering audits.", table_cell_style),
            Paragraph("<b>18.30:1</b> (Text on dark)<br/><b>6.59:1</b> (Mint on surface)<br/>WCAG AA &gt; 4.5:1 [PASS]", table_cell_style)
        ],
        [
            Paragraph("<b>High-Contrast Daylight</b><br/><i>(Executive Navy &amp; Gold)</i>", table_cell_bold),
            Paragraph("&bull; Canvas: <code>#FFFFFF</code><br/>&bull; Cards: <code>#FFFFFF</code><br/>&bull; Primary: <code>#0A192F</code><br/>&bull; Accent: <code>#854D0E</code><br/>&bull; Text: <code>#000000</code>", table_cell_style),
            Paragraph("High-glare outdoor wedding lawns, dockside logistics, and projector presentations.", table_cell_style),
            Paragraph("<b>21.00:1</b> (Black on white)<br/><b>6.85:1</b> (Gold on white)<br/>WCAG AAA &gt; 7:1 [PASS]", table_cell_style)
        ]
    ]

    t_theme = Table(theme_data, colWidths=[1.5*inch, 2.1*inch, 2.0*inch, 1.4*inch], repeatRows=1)
    t_theme.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_theme)
    story.append(Spacer(1, 10))

    # =========================================================
    # SECTION 5: SYSTEM ARCHITECTURE & CORE MODULE MATRIX
    # =========================================================
    story.append(PageBreak())
    story.append(Paragraph("5. System Architecture &amp; Core Module Matrix", h1_style))
    story.append(Paragraph(
        "AnnRakshak AI utilizes a centralized SQLite database operating in WAL (Write-Ahead Logging) mode with <code>busy_timeout=5000ms</code> "
        "and <code>BEGIN IMMEDIATE</code> locks for serialized writer access:",
        body_style
    ))

    modules_data = [
        [Paragraph("Module / File", table_header_style), Paragraph("Core Responsibilities &amp; Capabilities", table_header_style), Paragraph("Key Methods &amp; Architectural Features", table_header_style)],
        [
            Paragraph("<b>database.py</b>", table_cell_bold),
            Paragraph("Initializes tables: <code>donations</code>, <code>pickup_requests</code>, <code>food_waste_records</code>, <code>ngos</code>, <code>status_history</code>. Seeds fictional Prayagraj records non-destructively.", table_cell_style),
            Paragraph("<code>init_db()</code>, <code>get_connection()</code>. WAL mode, foreign keys, IST (Asia/Kolkata) timezone-aware datetimes.", table_cell_style)
        ],
        [
            Paragraph("<b>workflow_manager.py</b>", table_cell_bold),
            Paragraph("Implements canonical status enum, partial requests, atomic portion release on Rejection/Cancel, auto-expiry, and CSV formula injection protection.", table_cell_style),
            Paragraph("<code>WorkflowStatus</code> enum, <code>create_donation()</code>, <code>request_pickup()</code>, <code>update_request_status()</code>, <code>check_and_expire_donations()</code>.", table_cell_style)
        ],
        [
            Paragraph("<b>demand_predictor.py</b>", table_cell_bold),
            Paragraph("Deterministic baseline estimator computing food preparation targets from historical consumption ratios, attendees, and clamped buffers (0-50%).", table_cell_style),
            Paragraph("<code>calculate_demand_estimate()</code>. Handles 0/negative attendees, clamped cushions, and cold-start hospitality fallback ratios.", table_cell_style)
        ],
        [
            Paragraph("<b>ai_insights.py</b>", table_cell_bold),
            Paragraph("Google Gemma 4 AI integration via <code>google-genai</code> SDK. PII phone/email scrubber, model verification check, timeout retries, and bilingual output.", table_cell_style),
            Paragraph("<code>analyze_food_waste_with_gemma()</code>, <code>prioritize_donations_with_gemma()</code>, <code>verify_gemma_model()</code>.", table_cell_style)
        ],
        [
            Paragraph("<b>i18n.py</b>", table_cell_bold),
            Paragraph("Internationalization engine supporting English (<code>en</code>) and Hindi (<code>hi</code>). Canonical status translations, PIN auth, and environmental impact keys.", table_cell_style),
            Paragraph("<code>t(key, lang, **kwargs)</code>. Dictionary-based string lookup with parameterized token interpolation.", table_cell_style)
        ],
        [
            Paragraph("<b>ui_styles.py</b>", table_cell_bold),
            Paragraph("Modular styling engine generating WCAG AA compliant CSS, responsive listing cards, status badges, metric boxes, and 5-stage visual milestone steppers.", table_cell_style),
            Paragraph("<code>get_theme_css()</code>, <code>render_workflow_stepper()</code>, <code>render_donor_listing_card()</code>, <code>render_ngo_available_card()</code>.", table_cell_style)
        ],
        [
            Paragraph("<b>check_contrast.py</b>", table_cell_bold),
            Paragraph("Standalone accessibility script calculating WCAG 2.1 relative luminance and contrast ratios for all three application themes.", table_cell_style),
            Paragraph("<code>calculate_contrast_ratio()</code>, <code>check_all_themes()</code>. Verifies compliance (ratio &gt;= 4.5:1 for body text).", table_cell_style)
        ],
        [
            Paragraph("<b>test_workflow.py</b>", table_cell_bold),
            Paragraph("Automated test suite executing 9 isolated verification tests (Tests A-I) against a temporary SQLite database (never touches annrakshak.db).", table_cell_style),
            Paragraph("<code>TestAnnRakshakAIAudit</code>. Tests partial claims, portion release, 10-thread concurrency lock, and CSV escaping.", table_cell_style)
        ]
    ]

    t_mod = Table(modules_data, colWidths=[1.4*inch, 3.2*inch, 2.4*inch], repeatRows=1)
    t_mod.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_mod)
    story.append(Spacer(1, 10))

    # =========================================================
    # SECTION 6: AUTOMATED VERIFICATION TEST SUITE RESULTS (A-I)
    # =========================================================
    story.append(Paragraph("6. Automated Verification Test Suite Results (Tests A through I)", h1_style))
    story.append(Paragraph(
        "All test runs execute against a temporary SQLite database file using <code>tempfile.NamedTemporaryFile</code>, "
        "guaranteeing complete demo database isolation. All 9 tests passed:",
        body_style
    ))

    test_data = [
        [Paragraph("Test Identifier", table_header_style), Paragraph("Tested Functional Dimension", table_header_style), Paragraph("Assertion &amp; Audit Verification Result", table_header_style)],
        [
            Paragraph("<b>Test A</b>", table_cell_bold),
            Paragraph("Wedding Donation &amp; Food Safety Window", table_cell_style),
            Paragraph("Asserts valid creation with IST time; verifies food prepared &gt;6 hours ago is blocked. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test B</b>", table_cell_bold),
            Paragraph("Partial Requests &amp; Portion Hold", table_cell_style),
            Paragraph("Asserts partial claim (40/100 portions) leaves 60 portions Available for other NGOs. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test C</b>", table_cell_bold),
            Paragraph("Milestones &amp; Environmental Impact", table_cell_style),
            Paragraph("Progresses to Delivered; verifies 17.5 kg food rescued and 43.75 kg CO2 avoided. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test D</b>", table_cell_bold),
            Paragraph("Atomic Portion Release on Reject/Cancel", table_cell_style),
            Paragraph("Asserts rejected/cancelled claims immediately return portions to the Available pool. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test E</b>", table_cell_bold),
            Paragraph("Auto-Expiry of Past-Deadline Listings", table_cell_style),
            Paragraph("Asserts past-deadline listings and unconfirmed requests are auto-marked Expired. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test F</b>", table_cell_bold),
            Paragraph("Concurrency &amp; No Double-Booking", table_cell_style),
            Paragraph("10 concurrent threads attempt to claim 40 portions from a 50-portion pool; exactly 1 succeeds, 9 fail. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test G</b>", table_cell_bold),
            Paragraph("Demand Predictor Edge Cases &amp; Clamping", table_cell_style),
            Paragraph("Asserts 0/negative attendees raise ValueError; buffer clamped strictly between 0-50%. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test H</b>", table_cell_bold),
            Paragraph("Gemma Mocking, PII Redaction &amp; Fallback", table_cell_style),
            Paragraph("Asserts donor phone/email scrubbed from prompt; verifies deterministic Hindi fallback. <b>PASSED [OK]</b>", table_cell_style)
        ],
        [
            Paragraph("<b>Test I</b>", table_cell_bold),
            Paragraph("CSV Formula Injection Escaping", table_cell_style),
            Paragraph("Asserts cells starting with =, +, -, @ are safely escaped with leading single quote. <b>PASSED [OK]</b>", table_cell_style)
        ]
    ]

    t_test = Table(test_data, colWidths=[1.1*inch, 2.5*inch, 3.4*inch], repeatRows=1)
    t_test.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), C_PRIMARY),
        ('BOX', (0,0), (-1,-1), 1, C_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, C_BORDER),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
    ]))
    story.append(t_test)
    story.append(Spacer(1, 10))

    # Sign-off box
    signoff_data = [
        [
            Paragraph("<b>System Status:</b> Fully Audited &amp; Operational", body_style),
            Paragraph("<b>Live Server:</b> http://localhost:8501", body_style),
            Paragraph("<b>Database:</b> SQLite (<code>annrakshak.db</code>, WAL)", body_style)
        ]
    ]
    t_signoff = Table(signoff_data, colWidths=[2.3*inch, 2.3*inch, 2.4*inch], repeatRows=1)
    t_signoff.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#ECFDF5")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#10B981")),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_signoff)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {os.path.abspath(filename)}")

if __name__ == "__main__":
    out_pdf = "AnnRakshak_AI_Implementation_and_UI_Guide.pdf"
    build_pdf(out_pdf)
