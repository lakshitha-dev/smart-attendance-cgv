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
from webui.investigate_logic import display_score, investigate, verdict_sentence

# st.set_page_config lives in app.py — the router owns the single call.
st.title("Check a signature")


def _score_scale(score_0_100: int, threshold_0_100: int, matched: bool):
    """A 0-100 score line with the decision threshold marked (UX-DR11).

    Rendering lives in the adapter (AD-7); the engine's stored score/threshold
    stay 0-1. Colour follows the verdict but never carries it alone — the number
    and the verdict sentence do that too (UX-DR8)."""
    import matplotlib.pyplot as plt

    colour = "#256E4C" if matched else "#A63D2A"
    fig, ax = plt.subplots(figsize=(8, 1.2))
    ax.hlines(0, 0, 100, color="#B9B4A6", linewidth=6, zorder=1)
    ax.axvline(threshold_0_100, color="#33383F", linestyle="--", linewidth=2, zorder=2)
    ax.annotate(
        f"Threshold · {threshold_0_100}",
        (threshold_0_100, 0.6),
        ha="center",
        fontsize=9,
        color="#33383F",
    )
    ax.scatter([score_0_100], [0], s=320, color=colour, zorder=3)
    ax.annotate(
        str(score_0_100),
        (score_0_100, 0),
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
        zorder=4,
    )
    ax.set_xlim(0, 100)
    ax.set_ylim(-1, 1.2)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Similarity score (0–100)")
    for spine in ("left", "right", "top"):
        ax.spines[spine].set_visible(False)
    fig.tight_layout()
    return fig


def _render_found(result) -> None:
    """Side-by-side reference vs probe, the score scale, and the verdict (AD-9)."""
    best = result.best
    ref_caption = f"Reference Signature ({result.student_index})"
    probe_caption = f"Signature from sheet {result.probe_sheet_id}"

    left, right = st.columns(2)
    # Square-corner evidence images (DESIGN.md Shapes): captions double as the
    # accessible description of each crop (UX-DR15).
    with left:
        st.image(best.reference_path, caption=ref_caption, use_container_width=True)
    with right:
        st.image(result.probe_path, caption=probe_caption, use_container_width=True)

    score = display_score(best.score)
    threshold = display_score(result.threshold)
    st.pyplot(_score_scale(score, threshold, result.matched))
    import matplotlib.pyplot as plt

    plt.close("all")  # long-lived server: never accumulate figures

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
                    use_container_width=True,
                )


alias = st.text_input("Student number").strip()

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
