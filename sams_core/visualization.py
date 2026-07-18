"""Attendance timeline chart (FR-8, AD-7): renders per-Session Present/Absent
history from Attendance Records already in hand — no DB access, no image
re-processing.

`render_attendance_timeline` returns a Matplotlib `Figure` and never calls
`plt.show()`: the CLI adapter (`infovis.py`, via `cli_display.show_figure`)
displays it, and the Web UI renders the identical `Figure` object via
`st.pyplot` (FR-14 data-layer parity) — styling lives here exactly once.

Backend note: when SAMS_HEADLESS is set (any value but 0/false/no), the Agg
backend is forced BEFORE pyplot ever loads, so headless machines and worker
threads never initialize a GUI toolkit. Callers own the figure lifecycle and
must `plt.close(fig)` when done — long-lived processes (Streamlit) leak
otherwise.
"""

import os
from collections.abc import Sequence
from datetime import date

import matplotlib

if os.environ.get("SAMS_HEADLESS", "0").lower() not in ("0", "", "false", "no"):
    matplotlib.use("Agg", force=True)

from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from sams_core.errors import InputError
from sams_core.models import AttendanceRecord, AttendanceStatus

# Status -> (y-position, colour, icon, legend label). Ambiguous sits on its
# own mid-band (y=0) strictly between Absent (-1) and Present (1). Colours
# and icons per UX-DR8: icon + text + colour together, colour never the sole
# carrier (greyscale-survivable). The y-axis ticks are DERIVED from this
# table (single source of truth — never a parallel hardcoded copy).
_STATUS_STYLE = {
    AttendanceStatus.ABSENT: {"y": -1, "color": "#A63D2A", "icon": "✕", "label": "Absent"},
    AttendanceStatus.AMBIGUOUS: {"y": 0, "color": "#7A6212", "icon": "?", "label": "Ambiguous"},
    AttendanceStatus.PRESENT: {"y": 1, "color": "#256E4C", "icon": "✓", "label": "Present"},
}
# Legend reads Present / Absent / Ambiguous (AC order), independent of y-position order.
_LEGEND_ORDER = (AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.AMBIGUOUS)


def _attendance_rate_caption(records: Sequence[AttendanceRecord]) -> str:
    """Present / (Present + Absent); Ambiguous is pending and excluded from
    both sides of the ratio (Dev Notes), reported separately instead. With
    zero marked sessions the rate is n/a — an all-Ambiguous student must
    never be branded 0%."""
    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    ambiguous = sum(1 for r in records if r.status == AttendanceStatus.AMBIGUOUS)
    counted = present + absent
    rate = f"{present / counted * 100:.0f}%" if counted else "n/a"
    caption = f"Attendance rate: {rate} ({present}/{counted} sessions marked"
    if ambiguous:
        caption += f", {ambiguous} pending)"
    else:
        caption += ")"
    return caption


def _chronology_key(record: AttendanceRecord) -> tuple:
    """ISO-dated Sheet Identifiers sort chronologically; AD-11's
    filename-derived identifiers can't be dated, so they sort
    lexicographically AFTER all dated sheets rather than interleaving
    wrongly among them."""
    try:
        return (0, date.fromisoformat(record.sheet_id).toordinal(), record.sheet_id)
    except (TypeError, ValueError):
        return (1, 0, record.sheet_id)


def render_score_distribution(
    genuine_scores: Sequence[float],
    impostor_scores: Sequence[float],
    threshold: float,
) -> Figure:
    """Genuine-vs-impostor similarity histograms with the threshold line (Story 3.3).

    Justifies the `SIMILARITY_THRESHOLD` choice visually: genuine probe scores
    (a student's own probe vs their References) should sit RIGHT of the line and
    impostor scores (other students' probes) LEFT of it. Overlap across the line
    is the honest error the report reads off this figure. Returns a Matplotlib
    `Figure` (never shown here — the adapter/test owns display and closing),
    styled to match the attendance timeline: colour + label together, never
    colour alone (UX-DR8). At least one distribution must be non-empty.
    """
    if not len(genuine_scores) and not len(impostor_scores):
        raise InputError("no similarity scores to plot — nothing to draw")

    import matplotlib.pyplot as plt

    genuine = list(genuine_scores)
    impostor = list(impostor_scores)
    # Shared bins across 0-1 so the two distributions are directly comparable.
    bins = [i / 20 for i in range(21)]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    if impostor:
        ax.hist(
            impostor,
            bins=bins,
            color="#A63D2A",
            alpha=0.6,
            label=f"Impostor probes (n={len(impostor)})",
        )
    if genuine:
        ax.hist(
            genuine,
            bins=bins,
            color="#256E4C",
            alpha=0.6,
            label=f"Genuine probes (n={len(genuine)})",
        )
    ax.axvline(
        threshold,
        color="#33383F",
        linestyle="--",
        linewidth=2,
        label=f"Threshold = {threshold:.2f}",
    )

    ax.set_xlim(0.0, 1.0)
    ax.set_xlabel("Similarity score (0 = unlike, 1 = identical)")
    ax.set_ylabel("Number of comparisons")
    ax.set_title("Signature verification — genuine vs impostor score distribution")
    ax.legend(loc="upper right", frameon=False)
    fig.tight_layout()
    return fig


