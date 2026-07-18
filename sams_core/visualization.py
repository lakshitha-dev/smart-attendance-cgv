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

# Shared chart chrome (DESIGN.md "Quiet Clerk"): calm and minimal, styled once
# so the CLI figure and the identical Web `st.pyplot` figure read the same. The
# axes sit transparently on the app surface (no boxed black frame), guides are
# hairline, labels muted ink. Status hues stay exactly as _STATUS_STYLE defines
# them — chrome is neutral, colour still means only status.
_CHART_INK = "#33383F"  # ink-primary
_CHART_MUTED = "#7B818A"  # ink-muted: axis labels, ticks, captions
_CHART_HAIRLINE = "#E9E8E3"  # border-hairline: spines + grid
_CHART_GUIDE = "#C4BFB2"  # the quiet connector line between session marks
_CHART_TRACK = "#E4E0D5"  # the score-scale baseline track
_CHART_ACCENT = "#4F46E5"  # indigo accent for chart titles (matches the UI action colour)
# Soft status-tinted zones behind the timeline — colour that reinforces the
# Present / Ambiguous / Absent meaning of each row, not decoration.
_BAND_PRESENT = "#E7F3EC"
_BAND_AMBIGUOUS = "#F7F1DA"
_BAND_ABSENT = "#F6E7E2"


def _style_axes(ax, keep_spines=("left", "bottom"), grid_axis=None):
    """Apply the shared Quiet Clerk chrome to an Axes: transparent background,
    top/right spines dropped, the kept spines and any grid drawn as hairlines,
    ticks and axis labels in muted ink. Never touches the data artists, so the
    UX-locked status colours/positions are unaffected."""
    ax.figure.patch.set_alpha(0.0)
    ax.set_facecolor("none")
    for side, spine in ax.spines.items():
        if side in keep_spines:
            spine.set_visible(True)
            spine.set_color(_CHART_HAIRLINE)
            spine.set_linewidth(1.0)
        else:
            spine.set_visible(False)
    ax.tick_params(colors=_CHART_MUTED, labelcolor=_CHART_INK, length=0)
    ax.xaxis.label.set_color(_CHART_MUTED)
    ax.yaxis.label.set_color(_CHART_MUTED)
    if grid_axis is not None:
        ax.grid(axis=grid_axis, color=_CHART_HAIRLINE, linewidth=0.9, zorder=0)
        ax.set_axisbelow(True)


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
    ax.set_title(
        "Signature verification — genuine vs impostor score distribution",
        color=_CHART_ACCENT,
        fontsize=12.5,
        fontweight="700",
    )
    ax.legend(loc="upper right", frameon=False, labelcolor=_CHART_INK)
    _style_axes(ax, keep_spines=("left", "bottom"), grid_axis="y")
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
    # Soft status-tinted zones behind each row (Polygons via axhspan — patches,
    # not collections, so the scatter stays ax.collections[0]).
    ax.axhspan(0.5, 1.9, color=_BAND_PRESENT, zorder=0)
    ax.axhspan(-0.5, 0.5, color=_BAND_AMBIGUOUS, zorder=0)
    ax.axhspan(-1.9, -0.5, color=_BAND_ABSENT, zorder=0)
    # steps-mid: statuses are categorical — a diagonal line would render
    # Ambiguous as a quantity "halfway between" Absent and Present.
    ax.plot(
        x_positions,
        y_positions,
        color=_CHART_GUIDE,
        linewidth=1.4,
        zorder=1,
        drawstyle="steps-mid",
    )
    # White marker edge lifts each mark off the guide line and grid.
    ax.scatter(
        x_positions, y_positions, c=colors, s=150, zorder=3, edgecolors="white", linewidths=1.5
    )
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
    ax.set_title(
        f"Attendance timeline — {student.student_name} ({student.student_index})",
        color=_CHART_ACCENT,
        fontsize=13.5,
        fontweight="700",
        pad=30,
    )

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
    ax.legend(
        handles=handles, loc="upper center", ncol=3, frameon=False, labelcolor=_CHART_INK, fontsize=10
    )

    # Colour-tinted status bands are the guides now, so keep only a hairline
    # bottom spine — no grid, no boxed frame.
    _style_axes(ax, keep_spines=("bottom",), grid_axis=None)

    # Figure-level caption in layout-reserved space (an axes-transform text
    # below the axes is invisible to tight_layout and clips under long ticks).
    fig.text(
        0.5,
        0.02,
        _attendance_rate_caption(ordered),
        ha="center",
        fontsize=10,
        color=_CHART_MUTED,
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
    import numpy as np

    fig, ax = plt.subplots(figsize=(8, 1.2))
    # Colour the track itself: a red -> amber -> green similarity gradient, so
    # the score's position reads as "how similar" at a glance. The verdict dot
    # colour and the number still carry the decision (colour never alone).
    # pcolormesh is a figure-drawing call (not the banned cv2 GUI display path),
    # so it renders the gradient into the axes without a window.
    x_edges = np.linspace(0, 100, 257)
    ax.pcolormesh(
        x_edges,
        [-0.34, 0.34],
        np.linspace(0, 1, 256).reshape(1, -1),
        cmap="RdYlGn",
        shading="flat",
        zorder=1,
        alpha=0.92,
    )
    ax.axvline(threshold_0_100, color=_CHART_INK, linestyle="--", linewidth=1.6, zorder=3)
    ax.annotate(
        f"Threshold · {threshold_0_100}",
        (threshold_0_100, 0.6),
        ha="center",
        fontsize=9,
        color=_CHART_MUTED,
    )
    # White edge lifts the score dot off the gradient track.
    ax.scatter([score_0_100], [0], s=380, color=colour, zorder=5, edgecolors="white", linewidths=2.5)
    ax.annotate(
        str(score_0_100),
        (score_0_100, 0),
        ha="center",
        va="center",
        color="white",
        fontsize=10,
        fontweight="bold",
        zorder=6,
    )
    ax.set_xlim(0, 100)
    ax.set_ylim(-1, 1.2)
    ax.set_yticks([])
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Similarity score (0–100)")
    _style_axes(ax, keep_spines=())
    fig.tight_layout()
    return fig
