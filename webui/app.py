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

# No page_title here: st.navigation titles each browser tab per page
# ("Mark today's attendance", …) — a pinned title would flatten them all to
# one string. layout="wide" + the CSS cap below give the ~1100px content
# width honestly (centered layout would fight the cap with its own ~46rem).
st.set_page_config(layout="wide")

# UX-DR1 minimal CSS (DESIGN.md tokens): content max-width ~1100px, 18px page
# margin, 16px card padding, 10/12/14px radii; status-chip + row classes for
# the results list (consumed by Story 4.3), touch-target minimums (UX-DR14).
# Chip colours per UX-DR8 — coloured text/glyph only, no filled backgrounds.
st.markdown(
    """
    <style>
    .block-container { max-width: 1100px; margin: 0 auto; padding-left: 18px; padding-right: 18px; }
    .stButton button { min-height: 52px; border-radius: 12px; }
    /* UX-DR14 44px touch floor also covers the uploader Browse buttons and
       Streamlit's own nav chrome (sidebar toggle, main menu) on phones. */
    [data-testid='stFileUploader'] button { min-height: 44px; }
    [data-testid='stExpandSidebarButton'] button, [data-testid='stExpandSidebarButton'],
    [data-testid='stMainMenuButton'], [data-testid='stBaseButton-headerNoPadding'] {
        min-height: 44px; min-width: 44px;
    }
    .stAppDeployButton { display: none; }  /* dev-only chrome, not part of SAMS */
    .sams-card { padding: 16px; border-radius: 14px; background: #FFFFFF; }
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