def render_attendance_timeline(records: Sequence[AttendanceRecord]) -> Figure:
    """Render one student's per-Session attendance timeline (FR-8).

    `records` is one student's Attendance Records (Story 2.1's
    `query_attendance` result) and must be non-empty; order is not assumed —
    sorted here so the timeline reads chronologically left to right.
    """
    if not records:
        raise InputError("no Attendance Records to render — nothing to draw")

    import matplotlib.pyplot as plt

    ordered = sorted(records, key=_chronology_key)
    x_positions = range(len(ordered))
    y_positions = [_STATUS_STYLE[r.status]["y"] for r in ordered]
    colors = [_STATUS_STYLE[r.status]["color"] for r in ordered]

    # Width scales with session count so a semester of sheets stays legible.
    width = min(24.0, max(8.0, 0.55 * len(ordered)))
    fig, ax = plt.subplots(figsize=(width, 4.5))
    # steps-mid: statuses are categorical — a diagonal line would render
    # Ambiguous as a quantity "halfway between" Absent and Present.
    ax.plot(
        x_positions,
        y_positions,
        color="#B9B4A6",
        linewidth=1,
        zorder=1,
        drawstyle="steps-mid",
    )
    ax.scatter(x_positions, y_positions, c=colors, s=140, zorder=3)
    for xi, record in zip(x_positions, ordered):
        style = _STATUS_STYLE[record.status]
        ax.annotate(
            style["icon"],
            (xi, style["y"]),
            ha="center",
            va="center",
            color="white",
            fontsize=9,
            fontweight="bold",
            zorder=4,
        )

    ax.set_xticks(list(x_positions))
    ax.set_xticklabels([r.sheet_id for r in ordered], rotation=45, ha="right")
    # y ticks derived from _STATUS_STYLE — the one mapping (bottom-up order).
    bands = sorted(_STATUS_STYLE.values(), key=lambda s: s["y"])
    ax.set_yticks([band["y"] for band in bands])
    ax.set_yticklabels([band["label"] for band in bands])
    # Extra headroom above the Present band: the legend lives there, outside
    # the data's reach, so it can never occlude the most recent markers.
    ax.set_ylim(-1.9, 2.3)
    ax.set_xlabel("Session (Sheet Identifier)")
    ax.set_ylabel("Status")

    student = ordered[0]
    ax.set_title(f"Attendance timeline — {student.student_name} ({student.student_index})")

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="",
            markersize=10,
            markerfacecolor=_STATUS_STYLE[status]["color"],
            markeredgecolor=_STATUS_STYLE[status]["color"],
            label=f"{_STATUS_STYLE[status]['icon']} {_STATUS_STYLE[status]['label']}",
        )
        for status in _LEGEND_ORDER
    ]
    ax.legend(handles=handles, loc="upper center", ncol=3, frameon=False)

    # Figure-level caption in layout-reserved space (an axes-transform text
    # below the axes is invisible to tight_layout and clips under long ticks).
    fig.text(
        0.5,
        0.02,
        _attendance_rate_caption(ordered),
        ha="center",
        fontsize=10,
        color="#33383F",
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return fig


def render_score_scale(score_0_100: int, threshold_0_100: int, matched: bool) -> Figure:
    """A 0-100 similarity-score line with the decision threshold marked
    (UX-DR11, Story 4.6/4.1 review): figure construction lives in the engine's
    visualization module exactly once (AD-7) — pages only display it. Colour
    follows the verdict but never carries it alone; the number and the verdict
    sentence do that too (UX-DR8). Callers own closing the figure."""
    import matplotlib.pyplot as plt

    colour = (
        _STATUS_STYLE[AttendanceStatus.PRESENT]["color"]
        if matched
        else _STATUS_STYLE[AttendanceStatus.ABSENT]["color"]
    )
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
