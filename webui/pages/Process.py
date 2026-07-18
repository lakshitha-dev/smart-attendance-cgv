"""Process page — the landing (Story 4.1/4.2, FR-12/UX-DR3/DR4/DR5/DR12): two
labelled file slots, one Process button, and the one-tap processing run fenced
so Streamlit reruns never re-trigger it. ZERO engine logic here (AD-1/AD-8) —
`webui/process_logic.py` sequences the engine calls and owns the copy; this
page is widgets + session-state fencing only. The rich stage strip (UX-DR6)
and results row list (UX-DR7) arrive in Story 4.3."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from sams_core.repository import AttendanceRepository
from webui.process_logic import OVERWRITE_PROMPT, parse_info, run_process

st.title("Mark today's attendance")

# UX-DR12 verbatim upload hint.
st.markdown("Add the sheet photo and the info file, then tap Process. That's all you need to do.")


def _slot_ready(uploaded) -> bool:
    return uploaded is not None and uploaded.size > 0


def _ready_note(uploaded) -> None:
    """Quiet slate "Ready" (UX-DR3: primary slate, never Present green). The
    filename renders as a code span so markdown metacharacters in real names
    cannot break the directive."""
    if uploaded is None:
        return
    if uploaded.size == 0:
        st.markdown("That file looks empty — please pick it again.")
        return
    safe_name = uploaded.name.replace("`", "'")
    st.markdown(f":primary[✓ Ready] — `{safe_name}`")


# UX-DR3: two labelled slots.
sheet_photo = st.file_uploader("Signing Sheet", type=["jpeg", "jpg", "png"])
st.caption("JPEG or PNG. On iPhone, choose 'Most Compatible' or export the photo as JPEG.")
_ready_note(sheet_photo)

info_file = st.file_uploader("Info File", type=["xml"])
_ready_note(info_file)

# AD-11: a date field appears ONLY when the uploaded Info File lacks a session
# date — and the Web UI never falls back to the upload filename. Parse eagerly
# (cheap) so the field can appear before Process is tapped.
session_date = None
parsed = None
if _slot_ready(info_file):
    parsed = parse_info(info_file.getvalue())
    if parsed.error:
        st.error(parsed.error)
    elif parsed.needs_date:
        session_date = st.text_input(
            "Session date (YYYY-MM-DD)",
            help="This sheet's info file has no session date, so please enter it.",
        )
        parsed = parse_info(info_file.getvalue(), session_date=session_date or None)

both_ready = _slot_ready(sheet_photo) and _slot_ready(info_file)
date_ready = parsed is not None and parsed.sheet_id is not None

# UX-DR4: one full-width primary Process button, disabled until inputs (and a
# date, when required) are ready.
process_clicked = st.button(
    "Process",
    type="primary",
    width="stretch",
    disabled=not (both_ready and date_ready and parsed.error is None),
)


# --- Fence: process on the button-press rerun only ---------------------------
# st.button returns True only on the single rerun following the press, so the
# engine call happens once per tap; scrolling/expanding reruns skip this branch
# and just re-render the stored outcome below (AC: zero re-processing).
if process_clicked and both_ready and date_ready:
    with st.spinner("Reading the sheet…"):
        st.session_state["process_outcome"] = run_process(
            sheet_photo.getvalue(), parsed, AttendanceRepository(), overwrite=False
        )

outcome = st.session_state.get("process_outcome")

# --- UX-DR5: overwrite gate (modal-style) ------------------------------------
if outcome is not None and outcome.needs_overwrite_choice:
    st.warning(OVERWRITE_PROMPT)
    keep_col, overwrite_col = st.columns(2)
    keep = keep_col.button("Keep resolutions", type="primary", width="stretch")
    replace = overwrite_col.button("Overwrite everything", width="stretch")
    if keep or replace:
        with st.spinner("Reading the sheet…"):
            st.session_state["process_outcome"] = run_process(
                sheet_photo.getvalue(),
                parsed,
                AttendanceRepository(),
                overwrite=replace,
                overwrite_decided=True,
            )
        st.rerun()

# --- Outcome surface ---------------------------------------------------------
elif outcome is not None and outcome.error:
    st.error(outcome.error)  # inputs stay in their slots for fix-and-retry
elif outcome is not None and outcome.result is not None:
    result = outcome.result
    saved = result.persisted_count if result.persisted_count is not None else len(result.records)
    st.success(f"Saved {saved} attendance records for sheet {result.sheet_id}.")
    for warning in result.warnings:
        st.warning(warning)
    st.caption("Open the results below in the next update, or look a student up now.")
