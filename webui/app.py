"""SAMS web entry point (Story 4.1, FR-12/UX-DR1/UX-DR2): the three-page
shell. `st.navigation` declares EXACTLY Process (landing), Lookup, and
Investigate — no other navigation, and `pages/` auto-discovery is disabled by
the explicit router. Theme lives in .streamlit/config.toml (Quiet Clerk,
light-pinned); this file adds only the minimal chip/row CSS (UX-DR1) and owns
the single st.set_page_config call."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

st.set_page_config(page_title="SAMS", layout="centered")

# UX-DR1 minimal CSS: content width token, status-chip + row classes for the
# results list (consumed by Story 4.3), touch-target minimums (UX-DR14).
# Chip colours per UX-DR8 — coloured text/glyph only, no filled backgrounds.
st.markdown(
    """
    <style>
    .block-container { max-width: 1100px; }
    .stButton button { min-height: 52px; }
    .sams-row { padding: 10px 16px; border-radius: 10px; }
    .sams-row:hover { background: #F3F2EE; }
    .sams-chip { font-weight: 600; background: none; }
    .sams-chip-present { color: #256E4C; }
    .sams-chip-absent { color: #A63D2A; }
    .sams-chip-ambiguous { color: #7A6212; }
    </style>
    """,
    unsafe_allow_html=True,
)

pages = [
    st.Page("pages/Process.py", title="Mark today's attendance", default=True),
    st.Page("pages/Lookup.py", title="Look up a student"),
    st.Page("pages/Investigate.py", title="Check a signature"),
]
st.navigation(pages).run()
