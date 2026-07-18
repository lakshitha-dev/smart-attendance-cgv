"""Process page — the landing (Stories 4.1/4.2/4.3, FR-12/FR-13/UX-DR3–8/DR12):
two labelled file slots, one Process button, the one-tap processing run fenced
so Streamlit reruns never re-trigger it, the streaming stage strip, and the
results row list. ZERO engine logic here (AD-1/AD-8) — `webui/process_logic.py`
sequences the engine calls and owns the copy; this page is widgets +
session-state fencing + rendering only."""

import html
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import streamlit as st

from sams_core import config
from webui.process_logic import (
    MUTED_INK,
    OVERWRITE_PROMPT,
    STAGE_COUNT,
    STATUS_CHIP,
    check_image,
    needs_overwrite,
    parse_info,
    result_banners,
    results_summary,
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
    st.session_state.pop("process_stages", None)  # strip descriptors describe the OLD inputs
    st.session_state.pop("_overwrite_run", None)

# UX-DR4: one full-width primary Process button, disabled until inputs ready.
process_clicked = st.button("Process", type="primary", width="stretch", disabled=not inputs_ok)


def _overline(text: str) -> None:
    """The system's one overline (DESIGN.md): muted-ink, uppercase, tracked."""
    st.markdown(
        f"<div style='color:{MUTED_INK};font-weight:700;font-size:0.8rem;"
        f"letter-spacing:0.06em'>{html.escape(text)}</div>",
        unsafe_allow_html=True,
    )


def _stream_run(image_bytes, parsed_info, overwrite):
    """Run the engine while streaming each StageArtifact into an st.status strip
    (UX-DR6: the strip IS the loading state, no indeterminate spinner). Only
    called once the overwrite decision is settled, so it never flashes for a
    sheet still awaiting a Keep/Overwrite choice. Records the stage descriptors
    so a later rerun re-renders the strip from disk without re-processing.
    Images come solely from the engine emission (AD-2 RGB, st.image as-is)."""
    stages: list[tuple[int, str, str]] = []
    with st.status("Reading your photo…", expanded=True) as status:
        _overline("WHAT WE DID WITH YOUR PHOTO")
        current = st.empty()

        def _on_stage(stage) -> None:
            stages.append((stage.order, stage.slug, stage.label))
            # Current stage named in muted ink while running (UX-DR6/Dev Notes).
            current.markdown(
                f"<span style='color:{MUTED_INK}'>Reading your photo… "
                f"({html.escape(stage.label)})</span>",
                unsafe_allow_html=True,
            )
            st.image(
                stage.image,
                caption=f"Stage {stage.order} of {STAGE_COUNT} — {stage.label}",
                width="stretch",
            )

        outcome = run_process(
            image_bytes,
            parsed_info,
            AttendanceRepository(),
            overwrite=overwrite,
            overwrite_decided=True,  # the gate already ran; don't re-check
            on_stage=_on_stage,
        )
        if outcome.result is not None:
            status.update(label="All finished", state="complete")
        else:
            status.update(label="Couldn't finish that one", state="error")
    if outcome.result is not None:
        st.session_state["process_stages"] = (outcome.sheet_id, stages)
    return outcome


def _render_saved_strip() -> None:
    """Re-render the completed strip from disk on reruns (no reprocessing) —
    each stage in a labelled expander (UX-DR6)."""
    saved = st.session_state.get("process_stages")
    if not saved:
        return
    sheet_id, stages = saved
    _overline("WHAT WE DID WITH YOUR PHOTO")
    for order, slug, label in stages:
        png = config.OUTPUT_DIR / str(sheet_id) / f"{order:02d}-{slug}.png"
        with st.expander(f"Stage {order} of {STAGE_COUNT} — {label}"):
            if png.exists():
                st.image(str(png), caption=f"Stage {order} of {STAGE_COUNT} — {label}")
            else:
                st.caption("This stage image is no longer on disk.")


def _row_html(record) -> str:
    """One results row (UX-DR7): name (label) + Student Index (caption, tabular
    figures) + right-aligned status chip (icon + label + colour, no fill —
    UX-DR8). Untrusted name/index are HTML-escaped, so a name carrying markdown
    or markup can neither format nor inject."""
    icon, label, colour = STATUS_CHIP[record.status]
    name = html.escape(record.student_name or record.student_index)
    index = html.escape(record.student_index)
    return (
        "<div class='sams-row' style='display:flex;justify-content:space-between;"
        "align-items:baseline;gap:12px'>"
        f"<div><strong>{name}</strong><br>"
        f"<span style='color:{MUTED_INK};font-variant-numeric:tabular-nums;"
        f"font-size:0.85em'>{index}</span></div>"
        f"<div style='text-align:right;white-space:nowrap'>"
        f"<span style='color:{colour};font-weight:600'>{icon} {label}</span></div>"
        "</div>"
    )


def _render_results(result) -> None:
    """UX-DR7 results: completion line, summary, one saved notice, flag banners
    above the list, then a container row per Student Record."""
    if not result.records:
        st.info("We finished, but couldn't find any students on that sheet — "
                "check the photo shows the full signing table, then try again.")
        return

    st.subheader("All finished — your results are below.")
    st.write(results_summary(result.records))
    st.caption("Results saved.")  # stated exactly once (engine already persisted)

    for banner in result_banners(result):  # prominent flags, not failures
        st.warning(banner)

    for record in result.records:
        st.markdown(_row_html(record), unsafe_allow_html=True)


def _settle_after(outcome) -> None:
    """Store the outcome and, on success, rerun so the streamed strip settles
    into the stable collapsed-expander view (and never re-processes)."""
    st.session_state["process_outcome"] = outcome
    if outcome.result is not None:
        st.rerun()


# --- Fence: process on the button-press rerun only ---------------------------
# st.button returns True only on the single rerun following the press. The
# overwrite gate is checked BEFORE any streaming so a sheet awaiting a choice
# never flashes a strip; the chosen run then streams like any other.
if process_clicked and inputs_ok:
    image_bytes = sheet_photo.getvalue()
    if needs_overwrite(parsed, AttendanceRepository()):
        st.session_state["pending_overwrite"] = {"image": image_bytes, "parsed": parsed}
        st.session_state["process_outcome"] = None  # no result yet; show the gate
    else:
        _settle_after(_stream_run(image_bytes, parsed, overwrite=False))

# An overwrite decision made in the dialog runs (and streams) here, on the main
# page rather than inside the modal.
if "_overwrite_run" in st.session_state:
    replace = st.session_state.pop("_overwrite_run")
    pending = st.session_state.pop("pending_overwrite", None)
    if pending is not None:
        _settle_after(_stream_run(pending["image"], pending["parsed"], overwrite=replace))

outcome = st.session_state.get("process_outcome")


@st.dialog("You've already reviewed this sheet")
def _overwrite_dialog():
    """UX-DR5 overwrite gate — modal-style, centered. Records the choice and
    reruns; the run itself streams on the main page (above), acting on the
    captured snapshot so a mid-gate slot change can't redirect it."""
    st.write(OVERWRITE_PROMPT)
    keep_col, replace_col = st.columns(2)
    keep = keep_col.button("Keep resolutions", type="primary", width="stretch")
    replace = replace_col.button("Overwrite everything", width="stretch")
    if keep or replace:
        st.session_state["_overwrite_run"] = bool(replace)
        st.rerun()


# --- Outcome surface ---------------------------------------------------------
if st.session_state.get("pending_overwrite") is not None and (
    outcome is None or outcome.needs_overwrite_choice
):
    _overwrite_dialog()
elif outcome is not None and outcome.error:
    st.error(outcome.error)  # inputs stay in their slots for fix-and-retry
elif outcome is not None and outcome.result is not None:
    # Settled rerun (no fresh click): re-render the strip collapsed from disk so
    # the view is stable and reprocessing never happens.
    if not process_clicked:
        _render_saved_strip()
    _render_results(outcome.result)
