"""Investigate page (Story 4.6, FR-14): thin adapter — input, the engine
verification (Epic 3's single call via `investigate_logic.investigate`), then
render the returned `VerificationResult` side by side. ZERO comparison,
best-match, or no-data copy logic lives here (AD-1/AD-9) —
`investigate_logic.py` owns the copy, `sams_core/verification.py` owns the
score and the best-match selection. The page only displays `result.best` and
an expander of `result.all_scores` (AD-9)."""

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import matplotlib

matplotlib.use("Agg")  # server-side render only: never a GUI backend in a
# Streamlit worker thread. The score scale below is rasterized by st.pyplot.

import streamlit as st

from sams_core.errors import SamsError
from sams_core.repository import AttendanceRepository
from sams_core.visualization import render_score_scale
from webui.investigate_logic import display_score, investigate, verdict_sentence

# st.set_page_config lives in app.py — the router owns the single call.
st.title("Check a signature")


def _render_found(result) -> None:
    """Side-by-side reference vs probe, the score scale, and the verdict (AD-9)."""
    best = result.best
    ref_caption = f"Reference Signature ({result.student_index})"
    probe_caption = f"Signature from sheet {result.probe_sheet_id}"

    left, right = st.columns(2)
    # Square-corner evidence images (DESIGN.md Shapes): captions double as the
    # accessible description of each crop (UX-DR15).
    with left:
        st.image(best.reference_path, caption=ref_caption, width="stretch")
    with right:
        st.image(result.probe_path, caption=probe_caption, width="stretch")

    score = display_score(best.score)
    threshold = display_score(result.threshold)
    fig = render_score_scale(score, threshold, result.matched)
    # Keyed so the phone breakpoint can hold the scale at a legible width and
    # pan it, rather than scaling an 8in-wide figure into a ~366px column.
    with st.container(key="sams_chart"):
        st.pyplot(fig)
    import matplotlib.pyplot as plt

    plt.close(fig)  # long-lived server: never accumulate figures

    st.subheader(verdict_sentence(result.matched))
    st.caption("Compared against their best-matching Reference Signature.")
    st.caption("The score and threshold here are the same ones the class records tool uses.")

    others = [s for s in result.all_scores if s is not best]
    if others:
        with st.expander(f"Other reference signatures ({len(others)})"):
            for other in others:
                st.image(
                    other.reference_path,
                    caption=f"Reference from sheet {other.sheet_id} — score {display_score(other.score)}",
                    width="stretch",
                )


# Keyed so the Dashboard's signature alerts can prefill the student before
# switching here (SAMS design: alert rows deep-link to this check).
alias = st.text_input(
    "Student number", key="investigate_alias", placeholder="e.g. 001 or 10000409"
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
        st.session_state["investigate_alias"] = value

    options = list(dict.fromkeys((s["no"] or s["student_index"]) for s in _roster))[:12]
    with st.container(key="quick_pick"):
        columns = st.columns(max(len(options), 6))
        for column, option in zip(columns, options):
            column.button(option, key=f"pick_{option}", on_click=_pick, args=(option,))

if not alias:
    st.write("Type a student's number to check their signature.")
else:
    outcome = None
    with st.spinner("Comparing signatures…"):
        try:
            outcome = investigate(alias, AttendanceRepository())
        except SamsError:
            st.error("Something went wrong reading the saved records.")
        except Exception:  # AD-6: no raw traceback may reach the browser
            st.error("Something went wrong reading the saved records.")

    if outcome is not None:
        if outcome.message:
            st.write(outcome.message)
        elif outcome.result is not None:
            _render_found(outcome.result)
