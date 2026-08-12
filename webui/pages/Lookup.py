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

import matplotlib

matplotlib.use("Agg")  # server-side render only: never a GUI backend in a
# Streamlit worker thread (TkAgg off the main thread crashes; headless
# deploys have no display at all). st.pyplot rasterizes the figure anyway.

import streamlit as st

from sams_core.errors import SamsError
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_attendance_timeline
from webui.lookup_logic import lookup

# st.set_page_config lives in app.py — the router owns the single call.
st.title("Look up a student")

# Keyed so Dashboard/History can prefill the student before switching here
# (SAMS design: flagged rows deep-link to this timeline).
alias = st.text_input(
    "Student number", key="lookup_alias", placeholder="e.g. 001 or 10000409"
).strip()

# Quick pick (SAMS design): one round pill per known student, filling the
# input on tap. Roster read via resolve_with_roster so an empty install never
# creates a DB file on disk; the .st-key-quick_pick CSS shapes the pills.
_roster = ()
try:
    _, _, _roster = AttendanceRepository().resolve_with_roster("")
except Exception:
    _roster = ()
if _roster:

    def _pick(value: str) -> None:
        st.session_state["lookup_alias"] = value

    options = list(dict.fromkeys((s["no"] or s["student_index"]) for s in _roster))[:12]
    with st.container(key="quick_pick"):
        columns = st.columns(max(len(options), 6))
        for column, option in zip(columns, options):
            column.button(option, key=f"pick_{option}", on_click=_pick, args=(option,))

if not alias:
    st.write("Type a student's number to see their attendance.")
else:
    result = None
    fig = None
    with st.spinner("Looking that up…"):
        try:
            result = lookup(alias, AttendanceRepository())
            if result.records:
                # Render inside the spinner: the figure build (cold matplotlib
                # import included) is the slow step, not the DB read.
                fig = render_attendance_timeline(result.records)
        except SamsError:
            st.error("Something went wrong reading the saved records.")
        except Exception:  # AD-6: no raw traceback may reach the browser
            st.error("Something went wrong reading the saved records.")

    if result is not None:
        if result.message:
            st.write(result.message)
        elif fig is not None:
            # Keyed so the phone breakpoint can hold the figure at a legible
            # width and pan it, rather than scaling a 9in-wide chart into a
            # ~366px column where the axis labels land around 6pt.
            with st.container(key="sams_chart"):
                st.pyplot(fig)
            import matplotlib.pyplot as plt

            plt.close(fig)  # long-lived server: never accumulate figures
