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
from webui.process_logic import (
    OVERWRITE_PROMPT,
    check_image,
    parse_info,
    run_process,
)

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


def _memo(key: str, token, compute):
    """Cache a computed value against a token (a file id / date) in session
    state so scroll/expand reruns don't re-decode the image or re-parse the
    XML; recompute only when the token changes."""
    store = st.session_state.setdefault("_memo", {})
    if store.get(key, (None,))[0] != token:
        store[key] = (token, compute())
    return store[key][1]


# UX-DR3: two labelled slots.
sheet_photo = st.file_uploader("Signing Sheet", type=["jpeg", "jpg", "png"])
st.caption("JPEG or PNG. On iPhone, choose 'Most Compatible' or export the photo as JPEG.")
_ready_note(sheet_photo)

# UX-DR12 item #1: slot-level image error, before Process (decode-level only).
image_error = None
if _slot_ready(sheet_photo):
    image_error = _memo(
        "image", sheet_photo.file_id, lambda: check_image(sheet_photo.getvalue())
    )
    if image_error:
        st.error(image_error)

info_file = st.file_uploader("Info File", type=["xml"])
_ready_note(info_file)

# AD-11: a date field appears ONLY when the uploaded Info File lacks a session
# date — and the Web UI never falls back to the upload filename.
session_date = None
parsed = None
if _slot_ready(info_file):
    parsed = _memo(
        "info", info_file.file_id, lambda: parse_info(info_file.getvalue())
    )
    if parsed.error:
        st.error(parsed.error)
    elif parsed.needs_date:
        # Keyed to the file id so a different dateless file never inherits the
        # previous file's typed date.
        session_date = st.text_input(
            "Session date (YYYY-MM-DD)",
            key=f"session_date_{info_file.file_id}",
            help="This sheet's info file has no session date, so please enter it.",
        )
        parsed = parse_info(info_file.getvalue(), session_date=session_date or None)
        if parsed.error:
            st.error(parsed.error)  # show BAD_DATE for a bad manually-typed date

both_ready = _slot_ready(sheet_photo) and _slot_ready(info_file)
date_ready = parsed is not None and parsed.sheet_id is not None
inputs_ok = both_ready and date_ready and image_error is None and parsed.error is None

# Staleness: a stored outcome describes the inputs it ran on. If the inputs
# changed (new upload, cleared slot, edited date), drop the stale banner/gate
# so the page never asserts a save for files no longer loaded.
current_sig = (
    getattr(sheet_photo, "file_id", None),
    getattr(info_file, "file_id", None),
    session_date,
)
if st.session_state.get("_input_sig") != current_sig:
    st.session_state["_input_sig"] = current_sig
    st.session_state.pop("process_outcome", None)
    st.session_state.pop("pending_overwrite", None)

# UX-DR4: one full-width primary Process button, disabled until inputs ready.
process_clicked = st.button("Process", type="primary", width="stretch", disabled=not inputs_ok)


def _run(overwrite: bool, overwrite_decided: bool, image_bytes, parsed_info):
    with st.spinner("Reading the sheet…"):
        return run_process(
            image_bytes,
            parsed_info,
            AttendanceRepository(),
            overwrite=overwrite,
            overwrite_decided=overwrite_decided,
        )


# --- Fence: process on the button-press rerun only ---------------------------
# st.button returns True only on the single rerun following the press, so the
# engine call happens once per tap; other reruns skip this branch and re-render
# the stored outcome (AC: zero re-processing).
if process_clicked and inputs_ok:
    outcome = _run(False, False, sheet_photo.getvalue(), parsed)
    if outcome.needs_overwrite_choice:
        # Capture the exact inputs the warning is about, so the operator's
        # later choice acts on THESE files even if the slots change meanwhile.
        st.session_state["pending_overwrite"] = {
            "image": sheet_photo.getvalue(),
            "parsed": parsed,
        }
    st.session_state["process_outcome"] = outcome

outcome = st.session_state.get("process_outcome")


@st.dialog("You've already reviewed this sheet")
def _overwrite_dialog():
    """UX-DR5 overwrite gate — modal-style, centered. Acts on the captured
    snapshot, never the live widgets, so a mid-gate slot change can't redirect
    the decision to a different sheet."""
    pending = st.session_state.get("pending_overwrite")
    st.write(OVERWRITE_PROMPT)
    keep_col, replace_col = st.columns(2)
    keep = keep_col.button("Keep resolutions", type="primary", width="stretch")
    replace = replace_col.button("Overwrite everything", width="stretch")
    if (keep or replace) and pending is not None:
        st.session_state["process_outcome"] = _run(
            replace, True, pending["image"], pending["parsed"]
        )
        st.session_state.pop("pending_overwrite", None)
        st.rerun()


# --- Outcome surface ---------------------------------------------------------
if outcome is not None and outcome.needs_overwrite_choice:
    _overwrite_dialog()
elif outcome is not None and outcome.error:
    st.error(outcome.error)  # inputs stay in their slots for fix-and-retry
elif outcome is not None and outcome.result is not None:
    result = outcome.result
    saved = result.persisted_count if result.persisted_count is not None else len(result.records)
    kept = result.preserved_count or 0
    total = saved + kept
    message = f"Saved attendance for {total} students on sheet {result.sheet_id}."
    if kept:
        message += f" {kept} kept from your earlier fixes."
    st.success(message)
    for warning in result.warnings:
        st.warning(warning)
    st.caption("Look a student up now, or the full results arrive in the next update.")
