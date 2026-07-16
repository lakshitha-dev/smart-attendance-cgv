"""Lookup page (Story 4.5, FR-14): thin adapter — input, the engine query
(Story 2.1's single resolver via `lookup_logic.lookup`), then
`visualization.py`'s Figure rendered via `st.pyplot`. ZERO chart or no-data
copy logic lives here (AD-1/AD-8) — `lookup_logic.py` owns the copy,
`sams_core/visualization.py` owns the chart."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from sams_core.errors import SamsError
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_attendance_timeline
from webui.lookup_logic import lookup

st.title("Look up a student")

alias = st.text_input("Student number")

if not alias:
    st.write("Type a student's number to see their attendance.")
else:
    with st.spinner("Looking that up…"):
        try:
            result = lookup(alias, AttendanceRepository())
        except SamsError:
            result = None
            st.error("Something went wrong reading the saved records.")

    if result is not None:
        if result.message:
            st.write(result.message)
        else:
            st.pyplot(render_attendance_timeline(result.records))
