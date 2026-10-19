"""
UI Components and Modular View Controllers for AnnRakshak AI.
Decouples Streamlit dashboard rendering into role-based presentation modules.
"""

from .donor import render_donor_dashboard
from .ngo import render_ngo_dashboard
from .admin import render_admin_dashboard

__all__ = [
    "render_donor_dashboard",
    "render_ngo_dashboard",
    "render_admin_dashboard"
]
