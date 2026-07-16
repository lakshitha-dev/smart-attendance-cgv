"""SAMS web entry point (minimal landing stub for Story 4.5 — the full
three-page shell + Quiet Clerk theme is Story 4.1's scope, not built here).
Streamlit auto-discovers `webui/pages/` for sidebar navigation."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

st.title("SAMS")
st.write("Use the sidebar to open a page.")
